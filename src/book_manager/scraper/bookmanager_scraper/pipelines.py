"""Pipelines del scraper de Book Manager.

Cada pipeline es una etapa del procesamiento de los items que produce el
spider:

1. ``PrecioInternoPipeline``: confirma el libro del catálogo y le suma su
   precio interno.
2. ``ValidacionPipeline``: descarta los items que no aportan información
   utilizable.
3. ``PersistenciaPipeline``: guarda las extracciones en la base de datos.
"""

import datetime
from typing import Any, Dict, Optional

from scrapy import Item
from scrapy.exceptions import DropItem

from book_manager.entities.entities import PrecioWeb
from book_manager.repositories.repositories import RepositorioPrecioWeb
from book_manager.scraper.bookmanager_scraper.catalogo import (
    COINCIDENCIA_EXACTA,
    CatalogoInterno,
)


class PipelineBase:
    """Clase base de los pipelines del scraper.

    Implementa el contrato mínimo de Scrapy: todo item que entra al pipeline
    se devuelve sin modificar, de modo que cada etapa concreta pueda
    enfocarse en una única responsabilidad.
    """

    def process_item(self, item: Item, spider: Any = None) -> Item:
        """Procesa un item y lo devuelve sin alteraciones.

        Args:
            item (Item): Item producido por el spider.
            spider (Any): Spider que generó el item.

        Returns:
            Item: El mismo item, sin modificar.
        """
        return item

    def close_spider(self, spider: Any = None) -> None:
        """Libera los recursos del pipeline al finalizar la corrida.

        Args:
            spider (Any): Spider que terminó la corrida.
        """
        return None


class PrecioInternoPipeline(PipelineBase):
    """Confirma el libro del catálogo y completa su precio interno.

    El spider ya seleccionó únicamente las fichas cuyo título corresponde a
    un libro del catálogo, así que aquí se confirma la identificación con el
    ISBN (que es el dato más preciso: el sitio lo publica sin guiones y el
    catálogo con guiones) y se le suma el precio interno en pesos.
    """

    def __init__(self) -> None:
        self._catalogo: Optional[CatalogoInterno] = None

    def open_spider(self, spider: Any = None) -> None:
        """Carga el catálogo propio.

        Args:
            spider (Any): Spider que da inicio a la corrida.
        """
        self._catalogo = CatalogoInterno()

    def process_item(self, item: Item, spider: Any = None) -> Item:
        """Agrega al item el libro del catálogo y su precio interno.

        Args:
            item (Item): Item extraído de la ficha del producto.
            spider (Any): Spider que generó el item.

        Returns:
            Item: El item con `libro_id` y `precio_interno`.
        """
        if self._catalogo is None:
            self._catalogo = CatalogoInterno()

        libro_id = self._catalogo.libro_por_isbn(item.get("isbn"))
        if libro_id is None:
            libro_id = item.get("libro_id")
        if libro_id is None:
            return item

        item["libro_id"] = libro_id
        item["precio_interno"] = self._catalogo.precio_interno(int(libro_id))
        return item


class ValidacionPipeline(PipelineBase):
    """Descarta los items que no tienen información de precio utilizable.

    Un item es válido cuando corresponde a un libro del catálogo (se le pudo
    asignar su `libro_id`) y el sitio publica un precio válido.
    """

    def process_item(self, item: Item, spider: Any = None) -> Item:
        """Valida el item y descarta los que no sirven.

        Args:
            item (Item): Item extraído de la ficha del producto.
            spider (Any): Spider que generó el item.

        Returns:
            Item: El item validado.

        Raises:
            DropItem: Si el item no corresponde a un libro del catálogo o no
                tiene un precio publicado.
        """
        if not item.get("libro_id"):
            self._descartar(spider, "no corresponde a un libro del catálogo")
            raise DropItem("El item no corresponde a un libro del catálogo.")
        if not item.get("precio_ars"):
            self._descartar(spider, "no tiene precio publicado")
            raise DropItem("El item no tiene un precio publicado.")
        return item

    @staticmethod
    def _descartar(spider: Any, motivo: str) -> None:
        """Registra en el log por qué se descartó un item.

        Args:
            spider (Any): Spider en ejecución.
            motivo (str): Motivo del descarte.
        """
        if spider is not None and hasattr(spider, "logger"):
            spider.logger.info("Item descartado: %s", motivo)


