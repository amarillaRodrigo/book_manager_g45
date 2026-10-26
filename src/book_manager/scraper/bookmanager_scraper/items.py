"""Items del scraper de Book Manager.

Define el contrato de datos que viaja entre el spider y los pipelines: cada
item representa un libro del catálogo propio con la información pública
obtenida del sitio de Cúspide (precio, imagen, formas de pago y descripción)
más los campos que completan los pipelines (precio interno y diferencia).
"""

from typing import Any, Dict, List, Optional

import scrapy


class LibroCuspideItem(scrapy.Item):
    """Datos extraídos de la ficha de un libro en cuspide.com."""

    isbn = scrapy.Field()
    titulo = scrapy.Field()
    autor = scrapy.Field()
    precio_ars = scrapy.Field()
    precio_usd = scrapy.Field()
    url_imagen = scrapy.Field()
    formas_pago = scrapy.Field()
    descripcion = scrapy.Field()
    url_producto = scrapy.Field()
    fecha_extraccion = scrapy.Field()


class ComparacionPrecioItem(scrapy.Item):
    """Resultado de comparar el precio interno del catálogo con el precio web."""

    libro = scrapy.Field()
    isbn = scrapy.Field()
    precio_interno = scrapy.Field()
    precio_web = scrapy.Field()
    diferencia = scrapy.Field()
    diferencia_porcentaje = scrapy.Field()
    fecha_extraccion = scrapy.Field()
    en_alerta = scrapy.Field()


class ResumenScrapeItem(scrapy.Item):
    """Resumen de una corrida completa del scraper."""

    fecha_extraccion = scrapy.Field()
    titulos_consultados = scrapy.Field()
    libros_encontrados = scrapy.Field()
    alertas = scrapy.Field()


def item_a_dict(item: scrapy.Item) -> Dict[str, Any]:
    """Convierte un item de Scrapy en un diccionario plano.

    Args:
        item (scrapy.Item): Item a convertir.

    Returns:
        Dict[str, Any]: Diccionario con los campos definidos en el item.
    """
    return {campo: item.get(campo) for campo in item.fields}


def precio_a_float(valor: Any) -> Optional[float]:
    """Normaliza un precio extraído del HTML a `float`.

    El sitio publica los precios en formato argentino: los miles se separan
    con punto y los decimales con coma (por ejemplo ``47.900,00``). El parseo
    sigue esa convención, de modo que un punto aislado es siempre separador
    de miles y una coma aislada es siempre separador decimal.

    Args:
        valor (Any): Valor crudo extraído de la respuesta.

    Returns:
        Optional[float]: El precio como número, o None si no se pudo interpretar.
    """
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).replace("\xa0", " ").strip()
    for simbolo in ("$", "U$s", "US$", "€"):
        texto = texto.replace(simbolo, "")
    texto = "".join(c for c in texto if c.isdigit() or c in ".,")
    if not texto:
        return None
    if "," in texto and "." in texto:
        # Miles con punto y decimal con coma: 1.234,56 -> 1234.56
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        # Solo coma: separador decimal: 30,71 -> 30.71
        texto = texto.replace(",", ".")
    else:
        # Solo punto: separador de miles: 89.990 -> 89990
        texto = texto.replace(".", "")
    try:
        return float(texto)
    except ValueError:
        return None


def formas_pago_a_lista(valor: Any) -> List[str]:
    """Normaliza la lista de formas de pago a una lista de textos limpios.

    Args:
        valor (Any): Valor crudo extraído de la respuesta.

    Returns:
        List[str]: Formas de pago sin marcas, comillas ni espacios sobrantes.
    """
    if valor is None:
        return []
    if isinstance(valor, str):
        candidatos = [valor]
    elif isinstance(valor, (list, tuple)):
        candidatos = [str(v) for v in valor]
    else:
        candidatos = [str(valor)]

    formas: List[str] = []
    for candidato in candidatos:
        for parte in candidato.split(","):
            limpio = parte.strip().strip(".").strip()
            if limpio and limpio not in formas:
                formas.append(limpio)
    return formas
