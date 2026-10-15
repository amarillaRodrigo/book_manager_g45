"""Módulo para los repositorios y persistencia de datos.

En el Sprint 2 la persistencia del sistema se realiza sobre una base de datos
relacional mediante SQLAlchemy ORM (`ConexionDB` y modelos declarativos),
manteniendo las interfaces definidas por la cátedra y convirtiendo entre
modelos ORM y entidades de dominio.
"""

import abc
import csv
import datetime
import os
from pathlib import Path
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select

from book_manager.database.connection import ConexionDB, obtener_conexion
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
from book_manager.models.models import (
     Base,
    CotizacionDolar as ModeloCotizacionDolar,
    Editorial as ModeloEditorial,
    Genero as ModeloGenero,
    Libro as ModeloLibro,
    Moneda as ModeloMoneda,
    Precio as ModeloPrecio,
    Stock as ModeloStock,
    TipoCotizacion as ModeloTipoCotizacion,
)

T = TypeVar("T", bound=EntidadBase)
M = TypeVar("M", bound=Base)

# Carpeta donde viven los CSV de migración / trabajo histórico.
DIRECTORIO_DATOS = Path(__file__).resolve().parent.parent / "migrations" / "csv"


def _resolver_conexion(conexion: Optional[Any] = None) -> ConexionDB:
    """Obtiene una instancia válida de ConexionDB e inicializa las tablas."""
    if isinstance(conexion, ConexionDB):
        db = conexion
    elif isinstance(conexion, str):
        db = obtener_conexion(url=conexion)
    else:
        db = obtener_conexion()
    db.crear_tablas(Base)
    return db


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
# Acceso a archivos CSV (conservado para soporte de migraciones)
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
        """Reescribe el archivo completo con las entidades dadas."""
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


class RepositorioCSV(IRepositorio[T]):
    """Implementación histórica de IRepositorio sobre archivos CSV."""

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


# ---------------------------------------------------------------------------
# Repositorio genérico SQLAlchemy por ID
# ---------------------------------------------------------------------------


class RepositorioSQLAlchemy(IRepositorio[T], Generic[T, M]):
    """Implementación de IRepositorio que persiste las entidades usando SQLAlchemy."""

    def __init__(
        self,
        modelo_orm: Type[M],
        conexion: Optional[Any] = None,
    ) -> None:
        self._modelo_orm = modelo_orm
        self._db = _resolver_conexion(conexion)

    @abc.abstractmethod
    def _a_entidad(self, modelo: M) -> T:
        """Convierte una instancia del modelo ORM en una entidad de dominio."""

    @abc.abstractmethod
    def _a_datos_modelo(self, entidad: T) -> Dict[str, Any]:
        """Extrae los atributos de la entidad para poblar el modelo ORM."""

    def crear(self, entidad: T) -> T:
        with self._db.transaccion() as sesion:
            if entidad.id is not None and sesion.get(self._modelo_orm, entidad.id) is not None:
                raise ValueError(f"Ya existe una entidad con ID {entidad.id}.")
            datos = self._a_datos_modelo(entidad)
            if entidad.id is not None:
                datos["id"] = entidad.id
            nuevo = self._modelo_orm(**datos)
            sesion.add(nuevo)
            sesion.flush()
            entidad.id = nuevo.id
            return self._a_entidad(nuevo)

    def leer_por_id(self, id: int) -> Optional[T]:
        with self._db.transaccion() as sesion:
            registro = sesion.get(self._modelo_orm, id)
            return self._a_entidad(registro) if registro is not None else None

    def leer_todos(self) -> List[T]:
        with self._db.transaccion() as sesion:
            stmt = select(self._modelo_orm).order_by(self._modelo_orm.id)  # type: ignore[attr-defined]
            registros = sesion.scalars(stmt).all()
            return [self._a_entidad(r) for r in registros]

    def actualizar(self, entidad: T) -> T:
        if entidad.id is None:
            raise ValueError("La entidad a actualizar debe tener un ID válido.")
        with self._db.transaccion() as sesion:
            registro = sesion.get(self._modelo_orm, entidad.id)
            if registro is None:
                raise ValueError(
                    f"No se encontró una entidad con ID {entidad.id} para actualizar."
                )
            for campo, valor in self._a_datos_modelo(entidad).items():
                setattr(registro, campo, valor)
            sesion.flush()
            return self._a_entidad(registro)

    def eliminar(self, id: int) -> bool:
        with self._db.transaccion() as sesion:
            registro = sesion.get(self._modelo_orm, id)
            if registro is None:
                return False
            sesion.delete(registro)
            return True


