"""Módulo para la capa de servicios y lógica de negocio.

Los servicios aplican las reglas de negocio sobre los repositorios: validan
referencias entre entidades, evitan duplicados, protegen las eliminaciones
que dejarían datos huérfanos y resuelven operaciones propias del dominio
(movimientos de stock, conversión de precios y consulta de cotizaciones a API externa).
"""

import csv
import datetime
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar

import requests
from dotenv import load_dotenv

from book_manager.database.connection import ConexionDB, obtener_conexion
from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    EntidadBase,
    Genero,
    Libro,
    Moneda,
    Precio,
    PrecioWeb,
    Stock,
    TipoCotizacion,
)
from book_manager.repositories.repositories import (
    DIRECTORIO_DATOS,
    IRepositorio,
    IRepositorioCotizacionDolar,
    IRepositorioPrecioWeb,
    IRepositorioStock,
    RepositorioCotizacionDolar,
    RepositorioEditorial,
    RepositorioGenero,
    RepositorioLibro,
    RepositorioMoneda,
    RepositorioPrecio,
    RepositorioPrecioWeb,
    RepositorioStock,
    RepositorioTipoCotizacion,
)

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
_env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    load_dotenv()

T = TypeVar("T", bound=EntidadBase)

CODIGO_PESOS = "ARS"
CODIGO_DOLARES = "USD"
DEFAULT_API_URL = "https://dolarapi.com/v1/dolares"

# Carpeta donde se guardan los reportes generados (Excel y alertas CSV).
DIRECTORIO_REPORTES = Path(__file__).resolve().parent.parent / "reportes"

# Umbral de diferencia de precio, en porcentaje, que se usa por defecto.
UMBRAL_ALERTA_POR_DEFECTO = 10.0

# Mapeo entre los identificadores de dolarapi.com y los nombres de TipoCotizacion del sistema
MAPEO_TIPOS_API: Dict[str, str] = {
    "oficial": "Oficial",
    "blue": "Blue",
    "bolsa": "MEP",
    "mep": "MEP",
    "contadoconliqui": "CCL",
    "ccl": "CCL",
    "mayorista": "Mayorista",
    "cripto": "Cripto",
    "tarjeta": "Tarjeta",
}


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
# Libros, precios, stock y cotizaciones del dólar
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
        for precio in self._precios.leer_todos():
            if precio.libro_id == id and precio.id is not None:
                self._precios.eliminar(precio.id)
        self._stock.eliminar(id)
        return super().eliminar(id)


