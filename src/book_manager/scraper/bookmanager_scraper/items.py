"""Items y procesadores del scraper de Book Manager.

Define el contrato de datos que viaja entre el spider y los pipelines: cada
item representa un libro del catálogo propio con la información pública
obtenida del sitio de Cúspide (precio, imagen, formas de pago y descripción)
más los campos que completa el pipeline de comparación de precios.

Los procesadores son las funciones que se le pasan a los `ItemLoader` para
normalizar cada valor extraído antes de armar el item.
"""

import re
import unicodedata
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
    # Título del catálogo que originó la búsqueda (sirve para identificar el
    # libro cuando el ISBN de la edición publicada no coincide con el nuestro).
    titulo_buscado = scrapy.Field()
    # Qué tan exactamente coincide el título del sitio con el del catálogo.
    nivel_coincidencia = scrapy.Field()
    # Completados por los pipelines.
    libro_id = scrapy.Field()
    precio_interno = scrapy.Field()


def item_a_dict(item: scrapy.Item) -> Dict[str, Any]:
    """Convierte un item de Scrapy en un diccionario plano.

    Args:
        item (scrapy.Item): Item a convertir.

    Returns:
        Dict[str, Any]: Diccionario con los campos definidos en el item.
    """
    return {campo: item.get(campo) for campo in item.fields}


# ---------------------------------------------------------------------------
# Procesadores
# ---------------------------------------------------------------------------


def limpiar_texto(valor: Any) -> Optional[str]:
    """Normaliza un texto del HTML: sin entidades, espacios repetidos ni cortes.

    Args:
        valor (Any): Valor crudo extraído de la respuesta.

    Returns:
        Optional[str]: Texto limpio, o None si no queda contenido.
    """
    if valor is None:
        return None
    texto = str(valor).replace("\xa0", " ").replace("\u200b", "")
    texto = texto.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto or None


def normalizar_isbn(valor: Any) -> Optional[str]:
    """Normaliza un ISBN para poder compararlo entre el sitio y el catálogo.

    El sitio publica el ISBN sin guiones (`9789504982814`) mientras que el
    catálogo propio lo guarda con guiones (`978-9504982814`), de modo que la
    comparación se hace sobre los dígitos.

    Args:
        valor (Any): Valor crudo extraído de la respuesta.

    Returns:
        Optional[str]: Solo los dígitos del ISBN, o None si no hay.
    """
    if valor is None:
        return None
    digitos = re.sub(r"\D", "", str(valor))
    return digitos or None


def normalizar_titulo(valor: Any) -> Optional[str]:
    """Normaliza un título para comparar textos sin acentos ni signos.

    Args:
        valor (Any): Valor crudo extraído de la respuesta.

    Returns:
        Optional[str]: Título normalizado en minúsculas, o None si no hay.
    """
    if valor is None:
        return None
    texto = str(valor).lower()
    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )
    texto = re.sub(r"[^a-z0-9]+", " ", texto).strip()
    return texto or None


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
    if "." in texto and "," in texto:
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


def unir_textos(valores: Any, separador: str = " ") -> Optional[str]:
    """Une varios fragmentos de texto en uno solo.

    Los ``ItemLoader`` entregan a los procesadores la lista completa de los
    valores extraídos, de modo que este procesador normaliza cada fragmento y
    los une en un único texto.

    Args:
        valores (Any): Lista de fragmentos de texto.
        separador (str): Separador con el que se unen los fragmentos.

    Returns:
        Optional[str]: Texto unido, o None si no hay contenido.
    """
    if valores is None:
        return None
    candidatos = [valores] if isinstance(valores, str) else list(valores)
    partes: List[str] = []
    for candidato in candidatos:
        limpio = limpiar_texto(candidato)
        if limpio and limpio not in partes:
            partes.append(limpio)
    return separador.join(partes) if partes else None


def limpiar_formas_pago(valores: Any) -> Optional[str]:
    """Normaliza la lista de formas de pago a un único texto.

    El sitio las publica como una lista HTML donde cada elemento empieza con
    un signo `>` que sobra.

    Args:
        valores (Any): Lista de formas de pago.

    Returns:
        Optional[str]: Formas de pago separadas por punto y coma, o None.
    """
    texto = unir_textos(valores, separador="; ")
    if texto is None:
        return None
    formas: List[str] = []
    for parte in texto.split(";"):
        limpio = parte.strip().lstrip(">").strip().rstrip(":").strip()
        if limpio and limpio not in formas:
            formas.append(limpio)
    return "; ".join(formas) if formas else None
