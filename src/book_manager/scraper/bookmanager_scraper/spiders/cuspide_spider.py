"""Spider de Cúspide para Book Manager.

El spider consulta el sitio de Cúspide una vez por cada título del catálogo
propio (nunca se buscan libros que no estén en el catálogo) y, para cada
título, se queda únicamente con los diez primeros resultados devueltos.

De cada ficha de producto extrae el precio (en pesos y en dólares), la URL de
la imagen, las formas de pago y la descripción detallada. La lectura de esos
datos se hace con `ItemLoader`, que aplica los procesadores de normalización
de `bookmanager_scraper.items` a cada valor antes de armar el item.
"""

import csv
import datetime
import re
from pathlib import Path
from typing import Any, Iterable, List, Optional
from urllib.parse import quote_plus

import scrapy
from itemloaders import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst

from bookmanager_scraper.catalogo import (
    COINCIDENCIA_EXACTA,
    CatalogoInterno,
    normalizar_para_comparar,
)
from bookmanager_scraper.items import (
    LibroCuspideItem,
    limpiar_formas_pago,
    limpiar_texto,
    normalizar_isbn,
    precio_a_float,
    unir_textos,
)

# Carpeta con los CSV del catálogo propio (migrations/csv).
DIRECTORIO_CSVS = Path(__file__).resolve().parents[3] / "migrations" / "csv"
ARCHIVO_CATALOGO = DIRECTORIO_CSVS / "libros.csv"

# Cantidad máxima de resultados considerados por cada título.
MAXIMO_RESULTADOS_POR_TITULO = 10

# Plantilla por defecto de la URL de búsqueda. La configuración del proyecto
# Scrapy puede sobrescribirla mediante la variable URL_BUSQUEDA.
URL_BUSQUEDA_POR_DEFECTO = "https://cuspide.com/?s={titulo}&post_type=product"

# Expresión regular que valida un enlace a la ficha de un producto.
RE_ENLACE_PRODUCTO = re.compile(r"^https?://[^/]+/producto/[^/]+/?$")


