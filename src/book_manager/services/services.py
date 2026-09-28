"""Módulo para la capa de servicios y lógica de negocio.

Los servicios aplican las reglas de negocio sobre los repositorios: validan
referencias entre entidades, evitan duplicados, protegen las eliminaciones
que dejarían datos huérfanos y resuelven operaciones propias del dominio
(movimientos de stock y conversión de precios según la cotización del dólar).
"""

import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, List, Optional, TypeVar

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
from book_manager.repositories.repositories import (
    DIRECTORIO_DATOS,
    IRepositorio,
    IRepositorioCotizacionDolar,
    IRepositorioStock,
    RepositorioCotizacionDolar,
    RepositorioEditorial,
    RepositorioGenero,
    RepositorioLibro,
    RepositorioMoneda,
    RepositorioPrecio,
    RepositorioStock,
    RepositorioTipoCotizacion,
)

T = TypeVar("T", bound=EntidadBase)

CODIGO_PESOS = "ARS"
CODIGO_DOLARES = "USD"


class EntidadNoEncontradaError(ValueError):
    """Se solicitó una entidad que no existe."""


class ReglaDeNegocioError(ValueError):
    """La operación viola una regla de negocio del sistema."""


# ---------------------------------------------------------------------------
# Servicio genérico
# ---------------------------------------------------------------------------


class ServicioBase(Generic[T]):
    """CRUD común a las entidades identificadas por ID.

    Las subclases redefinen ``_validar`` y ``_validar_eliminacion`` para
    agregar sus reglas de negocio.
    """

    nombre_entidad = "entidad"

    def __init__(self, repositorio: IRepositorio[T]) -> None:
        self._repositorio = repositorio

    def listar(self) -> List[T]:
        """Devuelve todas las entidades."""
        return self._repositorio.leer_todos()

    def buscar(self, id: int) -> Optional[T]:
        """Devuelve la entidad con ese ID, o None si no existe."""
        return self._repositorio.leer_por_id(id)

    def obtener(self, id: int) -> T:
        """Devuelve la entidad con ese ID o lanza EntidadNoEncontradaError."""
        entidad = self._repositorio.leer_por_id(id)
        if entidad is None:
            raise EntidadNoEncontradaError(f"No existe {self.nombre_entidad} con ID {id}.")
        return entidad

    def crear(self, entidad: T) -> T:
        """Valida y da de alta la entidad."""
        self._validar(entidad)
        return self._repositorio.crear(entidad)

    def actualizar(self, entidad: T) -> T:
        """Valida y modifica una entidad existente."""
        if entidad.id is None:
            raise ReglaDeNegocioError(f"Para modificar {self.nombre_entidad} se necesita su ID.")
        self.obtener(entidad.id)
        self._validar(entidad)
        return self._repositorio.actualizar(entidad)

    def eliminar(self, id: int) -> bool:
        """Elimina la entidad si ninguna otra depende de ella."""
        if self._repositorio.leer_por_id(id) is None:
            return False
        self._validar_eliminacion(id)
        return self._repositorio.eliminar(id)

    def _validar(self, entidad: T) -> None:
        """Reglas previas al alta o la modificación (por defecto, ninguna)."""

    def _validar_eliminacion(self, id: int) -> None:
        """Reglas previas a la eliminación (por defecto, ninguna)."""

    def _verificar_unico(self, entidad: T, valor: str, atributo: str) -> None:
        """Impide que dos entidades distintas compartan el mismo valor de un atributo."""
        for existente in self._repositorio.leer_todos():
            mismo_valor = str(getattr(existente, atributo)).casefold() == valor.casefold()
            if mismo_valor and existente.id != entidad.id:
                raise ReglaDeNegocioError(
                    f"Ya existe {self.nombre_entidad} con {atributo} '{valor}'."
                )


# ---------------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------------


class ServicioGenero(ServicioBase[Genero]):
    """Géneros literarios: nombre único y sin libros asociados al eliminar."""

    nombre_entidad = "un género"

    def __init__(self, repositorio: IRepositorio[Genero], libros: IRepositorio[Libro]) -> None:
        super().__init__(repositorio)
        self._libros = libros

    def _validar(self, entidad: Genero) -> None:
        self._verificar_unico(entidad, entidad.nombre, "nombre")

    def _validar_eliminacion(self, id: int) -> None:
        if any(libro.genero_id == id for libro in self._libros.leer_todos()):
            raise ReglaDeNegocioError("No se puede eliminar un género con libros asociados.")


