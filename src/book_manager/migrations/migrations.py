"""Módulo de migraciones para Book Manager.

Permite la migración de datos almacenados en formato CSV hacia sentencias SQL
y la posterior carga en la base de datos relacional.

En el Sprint 3 se suma la carga directa de los archivos `.sql` ya generados,
de modo que los datos puedan restaurarse en la base de datos sin volver a
pasar por los CSV de origen.
"""

import csv
import datetime
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Type, Union

from sqlalchemy import Table, func, select, text

from book_manager.database.connection import ConexionDB, obtener_conexion
from book_manager.models.models import (
    Base,
    CotizacionDolarModel,
    EditorialModel,
    GeneroModel,
    LibroModel,
    MonedaModel,
    PrecioModel,
    StockModel,
    TipoCotizacionModel,
)

_Conversor = Callable[[str], Any]

# Carpetas por defecto utilizadas cuando el módulo se ejecuta como script.
_DIRECTORIO_CSVS_DEFECTO = Path(__file__).resolve().parent / "csv"
_DIRECTORIO_SQLS_DEFECTO = Path(__file__).resolve().parent / "sql"


def _entero(valor: str) -> Optional[int]:
    """Convierte un valor de CSV a entero, o a None si está vacío."""
    return int(valor) if valor not in (None, "") else None


def _decimal(valor: str) -> Optional[Decimal]:
    """Convierte un valor de CSV a `Decimal`, o a None si está vacío."""
    return Decimal(valor) if valor not in (None, "") else None


def _fecha(valor: str) -> Optional[datetime.date]:
    """Convierte un valor de CSV con formato ISO (AAAA-MM-DD) a `date`."""
    return datetime.date.fromisoformat(valor) if valor not in (None, "") else None


def _texto(valor: str) -> str:
    """Normaliza un valor de CSV de tipo texto, nunca retorna None."""
    return valor if valor is not None else ""


@dataclass(frozen=True)
class _EspecificacionTabla:
    """Describe cómo migrar una tabla puntual desde su CSV de origen.

    Agrupa el modelo ORM de destino, el archivo CSV de origen, el prefijo
    numérico que define el orden de generación de los `.sql` (respetando las
    dependencias de claves foráneas) y el mapeo ordenado de columna a función
    de conversión de tipos.
    """

    modelo: Type[Base]
    archivo_csv: str
    prefijo_sql: str
    columnas: Dict[str, _Conversor]


# Orden de migración: respeta las dependencias de claves foráneas, de modo
# que una tabla nunca se migra antes que las tablas que referencia.
_ESPECIFICACIONES: List[_EspecificacionTabla] = [
    _EspecificacionTabla(
        modelo=GeneroModel,
        archivo_csv="generos.csv",
        prefijo_sql="01_generos",
        columnas={"id": _entero, "nombre": _texto, "descripcion": _texto},
    ),
    _EspecificacionTabla(
        modelo=EditorialModel,
        archivo_csv="editoriales.csv",
        prefijo_sql="02_editoriales",
        columnas={"id": _entero, "nombre": _texto, "contacto": _texto, "direccion": _texto},
    ),
    _EspecificacionTabla(
        modelo=MonedaModel,
        archivo_csv="monedas.csv",
        prefijo_sql="03_monedas",
        columnas={"id": _entero, "codigo": _texto, "nombre": _texto, "simbolo": _texto},
    ),
    _EspecificacionTabla(
        modelo=TipoCotizacionModel,
        archivo_csv="tipos_cotizacion.csv",
        prefijo_sql="04_tipos_cotizacion",
        columnas={"id": _entero, "nombre": _texto, "descripcion": _texto},
    ),
    _EspecificacionTabla(
        modelo=LibroModel,
        archivo_csv="libros.csv",
        prefijo_sql="05_libros",
        columnas={
            "id": _entero,
            "isbn": _texto,
            "titulo": _texto,
            "autor": _texto,
            "anio_publicacion": _entero,
            "genero_id": _entero,
            "editorial_id": _entero,
        },
    ),
    _EspecificacionTabla(
        modelo=PrecioModel,
        archivo_csv="precios.csv",
        prefijo_sql="06_precios",
        columnas={"id": _entero, "libro_id": _entero, "moneda_id": _entero, "monto": _decimal},
    ),
    _EspecificacionTabla(
        modelo=StockModel,
        archivo_csv="stock.csv",
        prefijo_sql="07_stock",
        columnas={"id": _entero, "libro_id": _entero, "cantidad": _entero, "ubicacion": _texto},
    ),
    _EspecificacionTabla(
        modelo=CotizacionDolarModel,
        archivo_csv="cotizaciones.csv",
        prefijo_sql="08_cotizaciones",
        columnas={
            "id": _entero,
            "tipo_id": _entero,
            "fecha": _fecha,
            "valor_compra": _decimal,
            "valor_venta": _decimal,
        },
    ),
]