class CuspideSpider(scrapy.Spider):
    """Obtiene los datos públicos de los libros del catálogo en Cúspide."""

    name = "cuspide"

    def __init__(
        self,
        archivo_catalogo: Optional[str] = None,
        titulo: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        """Inicializa el spider con el catálogo propio a consultar.

        Args:
            archivo_catalogo (Optional[str]): Ruta alternativa al CSV de libros.
                Si no se indica se usa `migrations/csv/libros.csv`.
            titulo (Optional[str]): Si se indica, se consulta únicamente ese
                título del catálogo en lugar de todos.
            *args: Argumentos adicionales de Scrapy.
            **kwargs: Argumentos adicionales de Scrapy.
        """
        super().__init__(*args, **kwargs)
        self.archivo_catalogo = (
            Path(archivo_catalogo) if archivo_catalogo else ARCHIVO_CATALOGO
        )
        self.titulo_filtrado = titulo
        self.url_base = URL_BUSQUEDA_POR_DEFECTO
        self.catalogo: Optional[CatalogoInterno] = None

    @classmethod
    def from_crawler(cls, crawler: Any, *args, **kwargs) -> "CuspideSpider":
        """Construye el spider tomando la configuración del proyecto Scrapy.

        Scrapy inyecta `settings` recién después de construir el spider, por
        lo que la URL de búsqueda se aplica en este punto y no en `__init__`.

        Args:
            crawler (Any): Crawler que instancia el spider.
            *args: Argumentos adicionales de Scrapy.
            **kwargs: Argumentos adicionales de Scrapy.

        Returns:
            CuspideSpider: Spider listo para ejecutarse.
        """
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.url_base = crawler.settings.get("URL_BUSQUEDA", URL_BUSQUEDA_POR_DEFECTO)
        return spider

    # ------------------------------------------------------------------ catálogo
    def titulos_del_catalogo(self) -> List[str]:
        """Lee los títulos de los libros del catálogo propio.

        Returns:
            List[str]: Títulos de los libros del catálogo, en el orden del CSV.
        """
        if not self.archivo_catalogo.exists():
            self.logger.warning(
                "No se encontró el catálogo propio en %s", self.archivo_catalogo
            )
            return []

        titulos: List[str] = []
        with self.archivo_catalogo.open(mode="r", encoding="utf-8-sig", newline="") as archivo:
            for fila in csv.DictReader(archivo):
                titulo = (fila.get("titulo") or "").strip()
                if titulo and titulo not in titulos:
                    titulos.append(titulo)
        return titulos

    def url_de_busqueda(self, titulo: str) -> str:
        """Construye la URL de búsqueda de productos de Cúspide para un título.

        Args:
            titulo (str): Título del libro del catálogo.

        Returns:
            str: URL de la página de resultados.
        """
        return self.url_base.format(titulo=quote_plus(titulo))

    def catalogo_interno(self) -> CatalogoInterno:
        """Devuelve el catálogo propio, cargándolo la primera vez.

        Returns:
            CatalogoInterno: Vista del catálogo con ISBN, título y precios.
        """
        if self.catalogo is None:
            self.catalogo = CatalogoInterno()
        return self.catalogo

    # ----------------------------------------------------------------- requests
    def peticiones_de_busqueda(self) -> Iterable[scrapy.Request]:
        """Construye una petición de búsqueda por cada título del catálogo.

        Returns:
            Iterable[scrapy.Request]: Peticiones de búsqueda, una por título.
        """
        titulos = self.titulos_del_catalogo()
        if self.titulo_filtrado:
            titulos = [t for t in titulos if t == self.titulo_filtrado]
        if not titulos:
            self.logger.warning("El catálogo propio está vacío: no hay nada que consultar.")
            return

        self.logger.info("Consultando %d títulos del catálogo propio", len(titulos))
        for titulo in titulos:
            yield scrapy.Request(
                url=self.url_de_busqueda(titulo),
                callback=self.parse_busqueda,
                cb_kwargs={"titulo_buscado": titulo},
                dont_filter=True,
            )

    async def start(self):
        """Punto de entrada del spider (Scrapy 2.13 o superior)."""
        for peticion in self.peticiones_de_busqueda():
            yield peticion

    def start_requests(self) -> Iterable[scrapy.Request]:
        """Punto de entrada del spider (Scrapy anterior a 2.13)."""
        yield from self.peticiones_de_busqueda()

    # -------------------------------------------------------------------- parseo
    def parse_busqueda(self, response: Any, titulo_buscado: str = ""):
        """Parsea la página de resultados y sigue las fichas de los productos.

        Solo se toman los diez primeros resultados de la búsqueda, que es el
        límite que fija el enunciado. De esos resultados se siguen únicamente
        las fichas cuyo título corresponde a nuestro libro: así no se descarga
        ni se trabaja con obras que no tenemos en el catálogo.

        Args:
            response (Any): Respuesta de la página de resultados.
            titulo_buscado (str): Título consultado.

        Yields:
            scrapy.Request: Peticiones a las fichas de producto.
        """
        tarjetas = response.css("div.products div.product-small")
        self.logger.info(
            "Resultados para '%s': %d encontrados, se toman los primeros %d",
            titulo_buscado,
            len(tarjetas),
            MAXIMO_RESULTADOS_POR_TITULO,
        )

        if not tarjetas and RE_ENLACE_PRODUCTO.match(response.url):
            # El buscador redirigió directamente a la ficha del producto.
            self.logger.info(
                "La búsqueda de '%s' redirigió a la ficha %s", titulo_buscado, response.url
            )
            yield from self.parse_producto(
                response,
                titulo_buscado=titulo_buscado,
                nivel_coincidencia=COINCIDENCIA_EXACTA,
                libro_id=self.catalogo_interno().libro_por_titulo(titulo_buscado),
            )
            return

        # El buscador repite cada producto en la grilla: se sigue una sola vez
        # cada ficha para no descargar dos veces la misma página.
        ya_consultados: set = set()

        for posicion, tarjeta in enumerate(tarjetas[:MAXIMO_RESULTADOS_POR_TITULO], start=1):
            enlace = self._enlace_de_producto(tarjeta)
            if not enlace or enlace in ya_consultados:
                continue

            titulo_producto = self._titulo_de_producto(tarjeta, enlace)
            nivel = CatalogoInterno.nivel_de_coincidencia(titulo_producto, titulo_buscado)
            if nivel is None:
                continue

            libro_id = self.catalogo_interno().libro_por_titulo(titulo_buscado)
            if libro_id is None:
                continue

            ya_consultados.add(enlace)
            self.logger.info(
                "  Candidato: '%s' (nivel %d)", titulo_producto.strip(), nivel
            )
            yield response.follow(
                enlace,
                callback=self.parse_producto,
                cb_kwargs={
                    "titulo_buscado": titulo_buscado,
                    "nivel_coincidencia": nivel,
                    "libro_id": libro_id,
                    "posicion_resultado": posicion,
                },
            )

    @staticmethod
    def _titulo_de_producto(tarjeta: Any, enlace: str) -> str:
        """Obtiene el titulo del producto a partir de una tarjeta de resultado.

        El sitio muestra el resultado en distintos formatos, asi que se prueban
        varias fuentes en orden de fiabilidad:

        1. El texto del elemento que muestra el titulo del producto.
        2. El atributo `aria-label` del enlace al producto.
        3. El texto alternativo de la imagen del producto.
        4. El slug de la direccion, como ultimo recurso.

        Args:
            tarjeta (Any): Tarjeta de resultado del buscador.
            enlace (str): URL de la ficha del producto.

        Returns:
            str: El titulo del producto, o cadena vacia si no se pudo obtener.
        """
        fuentes = (
            tarjeta.css("p.product-title a::text").getall(),
            tarjeta.css("p.woocommerce-loop-product__title a::text").getall(),
            tarjeta.css("a[href*='/producto/']::attr(aria-label)").getall(),
            tarjeta.css("img::attr(alt)").getall(),
        )
        for valores in fuentes:
            for valor in valores:
                if valor and valor.strip():
                    return valor.strip()

        slug = enlace.rstrip("/").rsplit("/", 1)[-1]
        return slug.replace("-", " ").strip()

    @staticmethod
    def _enlace_de_producto(tarjeta: Any) -> Optional[str]:
        """Obtiene el enlace a la ficha de producto de una tarjeta de resultado.

        Args:
            tarjeta (Any): Tarjeta de resultado del buscador.

        Returns:
            Optional[str]: La URL de la ficha, o None si no se encontró.
        """
        for enlace in tarjeta.css("a[href*='/producto/']::attr(href)").getall():
            candidato = (enlace or "").strip()
            if RE_ENLACE_PRODUCTO.match(candidato):
                return candidato
        return None

    def parse_producto(
        self,
        response: Any,
        titulo_buscado: str = "",
        nivel_coincidencia: int = COINCIDENCIA_EXACTA,
        libro_id: Optional[int] = None,
        posicion_resultado: int = 0,
    ):
        """Extrae los datos públicos de la ficha de un producto.

        Los valores se leen con `ItemLoader`, que aplica a cada uno los
        procesadores de normalización correspondientes.

        Args:
            response (Any): Respuesta de la ficha de producto.
            titulo_buscado (str): Título del catálogo que originó la búsqueda.
            nivel_coincidencia (int): Cuán exactamente coincide el título del
                producto con el del catálogo.
            libro_id (Optional[int]): Libro del catálogo al que corresponde.
            posicion_resultado (int): Posición del producto entre los resultados
                del buscador.

        Yields:
            LibroCuspideItem: Item con los datos extraídos.
        """
        cargador = ItemLoader(item=LibroCuspideItem(), selector=response.selector)
        cargador.default_output_processor = TakeFirst()

        # Precio publicado en pesos: está dentro de div.price-wrapper.
        cargador.add_css(
            "precio_ars",
            "div.price-wrapper p.price bdi::text",
            MapCompose(precio_a_float),
        )
        # Precio en dólares: el sitio lo publica junto al precio en pesos.
        cargador.add_xpath(
            "precio_usd",
            '//span[contains(text(), "U$s")]/span/text()',
            MapCompose(precio_a_float),
        )
        # Identificación del libro.
        cargador.add_xpath(
            "isbn",
            "//span[@class='sku']/text()",
            MapCompose(normalizar_isbn),
        )
        cargador.add_css(
            "titulo",
            "h1.product_title::text",
            MapCompose(limpiar_texto),
        )
        cargador.add_xpath(
            "autor",
            "//p[contains(@class, 'livriz-authors')]/text()",
            MapCompose(limpiar_texto),
        )
        # Imagen de la portada.
        cargador.add_xpath(
            "url_imagen",
            "//img[contains(@class, 'wp-post-image')]/@data-large_image",
            MapCompose(limpiar_texto),
        )
        # Formas de pago y descripción detallada.
        cargador.add_css(
            "formas_pago",
            "#contentPaymentsPopUpArg li::text",
            unir_textos,
            limpiar_formas_pago,
        )
        cargador.add_css(
            "descripcion",
            "p.livriz-text-synopsis::text",
            unir_textos,
        )
        cargador.add_xpath(
            "url_producto",
            "link[@rel='canonical']/@href",
            MapCompose(limpiar_texto),
        )
        # Datos de control de la extracción.
        cargador.add_value("fecha_extraccion", datetime.date.today().isoformat())
        cargador.add_value("titulo_buscado", titulo_buscado)
        cargador.add_value("nivel_coincidencia", nivel_coincidencia)
        cargador.add_value("libro_id", libro_id)
        cargador.add_value("posicion_resultado", posicion_resultado)

        item = cargador.load_item()
        if not item.get("titulo"):
            item["titulo"] = titulo_buscado
        yield item