class ServicioEditorial(ServicioBase[Editorial]):
    """Editoriales: nombre único y sin libros asociados al eliminar."""

    nombre_entidad = "una editorial"

    def __init__(
        self, repositorio: IRepositorio[Editorial], libros: IRepositorio[Libro]
    ) -> None:
        super().__init__(repositorio)
        self._libros = libros

    def _validar(self, entidad: Editorial) -> None:
        self._verificar_unico(entidad, entidad.nombre, "nombre")

    def _validar_eliminacion(self, id: int) -> None:
        if any(libro.editorial_id == id for libro in self._libros.leer_todos()):
            raise ReglaDeNegocioError("No se puede eliminar una editorial con libros asociados.")


class ServicioMoneda(ServicioBase[Moneda]):
    """Monedas: código único y sin precios expresados en ella al eliminar."""

    nombre_entidad = "una moneda"

    def __init__(self, repositorio: IRepositorio[Moneda], precios: IRepositorio[Precio]) -> None:
        super().__init__(repositorio)
        self._precios = precios

    def buscar_por_codigo(self, codigo: str) -> Optional[Moneda]:
        """Busca una moneda por su código (ARS, USD, ...)."""
        codigo = codigo.strip().upper()
        return next((m for m in self.listar() if m.codigo == codigo), None)

    def _validar(self, entidad: Moneda) -> None:
        self._verificar_unico(entidad, entidad.codigo, "codigo")

    def _validar_eliminacion(self, id: int) -> None:
        if any(precio.moneda_id == id for precio in self._precios.leer_todos()):
            raise ReglaDeNegocioError("No se puede eliminar una moneda con precios cargados.")


class ServicioTipoCotizacion(ServicioBase[TipoCotizacion]):
    """Tipos de cotización: nombre único y sin cotizaciones cargadas al eliminar."""

    nombre_entidad = "un tipo de cotización"

    def __init__(
        self,
        repositorio: IRepositorio[TipoCotizacion],
        cotizaciones: IRepositorioCotizacionDolar,
    ) -> None:
        super().__init__(repositorio)
        self._cotizaciones = cotizaciones

    def _validar(self, entidad: TipoCotizacion) -> None:
        self._verificar_unico(entidad, entidad.nombre, "nombre")

    def _validar_eliminacion(self, id: int) -> None:
        if self._cotizaciones.leer_historico_por_tipo(id):
            raise ReglaDeNegocioError(
                "No se puede eliminar un tipo de cotización con cotizaciones cargadas."
            )


# ---------------------------------------------------------------------------
# Libros, precios y stock
# ---------------------------------------------------------------------------


class ServicioLibro(ServicioBase[Libro]):
    """Libros: ISBN único, género y editorial existentes.

    Al eliminar un libro se eliminan también su stock y sus precios, porque
    no tienen sentido sin el libro.
    """

    nombre_entidad = "un libro"

    def __init__(
        self,
        repositorio: IRepositorio[Libro],
        generos: IRepositorio[Genero],
        editoriales: IRepositorio[Editorial],
        precios: IRepositorio[Precio],
        stock: IRepositorioStock,
    ) -> None:
        super().__init__(repositorio)
        self._generos = generos
        self._editoriales = editoriales
        self._precios = precios
        self._stock = stock

    def buscar_por_isbn(self, isbn: str) -> Optional[Libro]:
        """Busca un libro por ISBN."""
        return next((libro for libro in self.listar() if libro.isbn == isbn.strip()), None)

    def _validar(self, entidad: Libro) -> None:
        self._verificar_unico(entidad, entidad.isbn, "isbn")
        if self._generos.leer_por_id(entidad.genero_id) is None:
            raise EntidadNoEncontradaError(f"No existe el género con ID {entidad.genero_id}.")
        if self._editoriales.leer_por_id(entidad.editorial_id) is None:
            raise EntidadNoEncontradaError(
                f"No existe la editorial con ID {entidad.editorial_id}."
            )

    def eliminar(self, id: int) -> bool:
        if not super().eliminar(id):
            return False
        for precio in self._precios.leer_todos():
            if precio.libro_id == id and precio.id is not None:
                self._precios.eliminar(precio.id)
        self._stock.eliminar(id)
        return True