class PersistenciaPipeline(PipelineBase):
    """Guarda las extracciones válidas en la base de datos.

    Existe a lo sumo un registro por libro y fecha de extracción: si la
    corrida vuelve a recoger el mismo libro el mismo día, el registro se
    actualiza en lugar de duplicarse.

    Cuando el sitio publica varias ediciones del mismo libro se conserva la
    que coincide con el ISBN del catálogo propio y, entre las demás, la que
    el sitio muestra como resultado principal de la búsqueda (la de coincidencia
    exacta con el título).
    """

    def __init__(self) -> None:
        self._repositorio = RepositorioPrecioWeb()
        self._isbn_del_catalogo: set = set()
        self._niveles: Dict[int, int] = {}

    def open_spider(self, spider: Any = None) -> None:
        """Carga los ISBN del catálogo propio.

        Args:
            spider (Any): Spider que da inicio a la corrida.
        """
        catalogo = CatalogoInterno()
        self._isbn_del_catalogo = {
            catalogo.normalizar_isbn(libro.isbn)
            for libro in catalogo.libros
            if catalogo.normalizar_isbn(libro.isbn)
        }

    def process_item(self, item: Item, spider: Any = None) -> Item:
        """Persiste el item en la tabla de precios web.

        Args:
            item (Item): Item extraído de la ficha del producto.
            spider (Any): Spider que generó el item.

        Returns:
            Item: El mismo item, ya persistido.
        """
        fecha = self._fecha_del_item(item)
        libro_id = int(item.get("libro_id") or 0)
        entidad = PrecioWeb(
            libro_id=libro_id,
            isbn=str(item.get("isbn") or ""),
            titulo=str(item.get("titulo") or ""),
            autor=str(item.get("autor") or ""),
            precio_ars=float(item.get("precio_ars") or 0),
            precio_usd=item.get("precio_usd"),
            precio_interno=item.get("precio_interno"),
            url_imagen=str(item.get("url_imagen") or ""),
            formas_pago=str(item.get("formas_pago") or ""),
            descripcion=str(item.get("descripcion") or ""),
            url_producto=str(item.get("url_producto") or ""),
            fecha_extraccion=fecha,
        )

        nivel = int(item.get("nivel_coincidencia") or COINCIDENCIA_EXACTA)
        nivel_guardado = self._niveles.get(libro_id)
        if nivel_guardado is not None and nivel > nivel_guardado:
            # Ya se guardó una coincidencia mejor para este libro.
            if spider is not None and hasattr(spider, "logger"):
                spider.logger.info(
                    "Se conserva la extracción anterior de '%s' (coincidencia más exacta)",
                    entidad.titulo,
                )
            return item

        existente = self._repositorio.leer_por_libro_y_fecha(libro_id, fecha)
        if existente is None or existente.id is None:
            self._repositorio.crear(entidad)
        else:
            entidad.id = existente.id
            self._repositorio.actualizar(entidad)

        self._niveles[libro_id] = nivel
        return item

    @staticmethod
    def _fecha_del_item(item: Item) -> datetime.date:
        """Obtiene la fecha de extracción del item.

        Args:
            item (Item): Item extraído de la ficha del producto.

        Returns:
            datetime.date: La fecha del item o la de hoy.
        """
        valor = item.get("fecha_extraccion")
        if isinstance(valor, datetime.date):
            return valor
        if isinstance(valor, str) and valor.strip():
            try:
                return datetime.date.fromisoformat(valor.strip())
            except ValueError:
                pass
        return datetime.date.today()
