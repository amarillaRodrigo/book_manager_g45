"""Vista del catálogo propio para el scraper de Book Manager.

Centraliza el acceso a los datos del catálogo (ISBN, título, autor y precio
interno en pesos) que necesitan tanto el spider para decidir qué resultados
son nuestros, como los pipelines para completar y persistir la extracción.
"""

from typing import Any, Dict, List, Optional

from book_manager.entities.entities import Libro
from book_manager.repositories.repositories import (
    RepositorioLibro,
    RepositorioMoneda,
    RepositorioPrecio,
)

# Nivel de coincidencia entre el título de un producto y el del catálogo.
COINCIDENCIA_EXACTA = 1
COINCIDENCIA_EDICION = 2


def normalizar_para_comparar(texto: Optional[str]) -> str:
    """Normaliza un texto para compararlo con otro.

    Se pasan a minúsculas y se quitan las tildes, pero **se conservan los
    paréntesis**, porque en el título del sitio la edición va entre paréntesis
    (``EL DUELO ( NE )``) y es la que permite distinguir nuestro libro de
    otro que empieza con las mismas palabras.

    Args:
        texto (Optional[str]): Texto a normalizar.

    Returns:
        str: Texto normalizado, o cadena vacía si no hay texto.
    """
    if not texto:
        return ""
    import unicodedata

    resultado = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", str(texto).lower())
        if unicodedata.category(caracter) != "Mn"
    )
    return " ".join(resultado.split())


class CatalogoInterno:
    """Catálogo propio del sistema, indexado para identificar sus libros.

    Permite reconocer, entre los resultados del buscador, cuáles son los
    libros que tenemos en catálogo y cuál es su precio interno en pesos.
    """

    def __init__(self) -> None:
        """Carga el catálogo desde la base de datos."""
        self.libros: List[Libro] = RepositorioLibro().leer_todos()
        self._por_isbn: Dict[str, int] = {}
        self._por_titulo: Dict[str, int] = {}
        self._titulo_por_id: Dict[int, str] = {}
        self._precios: Dict[int, float] = self._cargar_precios()

        for libro in self.libros:
            if libro.id is None:
                continue
            isbn = self.normalizar_isbn(libro.isbn)
            if isbn:
                self._por_isbn[isbn] = libro.id
            titulo = normalizar_para_comparar(libro.titulo)
            if titulo:
                self._por_titulo[titulo] = libro.id
                self._titulo_por_id[libro.id] = titulo

    @staticmethod
    def _cargar_precios() -> Dict[int, float]:
        """Carga el precio en pesos de cada libro del catálogo.

        Returns:
            Dict[int, float]: libro_id -> precio en pesos.
        """
        moneda_ars = None
        for moneda in RepositorioMoneda().leer_todos():
            if moneda.codigo.strip().upper() == "ARS":
                moneda_ars = moneda.id
                break
        if moneda_ars is None:
            return {}

        precios: Dict[int, float] = {}
        for precio in RepositorioPrecio().leer_todos():
            if precio.moneda_id == moneda_ars:
                precios[precio.libro_id] = float(precio.monto)
        return precios

    @staticmethod
    def normalizar_isbn(valor: Any) -> str:
        """Deja solo los dígitos de un ISBN.

        Args:
            valor (Any): Valor crudo del ISBN.

        Returns:
            str: Los dígitos del ISBN, o cadena vacía.
        """
        if valor is None:
            return ""
        return "".join(c for c in str(valor) if c.isdigit())

    def libro_por_isbn(self, isbn: Any) -> Optional[int]:
        """Busca un libro del catálogo por su ISBN.

        Args:
            isbn (Any): ISBN a buscar.

        Returns:
            Optional[int]: El ID del libro, o None si no está en el catálogo.
        """
        return self._por_isbn.get(self.normalizar_isbn(isbn))

    def libro_por_titulo(self, titulo: Any) -> Optional[int]:
        """Busca un libro del catálogo por su título exacto (ya normalizado).

        Args:
            titulo (Any): Título normalizado del libro.

        Returns:
            Optional[int]: El ID del libro, o None si no está en el catálogo.
        """
        return self._por_titulo.get(normalizar_para_comparar(titulo))

    def titulo_de(self, libro_id: int) -> str:
        """Devuelve el título normalizado de un libro del catálogo.

        Args:
            libro_id (int): ID del libro.

        Returns:
            str: El título normalizado, o cadena vacía.
        """
        return self._titulo_por_id.get(libro_id, "")

    def precio_interno(self, libro_id: int) -> Optional[float]:
        """Devuelve el precio interno en pesos de un libro.

        Args:
            libro_id (int): ID del libro.

        Returns:
            Optional[float]: El precio en pesos, o None si no tiene.
        """
        return self._precios.get(libro_id)

    @staticmethod
    def nivel_de_coincidencia(
        titulo_producto: Optional[str], titulo_catalogo: Optional[str]
    ) -> Optional[int]:
        """Indica si un título del sitio corresponde a un título del catálogo.

        Se aceptan dos formas:

        - Coincidencia exacta (``EL ETERNAUTA`` para ``El Eternauta``).
        - El título del sitio comienza por el del catálogo seguido de la
          edición entre paréntesis (``EL DUELO ( NE )``) o de un año
          (``EL ETERNAUTA 1969``).

        Se descartan los títulos que solo empiezan igual, porque corresponden
        a otras obras (``EL DUELO INFANTIL`` o ``EL ETERNAUTA PARA ARMAR``).

        Args:
            titulo_producto (Optional[str]): Título del producto en el sitio.
            titulo_catalogo (Optional[str]): Título del libro del catálogo.

        Returns:
            Optional[int]: `COINCIDENCIA_EXACTA`, `COINCIDENCIA_EDICION` o
                None si el título no corresponde al libro del catálogo.
        """
        producto = normalizar_para_comparar(titulo_producto)
        catalogo = normalizar_para_comparar(titulo_catalogo)
        if not producto or not catalogo:
            return None
        if producto == catalogo:
            return COINCIDENCIA_EXACTA
        if producto.startswith(catalogo + "(") or producto.startswith(catalogo + " ("):
            return COINCIDENCIA_EDICION
        resto = producto[len(catalogo) :].strip()
        if resto and resto[0].isdigit():
            return COINCIDENCIA_EDICION
        return None
