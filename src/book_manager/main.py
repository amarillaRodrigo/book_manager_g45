"""Módulo principal que inicializa y ejecuta la aplicación Book Manager."""

from book_manager.preload_data.preload_data import ejecutar_precarga
from book_manager.services.services import Servicios, crear_servicios
from book_manager.ui.console import ConsolaUI


def inicializar_servicios() -> Servicios:
    """Crea los repositorios e inyecta las dependencias en la capa de servicios.

    Delega en `crear_servicios` (book_manager.services.services), que es la
    única fábrica de servicios del sistema y ya conecta todos los
    repositorios con la conexión compartida a la base de datos.

    Returns:
        Servicios: Contenedor con todos los servicios del sistema.
    """
    return crear_servicios()


def main(import_default_data: bool = True) -> None:
    """Punto de entrada principal de la aplicación.

    Args:
        import_default_data (bool): Si es True, ejecuta la precarga de datos
            leyendo los archivos CSV iniciales si los repositorios están vacíos.
    """
    if import_default_data:
        ejecutar_precarga()

    servicios = inicializar_servicios()
    consola = ConsolaUI(servicios)
    consola.mostrar_menu_principal()


if __name__ == "__main__":
    main(import_default_data=True)
