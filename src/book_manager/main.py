"""Módulo principal que inicializa y ejecuta la aplicación Book Manager."""

from book_manager.preload_data.preload_data import ejecutar_precarga, precargar_datos_iniciales
from book_manager.services.services import crear_servicios
from book_manager.ui.console import ConsolaUI


def main(import_default_data: bool = True) -> None:
    """Punto de entrada principal de la aplicación.

    Args:
        import_default_data (bool): Si es True, ejecuta la generación de
            datos iniciales antes de iniciar.
    """
    if import_default_data:
        try:
            ejecutar_precarga()
        except Exception as e:
            print(f"Error durante la precarga de datos: {e}")

    try:
        servicios = crear_servicios()
        precargar_datos_iniciales(servicios)

        consola = ConsolaUI(servicios)
        consola.mostrar_menu_principal()
    except Exception as e:
        print(f"Error crítico al iniciar la aplicación: {e}")


if __name__ == "__main__":
    main(import_default_data=False)
