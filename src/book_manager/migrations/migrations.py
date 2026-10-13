"""Módulo de migraciones para Book Manager.

Permite la migración de datos almacenados en formato CSV hacia sentencias SQL
y la posterior carga en la base de datos relacional.
"""


def migrar_datos(carpeta_csvs: str, carpeta_sqls: str) -> None:
    """Función encargada de la migración de datos de csv a sql.
    Se encarga de leer los archivos csv y crear los archivos sql
    para la inserción en la base de datos.

    Args:
        carpeta_csvs (str): Carpeta donde se encuentran los archivos csv de origen.
        carpeta_sqls (str): Carpeta donde se deben guardar los archivos sql generados.
    """
    pass