def _formatear_valor_sql(valor: Optional[Any]) -> str:
    """Devuelve la representación SQL literal de un valor para un INSERT.

    Los valores nulos se representan como `NULL`, los numéricos se escriben
    sin comillas y las cadenas y fechas se encierran en comillas simples,
    duplicando las comillas simples internas para que la sentencia generada
    sea válida.

    Args:
        valor (Optional[Any]): Valor ya convertido a su tipo de destino.

    Returns:
        str: Fragmento SQL listo para insertarse en la lista de VALUES.
    """
    if valor is None:
        return "NULL"
    if isinstance(valor, (int, float, Decimal)):
        return str(valor)
    if isinstance(valor, (datetime.date, datetime.datetime)):
        return f"'{valor.isoformat()}'"
    texto_escapado = str(valor).replace("'", "''")
    return f"'{texto_escapado}'"


def _generar_sentencia_insert(nombre_tabla: str, columnas: Sequence[str], fila: Dict[str, Any]) -> str:
    """Construye una sentencia `INSERT` para una fila ya convertida a tipos nativos.

    Args:
        nombre_tabla (str): Nombre de la tabla destino.
        columnas (Sequence[str]): Columnas a insertar, en el orden deseado.
        fila (Dict[str, Any]): Valores ya convertidos, indexados por columna.

    Returns:
        str: Sentencia `INSERT INTO ...` terminada en punto y coma.
    """
    columnas_sql = ", ".join(columnas)
    valores_sql = ", ".join(_formatear_valor_sql(fila[columna]) for columna in columnas)
    return f"INSERT INTO {nombre_tabla} ({columnas_sql}) VALUES ({valores_sql});"


def _leer_filas_csv(especificacion: _EspecificacionTabla, directorio_csvs: Path) -> List[Dict[str, Any]]:
    """Lee y convierte las filas del CSV correspondiente a una especificación de tabla.

    Args:
        especificacion (_EspecificacionTabla): Descripción de la tabla a migrar.
        directorio_csvs (Path): Carpeta donde se encuentran los CSV de origen.

    Returns:
        List[Dict[str, Any]]: Filas convertidas a los tipos nativos de cada columna.
    """
    ruta_csv = directorio_csvs / especificacion.archivo_csv
    filas: List[Dict[str, Any]] = []
    if not ruta_csv.exists():
        return filas

    with open(ruta_csv, mode="r", encoding="utf-8", newline="") as archivo_csv:
        lector = csv.DictReader(archivo_csv)
        for fila_csv in lector:
            fila = {
                columna: conversor(fila_csv.get(columna, ""))
                for columna, conversor in especificacion.columnas.items()
            }
            filas.append(fila)
    return filas


def _resolver_conexion_migracion(conexion: Optional[Union[str, ConexionDB]]) -> ConexionDB:
    """Obtiene la instancia de `ConexionDB` sobre la que se va a migrar.

    Args:
        conexion (Optional[Union[str, ConexionDB]]): Instancia de `ConexionDB`
            ya configurada, una cadena de conexión alternativa (pensada para
            pruebas con una base de datos temporal) o None para reutilizar la
            conexión global por defecto.

    Returns:
        ConexionDB: Conexión lista para crear tablas y ejecutar transacciones.
    """
    if isinstance(conexion, ConexionDB):
        return conexion
    if isinstance(conexion, str):
        return obtener_conexion(url=conexion)
    return obtener_conexion()


def _tabla_tiene_filas(sesion: Any, modelo: Union[Type[Base], Table]) -> bool:
    """Indica si la tabla asociada a un modelo ya contiene registros.

    Args:
        sesion (Any): Sesión de SQLAlchemy abierta.
        modelo (Union[Type[Base], Table]): Modelo ORM o tabla del metadata.

    Returns:
        bool: True si la tabla tiene al menos una fila.
    """
    cantidad = sesion.execute(select(func.count()).select_from(modelo)).scalar_one()
    return bool(cantidad)


