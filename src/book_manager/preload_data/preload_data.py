"""Módulo para la precarga e importación de datos por defecto."""

import datetime
from pathlib import Path

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar,
    RepositorioEditorial,
    RepositorioGenero,
    RepositorioLibro,
    RepositorioMoneda,
    RepositorioPrecio,
    RepositorioStock,
    RepositorioTipoCotizacion,
)
from book_manager.services.services import Servicios


def precargar_datos_iniciales(servicios: Servicios) -> None:
    """Precarga monedas y tipos de cotización iniciales si no existen en el sistema."""
    monedas_existentes = {m.codigo for m in servicios.monedas.listar()}
    if "ARS" not in monedas_existentes:
        servicios.monedas.crear(Moneda(codigo="ARS", nombre="Peso Argentino", simbolo="$"))
    if "USD" not in monedas_existentes:
        servicios.monedas.crear(Moneda(codigo="USD", nombre="Dólar estadounidense", simbolo="U$S"))

    tipos_existentes = {t.nombre.casefold() for t in servicios.tipos_cotizacion.listar()}
    if "oficial" not in tipos_existentes:
        t_oficial = servicios.tipos_cotizacion.crear(
            TipoCotizacion(nombre="Oficial", descripcion="Cotización del dólar del Banco Nación")
        )
        if t_oficial.id is not None:
            servicios.cotizaciones.registrar(
                CotizacionDolar(
                    tipo_id=t_oficial.id,
                    fecha=datetime.date.today(),
                    valor_compra=980.0,
                    valor_venta=1020.0,
                )
            )

    if "blue" not in tipos_existentes:
        t_blue = servicios.tipos_cotizacion.crear(
            TipoCotizacion(nombre="Blue", descripcion="Cotización del dólar libre")
        )
        if t_blue.id is not None:
            servicios.cotizaciones.registrar(
                CotizacionDolar(
                    tipo_id=t_blue.id,
                    fecha=datetime.date.today(),
                    valor_compra=1200.0,
                    valor_venta=1230.0,
                )
            )


def ejecutar_precarga() -> None:
    """Ejecuta la precarga completa de registros de prueba en archivos CSV."""
    csv_dir = Path(__file__).resolve().parent.parent / "migrations" / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)

    repo_genero = RepositorioGenero(csv_dir)
    repo_editorial = RepositorioEditorial(csv_dir)
    repo_moneda = RepositorioMoneda(csv_dir)
    repo_tipo_cot = RepositorioTipoCotizacion(csv_dir)
    repo_libro = RepositorioLibro(csv_dir)
    repo_precio = RepositorioPrecio(csv_dir)
    repo_stock = RepositorioStock(csv_dir)
    repo_cot_dolar = RepositorioCotizacionDolar(csv_dir)

    generos_data = [
        "Ficción",
        "No Ficción",
        "Fantasía",
        "Ciencia Ficción",
        "Terror",
        "Misterio",
        "Romance",
        "Historia",
        "Biografía",
        "Poesía",
    ]
    if not repo_genero.leer_todos():
        for g in generos_data:
            repo_genero.crear(Genero(nombre=g))

    editoriales_data = [
        "Planeta",
        "Penguin",
        "Alfaguara",
        "Anagrama",
        "Sudamericana",
        "Siglo XXI",
        "Tusquets",
        "Salamandra",
        "Norma",
        "Minotauro",
    ]
    if not repo_editorial.leer_todos():
        for e in editoriales_data:
            repo_editorial.crear(Editorial(nombre=e))

    monedas_data = [
        ("ARS", "Peso Argentino", "$"),
        ("USD", "Dólar", "U$S"),
        ("EUR", "Euro", "€"),
        ("BRL", "Real", "R$"),
        ("GBP", "Libra", "£"),
        ("CLP", "Peso Chileno", "$"),
        ("UYU", "Peso Uruguayo", "$U"),
        ("PYG", "Guaraní", "Gs"),
        ("BOB", "Boliviano", "Bs"),
        ("MXN", "Peso Mexicano", "$"),
    ]
    if not repo_moneda.leer_todos():
        for m in monedas_data:
            repo_moneda.crear(Moneda(codigo=m[0], nombre=m[1], simbolo=m[2]))

    tipos_data = [
        "Oficial",
        "Blue",
        "MEP",
        "CCL",
        "Tarjeta",
        "Mayorista",
        "Minorista",
        "Cripto",
        "Turista",
        "Solidario",
    ]
    if not repo_tipo_cot.leer_todos():
        for t in tipos_data:
            repo_tipo_cot.crear(TipoCotizacion(nombre=t))

    if not repo_libro.leer_todos():
        for i in range(1, 11):
            repo_libro.crear(
                Libro(
                    isbn=f"978-000000000{i}",
                    titulo=f"Libro de Prueba {i}",
                    autor=f"Autor {i}",
                    genero_id=i,
                    editorial_id=i,
                    anio_publicacion=2020 + (i % 5),
                )
            )

    if not repo_precio.leer_todos():
        for i in range(1, 11):
            repo_precio.crear(
                Precio(
                    libro_id=i,
                    moneda_id=1,
                    monto=15000.0 + (i * 1000),
                )
            )

    if not repo_stock.leer_todos():
        for i in range(1, 11):
            repo_stock.crear(
                Stock(
                    libro_id=i,
                    cantidad=10 + (i * 5),
                )
            )

    if not repo_cot_dolar.leer_todos():
        hoy = datetime.date.today()
        for i in range(1, 11):
            repo_cot_dolar.crear(
                CotizacionDolar(
                    tipo_id=2,
                    fecha=hoy - datetime.timedelta(days=i),
                    valor_compra=1200.0 + (i * 5),
                    valor_venta=1220.0 + (i * 5),
                )
            )

    print("Datos precargados exitosamente. Archivos CSV generados en migrations/csv.")


if __name__ == "__main__":
    ejecutar_precarga()
