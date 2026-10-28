"""Módulo principal que inicializa y ejecuta la aplicación Book Manager."""

import sys

from book_manager.preload_data.preload_data import ejecutar_precarga
from book_manager.services.services import Servicios, crear_servicios
from book_manager.ui.console import ENTRADAS_DEMOSTRACION, ConsolaUI


def es_entorno_interactivo() -> bool:
    """Indica si la entrada estándar permite escribir al usuario.

    En una terminal hay una persona delante, pero en un notebook (Colab) o
    cuando la entrada está redireccionada no la hay. En ese caso la aplicación
    corre en modo demostración: hace el recorrido de listados, altas y reportes
    pedido por el enunciado y termina sola, de modo que un "ejecutar todo" no
    quede esperando una pulsación.

    Returns:
        bool: True si se puede leer la entrada del usuario.
    """
    if "google.colab" in sys.modules:
        return False
    if _corre_en_un_notebook():
        return False
    try:
        return bool(sys.stdin) and sys.stdin.isatty()
    except (AttributeError, ValueError):
        return False


def _corre_en_un_notebook() -> bool:
    """Indica si el código se está ejecutando dentro de un notebook.

    Returns:
        bool: True si se está corriendo en un kernel de IPython (Colab, Jupyter).
    """
    try:
        from IPython import get_ipython

        shell = get_ipython()
    except Exception:
        return False
    return shell is not None and type(shell).__name__ == "ZMQInteractiveShell"


def inicializar_servicios() -> Servicios:
    """Crea los repositorios e inyecta las dependencias en la capa de servicios.

    Delega en `crear_servicios` (book_manager.services.services), que es la
    única fábrica de servicios del sistema y ya conecta todos los
    repositorios con la conexión compartida a la base de datos.

    Returns:
        Servicios: Contenedor con todos los servicios del sistema.
    """
    return crear_servicios()


def main(import_default_data: bool = True, interactivo: bool | None = None) -> None:
    """Punto de entrada principal de la aplicación.

    Args:
        import_default_data (bool): Si es True, ejecuta la precarga de datos
            leyendo los archivos CSV iniciales si los repositorios están vacíos.
        interactivo (bool | None): Si es None se detecta el entorno. Cuando
            no hay entrada interactiva (por ejemplo, en un notebook) la
            aplicación corre en modo demostración y termina sola.
    """
    if import_default_data:
        ejecutar_precarga()

    if interactivo is None:
        interactivo = es_entorno_interactivo()

    servicios = inicializar_servicios()
    entradas = None if interactivo else ENTRADAS_DEMOSTRACION
    if not interactivo:
        print("=== MODO DEMOSTRACION (sin entrada interactiva) ===")
    consola = ConsolaUI(servicios, entradas=entradas)
    consola.mostrar_menu_principal()


if __name__ == "__main__":
    main(import_default_data=True)