def migrar_datos(
    carpeta_csvs: str,
    carpeta_sqls: str,
    conexion: Optional[Union[str, ConexionDB]] = None,
) -> None:
    """Función encargada de la migración de datos de csv a sql.
    Se encarga de leer los archivos csv y crear los archivos sql
    para la inserción en la base de datos.

    Lee los CSV generados en el TP1 (`generos`, `editoriales`, `monedas`,
    `tipos_cotizacion`, `libros`, `precios`, `stock` y `cotizaciones`),
    genera un archivo `.sql` por tabla dentro de `carpeta_sqls` con las
    sentencias `INSERT` correspondientes (numerados según el orden de
    dependencia de claves foráneas, de `01_generos.sql` a
    `08_cotizaciones.sql`) y ejecuta esas mismas sentencias contra la base
    de datos dentro de una única transacción, de modo que cualquier error
    revierte todos los cambios.

    Las referencias a claves foráneas (`genero_id`, `editorial_id`,
    `moneda_id`, `libro_id`, `tipo_id`) se toman directamente de los CSV,
    ya que estos expresan dichas relaciones mediante el id de la fila
    referenciada en el CSV correspondiente.

    La migración es segura de repetir: antes de insertar los datos de una
    tabla se verifica si ya tiene filas y, en ese caso, se omite su
    inserción (no se reintentan los INSERT), evitando así violaciones de
    las restricciones de unicidad sin depender de sintaxis específica de
    un motor de base de datos en particular (por ejemplo `INSERT OR
    IGNORE` de SQLite). Los archivos `.sql` sí se regeneran por completo
    en cada ejecución.

    Args:
        carpeta_csvs (str): Carpeta donde se encuentran los archivos csv de origen.
        carpeta_sqls (str): Carpeta donde se deben guardar los archivos sql generados.
        conexion (Optional[Union[str, ConexionDB]]): Conexión o cadena de
            conexión a utilizar en lugar de la conexión global por defecto.
            Pensado principalmente para pruebas, que pueden apuntar a una
            base de datos temporal sin afectar la base de datos real.
    """
    directorio_csvs = Path(carpeta_csvs)
    directorio_sqls = Path(carpeta_sqls)
    directorio_sqls.mkdir(parents=True, exist_ok=True)

    datos_por_tabla: List[Tuple[_EspecificacionTabla, List[str]]] = []
    for especificacion in _ESPECIFICACIONES:
        filas = _leer_filas_csv(especificacion, directorio_csvs)
        columnas = list(especificacion.columnas.keys())
        sentencias = [
            _generar_sentencia_insert(especificacion.modelo.__tablename__, columnas, fila)
            for fila in filas
        ]

        contenido = "\n".join(sentencias)
        if contenido:
            contenido += "\n"
        ruta_sql = directorio_sqls / f"{especificacion.prefijo_sql}.sql"
        ruta_sql.write_text(contenido, encoding="utf-8")

        datos_por_tabla.append((especificacion, sentencias))

    db = _resolver_conexion_migracion(conexion)
    db.crear_tablas(Base)

    with db.transaccion() as sesion:
        for especificacion, sentencias in datos_por_tabla:
            if not sentencias or _tabla_tiene_filas(sesion, especificacion.modelo):
                continue
            for sentencia in sentencias:
                sesion.execute(text(sentencia))


# ---------------------------------------------------------------------------
# Carga de datos desde los archivos SQL (Sprint 3 - Ejercicio 02)
# ---------------------------------------------------------------------------