class ServicioCotizacion:
    """Cotizaciones del dólar por tipo y fecha, y conversión entre pesos y dólares.

    Para convertir se usa el valor de venta de la cotización, que es el que la
    librería aplica al fijar sus precios.
    """

    def __init__(
        self,
        repositorio: IRepositorioCotizacionDolar,
        tipos: IRepositorio[TipoCotizacion],
    ) -> None:
        self._repositorio = repositorio
        self._tipos = tipos

    def registrar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Da de alta una cotización validando el tipo y los valores."""
        self._validar(cotizacion)
        return self._repositorio.crear(cotizacion)

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Modifica la cotización de un tipo en una fecha."""
        self._validar(cotizacion)
        return self._repositorio.actualizar(cotizacion)

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Elimina la cotización de un tipo en una fecha."""
        return self._repositorio.eliminar(tipo_id, fecha)

    def obtener(self, tipo_id: int, fecha: datetime.date) -> Optional[CotizacionDolar]:
        """Cotización de un tipo en una fecha exacta."""
        return self._repositorio.leer_por_tipo_y_fecha(tipo_id, fecha)

    def historico(self, tipo_id: int) -> List[CotizacionDolar]:
        """Histórico de un tipo, ordenado por fecha."""
        return self._repositorio.leer_historico_por_tipo(tipo_id)

    def vigente(
        self, tipo_id: int, fecha: Optional[datetime.date] = None
    ) -> CotizacionDolar:
        """Última cotización del tipo registrada hasta la fecha dada (hoy por defecto)."""
        fecha = fecha or datetime.date.today()
        anteriores = [c for c in self.historico(tipo_id) if c.fecha <= fecha]
        if not anteriores:
            raise EntidadNoEncontradaError(
                f"No hay cotizaciones del tipo {tipo_id} hasta el {fecha.isoformat()}."
            )
        return anteriores[-1]

    def dolares_a_pesos(
        self, monto: float, tipo_id: int, fecha: Optional[datetime.date] = None
    ) -> float:
        """Convierte un monto en dólares a pesos."""
        return round(monto * self.vigente(tipo_id, fecha).valor_venta, 2)

    def pesos_a_dolares(
        self, monto: float, tipo_id: int, fecha: Optional[datetime.date] = None
    ) -> float:
        """Convierte un monto en pesos a dólares."""
        return round(monto / self.vigente(tipo_id, fecha).valor_venta, 2)

    def _validar(self, cotizacion: CotizacionDolar) -> None:
        if self._tipos.leer_por_id(cotizacion.tipo_id) is None:
            raise EntidadNoEncontradaError(
                f"No existe el tipo de cotización con ID {cotizacion.tipo_id}."
            )
        if cotizacion.valor_venta < cotizacion.valor_compra:
            raise ReglaDeNegocioError("El valor de venta no puede ser menor al de compra.")


class ServicioPrecio(ServicioBase[Precio]):
    """Precios: libro y moneda existentes, un único precio por libro y moneda."""

    nombre_entidad = "un precio"

    def __init__(
        self,
        repositorio: IRepositorio[Precio],
        libros: IRepositorio[Libro],
        monedas: IRepositorio[Moneda],
        cotizaciones: ServicioCotizacion,
    ) -> None:
        super().__init__(repositorio)
        self._libros = libros
        self._monedas = monedas
        self._cotizaciones = cotizaciones

    def precios_de_libro(self, libro_id: int) -> List[Precio]:
        """Todos los precios cargados para un libro."""
        return [precio for precio in self.listar() if precio.libro_id == libro_id]

    def precio_en(
        self,
        libro_id: int,
        codigo_moneda: str,
        tipo_cotizacion_id: int,
        fecha: Optional[datetime.date] = None,
    ) -> float:
        """Precio del libro en la moneda pedida (ARS o USD).

        Si el libro tiene precio cargado en esa moneda se devuelve tal cual; si
        no, se convierte desde el otro precio con la cotización vigente.
        """
        destino = codigo_moneda.strip().upper()
        precios = self.precios_de_libro(libro_id)
        if not precios:
            raise EntidadNoEncontradaError(f"El libro {libro_id} no tiene precios cargados.")
        for precio in precios:
            if self._codigo_de(precio) == destino:
                return precio.monto
        for precio in precios:
            origen = self._codigo_de(precio)
            if (origen, destino) == (CODIGO_DOLARES, CODIGO_PESOS):
                return self._cotizaciones.dolares_a_pesos(
                    precio.monto, tipo_cotizacion_id, fecha
                )
            if (origen, destino) == (CODIGO_PESOS, CODIGO_DOLARES):
                return self._cotizaciones.pesos_a_dolares(
                    precio.monto, tipo_cotizacion_id, fecha
                )
        raise ReglaDeNegocioError(
            f"Solo se convierte entre {CODIGO_PESOS} y {CODIGO_DOLARES}; "
            f"no hay precio del libro {libro_id} para convertir a {destino}."
        )

    def _codigo_de(self, precio: Precio) -> str:
        moneda = self._monedas.leer_por_id(precio.moneda_id)
        return moneda.codigo if moneda else ""

    def _validar(self, entidad: Precio) -> None:
        if self._libros.leer_por_id(entidad.libro_id) is None:
            raise EntidadNoEncontradaError(f"No existe el libro con ID {entidad.libro_id}.")
        if self._monedas.leer_por_id(entidad.moneda_id) is None:
            raise EntidadNoEncontradaError(f"No existe la moneda con ID {entidad.moneda_id}.")
        for existente in self.listar():
            misma_clave = (existente.libro_id, existente.moneda_id) == (
                entidad.libro_id,
                entidad.moneda_id,
            )
            if misma_clave and existente.id != entidad.id:
                raise ReglaDeNegocioError(
                    "El libro ya tiene un precio en esa moneda; modificá el existente."
                )


class ServicioStock:
    """Stock por libro: alta, consulta, ingresos y retiros de unidades."""

    def __init__(self, repositorio: IRepositorioStock, libros: IRepositorio[Libro]) -> None:
        self._repositorio = repositorio
        self._libros = libros

    def crear(self, stock: Stock) -> Stock:
        """Da de alta el stock de un libro existente."""
        self._verificar_libro(stock.libro_id)
        return self._repositorio.crear(stock)

    def obtener(self, libro_id: int) -> Optional[Stock]:
        """Stock de un libro, o None si no tiene registro."""
        return self._repositorio.leer_por_libro(libro_id)

    def listar(self) -> List[Stock]:
        """Stock de todos los libros que tienen registro."""
        registros = []
        for libro in self._libros.leer_todos():
            stock = self.obtener(libro.id) if libro.id is not None else None
            if stock is not None:
                registros.append(stock)
        return registros

    def actualizar(self, stock: Stock) -> Stock:
        """Reemplaza el registro de stock de un libro."""
        self._verificar_libro(stock.libro_id)
        return self._repositorio.actualizar(stock)

    def eliminar(self, libro_id: int) -> bool:
        """Elimina el registro de stock de un libro."""
        return self._repositorio.eliminar(libro_id)

    def ingresar(self, libro_id: int, cantidad: int) -> Stock:
        """Suma unidades; si el libro no tenía registro, lo crea."""
        if cantidad <= 0:
            raise ReglaDeNegocioError("La cantidad a ingresar debe ser mayor a 0.")
        actual = self.obtener(libro_id)
        if actual is None:
            return self.crear(Stock(libro_id, cantidad))
        actual.cantidad += cantidad
        return self._repositorio.actualizar(actual)

    def retirar(self, libro_id: int, cantidad: int) -> Stock:
        """Resta unidades sin permitir que el stock quede negativo."""
        if cantidad <= 0:
            raise ReglaDeNegocioError("La cantidad a retirar debe ser mayor a 0.")
        actual = self.obtener(libro_id)
        if actual is None or actual.cantidad < cantidad:
            disponible = actual.cantidad if actual else 0
            raise ReglaDeNegocioError(
                f"Stock insuficiente para el libro {libro_id}: hay {disponible}."
            )
        actual.cantidad -= cantidad
        return self._repositorio.actualizar(actual)

    def sin_stock(self) -> List[Libro]:
        """Libros sin registro de stock o con cantidad 0."""
        faltantes = []
        for libro in self._libros.leer_todos():
            stock = self.obtener(libro.id) if libro.id is not None else None
            if stock is None or stock.cantidad == 0:
                faltantes.append(libro)
        return faltantes

    def _verificar_libro(self, libro_id: int) -> None:
        if self._libros.leer_por_id(libro_id) is None:
            raise EntidadNoEncontradaError(f"No existe el libro con ID {libro_id}.")


# ---------------------------------------------------------------------------
# Composición
# ---------------------------------------------------------------------------


@dataclass
class Servicios:
    """Agrupa todos los servicios del sistema para la consola y el main."""

    generos: ServicioGenero
    editoriales: ServicioEditorial
    monedas: ServicioMoneda
    tipos_cotizacion: ServicioTipoCotizacion
    libros: ServicioLibro
    precios: ServicioPrecio
    stock: ServicioStock
    cotizaciones: ServicioCotizacion


def crear_servicios(directorio: Path = DIRECTORIO_DATOS) -> Servicios:
    """Arma los servicios con repositorios CSV que comparten la misma carpeta."""
    generos = RepositorioGenero(directorio)
    editoriales = RepositorioEditorial(directorio)
    monedas = RepositorioMoneda(directorio)
    tipos = RepositorioTipoCotizacion(directorio)
    libros = RepositorioLibro(directorio)
    precios = RepositorioPrecio(directorio)
    stock = RepositorioStock(directorio)
    cotizaciones = RepositorioCotizacionDolar(directorio)
    servicio_cotizaciones = ServicioCotizacion(cotizaciones, tipos)
    return Servicios(
        generos=ServicioGenero(generos, libros),
        editoriales=ServicioEditorial(editoriales, libros),
        monedas=ServicioMoneda(monedas, precios),
        tipos_cotizacion=ServicioTipoCotizacion(tipos, cotizaciones),
        libros=ServicioLibro(libros, generos, editoriales, precios, stock),
        precios=ServicioPrecio(precios, libros, monedas, servicio_cotizaciones),
        stock=ServicioStock(stock, libros),
        cotizaciones=servicio_cotizaciones,
    )