class ServicioCotizacionDolar:
    """Cotizaciones del dólar por tipo y fecha, descarga desde API y conversión monetaria.

    Para convertir se usa el valor de venta de la cotización, que es el que la
    librería aplica al fijar sus precios.
    """

    def __init__(
        self,
        repositorio: IRepositorioCotizacionDolar,
        tipos: IRepositorio[TipoCotizacion],
        api_url: Optional[str] = None,
    ) -> None:
        self._repositorio = repositorio
        self._tipos = tipos
        self._api_url = api_url or os.getenv("API_URL") or DEFAULT_API_URL

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

    def obtener_cotizaciones(self, url: Optional[str] = None) -> List[CotizacionDolar]:
        """Busca, descarga y registra las cotizaciones del dólar desde la API externa.

        Args:
            url (Optional[str]): URL de la API a consultar. Si no se indica, se
                utiliza la variable de entorno ``API_URL`` configurada en ``.env``.

        Returns:
            List[CotizacionDolar]: Lista de cotizaciones registradas o actualizadas
                en la base de datos.

        Raises:
            ReglaDeNegocioError: Si ocurre un error de red o formato al consultar la API.
        """
        endpoint = url or os.getenv("API_URL") or self._api_url
        try:
            respuesta = requests.get(endpoint, timeout=10)
            respuesta.raise_for_status()
            datos = respuesta.json()
        except Exception as exc:
            raise ReglaDeNegocioError(
                f"Error al obtener las cotizaciones desde la API ({endpoint}): {exc}"
            ) from exc

        if not isinstance(datos, list):
            raise ReglaDeNegocioError("Formato de respuesta inválido recibido desde la API.")

        registradas: List[CotizacionDolar] = []
        tipos_actuales = {t.nombre.casefold(): t for t in self._tipos.leer_todos()}

        for item in datos:
            if not isinstance(item, dict):
                continue

            compra_raw = item.get("compra")
            venta_raw = item.get("venta")
            if compra_raw is None or venta_raw is None:
                continue

            valor_compra = float(compra_raw)
            valor_venta = float(venta_raw)
            if valor_venta < valor_compra:
                valor_compra = valor_venta

            casa = str(item.get("casa") or "").strip().lower()
            nombre_api = str(item.get("nombre") or casa).strip()
            nombre_tipo = MAPEO_TIPOS_API.get(casa) or MAPEO_TIPOS_API.get(
                nombre_api.lower(), nombre_api.capitalize()
            )
            if not nombre_tipo:
                continue

            tipo = tipos_actuales.get(nombre_tipo.casefold())
            if tipo is None:
                tipo = self._tipos.crear(
                    TipoCotizacion(
                        nombre=nombre_tipo,
                        descripcion=f"Dólar {nombre_api or nombre_tipo} (API)",
                    )
                )
                tipos_actuales[nombre_tipo.casefold()] = tipo

            if tipo.id is None:
                continue

            fecha = self._extraer_fecha(item.get("fechaActualizacion"))
            cotizacion = CotizacionDolar(
                tipo_id=tipo.id,
                fecha=fecha,
                valor_compra=valor_compra,
                valor_venta=valor_venta,
            )

            existente = self._repositorio.leer_por_tipo_y_fecha(tipo.id, fecha)
            if existente is not None:
                guardada = self.actualizar(cotizacion)
            else:
                guardada = self.registrar(cotizacion)
            registradas.append(guardada)

        return registradas

    @staticmethod
    def _extraer_fecha(fecha_raw: Any) -> datetime.date:
        """Extrae la fecha desde una cadena ISO 8601 devuelta por la API o retorna hoy."""
        if isinstance(fecha_raw, str) and fecha_raw.strip():
            texto = fecha_raw.strip()
            try:
                return datetime.date.fromisoformat(texto[:10])
            except ValueError:
                try:
                    return datetime.datetime.fromisoformat(
                        texto.replace("Z", "+00:00")
                    ).date()
                except ValueError:
                    pass
        return datetime.date.today()

    def _validar(self, cotizacion: CotizacionDolar) -> None:
        if self._tipos.leer_por_id(cotizacion.tipo_id) is None:
            raise EntidadNoEncontradaError(
                f"No existe el tipo de cotización con ID {cotizacion.tipo_id}."
            )
        if cotizacion.valor_venta < cotizacion.valor_compra:
            raise ReglaDeNegocioError("El valor de venta no puede ser menor al de compra.")


# Alias para mantener total compatibilidad con código que importe ServicioCotizacion
ServicioCotizacion = ServicioCotizacionDolar


