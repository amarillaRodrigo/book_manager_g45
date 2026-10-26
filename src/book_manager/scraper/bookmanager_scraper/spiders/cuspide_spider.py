"""Spider de Cúspide para Book Manager.

El spider consulta el sitio de Cúspide una vez por cada título del catálogo
propio (nunca se buscan libros que no estén en el catálogo) y, para cada
título, se queda únicamente con los diez primeros resultados devueltos.

En este Ejercicio 01 queda construida la estructura del spider: la lectura del
catálogo propio y la generación de las peticiones de búsqueda. El parseo de
los resultados y de la ficha de cada producto, junto con los loaders y los
pipelines, se desarrolla en el Ejercicio 03.
"""

import csv
from pathlib import Path
from typing import Any, Iterable, List, Optional
from urllib.parse import quote_plus

import scrapy

# Carpeta con los CSV del catálogo propio (migrations/csv).
DIRECTORIO_CSVS = Path(__file__).resolve().parents[3] / "migrations" / "csv"
ARCHIVO_CATALOGO = DIRECTORIO_CSVS / "libros.csv"

# Cantidad máxima de resultados considerados por cada título.
MAXIMO_RESULTADOS_POR_TITULO = 10

# Plantilla por defecto de la URL de búsqueda. La configuración del proyecto
# Scrapy puede sobrescribirla mediante la variable URL_BUSQUEDA.
URL_BUSQUEDA_POR_DEFECTO = "https://cuspide.com/?s={titulo}&post_type=product"


class CuspideSpider(scrapy.Spider):
    """Obtiene los datos públicos de los libros del catálogo en Cúspide."""

    name = "cuspide"

    def __init__(self, archivo_catalogo: Optional[str] = None, *args, **kwargs) -> None:
        """Inicializa el spider con el catálogo propio a consultar.

        Args:
            archivo_catalogo (Optional[str]): Ruta alternativa al CSV de libros.
                Si no se indica se usa `migrations/csv/libros.csv`.
            *args: Argumentos adicionales de Scrapy.
            **kwargs: Argumentos adicionales de Scrapy.
        """
        super().__init__(*args, **kwargs)
        self.archivo_catalogo = Path(archivo_catalogo) if archivo_catalogo else ARCHIVO_CATALOGO
        self.url_base = URL_BUSQUEDA_POR_DEFECTO

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
            self.logger.warning("No se encontró el catálogo propio en %s", self.archivo_catalogo)
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

    # ----------------------------------------------------------------- requests
    def peticiones_de_busqueda(self) -> Iterable[scrapy.Request]:
        """Construye una petición de búsqueda por cada título del catálogo.

        Returns:
            Iterable[scrapy.Request]: Peticiones de búsqueda, una por título.
        """
        titulos = self.titulos_del_catalogo()
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
        """Parsea la página de resultados de una búsqueda.

        Implementado en el Ejercicio 03: se extraen los diez primeros
        resultados y se delega en `parse_producto` la ficha de cada libro.

        Args:
            response (Any): Respuesta de la página de resultados.
            titulo_buscado (str): Título consultado, para el registro de logs.

        Yields:
            scrapy.Request: Peticiones a las fichas de producto.
        """
        self.logger.info("Resultados para '%s': %s", titulo_buscado, response.url)
        return