# ---------------------------------------------------------------------------
# Repositorios concretos por entidad
# ---------------------------------------------------------------------------


class RepositorioGenero(RepositorioSQLAlchemy[Genero, ModeloGenero]):
    """Repositorio de géneros literarios en base de datos."""

    def __init__(self, conexion: Optional[Any] = None) -> None:
        super().__init__(ModeloGenero, conexion)

    def _a_entidad(self, modelo: ModeloGenero) -> Genero:
        return Genero(
            nombre=modelo.nombre,
            descripcion=modelo.descripcion,
            id=modelo.id,
        )

    def _a_datos_modelo(self, entidad: Genero) -> Dict[str, Any]:
        return {
            "nombre": entidad.nombre,
            "descripcion": entidad.descripcion,
        }


class RepositorioEditorial(RepositorioSQLAlchemy[Editorial, ModeloEditorial]):
    """Repositorio de editoriales en base de datos."""

    def __init__(self, conexion: Optional[Any] = None) -> None:
        super().__init__(ModeloEditorial, conexion)

    def _a_entidad(self, modelo: ModeloEditorial) -> Editorial:
        return Editorial(
            nombre=modelo.nombre,
            contacto=modelo.contacto,
            direccion=modelo.direccion,
            id=modelo.id,
        )

    def _a_datos_modelo(self, entidad: Editorial) -> Dict[str, Any]:
        return {
            "nombre": entidad.nombre,
            "contacto": entidad.contacto,
            "direccion": entidad.direccion,
        }


class RepositorioMoneda(RepositorioSQLAlchemy[Moneda, ModeloMoneda]):
    """Repositorio de monedas en base de datos."""

    def __init__(self, conexion: Optional[Any] = None) -> None:
        super().__init__(ModeloMoneda, conexion)

    def _a_entidad(self, modelo: ModeloMoneda) -> Moneda:
        return Moneda(
            codigo=modelo.codigo,
            nombre=modelo.nombre,
            simbolo=modelo.simbolo,
            id=modelo.id,
        )

    def _a_datos_modelo(self, entidad: Moneda) -> Dict[str, Any]:
        return {
            "codigo": entidad.codigo,
            "nombre": entidad.nombre,
            "simbolo": entidad.simbolo,
        }


class RepositorioTipoCotizacion(RepositorioSQLAlchemy[TipoCotizacion, ModeloTipoCotizacion]):
    """Repositorio de tipos de cotización del dólar en base de datos."""

    def __init__(self, conexion: Optional[Any] = None) -> None:
        super().__init__(ModeloTipoCotizacion, conexion)

    def _a_entidad(self, modelo: ModeloTipoCotizacion) -> TipoCotizacion:
        return TipoCotizacion(
            nombre=modelo.nombre,
            descripcion=modelo.descripcion,
            id=modelo.id,
        )

    def _a_datos_modelo(self, entidad: TipoCotizacion) -> Dict[str, Any]:
        return {
            "nombre": entidad.nombre,
            "descripcion": entidad.descripcion,
        }


