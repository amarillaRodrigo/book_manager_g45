"""Módulo para la precarga e importación de datos por defecto tomando como referencia el catálogo de Cúspide."""

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
    """Ejecuta la precarga de 10 libros del catálogo oficial de Cúspide en archivos CSV."""
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

    # 1. Géneros Cúspide (10 registros)
    generos_data = [
        ("Novela / Ficción", "Obras narrativas de ficción"),
        ("Terror / Cuentos", "Narrativa de suspenso y elementos oscuros"),
        ("Ficción Contemporánea", "Obras de autores contemporáneos"),
        ("Psicología / Autoayuda", "Libros de bienestar y crecimiento personal"),
        ("Desarrollo Personal", "Reflexiones y herramientas de superación"),
        ("Economía / Finanzas", "Finanzas personales y manejo del dinero"),
        ("Psicología", "Ensayos y análisis de la mente humana"),
        ("Fantasía / Romantasy", "Novelas épicas y romance fantástico"),
        ("Historieta / Cómic", "Novelas gráficas e historietas ilustradas"),
        ("Ensayo / Divulgación", "Libros informativos y de divulgación"),
    ]
    if not repo_genero.leer_todos():
        for g_nom, g_desc in generos_data:
            repo_genero.crear(Genero(nombre=g_nom, descripcion=g_desc))

    # 2. Editoriales Cúspide (10 registros)
    editoriales_data = [
        ("Random House", "contacto@penguinrandomhouse.com", "Buenos Aires, Argentina"),
        ("Anagrama", "info@anagrama-ed.es", "Barcelona, España"),
        ("Plaza & Janés", "contacto@plazayjanes.com", "Barcelona, España"),
        ("Gaia Ediciones", "info@alfaomega.es", "Madrid, España"),
        ("Sudamericana", "contacto@sudamericana.com.ar", "Buenos Aires, Argentina"),
        ("Planeta", "contacto@editorialplaneta.com.ar", "Buenos Aires, Argentina"),
        ("Debolsillo", "info@debolsillo.com", "Buenos Aires, Argentina"),
        ("Minotauro", "consultas@editorialminotauro.com", "Barcelona, España"),
        ("VR Editoras", "contacto@vreditoras.com", "Buenos Aires, Argentina"),
        ("Siglo XXI", "info@sigloxxieditores.com.ar", "Buenos Aires, Argentina"),
    ]
    if not repo_editorial.leer_todos():
        for ed_nom, ed_cont, ed_dir in editoriales_data:
            repo_editorial.crear(Editorial(nombre=ed_nom, contacto=ed_cont, direccion=ed_dir))

    # 3. Monedas (10 registros)
    monedas_data = [
        ("ARS", "Peso Argentino", "$"),
        ("USD", "Dólar Estadounidense", "U$S"),
        ("EUR", "Euro", "€"),
        ("BRL", "Real Brasileño", "R$"),
        ("GBP", "Libra Esterlina", "£"),
        ("CLP", "Peso Chileno", "$"),
        ("UYU", "Peso Uruguayo", "$U"),
        ("PYG", "Guaraní Paraguayo", "Gs"),
        ("BOB", "Boliviano", "Bs"),
        ("MXN", "Peso Mexicano", "$"),
    ]
    if not repo_moneda.leer_todos():
        for m_cod, m_nom, m_simb in monedas_data:
            repo_moneda.crear(Moneda(codigo=m_cod, nombre=m_nom, simbolo=m_simb))

    # 4. Tipos de Cotización (10 registros)
    tipos_data = [
        ("Oficial", "Cotización oficial Banco Nación"),
        ("Blue", "Cotización del dólar libre"),
        ("MEP", "Mercado Electrónico de Pagos"),
        ("CCL", "Contado con Liquidación"),
        ("Tarjeta", "Dólar turista / tarjeta"),
        ("Mayorista", "Dólar bancario mayorista"),
        ("Minorista", "Dólar bancario minorista"),
        ("Cripto", "Cotización USDT/USDC"),
        ("Turista", "Dólar para consumo en el exterior"),
        ("Solidario", "Dólar ahorro con recargos"),
    ]
    if not repo_tipo_cot.leer_todos():
        for t_nom, t_desc in tipos_data:
            repo_tipo_cot.crear(TipoCotizacion(nombre=t_nom, descripcion=t_desc))

    # 5. Libros reales tomados del catálogo de Cúspide (10 registros)
    libros_cuspide = [
        ("978-8420479705", "En agosto nos vemos", "García Márquez, Gabriel", 1, 1, 2024),
        ("978-8433921864", "Un lugar soleado para gente sombría", "Enríquez, Mariana", 2, 2, 2024),
        ("978-8433922656", "El buen mal", "Schweblin, Samanta", 3, 2, 2024),
        ("978-8417854614", "Antes de que se enfríe el café", "Kawaguchi, Toshikazu", 3, 3, 2021),
        ("978-8416429943", "Este dolor no es mío", "Wolynn, Mark", 4, 4, 2017),
        ("978-9877389654", "Espíritu Animal", "Tajes, Magalí", 5, 5, 2024),
        ("978-9500768436", "Fluí con el dinero", "Starobinsky, Ezequiel", 6, 5, 2023),
        ("978-9504971849", "El duelo", "Rolón, Gabriel", 7, 6, 2020),
        ("978-8419654854", "Alas de ónix", "Yarros, Rebecca", 8, 6, 2024),
        ("978-9878191232", "El Eternauta", "Oesterheld, Héctor Germán", 9, 6, 2022),
    ]
    if not repo_libro.leer_todos():
        for isbn, tit, aut, gen_id, ed_id, anio in libros_cuspide:
            repo_libro.crear(
                Libro(
                    isbn=isbn,
                    titulo=tit,
                    autor=aut,
                    genero_id=gen_id,
                    editorial_id=ed_id,
                    anio_publicacion=anio,
                )
            )

    # 6. Precios exactos en ARS según Cúspide (10 registros)
    precios_cuspide = [
        (1, 1, 36499.0),
        (2, 1, 40900.0),
        (3, 1, 35499.0),
        (4, 1, 41999.0),
        (5, 1, 47500.0),
        (6, 1, 38499.0),
        (7, 1, 41999.0),
        (8, 1, 30900.0),
        (9, 1, 61900.0),
        (10, 1, 47900.0),
    ]
    if not repo_precio.leer_todos():
        for lib_id, mon_id, monto in precios_cuspide:
            repo_precio.crear(Precio(libro_id=lib_id, moneda_id=mon_id, monto=monto))

    # 7. Stock inicial Cúspide (10 registros)
    stock_cuspide = [
        (1, 20),
        (2, 15),
        (3, 18),
        (4, 25),
        (5, 12),
        (6, 30),
        (7, 10),
        (8, 40),
        (9, 8),
        (10, 22),
    ]
    if not repo_stock.leer_todos():
        for lib_id, cant in stock_cuspide:
            repo_stock.crear(Stock(libro_id=lib_id, cantidad=cant))

    # 8. Cotización Dólar (10 registros históricos)
    if not repo_cot_dolar.leer_todos():
        hoy = datetime.date.today()
        for i in range(1, 11):
            repo_cot_dolar.crear(
                CotizacionDolar(
                    tipo_id=2,  # Blue
                    fecha=hoy - datetime.timedelta(days=i),
                    valor_compra=1200.0 + (i * 2),
                    valor_venta=1225.0 + (i * 2),
                )
            )

    print("Datos oficiales de Cúspide precargados exitosamente en migrations/csv.")


if __name__ == "__main__":
    ejecutar_precarga()
