"""Módulo principal que inicializa y ejecuta la aplicación Book Manager."""

from pathlib import Path

from book_manager.preload_data.preload_data import ejecutar_precarga
from book_manager.repositories.repositories import (
    DIRECTORIO_DATOS,
    RepositorioCotizacionDolar,
    RepositorioEditorial,
    RepositorioGenero,
    RepositorioLibro,
    RepositorioMoneda,
    RepositorioPrecio,
    RepositorioStock,
    RepositorioTipoCotizacion,
)
from book_manager.services.services import (
    ServicioCotizacion,
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioMoneda,
    ServicioPrecio,
    ServicioStock,
    ServicioTipoCotizacion,
    Servicios,
)
from book_manager.ui.console import ConsolaUI


def inicializar_servicios(directorio_datos: Path = DIRECTORIO_DATOS) -> Servicios:
    """Crea los repositorios e inyecta las dependencias en la capa de servicios."""
    repo_generos = RepositorioGenero(directorio_datos)
    repo_editoriales = RepositorioEditorial(directorio_datos)
    repo_monedas = RepositorioMoneda(directorio_datos)
    repo_tipos = RepositorioTipoCotizacion(directorio_datos)
    repo_libros = RepositorioLibro(directorio_datos)
    repo_precios = RepositorioPrecio(directorio_datos)
    repo_stock = RepositorioStock(directorio_datos)
    repo_cotizaciones = RepositorioCotizacionDolar(directorio_datos)

    srv_cotizaciones = ServicioCotizacion(repo_cotizaciones, repo_tipos)
    srv_generos = ServicioGenero(repo_generos, repo_libros)
    srv_editoriales = ServicioEditorial(repo_editoriales, repo_libros)
    srv_monedas = ServicioMoneda(repo_monedas, repo_precios)
    srv_tipos = ServicioTipoCotizacion(repo_tipos, repo_cotizaciones)
    srv_libros = ServicioLibro(repo_libros, repo_generos, repo_editoriales, repo_precios, repo_stock)
    srv_precios = ServicioPrecio(repo_precios, repo_libros, repo_monedas, srv_cotizaciones)
    srv_stock = ServicioStock(repo_stock, repo_libros)

    return Servicios(
        generos=srv_generos,
        editoriales=srv_editoriales,
        monedas=srv_monedas,
        tipos_cotizacion=srv_tipos,
        libros=srv_libros,
        precios=srv_precios,
        stock=srv_stock,
        cotizaciones=srv_cotizaciones,
    )


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
