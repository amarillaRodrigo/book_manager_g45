"""Módulo para los repositorios y persistencia de datos.

Cada entidad se persiste en su propio archivo CSV. La lectura y escritura del
archivo está aislada en ``ArchivoCSV``; los repositorios solo implementan la
lógica CRUD sobre las interfaces definidas por la cátedra.
"""

import abc
import csv
import datetime
import os
from pathlib import Path
from typing import Callable, Generic, List, Optional, Type, TypeVar

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    EntidadBase,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)

T = TypeVar("T", bound=EntidadBase)

# Carpeta donde viven los CSV de trabajo del sistema. Se puede reemplazar
# pasando otra carpeta a cada repositorio (por ejemplo, en pruebas).
DIRECTORIO_DATOS = Path(__file__).resolve().parent.parent / "migrations" / "csv"


# ---------------------------------------------------------------------------
# Interfaces (provistas por la cátedra)
# ---------------------------------------------------------------------------


class IRepositorio(abc.ABC, Generic[T]):
    """Interfaz para repositorios que manejan entidades con operaciones CRUD básicas."""

    @abc.abstractmethod
    def crear(self, entidad: T) -> T:
        """Crea una nueva entidad en el repositorio.

        Args:
            entidad (T): La entidad a crear.

        Returns:
            T: La entidad creada.

        Raises:
            ValueError: Si ya existe una entidad con el mismo ID.
        """

    @abc.abstractmethod
    def leer_por_id(self, id: int) -> Optional[T]:
        """Lee una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a leer.

        Returns:
            Optional[T]: La entidad si se encuentra, None en caso contrario.
        """

    @abc.abstractmethod
    def leer_todos(self) -> List[T]:
        """Lee todas las entidades del repositorio.

        Returns:
            List[T]: Una lista de todas las entidades.
        """

    @abc.abstractmethod
    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente en el repositorio.

        Args:
            entidad (T): La entidad a actualizar (debe tener un ID existente).

        Returns:
            T: La entidad actualizada.

        Raises:
            ValueError: Si no se encuentra la entidad para actualizar.
        """

    @abc.abstractmethod
    def eliminar(self, id: int) -> bool:
        """Elimina una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a eliminar.

        Returns:
            bool: True si la entidad fue eliminada, False si no se encontró.
        """


class IRepositorioStock(abc.ABC):
    """Interfaz para repositorios del tipo Stock."""

    @abc.abstractmethod
    def crear(self, stock: Stock) -> Stock:
        """Crea un nuevo registro de stock.

        Args:
            stock (Stock): El objeto Stock a crear.

        Returns:
            Stock: El objeto Stock creado.

        Raises:
            ValueError: Si ya existe un registro de stock para el mismo libro.
        """

    @abc.abstractmethod
    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Lee un registro de stock por ID de libro.

        Args:
            libro_id (int): El ID del libro asociado al stock.

        Returns:
            Optional[Stock]: El objeto Stock si se encuentra, None en caso contrario.
        """

    @abc.abstractmethod
    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza un registro de stock existente.

        Args:
            stock (Stock): El objeto Stock a actualizar (debe tener un libro_id existente).

        Returns:
            Stock: El objeto Stock actualizado.

        Raises:
            ValueError: Si no se encuentra el stock para actualizar.
        """

    @abc.abstractmethod
    def eliminar(self, libro_id: int) -> bool:
        """Elimina un registro de stock por ID de libro.

        Args:
            libro_id (int): El ID del libro asociado al stock a eliminar.

        Returns:
            bool: True si el stock fue eliminado, False si no se encontró.
        """


class IRepositorioCotizacionDolar(abc.ABC):
    """Interfaz para repositorios del tipo RepositorioCotizacionDolar."""

    @abc.abstractmethod
    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea una nueva cotización de dólar.

        Args:
            cotizacion (CotizacionDolar): El objeto CotizacionDolar a crear.

        Returns:
            CotizacionDolar: El objeto CotizacionDolar creado.

        Raises:
            ValueError: Si ya existe una cotización para el mismo tipo y fecha.
        """

    @abc.abstractmethod
    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: datetime.date
    ) -> Optional[CotizacionDolar]:
        """Lee una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización (e.g., 'Oficial', 'Blue').
            fecha (datetime.date): La fecha de la cotización.

        Returns:
            Optional[CotizacionDolar]: La cotización si se encuentra, None en caso contrario.
        """

    @abc.abstractmethod
    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Lee el histórico de cotizaciones para un tipo específico.

        Args:
            tipo_id (int): El ID del tipo de cotización.

        Returns:
            List[CotizacionDolar]: Una lista de cotizaciones históricas para el tipo dado.
        """

    @abc.abstractmethod
    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza una cotización de dólar existente.

        Args:
            cotizacion (CotizacionDolar): El objeto CotizacionDolar a actualizar.

        Returns:
            CotizacionDolar: El objeto CotizacionDolar actualizado.
        """

    @abc.abstractmethod
    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Elimina una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización.
            fecha (datetime.date): La fecha de la cotización a eliminar.

        Returns:
            bool: True si la cotización fue eliminada, False si no se encontró.
        """


# ---------------------------------------------------------------------------
# Acceso a archivos CSV
# ---------------------------------------------------------------------------


class ArchivoCSV(Generic[T]):
    """Lee y escribe entidades en un archivo CSV usando to_dict/from_dict."""

    def __init__(self, ruta: Path, clase: Type[T]) -> None:
        self._ruta = ruta
        self._clase = clase

    @property
    def ruta(self) -> Path:
        """Ruta del archivo CSV."""
        return self._ruta

    def leer(self) -> List[T]:
        """Devuelve todas las entidades del archivo, o una lista vacía si no existe."""
        if not self._ruta.exists():
            return []
        with self._ruta.open("r", newline="", encoding="utf-8") as archivo:
            return [self._clase.from_dict(fila) for fila in csv.DictReader(archivo)]

    def escribir(self, entidades: List[T]) -> None:
        """Reescribe el archivo completo con las entidades dadas.

        Se escribe primero un archivo temporal y luego se reemplaza el original,
        para no dejar un CSV a medio escribir si el programa se interrumpe.
        """
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = self._ruta.with_suffix(".tmp")
        with temporal.open("w", newline="", encoding="utf-8") as archivo:
            if entidades:
                filas = [entidad.to_dict() for entidad in entidades]
                escritor = csv.DictWriter(archivo, fieldnames=list(filas[0].keys()))
                escritor.writeheader()
                escritor.writerows(filas)
        os.replace(temporal, self._ruta)


def _siguiente_id(entidades: List[T]) -> int:
    """Calcula el próximo ID libre (máximo actual + 1)."""
    return max((e.id for e in entidades if e.id is not None), default=0) + 1


# ---------------------------------------------------------------------------
# Repositorio genérico por ID
# ---------------------------------------------------------------------------


class RepositorioCSV(IRepositorio[T]):
    """Implementación de IRepositorio que persiste las entidades en un CSV."""

    def __init__(
        self, clase: Type[T], nombre_archivo: str, directorio: Path = DIRECTORIO_DATOS
    ) -> None:
        self._archivo: ArchivoCSV[T] = ArchivoCSV(directorio / nombre_archivo, clase)

    def crear(self, entidad: T) -> T:
        entidades = self._archivo.leer()
        if entidad.id is None:
            entidad.id = _siguiente_id(entidades)
        elif any(e.id == entidad.id for e in entidades):
            raise ValueError(f"Ya existe una entidad con ID {entidad.id}.")
        entidades.append(entidad)
        self._archivo.escribir(entidades)
        return entidad

    def leer_por_id(self, id: int) -> Optional[T]:
        return next((e for e in self._archivo.leer() if e.id == id), None)

    def leer_todos(self) -> List[T]:
        return self._archivo.leer()

    def actualizar(self, entidad: T) -> T:
        entidades = self._archivo.leer()
        for indice, existente in enumerate(entidades):
            if entidad.id is not None and existente.id == entidad.id:
                entidades[indice] = entidad
                self._archivo.escribir(entidades)
                return entidad
        raise ValueError(f"No se encontró una entidad con ID {entidad.id} para actualizar.")

    def eliminar(self, id: int) -> bool:
        entidades = self._archivo.leer()
        restantes = [e for e in entidades if e.id != id]
        if len(restantes) == len(entidades):
            return False
        self._archivo.escribir(restantes)
        return True


class RepositorioGenero(RepositorioCSV[Genero]):
    """Repositorio de géneros literarios."""

    def __init__(self, directorio: Path = DIRECTORIO_DATOS) -> None:
        super().__init__(Genero, "generos.csv", directorio)


class RepositorioEditorial(RepositorioCSV[Editorial]):
    """Repositorio de editoriales."""

    def __init__(self, directorio: Path = DIRECTORIO_DATOS) -> None:
        super().__init__(Editorial, "editoriales.csv", directorio)


class RepositorioMoneda(RepositorioCSV[Moneda]):
    """Repositorio de monedas."""

    def __init__(self, directorio: Path = DIRECTORIO_DATOS) -> None:
        super().__init__(Moneda, "monedas.csv", directorio)


class RepositorioTipoCotizacion(RepositorioCSV[TipoCotizacion]):
    """Repositorio de tipos de cotización del dólar."""

    def __init__(self, directorio: Path = DIRECTORIO_DATOS) -> None:
        super().__init__(TipoCotizacion, "tipos_cotizacion.csv", directorio)


class RepositorioLibro(RepositorioCSV[Libro]):
    """Repositorio de libros."""

    def __init__(self, directorio: Path = DIRECTORIO_DATOS) -> None:
        super().__init__(Libro, "libros.csv", directorio)


class RepositorioPrecio(RepositorioCSV[Precio]):
    """Repositorio de precios de libros."""

    def __init__(self, directorio: Path = DIRECTORIO_DATOS) -> None:
        super().__init__(Precio, "precios.csv", directorio)


# ---------------------------------------------------------------------------
# Repositorios con clave propia
# ---------------------------------------------------------------------------


class RepositorioStock(IRepositorioStock):
    """Repositorio de stock: un único registro por libro, identificado por libro_id."""

    def __init__(self, directorio: Path = DIRECTORIO_DATOS) -> None:
        self._archivo: ArchivoCSV[Stock] = ArchivoCSV(directorio / "stock.csv", Stock)

    def crear(self, stock: Stock) -> Stock:
        registros = self._archivo.leer()
        if any(r.libro_id == stock.libro_id for r in registros):
            raise ValueError(f"Ya existe stock para el libro {stock.libro_id}.")
        if stock.id is None:
            stock.id = _siguiente_id(registros)
        registros.append(stock)
        self._archivo.escribir(registros)
        return stock

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        return next((r for r in self._archivo.leer() if r.libro_id == libro_id), None)

    def leer_todos(self) -> List[Stock]:
        """Lee todos los registros de stock (usado por la consola)."""
        return self._archivo.leer()

    def actualizar(self, stock: Stock) -> Stock:
        registros = self._archivo.leer()
        for indice, existente in enumerate(registros):
            if existente.libro_id == stock.libro_id:
                stock.id = existente.id
                registros[indice] = stock
                self._archivo.escribir(registros)
                return stock
        raise ValueError(f"No se encontró stock para el libro {stock.libro_id}.")

    def eliminar(self, libro_id: int) -> bool:
        registros = self._archivo.leer()
        restantes = [r for r in registros if r.libro_id != libro_id]
        if len(restantes) == len(registros):
            return False
        self._archivo.escribir(restantes)
        return True


class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
    """Repositorio de cotizaciones: una por tipo y fecha, con histórico ordenado."""

    def __init__(self, directorio: Path = DIRECTORIO_DATOS) -> None:
        self._archivo: ArchivoCSV[CotizacionDolar] = ArchivoCSV(
            directorio / "cotizaciones.csv", CotizacionDolar
        )

    @staticmethod
    def _misma_clave(tipo_id: int, fecha: datetime.date) -> Callable[[CotizacionDolar], bool]:
        """Devuelve un filtro que identifica la cotización de un tipo en una fecha."""
        return lambda c: c.tipo_id == tipo_id and c.fecha == fecha

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        registros = self._archivo.leer()
        es_misma = self._misma_clave(cotizacion.tipo_id, cotizacion.fecha)
        if any(es_misma(r) for r in registros):
            raise ValueError(
                f"Ya existe una cotización del tipo {cotizacion.tipo_id} "
                f"para el {cotizacion.fecha.isoformat()}."
            )
        if cotizacion.id is None:
            cotizacion.id = _siguiente_id(registros)
        registros.append(cotizacion)
        self._archivo.escribir(registros)
        return cotizacion

    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: datetime.date
    ) -> Optional[CotizacionDolar]:
        es_misma = self._misma_clave(tipo_id, fecha)
        return next((r for r in self._archivo.leer() if es_misma(r)), None)

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        historico = [r for r in self._archivo.leer() if r.tipo_id == tipo_id]
        return sorted(historico, key=lambda c: c.fecha)

    def leer_todos(self) -> List[CotizacionDolar]:
        """Lee todas las cotizaciones (usado por la consola)."""
        return self._archivo.leer()

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        registros = self._archivo.leer()
        es_misma = self._misma_clave(cotizacion.tipo_id, cotizacion.fecha)
        for indice, existente in enumerate(registros):
            if es_misma(existente):
                cotizacion.id = existente.id
                registros[indice] = cotizacion
                self._archivo.escribir(registros)
                return cotizacion
        raise ValueError(
            f"No se encontró una cotización del tipo {cotizacion.tipo_id} "
            f"para el {cotizacion.fecha.isoformat()}."
        )

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        registros = self._archivo.leer()
        es_misma = self._misma_clave(tipo_id, fecha)
        restantes = [r for r in registros if not es_misma(r)]
        if len(restantes) == len(registros):
            return False
        self._archivo.escribir(restantes)
        return True