class RepositorioLibro(RepositorioSQLAlchemy[Libro, ModeloLibro]):
    """Repositorio de libros en base de datos."""

    def __init__(self, conexion: Optional[Any] = None) -> None:
        super().__init__(ModeloLibro, conexion)

    def _a_entidad(self, modelo: ModeloLibro) -> Libro:
        return Libro(
            isbn=modelo.isbn,
            titulo=modelo.titulo,
            autor=modelo.autor,
            anio_publicacion=int(modelo.anio_publicacion),
            genero_id=int(modelo.genero_id),
            editorial_id=int(modelo.editorial_id),
            id=modelo.id,
        )

    def _a_datos_modelo(self, entidad: Libro) -> Dict[str, Any]:
        return {
            "isbn": entidad.isbn,
            "titulo": entidad.titulo,
            "autor": entidad.autor,
            "anio_publicacion": entidad.anio_publicacion,
            "genero_id": entidad.genero_id,
            "editorial_id": entidad.editorial_id,
        }


class RepositorioPrecio(RepositorioSQLAlchemy[Precio, ModeloPrecio]):
    """Repositorio de precios de libros en base de datos."""

    def __init__(self, conexion: Optional[Any] = None) -> None:
        super().__init__(ModeloPrecio, conexion)

    def _a_entidad(self, modelo: ModeloPrecio) -> Precio:
        return Precio(
            libro_id=int(modelo.libro_id),
            moneda_id=int(modelo.moneda_id),
            monto=float(modelo.monto),
            id=modelo.id,
        )

    def _a_datos_modelo(self, entidad: Precio) -> Dict[str, Any]:
        return {
            "libro_id": entidad.libro_id,
            "moneda_id": entidad.moneda_id,
            "monto": float(entidad.monto),
        }


# ---------------------------------------------------------------------------
# Repositorios con clave propia (Stock y CotizacionDolar)
# ---------------------------------------------------------------------------


class RepositorioStock(IRepositorioStock):
    """Repositorio de stock en base de datos: un único registro por libro."""

    def __init__(self, conexion: Optional[Any] = None) -> None:
        self._db = _resolver_conexion(conexion)

    @staticmethod
    def _a_entidad(modelo: ModeloStock) -> Stock:
        return Stock(
            libro_id=int(modelo.libro_id),
            cantidad=int(modelo.cantidad),
            ubicacion=modelo.ubicacion,
            id=modelo.id,
        )

    def crear(self, stock: Stock) -> Stock:
        with self._db.transaccion() as sesion:
            existente = sesion.scalars(
                select(ModeloStock).where(ModeloStock.libro_id == stock.libro_id)
            ).first()
            if existente is not None:
                raise ValueError(f"Ya existe stock para el libro {stock.libro_id}.")
            datos: Dict[str, Any] = {
                "libro_id": stock.libro_id,
                "cantidad": stock.cantidad,
                "ubicacion": stock.ubicacion,
            }
            if stock.id is not None:
                datos["id"] = stock.id
            nuevo = ModeloStock(**datos)
            sesion.add(nuevo)
            sesion.flush()
            stock.id = nuevo.id
            return self._a_entidad(nuevo)

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        with self._db.transaccion() as sesion:
            registro = sesion.scalars(
                select(ModeloStock).where(ModeloStock.libro_id == libro_id)
            ).first()
            return self._a_entidad(registro) if registro is not None else None

    def leer_todos(self) -> List[Stock]:
        """Lee todos los registros de stock (usado por la consola)."""
        with self._db.transaccion() as sesion:
            registros = sesion.scalars(
                select(ModeloStock).order_by(ModeloStock.id)
            ).all()
            return [self._a_entidad(r) for r in registros]

    def actualizar(self, stock: Stock) -> Stock:
        with self._db.transaccion() as sesion:
            registro = sesion.scalars(
                select(ModeloStock).where(ModeloStock.libro_id == stock.libro_id)
            ).first()
            if registro is None:
                raise ValueError(f"No se encontró stock para el libro {stock.libro_id}.")
            registro.cantidad = stock.cantidad
            registro.ubicacion = stock.ubicacion
            sesion.flush()
            stock.id = registro.id
            return self._a_entidad(registro)

    def eliminar(self, libro_id: int) -> bool:
        with self._db.transaccion() as sesion:
            registro = sesion.scalars(
                select(ModeloStock).where(ModeloStock.libro_id == libro_id)
            ).first()
            if registro is None:
                return False
            sesion.delete(registro)
            return True