# Expresión regular que reconoce el nombre de la tabla destino de un INSERT.
_RE_INSERTAR_EN = re.compile(r"INSERT\s+INTO\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)

# Prefijo numérico de los archivos .sql, que define su orden de carga.
_RE_PREFIJO_NUMERICO = re.compile(r"^(\d+)")


def _clave_de_orden(ruta: Path) -> Tuple[int, str]:
    """Calcula la clave de ordenación de un archivo `.sql`.

    Los archivos se numeran según el orden de dependencia de sus claves
    foráneas (`01_generos.sql`, `02_editoriales.sql`, ...), por lo que el
    prefijo numérico determina el orden en que deben ejecutarse.

    Args:
        ruta (Path): Ruta del archivo `.sql`.

    Returns:
        Tuple[int, str]: Prefijo numérico (o un valor alto si no tiene) y nombre.
    """
    coincidencia = _RE_PREFIJO_NUMERICO.match(ruta.stem)
    numero = int(coincidencia.group(1)) if coincidencia else 9999
    return (numero, ruta.stem)


def _separar_sentencias(texto: str) -> List[str]:
    """Divide un script SQL en sus sentencias individuales.

    El separador de statements es el punto y coma, pero se respetan los
    textos entre comillas simples (incluyendo las comillas dobles internas
    que escapan una comilla simple) y se descartan los comentarios de línea
    (`--`) y de bloque (`/* ... */`), de modo que un `;` dentro de un texto o
    de un comentario no parte la sentencia por la mitad.

    Args:
        texto (str): Contenido completo del archivo `.sql`.

    Returns:
        List[str]: Sentencias SQL individualizadas, sin el `;` final.
    """
    sentencias: List[str] = []
    actual: List[str] = []
    en_cadena = False
    en_comentario_de_bloque = False
    indice = 0

    while indice < len(texto):
        caracter = texto[indice]

        if en_comentario_de_bloque:
            if caracter == "*" and texto[indice : indice + 2] == "*/":
                en_comentario_de_bloque = False
                indice += 2
                continue
            indice += 1
            continue

        if en_cadena:
            actual.append(caracter)
            if caracter == "'":
                if texto[indice : indice + 2] == "''":
                    actual.append("'")
                    indice += 2
                    continue
                en_cadena = False
            indice += 1
            continue

        if caracter == "'":
            en_cadena = True
            actual.append(caracter)
            indice += 1
            continue

        if texto[indice : indice + 2] == "--":
            fin_de_linea = texto.find("\n", indice)
            indice = len(texto) if fin_de_linea == -1 else fin_de_linea
            continue

        if texto[indice : indice + 2] == "/*":
            en_comentario_de_bloque = True
            indice += 2
            continue

        if caracter == ";":
            sentencia = "".join(actual).strip()
            if sentencia:
                sentencias.append(sentencia)
            actual = []
            indice += 1
            continue

        actual.append(caracter)
        indice += 1

    sentencia = "".join(actual).strip()
    if sentencia:
        sentencias.append(sentencia)

    return sentencias


def _tabla_de_sentencia(sentencia: str) -> Optional[str]:
    """Obtiene el nombre de la tabla destino de una sentencia `INSERT`.

    Args:
        sentencia (str): Sentencia SQL a inspeccionar.

    Returns:
        Optional[str]: Nombre de la tabla, o None si la sentencia no es un
            `INSERT INTO`.
    """
    coincidencia = _RE_INSERTAR_EN.search(sentencia)
    return coincidencia.group(1) if coincidencia else None


def cargar_datos_desde_sql(
    carpeta_sql: str,
    conexion: Optional[Union[str, ConexionDB]] = None,
    crear_tablas: bool = True,
) -> Dict[str, int]:
    """Función encargada de cargar los datos de los archivos `.sql` en la base.

    Lee los archivos `.sql` de la carpeta indicada y ejecuta sus sentencias
    contra la base de datos. Los archivos se procesan en orden numérico
    (`01_generos.sql`, `02_editoriales.sql`, ...) para respetar el orden de
    dependencia de las claves foráneas.

    Todas las sentencias se ejecutan dentro de una única transacción: si
    alguna falla, se revierte la carga completa y no queda nada a medias.

    La carga es idempotente: si la tabla destino ya contiene filas, su
    archivo se omite, de modo que la función puede ejecutarse reiteradamente
    sin duplicar registros ni violar las restricciones de unicidad.

    Args:
        carpeta_sql (str): Carpeta donde se encuentran los archivos `.sql`.
        conexion (Optional[Union[str, ConexionDB]]): Conexión o cadena de
            conexión a utilizar en lugar de la conexión global por defecto.
            Pensado principalmente para pruebas con una base temporal.
        crear_tablas (bool): Si es True, crea las tablas del modelo antes de
            cargar los datos.

    Returns:
        Dict[str, int]: Cantidad de filas insertadas por tabla. Las tablas
            omitidas por estar ya cargadas aparecen con valor 0.

    Raises:
        FileNotFoundError: Si la carpeta de archivos `.sql` no existe.
    """
    directorio_sql = Path(carpeta_sql)
    if not directorio_sql.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de archivos SQL: {directorio_sql}")

    archivos = sorted(
        (ruta for ruta in directorio_sql.glob("*.sql") if ruta.is_file()),
        key=_clave_de_orden,
    )
    if not archivos:
        raise FileNotFoundError(f"La carpeta {directorio_sql} no contiene archivos .sql")

    db = _resolver_conexion_migracion(conexion)
    if crear_tablas:
        db.crear_tablas(Base)

    filas_por_tabla: Dict[str, int] = {}

    with db.transaccion() as sesion:
        for ruta in archivos:
            sentencias = _separar_sentencias(ruta.read_text(encoding="utf-8"))
            if not sentencias:
                continue

            tabla = _tabla_de_sentencia(sentencias[0])
            if tabla is None:
                continue

            if tabla not in Base.metadata.tables:
                print(f"  [omitido] {ruta.name}: la tabla '{tabla}' no existe en el modelo.")
                filas_por_tabla.setdefault(tabla, 0)
                continue

            if _tabla_tiene_filas(sesion, Base.metadata.tables[tabla]):
                print(f"  [omitido] {ruta.name}: la tabla '{tabla}' ya contiene datos.")
                filas_por_tabla.setdefault(tabla, 0)
                continue

            for sentencia in sentencias:
                sesion.execute(text(sentencia))
            filas_por_tabla[tabla] = len(sentencias)

    return filas_por_tabla


if __name__ == "__main__":
    migrar_datos(str(_DIRECTORIO_CSVS_DEFECTO), str(_DIRECTORIO_SQLS_DEFECTO))