class ServicioPrecio(ServicioBase[Precio]):
    """Precios: libro y moneda existentes, un único precio por libro y moneda."""

    nombre_entidad = "un precio"

    def __init__(
        self,
        repositorio: IRepositorio[Precio],
        libros: IRepositorio[Libro],
        monedas: IRepositorio[Moneda],
        cotizaciones: ServicioCotizacionDolar,
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
    cotizaciones: ServicioCotizacionDolar
    comparacion_precios: "ServicioComparacionPrecios"


def crear_servicios(conexion: Optional[Any] = None) -> Servicios:
    """Arma los servicios con repositorios SQLAlchemy conectados a la base de datos."""
    db = conexion if isinstance(conexion, ConexionDB) else obtener_conexion()
    generos = RepositorioGenero(db)
    editoriales = RepositorioEditorial(db)
    monedas = RepositorioMoneda(db)
    tipos = RepositorioTipoCotizacion(db)
    libros = RepositorioLibro(db)
    precios = RepositorioPrecio(db)
    stock = RepositorioStock(db)
    cotizaciones = RepositorioCotizacionDolar(db)
    precios_web = RepositorioPrecioWeb(db)
    servicio_cotizaciones = ServicioCotizacionDolar(cotizaciones, tipos)
    return Servicios(
        generos=ServicioGenero(generos, libros),
        editoriales=ServicioEditorial(editoriales, libros),
        monedas=ServicioMoneda(monedas, precios),
        tipos_cotizacion=ServicioTipoCotizacion(tipos, cotizaciones),
        libros=ServicioLibro(libros, generos, editoriales, precios, stock),
        precios=ServicioPrecio(precios, libros, monedas, servicio_cotizaciones),
        stock=ServicioStock(stock, libros),
        cotizaciones=servicio_cotizaciones,
        comparacion_precios=ServicioComparacionPrecios(precios_web, precios, monedas),
    )


# ---------------------------------------------------------------------------
# Comparación de precios internos contra los precios de la web (Sprint 3)
# ---------------------------------------------------------------------------


@dataclass
class ComparacionPrecio:
    """Comparación entre el precio interno de un libro y el publicado en la web."""

    libro: str
    isbn: str
    precio_interno: float
    precio_web: float
    diferencia: float
    diferencia_porcentaje: float
    fecha_extraccion: datetime.date
    en_alerta: bool


class ServicioComparacionPrecios:
    """Compara los precios internos del catálogo con los extraídos de la web.

    La diferencia se calcula sobre el precio en pesos: el interno es el que
    tenemos en el sistema y el web el que publica el sitio. Superado el
    umbral de diferencia, que el usuario ingresa antes de cada ejecución del
    scraper, el libro queda en alerta.
    """

    def __init__(
        self,
        precios_web: IRepositorioPrecioWeb,
        precios: IRepositorio[Precio],
        monedas: IRepositorio[Moneda],
        directorio_reportes: Path = DIRECTORIO_REPORTES,
    ) -> None:
        """Inicializa el servicio de comparación.

        Args:
            precios_web (IRepositorioPrecioWeb): Repositorio con las
                extracciones del sitio.
            precios (IRepositorio[Precio]): Repositorio de los precios internos.
            monedas (IRepositorio[Moneda]): Repositorio de las monedas.
            directorio_reportes (Path): Carpeta donde se guardan los reportes.
        """
        self._precios_web = precios_web
        self._precios = precios
        self._monedas = monedas
        self._directorio_reportes = Path(directorio_reportes)
        self._id_pesos = self._buscar_id_pesos()

    def _buscar_id_pesos(self) -> Optional[int]:
        """Busca el ID de la moneda de pesos.

        Returns:
            Optional[int]: El ID de la moneda ARS, o None si no existe.
        """
        for moneda in self._monedas.leer_todos():
            if moneda.codigo.strip().upper() == CODIGO_PESOS:
                return moneda.id
        return None

    def _precio_interno_de(self, libro_id: int) -> Optional[float]:
        """Busca el precio interno en pesos de un libro.

        Args:
            libro_id (int): ID del libro del catálogo.

        Returns:
            Optional[float]: El precio en pesos, o None si el libro no tiene.
        """
        if self._id_pesos is None:
            return None
        for precio in self._precios.leer_todos():
            if precio.libro_id == libro_id and precio.moneda_id == self._id_pesos:
                return float(precio.monto)
        return None

    @staticmethod
    def _validar_umbral(umbral_porcentaje: float) -> float:
        """Comprueba que el umbral de diferencia sea utilizable.

        Args:
            umbral_porcentaje (float): Umbral expresado en porcentaje.

        Returns:
            float: El umbral validado.

        Raises:
            ReglaDeNegocioError: Si el umbral es negativo.
        """
        try:
            umbral = float(umbral_porcentaje)
        except (TypeError, ValueError):
            raise ReglaDeNegocioError("El umbral de diferencia debe ser un número.")
        if umbral < 0:
            raise ReglaDeNegocioError("El umbral de diferencia no puede ser negativo.")
        return umbral

    def _precio_interno_de(self, libro_id: int) -> Optional[float]:
        """Busca el precio interno en pesos de un libro.

        Args:
            libro_id (int): ID del libro del catálogo.

        Returns:
            Optional[float]: El precio en pesos, o None si el libro no tiene.
        """
        if self._id_pesos is None:
            return None
        for precio in self._precios.leer_todos():
            if precio.libro_id == libro_id and precio.moneda_id == self._id_pesos:
                return float(precio.monto)
        return None

    def _nombre_moneda(self, moneda_id: int) -> str:
        """Devuelve el código de una moneda.

        Args:
            moneda_id (int): ID de la moneda.

        Returns:
            str: El código de la moneda, o cadena vacía.
        """
        for moneda in self._monedas.leer_todos():
            if moneda.id == moneda_id:
                return moneda.codigo
        return ""

    def comparar(self, umbral_porcentaje: float = UMBRAL_ALERTA_POR_DEFECTO) -> List[ComparacionPrecio]:
        """Compara los precios internos con los precios extraídos de la web.

        Args:
            umbral_porcentaje (float): Diferencia máxima aceptada, en
                porcentaje, antes de considerar que hay una alerta.

        Returns:
            List[ComparacionPrecio]: Una comparación por libro con precio web,
                ordenadas por la magnitud de la diferencia.
        """
        umbral = self._validar_umbral(umbral_porcentaje)
        comparaciones: List[ComparacionPrecio] = []

        for precio_web in self._precios_web.ultimas_extracciones():
            interno = precio_web.precio_interno
            if interno is None:
                interno = self._precio_interno_de(precio_web.libro_id)
            if not interno:
                continue

            diferencia = round(float(precio_web.precio_ars) - float(interno), 2)
            porcentaje = round(diferencia / float(interno) * 100, 2)
            comparaciones.append(
                ComparacionPrecio(
                    libro=precio_web.titulo,
                    isbn=precio_web.isbn,
                    precio_interno=float(interno),
                    precio_web=float(precio_web.precio_ars),
                    diferencia=diferencia,
                    diferencia_porcentaje=porcentaje,
                    fecha_extraccion=precio_web.fecha_extraccion,
                    en_alerta=abs(porcentaje) > umbral,
                )
            )

        comparaciones.sort(key=lambda comparacion: abs(comparacion.diferencia_porcentaje), reverse=True)
        return comparaciones

    def alertas(self, umbral_porcentaje: float = UMBRAL_ALERTA_POR_DEFECTO) -> List[ComparacionPrecio]:
        """Devuelve solo las comparaciones que superan el umbral.

        Args:
            umbral_porcentaje (float): Diferencia máxima aceptada, en porcentaje.

        Returns:
            List[ComparacionPrecio]: Las comparaciones que están en alerta.
        """
        return [c for c in self.comparar(umbral_porcentaje) if c.en_alerta]

    def generar_reporte_excel(
        self,
        umbral_porcentaje: float = UMBRAL_ALERTA_POR_DEFECTO,
        directorio: Optional[Path] = None,
    ) -> Path:
        """Genera el reporte en Excel con la comparación de precios.

        El libro tiene dos hojas: ``Comparación`` con una fila por libro del
        catálogo y las columnas pedidas (Libro, Precio interno, Precio web,
        Diferencia y Fecha de extracción), y ``Alertas`` con los libros que
        superan el umbral de diferencia.

        Args:
            umbral_porcentaje (float): Diferencia máxima aceptada, en porcentaje.
            directorio (Optional[Path]): Carpeta donde se guarda el archivo. Si
                no se indica se usa la carpeta de reportes del proyecto.

        Returns:
            Path: La ruta del archivo `.xlsx` generado.

        Raises:
            ReglaDeNegocioError: Si no hay extracciones para comparar.
        """
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter

        comparaciones = self.comparar(umbral_porcentaje)
        if not comparaciones:
            raise ReglaDeNegocioError(
                "No hay precios web registrados para generar el reporte. "
                "Ejecute el scraping antes de generar el reporte."
            )

        carpeta = Path(directorio) if directorio is not None else self._directorio_reportes
        carpeta.mkdir(parents=True, exist_ok=True)
        marca = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta = carpeta / f"reporte_precios_{marca}.xlsx"

        libro = Workbook()
        encabezado_fondo = PatternFill("solid", fgColor="F26531")
        encabezado_texto = Font(bold=True, color="FFFFFF")

        def escribir_encabezado(hoja: Any, titulos: List[str]) -> None:
            """Escribe la fila de encabezados de una hoja.

            Args:
                hoja (Any): Hoja de trabajo.
                titulos (List[str]): Títulos de las columnas.
            """
            for indice, titulo in enumerate(titulos, start=1):
                celda = hoja.cell(row=1, column=indice, value=titulo)
                celda.fill = encabezado_fondo
                celda.font = encabezado_texto
                celda.alignment = Alignment(horizontal="center", vertical="center")
            hoja.freeze_panes = "A2"

        # ---------------------------------------------------- Hoja Comparación
        hoja = libro.active
        hoja.title = "Comparación"
        titulos = [
            "Libro",
            "Precio interno",
            "Precio web",
            "Diferencia",
            "Fecha de extracción",
            "ISBN",
            "Diferencia %",
            "Estado",
        ]
        escribir_encabezado(hoja, titulos)

        for fila, comparacion in enumerate(comparaciones, start=2):
            hoja.cell(row=fila, column=1, value=comparacion.libro)
            hoja.cell(row=fila, column=2, value=comparacion.precio_interno).number_format = "#,##0.00"
            hoja.cell(row=fila, column=3, value=comparacion.precio_web).number_format = "#,##0.00"
            hoja.cell(row=fila, column=4, value=comparacion.diferencia).number_format = "#,##0.00"
            hoja.cell(row=fila, column=5, value=comparacion.fecha_extraccion.isoformat())
            hoja.cell(row=fila, column=6, value=comparacion.isbn)
            hoja.cell(row=fila, column=7, value=comparacion.diferencia_porcentaje).number_format = "0.00"
            celda_estado = hoja.cell(
                row=fila, column=8, value="SOBRE EL UMBRAL" if comparacion.en_alerta else "OK"
            )
            if comparacion.en_alerta:
                celda_estado.font = Font(bold=True, color="B20000")

        # -------------------------------------------------------- Hoja Alertas
        hoja_alertas = libro.create_sheet("Alertas")
        escribir_encabezado(hoja_alertas, titulos)
        fila = 2
        for comparacion in comparaciones:
            if not comparacion.en_alerta:
                continue
            hoja_alertas.cell(row=fila, column=1, value=comparacion.libro)
            hoja_alertas.cell(row=fila, column=2, value=comparacion.precio_interno).number_format = "#,##0.00"
            hoja_alertas.cell(row=fila, column=3, value=comparacion.precio_web).number_format = "#,##0.00"
            hoja_alertas.cell(row=fila, column=4, value=comparacion.diferencia).number_format = "#,##0.00"
            hoja_alertas.cell(row=fila, column=5, value=comparacion.fecha_extraccion.isoformat())
            hoja_alertas.cell(row=fila, column=6, value=comparacion.isbn)
            hoja_alertas.cell(row=fila, column=7, value=comparacion.diferencia_porcentaje).number_format = "0.00"
            hoja_alertas.cell(row=fila, column=8, value="SOBRE EL UMBRAL").font = Font(
                bold=True, color="B20000"
            )
            fila += 1

        # Ancho automatico de las columnas segun el contenido.
        for hoja_actual in (hoja, hoja_alertas):
            for indice in range(1, len(titulos) + 1):
                columna = get_column_letter(indice)
                largo = max(
                    len(str(hoja_actual.cell(row=f, column=indice).value or ""))
                    for f in range(1, hoja_actual.max_row + 1)
                )
                hoja_actual.column_dimensions[columna].width = min(max(largo + 2, 12), 55)

        libro.save(ruta)
        return ruta

    def generar_alertas_csv(
        self,
        umbral_porcentaje: float = UMBRAL_ALERTA_POR_DEFECTO,
        directorio: Optional[Path] = None,
    ) -> Path:
        """Genera el archivo CSV con las alertas de diferencia de precio.

        Args:
            umbral_porcentaje (float): Diferencia máxima aceptada, en porcentaje.
            directorio (Optional[Path]): Carpeta donde se guarda el archivo. Si
                no se indica se usa la carpeta de reportes del proyecto.

        Returns:
            Path: La ruta del archivo CSV generado.

        Raises:
            ReglaDeNegocioError: Si no hay extracciones para comparar.
        """
        alertas = self.alertas(umbral_porcentaje)
        if not alertas:
            raise ReglaDeNegocioError(
                "No hay alertas de diferencia de precio para el umbral indicado."
            )

        carpeta = Path(directorio) if directorio is not None else self._directorio_reportes
        carpeta.mkdir(parents=True, exist_ok=True)
        marca = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta = carpeta / f"alertas_precios_{marca}.csv"

        with ruta.open("w", newline="", encoding="utf-8-sig") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(
                [
                    "Libro",
                    "ISBN",
                    "Precio interno",
                    "Precio web",
                    "Diferencia",
                    "Diferencia %",
                    "Fecha de extracción",
                    "Estado",
                ]
            )
            for alerta in alertas:
                escritor.writerow(
                    [
                        alerta.libro,
                        alerta.isbn,
                        f"{alerta.precio_interno:.2f}",
                        f"{alerta.precio_web:.2f}",
                        f"{alerta.diferencia:.2f}",
                        f"{alerta.diferencia_porcentaje:.2f}",
                        alerta.fecha_extraccion.isoformat(),
                        "SOBRE EL UMBRAL",
                    ]
                )

        return ruta


def pedir_umbral_diferencia(por_defecto: float = UMBRAL_ALERTA_POR_DEFECTO) -> float:
    """Pide al usuario el umbral de diferencia de precio.

    El umbral se ingresa antes de cada ejecución del scraper, como pide el
    enunciado, y se usa para decidir qué diferencias se consideran alerta.

    Args:
        por_defecto (float): Valor que se propone por defecto.

    Returns:
        float: El umbral ingresado por el usuario.
    """
    while True:
        try:
            respuesta = input(
                f"Umbral de diferencia de precio en % (por defecto {por_defecto:g}): "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            return por_defecto
        if not respuesta:
            return por_defecto
        try:
            valor = float(respuesta.replace(",", "."))
        except ValueError:
            print("Ingrese un número válido.")
            continue
        if valor < 0:
            print("El umbral no puede ser negativo.")
            continue
        return valor