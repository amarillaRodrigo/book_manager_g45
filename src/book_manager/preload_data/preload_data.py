"""Módulo para la precarga e importación de datos leyendo los archivos CSV de migrations/csv."""

import csv
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
        servicios.monedas.crear(Moneda(codigo="USD", nombre="Dólar Estadounidense", simbolo="U$S"))

    tipos_existentes = {t.nombre.casefold() for t in servicios.tipos_cotizacion.listar()}
    if "oficial" not in tipos_existentes:
        t_oficial = servicios.tipos_cotizacion.crear(
            TipoCotizacion(nombre="Oficial", descripcion="Cotización del dólar del Banco Nación")
        )
        if t_oficial.id is not None:
            servicios.cotizaciones.registrar(
                CotizacionDolar(
                    tipo_cotizacion=t_oficial,
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
                    tipo_cotizacion=t_blue,
                    fecha=datetime.date.today(),
                    valor_compra=1200.0,
                    valor_venta=1230.0,
                )
            )


def ejecutar_precarga(carpeta_csvs: Path | str | None = None) -> None:
    """Ejecuta la precarga de datos leyendo directamente los archivos CSV de migrations/csv.

    Lee cada archivo CSV oficial (generos, editoriales, monedas, tipos_cotizacion,
    libros, precios, stock y cotizaciones) y puebla los repositorios asegurando
    que los datos provengan de los archivos persistidos y no de valores hardcodeados en código.
    """
    if carpeta_csvs is None:
        csv_dir = Path(__file__).resolve().parent.parent / "migrations" / "csv"
    else:
        csv_dir = Path(carpeta_csvs)

    csv_dir.mkdir(parents=True, exist_ok=True)

    repo_genero = RepositorioGenero(csv_dir)
    repo_editorial = RepositorioEditorial(csv_dir)
    repo_moneda = RepositorioMoneda(csv_dir)
    repo_tipo_cot = RepositorioTipoCotizacion(csv_dir)
    repo_libro = RepositorioLibro(csv_dir)
    repo_precio = RepositorioPrecio(csv_dir)
    repo_stock = RepositorioStock(csv_dir)
    repo_cot_dolar = RepositorioCotizacionDolar(csv_dir)

    # 1. Cargar Géneros desde CSV
    generos_csv = csv_dir / "generos.csv"
    if generos_csv.exists() and not repo_genero.leer_todos():
        with open(generos_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                repo_genero.crear(Genero.from_dict(row))

    # 2. Cargar Editoriales desde CSV
    editoriales_csv = csv_dir / "editoriales.csv"
    if editoriales_csv.exists() and not repo_editorial.leer_todos():
        with open(editoriales_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                repo_editorial.crear(Editorial.from_dict(row))

    # 3. Cargar Monedas desde CSV
    monedas_csv = csv_dir / "monedas.csv"
    if monedas_csv.exists() and not repo_moneda.leer_todos():
        with open(monedas_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                repo_moneda.crear(Moneda.from_dict(row))

    # 4. Cargar Tipos de Cotización desde CSV
    tipos_csv = csv_dir / "tipos_cotizacion.csv"
    if tipos_csv.exists() and not repo_tipo_cot.leer_todos():
        with open(tipos_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                repo_tipo_cot.crear(TipoCotizacion.from_dict(row))

    # 5. Cargar Libros desde CSV vinculando objetos Genero y Editorial
    libros_csv = csv_dir / "libros.csv"
    if libros_csv.exists() and not repo_libro.leer_todos():
        with open(libros_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                libro = Libro.from_dict(row)
                if libro.genero_id:
                    libro.genero = repo_genero.leer_por_id(libro.genero_id)
                if libro.editorial_id:
                    libro.editorial = repo_editorial.leer_por_id(libro.editorial_id)
                repo_libro.crear(libro)

    # 6. Cargar Precios desde CSV vinculando Libro y Moneda
    precios_csv = csv_dir / "precios.csv"
    if precios_csv.exists() and not repo_precio.leer_todos():
        with open(precios_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                precio = Precio.from_dict(row)
                if precio.libro_id:
                    precio.libro = repo_libro.leer_por_id(precio.libro_id)
                if precio.moneda_id:
                    precio.moneda = repo_moneda.leer_por_id(precio.moneda_id)
                repo_precio.crear(precio)

    # 7. Cargar Stock desde CSV vinculando Libro
    stock_csv = csv_dir / "stock.csv"
    if stock_csv.exists() and not repo_stock.leer_todos():
        with open(stock_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stk = Stock.from_dict(row)
                if stk.libro_id:
                    stk.libro = repo_libro.leer_por_id(stk.libro_id)
                repo_stock.crear(stk)

    # 8. Cargar Cotizaciones desde CSV vinculando TipoCotizacion
    cotizaciones_csv = csv_dir / "cotizaciones.csv"
    if cotizaciones_csv.exists() and not repo_cot_dolar.leer_todos():
        with open(cotizaciones_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cot = CotizacionDolar.from_dict(row)
                if cot.tipo_id:
                    cot.tipo_cotizacion = repo_tipo_cot.leer_por_id(cot.tipo_id)
                repo_cot_dolar.crear(cot)

    print("Precarga completada leyendo los archivos CSV de migrations/csv.")


if __name__ == "__main__":
    ejecutar_precarga()
