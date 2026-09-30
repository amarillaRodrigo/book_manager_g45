"""Módulo principal que inicializa y ejecuta la aplicación Book Manager."""

from book_manager.services.services import crear_servicios
from book_manager.ui.console import ConsolaUI
from book_manager.preload_data.preload_data import ejecutar_precarga

def main(import_default_data: bool = False) -> None:
    """
    Punto de entrada principal de la aplicación.

    Args:
        import_default_data (bool): Si es True, ejecuta la generación de
                                    los CSV con datos iniciales antes de iniciar.
    """
    # Si la cátedra o el tester pide precargar datos por defecto
    if import_default_data:
        print("Ejecutando precarga inicial de datos...")
        try:
            ejecutar_precarga()
        except Exception as e:
            print(f"Error durante la precarga de datos: {e}")

    try:
        # 1. Inicializar todos los servicios (conecta la lógica de negocio con los CSV)
        servicios = crear_servicios()

        # 2. Instanciar la interfaz de consola, inyectando los servicios
        consola = ConsolaUI(servicios)

        # 3. Iniciar el ciclo de la interfaz mostrando el menú principal
        consola.mostrar_menu_principal()

    except Exception as e:
        print(f"Error crítico al iniciar la aplicación: {e}")

if __name__ == "__main__":
    # Ejecución estándar al llamar el script directamente desde consola
    main(import_default_data=False)
