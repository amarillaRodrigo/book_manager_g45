"""Módulo principal que inicializa y ejecuta la aplicación Book Manager."""

from book_manager.preload_data.preload_data import ejecutar_precarga
from book_manager.services.services import crear_servicios
from book_manager.ui.console import ConsolaUI


def main(import_default_data: bool = True) -> None:
    """Punto de entrada principal de la aplicación.

    Args:
        import_default_data (bool): Si los repositorios están vacíos, realiza
            la precarga automática de los 10 registros por entidad en los CSV.
    """
    try:
        # Precargar los 10 registros iniciales si aún no existen los datos
        ejecutar_precarga()
    except Exception as e:
        print(f"Error durante la precarga de datos: {e}")

    try:
        servicios = crear_servicios()
        consola = ConsolaUI(servicios)
        consola.mostrar_menu_principal()
    except Exception as e:
        print(f"Error crítico al iniciar la aplicación: {e}")


if __name__ == "__main__":
    main(import_default_data=True)
