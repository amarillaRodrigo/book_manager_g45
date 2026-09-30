"""Módulo para la precarga e importación de datos."""
import datetime
from pathlib import Path

from book_manager.entities.entities import (
    Genero, Editorial, Moneda, TipoCotizacion, Libro, Precio, Stock, CotizacionDolar
)
from book_manager.repositories.repositories import (
    RepositorioGenero, RepositorioEditorial, RepositorioMoneda,
    RepositorioTipoCotizacion, RepositorioLibro, RepositorioPrecio,
    RepositorioStock, RepositorioCotizacionDolar
)

def ejecutar_precarga():
    # Aseguramos que la carpeta exista en la ruta pedida
    csv_dir = Path(__file__).resolve().parent.parent / "migrations" / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)

    # Instanciamos los repositorios apuntando a la carpeta de migraciones
    repo_genero = RepositorioGenero(csv_dir)
    repo_editorial = RepositorioEditorial(csv_dir)
    repo_moneda = RepositorioMoneda(csv_dir)
    repo_tipo_cot = RepositorioTipoCotizacion(csv_dir)
    repo_libro = RepositorioLibro(csv_dir)
    repo_precio = RepositorioPrecio(csv_dir)
    repo_stock = RepositorioStock(csv_dir)
    repo_cot_dolar = RepositorioCotizacionDolar(csv_dir)

    # 1. Géneros (10 registros)
    generos_data = ["Ficción", "No Ficción", "Fantasía", "Ciencia Ficción", "Terror", 
                    "Misterio", "Romance", "Historia", "Biografía", "Poesía"]
    if not repo_genero.leer_todos():
        for g in generos_data:
            repo_genero.crear(Genero(nombre=g))

    # 2. Editoriales (10 registros)
    editoriales_data = ["Planeta", "Penguin", "Alfaguara", "Anagrama", "Sudamericana", 
                        "Siglo XXI", "Tusquets", "Salamandra", "Norma", "Minotauro"]
    if not repo_editorial.leer_todos():
        for e in editoriales_data:
            repo_editorial.crear(Editorial(nombre=e))

    # 3. Monedas (10 registros)
    monedas_data = [
        ("ARS", "Peso Argentino", "$"), ("USD", "Dólar", "U$S"), ("EUR", "Euro", "€"),
        ("BRL", "Real", "R$"), ("GBP", "Libra", "£"), ("CLP", "Peso Chileno", "$"),
        ("UYU", "Peso Uruguayo", "$U"), ("PYG", "Guaraní", "Gs"), ("BOB", "Boliviano", "Bs"),
        ("MXN", "Peso Mexicano", "$")
    ]
    if not repo_moneda.leer_todos():
        for m in monedas_data:
            repo_moneda.crear(Moneda(codigo=m[0], nombre=m[1], simbolo=m[2]))

    # 4. Tipo Cotización (10 registros)
    tipos_data = ["Oficial", "Blue", "MEP", "CCL", "Tarjeta", "Mayorista", "Minorista", "Cripto", "Turista", "Solidario"]
    if not repo_tipo_cot.leer_todos():
        for t in tipos_data:
            repo_tipo_cot.crear(TipoCotizacion(nombre=t))

    # 5. Libros (10 registros atados a los IDs 1 al 10 de Genero y Editorial)
    if not repo_libro.leer_todos():
        for i in range(1, 11):
            repo_libro.crear(Libro(
                isbn=f"978-000000000{i}",
                titulo=f"Libro de Prueba {i}",
                autor=f"Autor {i}",
                genero_id=i,       
                editorial_id=i,    
                anio_publicacion=2020 + (i % 5)
            ))

    # 6. Precios (10 registros, uno para cada libro en ARS)
    if not repo_precio.leer_todos():
        for i in range(1, 11):
            repo_precio.crear(Precio(
                libro_id=i,
                monto=15000.0 + (i * 1000),
                moneda_id=1 
            ))

    # 7. Stock (10 registros, uno para cada libro)
    if not repo_stock.leer_todos():
        for i in range(1, 11):
            repo_stock.crear(Stock(
                libro_id=i,
                cantidad=10 + (i * 5)
            ))

    # 8. Cotizacion Dolar (10 registros históricos para el Blue)
    if not repo_cot_dolar.leer_todos():
        hoy = datetime.date.today()
        for i in range(1, 11):
            repo_cot_dolar.crear(CotizacionDolar(
                tipo_id=2, # Dólar Blue
                fecha=hoy - datetime.timedelta(days=i),
                valor_compra=1200.0 + (i * 5),
                valor_venta=1220.0 + (i * 5) # Venta siempre > Compra
            ))

    print("Datos precargados exitosamente. Archivos CSV generados en migrations/csv.")

if __name__ == "__main__":
    ejecutar_precarga()
