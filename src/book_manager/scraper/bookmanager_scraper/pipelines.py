"""Pipelines del scraper de Book Manager.

Cada pipeline es una etapa del procesamiento de los items que produce el
spider. La estructura de las etapas queda definida en el Ejercicio 01 y su
lógica concreta (precio interno, validación, persistencia y auditoría) se
desarrolla en el Ejercicio 03.
"""

from typing import Any, Optional

from scrapy import Item


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
    """Completa cada item con el precio interno del catálogo.

    Busca en la base de datos el precio en pesos del libro cuyo ISBN coincide
    con el del item extraído y lo agrega como `precio_interno`.
    """


class ValidacionPipeline(PipelineBase):
    """Descarta los items que no tienen información de precio utilizable."""


class PersistenciaPipeline(PipelineBase):
    """Guarda los items válidos en la base de datos y en el JSON de respaldo."""


class AuditoriaPipeline(PipelineBase):
    """Registra la corrida del scraper en la tabla de auditorías del sistema."""


def precio_interno_de_precios(precios: Optional[Any]) -> Optional[float]:
    """Extrae el monto en pesos de una lista de precios interna.

    Args:
        precios (Optional[Any]): Lista de precios del libro en la base interna.

    Returns:
        Optional[float]: El monto en pesos, o None si no hay precio en ARS.
    """
    if not precios:
        return None
    for precio in precios:
        moneda = getattr(precio, "moneda", None)
        codigo = getattr(moneda, "codigo", "") if moneda is not None else ""
        if str(codigo).upper() == "ARS":
            return float(getattr(precio, "monto", 0) or 0)
    return None