class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
    """Repositorio de cotizaciones en base de datos: una por tipo y fecha."""

    def __init__(self, conexion: Optional[Any] = None) -> None:
        self._db = _resolver_conexion(conexion)

    @staticmethod
    def _a_entidad(modelo: ModeloCotizacionDolar) -> CotizacionDolar:
        return CotizacionDolar(
            tipo_id=int(modelo.tipo_id),
            fecha=modelo.fecha,
            valor_compra=float(modelo.valor_compra),
            valor_venta=float(modelo.valor_venta),
            id=modelo.id,
        )

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        with self._db.transaccion() as sesion:
            existente = sesion.scalars(
                select(ModeloCotizacionDolar).where(
                    ModeloCotizacionDolar.tipo_id == cotizacion.tipo_id,
                    ModeloCotizacionDolar.fecha == cotizacion.fecha,
                )
            ).first()
            if existente is not None:
                raise ValueError(
                    f"Ya existe una cotización del tipo {cotizacion.tipo_id} "
                    f"para el {cotizacion.fecha.isoformat()}."
                )
            datos: Dict[str, Any] = {
                "tipo_id": cotizacion.tipo_id,
                "fecha": cotizacion.fecha,
                "valor_compra": float(cotizacion.valor_compra),
                "valor_venta": float(cotizacion.valor_venta),
            }
            if cotizacion.id is not None:
                datos["id"] = cotizacion.id
            nueva = ModeloCotizacionDolar(**datos)
            sesion.add(nueva)
            sesion.flush()
            cotizacion.id = nueva.id
            return self._a_entidad(nueva)

    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: datetime.date
    ) -> Optional[CotizacionDolar]:
        with self._db.transaccion() as sesion:
            registro = sesion.scalars(
                select(ModeloCotizacionDolar).where(
                    ModeloCotizacionDolar.tipo_id == tipo_id,
                    ModeloCotizacionDolar.fecha == fecha,
                )
            ).first()
            return self._a_entidad(registro) if registro is not None else None

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        with self._db.transaccion() as sesion:
            registros = sesion.scalars(
                select(ModeloCotizacionDolar)
                .where(ModeloCotizacionDolar.tipo_id == tipo_id)
                .order_by(ModeloCotizacionDolar.fecha.asc())
            ).all()
            return [self._a_entidad(r) for r in registros]

    def leer_todos(self) -> List[CotizacionDolar]:
        """Lee todas las cotizaciones ordenadas por fecha (usado por la consola)."""
        with self._db.transaccion() as sesion:
            registros = sesion.scalars(
                select(ModeloCotizacionDolar).order_by(
                    ModeloCotizacionDolar.fecha.asc(),
                    ModeloCotizacionDolar.tipo_id.asc(),
                )
            ).all()
            return [self._a_entidad(r) for r in registros]

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        with self._db.transaccion() as sesion:
            registro = sesion.scalars(
                select(ModeloCotizacionDolar).where(
                    ModeloCotizacionDolar.tipo_id == cotizacion.tipo_id,
                    ModeloCotizacionDolar.fecha == cotizacion.fecha,
                )
            ).first()
            if registro is None:
                raise ValueError(
                    f"No se encontró una cotización del tipo {cotizacion.tipo_id} "
                    f"para el {cotizacion.fecha.isoformat()}."
                )
            registro.valor_compra = float(cotizacion.valor_compra)
            registro.valor_venta = float(cotizacion.valor_venta)
            sesion.flush()
            cotizacion.id = registro.id
            return self._a_entidad(registro)

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        with self._db.transaccion() as sesion:
            registro = sesion.scalars(
                select(ModeloCotizacionDolar).where(
                    ModeloCotizacionDolar.tipo_id == tipo_id,
                    ModeloCotizacionDolar.fecha == fecha,
                )
            ).first()
            if registro is None:
                return False
            sesion.delete(registro)
            return True