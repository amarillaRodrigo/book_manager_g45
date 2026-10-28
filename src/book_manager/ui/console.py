"""Módulo de interfaz de usuario de consola (CLI) para Book Manager."""

import csv
import datetime
from pathlib import Path
from typing import Optional
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
from book_manager.services.services import (
    EntidadNoEncontradaError,
    ReglaDeNegocioError,
    Servicios,
)


class ConsolaUI:
    """Clase encargada de la interfaz interactiva basada en consola."""

    def __init__(self, servicios: Servicios) -> None:
        self._s = servicios
        self.servicios = servicios

    def ejecutar(self) -> None:
        """Alias para mostrar_menu_principal."""
        self.mostrar_menu_principal()

    def mostrar_menu_principal(self) -> None:
        """Menú principal del sistema."""
        while True:
            print("\n=== GESTOR DE LIBROS ===")
            print("1. Libros")
            print("2. Géneros")
            print("3. Editoriales")
            print("4. Monedas")
            print("5. Tipos de cotización")
            print("6. Precios")
            print("7. Stock")
            print("8. Cotizaciones del dólar")
            print("9. Ejecutar scraping")
            print("10. Generar reporte")
            print("11. Ver historial de auditoría")
            print("0. Salir")

            opcion = self._leer("Opción: ").strip()
            if opcion == "1":
                self._menu_libros()
            elif opcion == "2":
                self._menu_generos()
            elif opcion == "3":
                self._menu_editoriales()
            elif opcion == "4":
                self._menu_monedas()
            elif opcion == "5":
                self._menu_tipos_cotizacion()
            elif opcion == "6":
                self._menu_precios()
            elif opcion == "7":
                self._menu_stock()
            elif opcion == "8":
                self._menu_cotizaciones()
            elif opcion == "9":
                self._menu_scraping()
            elif opcion == "10":
                self._menu_reporte()
            elif opcion == "11":
                self._menu_auditoria()
            elif opcion == "0":
                print("¡Hasta luego!")
                break
            else:
                print("Opción inválida. Intente de nuevo.")

    def _leer(self, prompt: str) -> str:
        """Lee una opcion del menu tolerando el fin de la entrada.

        En una ejecucion no interactiva (por ejemplo, cuando el notebook se
        corre con "Run all") no hay entrada disponible: en ese caso se
        devuelve "0" para salir del menu, en lugar de cortar la ejecucion.

        Args:
            prompt (str): Texto que se muestra al usuario.

        Returns:
            str: Lo que ingreso el usuario, o "0" si no hay entrada.
        """
        try:
            return input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return "0"

    # ---------------------------------------------------------------------------
    # Menú Libros
    # ---------------------------------------------------------------------------
    def _menu_libros(self) -> None:
        while True:
            print("\n=== LIBROS ===")
            print("1. Listar")
            print("2. Crear")
            print("3. Modificar")
            print("4. Eliminar")
            print("0. Volver")

            opcion = self._leer("Opción: ").strip()
            try:
                if opcion == "1":
                    libros = self._s.libros.listar()
                    if not libros:
                        print("No hay registros para mostrar.")
                    else:
                        for l in libros:
                            print(f"{l.id} | {l.isbn} | {l.titulo} | {l.autor}")
                elif opcion == "2":
                    isbn = self._leer("ISBN: ").strip()
                    titulo = self._leer("Título: ").strip()
                    autor = self._leer("Autor: ").strip()
                    editorial_id = int(self._leer("ID Editorial: ").strip())
                    genero_id = int(self._leer("ID Género: ").strip())
                    pub_str = self._leer("Año de publicación (ej: 2024): ").strip()
                    anio_pub = int(pub_str) if pub_str else 2024
                    nuevo = Libro(
                        isbn=isbn,
                        titulo=titulo,
                        autor=autor,
                        editorial_id=editorial_id,
                        genero_id=genero_id,
                        anio_publicacion=anio_pub,
                    )
                    creado = self._s.libros.crear(nuevo)
                    print(f"Libro creado exitosamente con ID {creado.id}.")
                elif opcion == "3":
                    id_lib = int(self._leer("ID del libro a modificar: ").strip())
                    libro = self._s.libros.obtener(id_lib)
                    isbn = self._leer(f"Nuevo ISBN (actual: {libro.isbn}): ").strip() or libro.isbn
                    titulo = self._leer(f"Nuevo Título (actual: {libro.titulo}): ").strip() or libro.titulo
                    autor = self._leer(f"Nuevo Autor (actual: {libro.autor}): ").strip() or libro.autor
                    ed_str = self._leer(f"Nuevo ID Editorial (actual: {libro.editorial_id}): ").strip()
                    editorial_id = int(ed_str) if ed_str else libro.editorial_id
                    gen_str = self._leer(f"Nuevo ID Género (actual: {libro.genero_id}): ").strip()
                    genero_id = int(gen_str) if gen_str else libro.genero_id

                    libro.isbn = isbn
                    libro.titulo = titulo
                    libro.autor = autor
                    libro.editorial_id = editorial_id
                    libro.genero_id = genero_id
                    self._s.libros.actualizar(libro)
                    print("Libro modificado exitosamente.")
                elif opcion == "4":
                    id_lib = int(self._leer("ID del libro a eliminar: ").strip())
                    if self._s.libros.eliminar(id_lib):
                        print("Libro eliminado exitosamente.")
                    else:
                        print("No se encontró el libro.")
                elif opcion == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # Menú Géneros
    # ---------------------------------------------------------------------------
    def _menu_generos(self) -> None:
        while True:
            print("\n=== GÉNEROS ===")
            print("1. Listar")
            print("2. Crear")
            print("3. Modificar")
            print("4. Eliminar")
            print("0. Volver")

            opcion = self._leer("Opción: ").strip()
            try:
                if opcion == "1":
                    generos = self._s.generos.listar()
                    if not generos:
                        print("No hay registros para mostrar.")
                    else:
                        for g in generos:
                            print(f"{g.id} | {g.nombre}")
                elif opcion == "2":
                    nom = self._leer("Nombre: ").strip()
                    desc = self._leer("Descripción (opcional): ").strip()
                    nuevo = Genero(nombre=nom, descripcion=desc)
                    creado = self._s.generos.crear(nuevo)
                    print(f"Género creado exitosamente con ID {creado.id}.")
                elif opcion == "3":
                    id_g = int(self._leer("ID a modificar: ").strip())
                    g = self._s.generos.obtener(id_g)
                    nom = self._leer(f"Nuevo nombre (actual: {g.nombre}): ").strip() or g.nombre
                    desc = self._leer(f"Nueva descripción (actual: {g.descripcion}): ").strip() or g.descripcion
                    g.nombre = nom
                    g.descripcion = desc
                    self._s.generos.actualizar(g)
                    print("Género modificado exitosamente.")
                elif opcion == "4":
                    id_g = int(self._leer("ID a eliminar: ").strip())
                    if self._s.generos.eliminar(id_g):
                        print("Género eliminado exitosamente.")
                    else:
                        print("No se encontró el género.")
                elif opcion == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # Menú Editoriales
    # ---------------------------------------------------------------------------
    def _menu_editoriales(self) -> None:
        while True:
            print("\n=== EDITORIALES ===")
            print("1. Listar")
            print("2. Crear")
            print("3. Modificar")
            print("4. Eliminar")
            print("0. Volver")

            opcion = self._leer("Opción: ").strip()
            try:
                if opcion == "1":
                    editoriales = self._s.editoriales.listar()
                    if not editoriales:
                        print("No hay registros para mostrar.")
                    else:
                        for e in editoriales:
                            print(f"{e.id} | {e.nombre}")
                elif opcion == "2":
                    nom = self._leer("Nombre: ").strip()
                    cont = self._leer("Contacto (opcional): ").strip()
                    dire = self._leer("Dirección (opcional): ").strip()
                    nueva = Editorial(nombre=nom, contacto=cont, direccion=dire)
                    creada = self._s.editoriales.crear(nueva)
                    print(f"Editorial creada exitosamente con ID {creada.id}.")
                elif opcion == "3":
                    id_ed = int(self._leer("ID a modificar: ").strip())
                    e = self._s.editoriales.obtener(id_ed)
                    nom = self._leer(f"Nuevo nombre (actual: {e.nombre}): ").strip() or e.nombre
                    cont = self._leer(f"Nuevo contacto (actual: {e.contacto}): ").strip() or e.contacto
                    dire = self._leer(f"Nueva dirección (actual: {e.direccion}): ").strip() or e.direccion
                    e.nombre = nom
                    e.contacto = cont
                    e.direccion = dire
                    self._s.editoriales.actualizar(e)
                    print("Editorial modificada exitosamente.")
                elif opcion == "4":
                    id_ed = int(self._leer("ID a eliminar: ").strip())
                    if self._s.editoriales.eliminar(id_ed):
                        print("Editorial eliminada exitosamente.")
                    else:
                        print("No se encontró la editorial.")
                elif opcion == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # Menú Monedas
    # ---------------------------------------------------------------------------
    def _menu_monedas(self) -> None:
        while True:
            print("\n=== MONEDAS ===")
            print("1. Listar")
            print("2. Crear")
            print("3. Modificar")
            print("4. Eliminar")
            print("0. Volver")

            opcion = self._leer("Opción: ").strip()
            try:
                if opcion == "1":
                    monedas = self._s.monedas.listar()
                    if not monedas:
                        print("No hay registros para mostrar.")
                    else:
                        for m in monedas:
                            print(f"{m.id} | {m.codigo} | {m.nombre}")
                elif opcion == "2":
                    cod = self._leer("Código (ej: ARS, USD): ").strip()
                    nom = self._leer("Nombre: ").strip()
                    simb = self._leer("Símbolo (ej: $): ").strip() or "$"
                    nueva = Moneda(codigo=cod, nombre=nom, simbolo=simb)
                    creada = self._s.monedas.crear(nueva)
                    print(f"Moneda creada exitosamente con ID {creada.id}.")
                elif opcion == "3":
                    id_m = int(self._leer("ID a modificar: ").strip())
                    m = self._s.monedas.obtener(id_m)
                    cod = self._leer(f"Nuevo código (actual: {m.codigo}): ").strip() or m.codigo
                    nom = self._leer(f"Nuevo nombre (actual: {m.nombre}): ").strip() or m.nombre
                    simb = self._leer(f"Nuevo símbolo (actual: {m.simbolo}): ").strip() or m.simbolo
                    m.codigo = cod
                    m.nombre = nom
                    m.simbolo = simb
                    self._s.monedas.actualizar(m)
                    print("Moneda modificada exitosamente.")
                elif opcion == "4":
                    id_m = int(self._leer("ID a eliminar: ").strip())
                    if self._s.monedas.eliminar(id_m):
                        print("Moneda eliminada exitosamente.")
                    else:
                        print("No se encontró la moneda.")
                elif opcion == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # Menú Tipos de cotización
    # ---------------------------------------------------------------------------
    def _menu_tipos_cotizacion(self) -> None:
        while True:
            print("\n=== TIPOS DE COTIZACIÓN ===")
            print("1. Listar")
            print("2. Crear")
            print("3. Modificar")
            print("4. Eliminar")
            print("0. Volver")

            opcion = self._leer("Opción: ").strip()
            try:
                if opcion == "1":
                    tipos = self._s.tipos_cotizacion.listar()
                    if not tipos:
                        print("No hay registros para mostrar.")
                    else:
                        for t in tipos:
                            print(f"{t.id} | {t.nombre}")
                elif opcion == "2":
                    nom = self._leer("Nombre: ").strip()
                    desc = self._leer("Descripción (opcional): ").strip()
                    nuevo = TipoCotizacion(nombre=nom, descripcion=desc)
                    creado = self._s.tipos_cotizacion.crear(nuevo)
                    print(f"Tipo de cotización creado exitosamente con ID {creado.id}.")
                elif opcion == "3":
                    id_t = int(self._leer("ID a modificar: ").strip())
                    t = self._s.tipos_cotizacion.obtener(id_t)
                    nom = self._leer(f"Nuevo nombre (actual: {t.nombre}): ").strip() or t.nombre
                    desc = self._leer(f"Nueva descripción (actual: {t.descripcion}): ").strip() or t.descripcion
                    t.nombre = nom
                    t.descripcion = desc
                    self._s.tipos_cotizacion.actualizar(t)
                    print("Tipo de cotización modificado exitosamente.")
                elif opcion == "4":
                    id_t = int(self._leer("ID a eliminar: ").strip())
                    if self._s.tipos_cotizacion.eliminar(id_t):
                        print("Tipo de cotización eliminado exitosamente.")
                    else:
                        print("No se encontró el tipo de cotización.")
                elif opcion == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # Menú Precios
    # ---------------------------------------------------------------------------
    def _menu_precios(self) -> None:
        while True:
            print("\n=== PRECIOS ===")
            print("1. Listar")
            print("2. Crear")
            print("3. Modificar")
            print("4. Eliminar")
            print("5. Consultar precio (ARS / USD)")
            print("6. Listar precios bimonetarios")
            print("7. Exportar precios a CSV (todas las monedas)")
            print("0. Volver")

            opcion = self._leer("Opción: ").strip()
            try:
                if opcion == "1":
                    precios = self._s.precios.listar()
                    if not precios:
                        print("No hay registros para mostrar.")
                    else:
                        for p in precios:
                            print(f"{p.id} | Libro ID: {p.libro_id} | Moneda ID: {p.moneda_id} | ${p.monto:.2f}")
                elif opcion == "2":
                    libro_id = int(self._leer("ID Libro: ").strip())
                    moneda_id = int(self._leer("ID Moneda: ").strip())
                    monto = float(self._leer("Monto: ").strip())
                    nuevo = Precio(libro_id=libro_id, moneda_id=moneda_id, monto=monto)
                    creado = self._s.precios.crear(nuevo)
                    print(f"Precio creado exitosamente con ID {creado.id}.")
                elif opcion == "3":
                    id_p = int(self._leer("ID a modificar: ").strip())
                    p = self._s.precios.obtener(id_p)
                    monto = float(self._leer(f"Nuevo monto (actual: ${p.monto:.2f}): ").strip() or p.monto)
                    p.monto = monto
                    self._s.precios.actualizar(p)
                    print("Precio modificado exitosamente.")
                elif opcion == "4":
                    id_p = int(self._leer("ID a eliminar: ").strip())
                    if self._s.precios.eliminar(id_p):
                        print("Precio eliminado exitosamente.")
                    else:
                        print("No se encontró el precio.")
                elif opcion == "5":
                    libro_id = int(self._leer("ID Libro: ").strip())
                    cod = self._leer("Moneda destino (ARS / USD): ").strip().upper()
                    tipo_id = int(self._leer("ID Tipo de cotización: ").strip())
                    val = self._s.precios.precio_en(libro_id, cod, tipo_id)
                    print(f"Precio del libro {libro_id} en {cod}: ${val:.2f}")
                elif opcion == "6":
                    self._listar_precios_bimonetarios()
                elif opcion == "7":
                    self._exportar_precios_csv()
                elif opcion == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # Menú Stock
    # ---------------------------------------------------------------------------
    def _menu_stock(self) -> None:
        while True:
            print("\n=== STOCK ===")
            print("1. Listar")
            print("2. Ingresar stock")
            print("3. Retirar stock")
            print("4. Ver sin stock")
            print("0. Volver")

            opcion = self._leer("Opción: ").strip()
            try:
                if opcion == "1":
                    stocks = self._s.stock.listar()
                    if not stocks:
                        print("No hay registros para mostrar.")
                    else:
                        for st in stocks:
                            print(f"Libro ID: {st.libro_id} | Unidades: {st.cantidad}")
                elif opcion == "2":
                    libro_id = int(self._leer("ID Libro: ").strip())
                    cant = int(self._leer("Cantidad a ingresar: ").strip())
                    st = self._s.stock.ingresar(libro_id, cant)
                    print(f"Stock actualizado. Libro {libro_id} ahora tiene {st.cantidad} unidades.")
                elif opcion == "3":
                    libro_id = int(self._leer("ID Libro: ").strip())
                    cant = int(self._leer("Cantidad a retirar: ").strip())
                    st = self._s.stock.retirar(libro_id, cant)
                    print(f"Stock actualizado. Libro {libro_id} ahora tiene {st.cantidad} unidades.")
                elif opcion == "4":
                    faltantes = self._s.stock.sin_stock()
                    if not faltantes:
                        print("Todos los libros tienen stock.")
                    else:
                        for f in faltantes:
                            print(f"Sin stock -> {f.id} | {f.isbn} | {f.titulo}")
                elif opcion == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # Menú Cotizaciones del dólar
    # ---------------------------------------------------------------------------
    def _menu_cotizaciones(self) -> None:
        while True:
            print("\n=== COTIZACIONES DEL DÓLAR ===")
            print("1. Listar / Vigente")
            print("2. Histórico por tipo")
            print("3. Registrar cotización")
            print("4. Modificar cotización")
            print("5. Eliminar cotización")
            print("6. Obtener cotizaciones desde API")
            print("0. Volver")

            opcion = self._leer("Opción: ").strip()
            try:
                if opcion == "1":
                    tipo_id = int(self._leer("ID Tipo de cotización: ").strip())
                    v = self._s.cotizaciones.vigente(tipo_id)
                    print(f"Vigente al {v.fecha}: Compra = ${v.valor_compra:.2f} | Venta = ${v.valor_venta:.2f}")
                elif opcion == "2":
                    tipo_id = int(self._leer("ID Tipo de cotización: ").strip())
                    hist = self._s.cotizaciones.historico(tipo_id)
                    if not hist:
                        print("No hay historial para este tipo.")
                    else:
                        for c in hist:
                            print(f"Fecha: {c.fecha} | Compra: ${c.valor_compra:.2f} | Venta: ${c.valor_venta:.2f}")
                elif opcion == "3":
                    tipo_id = int(self._leer("ID Tipo de cotización: ").strip())
                    fecha_str = self._leer("Fecha (YYYY-MM-DD) [dejar vacío para HOY]: ").strip()
                    fecha = datetime.date.fromisoformat(fecha_str) if fecha_str else datetime.date.today()
                    compra = float(self._leer("Valor Compra: ").strip())
                    venta = float(self._leer("Valor Venta: ").strip())
                    cot = CotizacionDolar(tipo_id=tipo_id, fecha=fecha, valor_compra=compra, valor_venta=venta)
                    self._s.cotizaciones.registrar(cot)
                    print("Cotización registrada exitosamente.")
                elif opcion == "4":
                    tipo_id = int(self._leer("ID Tipo de cotización: ").strip())
                    fecha_str = self._leer("Fecha (YYYY-MM-DD): ").strip()
                    fecha = datetime.date.fromisoformat(fecha_str)
                    compra = float(self._leer("Nuevo Valor Compra: ").strip())
                    venta = float(self._leer("Nuevo Valor Venta: ").strip())
                    cot = CotizacionDolar(tipo_id=tipo_id, fecha=fecha, valor_compra=compra, valor_venta=venta)
                    self._s.cotizaciones.actualizar(cot)
                    print("Cotización modificada exitosamente.")
                elif opcion == "5":
                    tipo_id = int(self._leer("ID Tipo de cotización: ").strip())
                    fecha_str = self._leer("Fecha (YYYY-MM-DD): ").strip()
                    fecha = datetime.date.fromisoformat(fecha_str)
                    if self._s.cotizaciones.eliminar(tipo_id, fecha):
                        print("Cotización eliminada exitosamente.")
                    else:
                        print("No se encontró la cotización.")
                elif opcion == "6":
                    cotizaciones = self._s.cotizaciones.obtener_cotizaciones()
                    if not cotizaciones:
                        print("La API no devolvió cotizaciones para registrar.")
                    else:
                        print("\n=== COTIZACIONES OBTENIDAS DESDE API ===")
                        for cot in cotizaciones:
                            tipo = self._s.tipos_cotizacion.obtener(cot.tipo_id)
                            print(
                                f"{tipo.nombre} | Fecha: {cot.fecha} | "
                                f"Compra: ${cot.valor_compra:.2f} | "
                                f"Venta: ${cot.valor_venta:.2f}"
                            )
                        print(f"Total: {len(cotizaciones)} cotizaciones guardadas/actualizadas.")
                elif opcion == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")


    # ---------------------------------------------------------------------------
    # Ejercicio 08: listado bimonetario y exportación de precios a CSV
    # ---------------------------------------------------------------------------
    def _elegir_tipo_cotizacion_opcional(self) -> Optional[int]:
        """Permite elegir un tipo de dólar para convertir precios entre ARS y USD."""
        tipos = self._s.tipos_cotizacion.listar()
        if tipos:
            print("Tipos de cotización disponibles:")
            for tipo in tipos:
                print(f"  {tipo.id}. {tipo.nombre}")
        texto = self._leer(
            "ID del tipo de cotización (Enter para usar solo precios cargados): "
        ).strip()
        if not texto:
            return None
        tipo_id = int(texto)
        self._s.tipos_cotizacion.obtener(tipo_id)  # Valida que exista.
        return tipo_id

    def _precio_en_moneda(self, libro_id: int, codigo: str, tipo_id: Optional[int]):
        """Devuelve (monto, origen); no inventa conversiones para otras monedas."""
        moneda = self._s.monedas.buscar_por_codigo(codigo)
        if moneda is None:
            return None, "Moneda no registrada"

        # Primero usar un precio registrado explícitamente en la moneda.
        for precio in self._s.precios.precios_de_libro(libro_id):
            if precio.moneda_id == moneda.id:
                return precio.monto, "Registrado"

        # El servicio del Sprint 2 solo convierte automáticamente ARS <-> USD.
        if codigo in ("ARS", "USD") and tipo_id is not None:
            try:
                monto = self._s.precios.precio_en(libro_id, codigo, tipo_id)
                return monto, "Convertido"
            except (EntidadNoEncontradaError, ReglaDeNegocioError, ZeroDivisionError):
                pass

        return None, "No disponible"

    def _listar_precios_bimonetarios(self) -> None:
        """Lista cada libro en ARS y en una segunda moneda elegida por el usuario."""
        monedas = self._s.monedas.listar()
        print("Monedas disponibles:")
        for moneda in monedas:
            print(f"  {moneda.codigo} - {moneda.nombre}")

        codigo = self._leer("Moneda a comparar con ARS: ").strip().upper()
        if codigo == "ARS":
            print("Elegí una moneda distinta de ARS para comparar.")
            return
        if self._s.monedas.buscar_por_codigo(codigo) is None:
            print(f"La moneda {codigo} no está registrada.")
            return
        if self._s.monedas.buscar_por_codigo("ARS") is None:
            print("La moneda ARS no está registrada.")
            return

        tipo_id = self._elegir_tipo_cotizacion_opcional()
        libros = self._s.libros.listar()
        if not libros:
            print("No hay libros para mostrar.")
            return

        print(f"\n=== LISTA DE PRECIOS BIMONETARIA: ARS / {codigo} ===")
        for libro in libros:
            pesos, _ = self._precio_en_moneda(libro.id, "ARS", tipo_id)
            otro, _ = self._precio_en_moneda(libro.id, codigo, tipo_id)
            texto_ars = f"{pesos:.2f}" if pesos is not None else "N/D"
            texto_otro = f"{otro:.2f}" if otro is not None else "N/D"
            print(
                f"{libro.id} | {libro.titulo} | "
                f"ARS: {texto_ars} | {codigo}: {texto_otro}"
            )
        print("N/D significa que no existe precio registrado ni conversión disponible.")

    def _exportar_precios_csv(self) -> None:
        """Exporta cada libro para todas las monedas registradas en un archivo CSV."""
        libros = self._s.libros.listar()
        monedas = self._s.monedas.listar()
        if not libros:
            print("No hay libros para exportar.")
            return
        if not monedas:
            print("No hay monedas registradas para exportar.")
            return

        tipo_id = self._elegir_tipo_cotizacion_opcional()
        archivo = Path(__file__).resolve().parents[3] / "precios_todas_monedas.csv"
        with archivo.open("w", newline="", encoding="utf-8-sig") as salida:
            escritor = csv.writer(salida)
            escritor.writerow(["libro_id", "isbn", "titulo", "moneda", "precio", "origen"])
            for libro in libros:
                for moneda in monedas:
                    monto, origen = self._precio_en_moneda(
                        libro.id, moneda.codigo, tipo_id
                    )
                    escritor.writerow([
                        libro.id,
                        libro.isbn,
                        libro.titulo,
                        moneda.codigo,
                        f"{monto:.2f}" if monto is not None else "",
                        origen,
                    ])
        print(f"CSV exportado correctamente: {archivo}")
        print(f"Filas exportadas: {len(libros) * len(monedas)}.")
        print("Los precios no disponibles se dejan vacíos, sin inventar cotizaciones.")

    # ---------------------------------------------------------------------------
    # Menú Sprint 3: scraping, reportes y auditoría
    # ---------------------------------------------------------------------------
    def _menu_scraping(self) -> None:
        """Ejecuta el scraping de Cúspide y genera el archivo de alertas.

        El umbral de diferencia de precio se pide antes de la corrida, tal
        como pide el enunciado, y es el que define qué diferencias se
        consideran alerta.
        """
        from book_manager.scraper.bookmanager_scraper.runner import (
            ejecutar_scraping_con_alertas,
        )

        print("\n=== SCRAPING DE PRECIOS EN CÚSPIDE ===")
        try:
            resumen = ejecutar_scraping_con_alertas(self._s)
        except Exception as error:
            print(f"No se pudo ejecutar el scraping: {error}")
            return

        print(f"\nLibros comparados: {resumen.get('comparaciones', 0)}")
        print(f"Alertas detectadas: {resumen.get('alertas', 0)}")
        archivo = resumen.get("archivo_alertas")
        if archivo:
            print(f"Archivo de alertas: {archivo}")

    def _menu_reporte(self) -> None:
        """Genera el reporte en Excel con la comparación de precios."""
        print("\n=== REPORTE DE COMPARACIÓN DE PRECIOS ===")
        try:
            umbral = self._leer(
                f"Umbral de diferencia de precio en % (por defecto 10): "
            )
            valor = float(umbral.replace(",", ".")) if umbral else 10.0
        except ValueError:
            print("El umbral debe ser un número. Se usa el valor por defecto.")
            valor = 10.0

        try:
            ruta = self._s.comparacion_precios.generar_reporte_excel(valor)
        except Exception as error:
            print(f"No se pudo generar el reporte: {error}")
            return

        print(f"Reporte generado en: {ruta}")

    def _menu_auditoria(self) -> None:
        """Muestra el historial de auditoría del sistema."""
        print("\n=== HISTORIAL DE AUDITORÍA ===")
        registros = self._s.auditoria.historico(50)
        if not registros:
            print("Todavía no hay operaciones auditadas.")
            return

        print(f"{'ID':>5} | {'FECHA':<19} | {'ACCIÓN':<12} | DETALLES")
        for registro in registros:
            fecha = registro.fecha.strftime("%Y-%m-%d %H:%M:%S")
            print(f"{registro.id:>5} | {fecha:<19} | {registro.accion:<12} | {registro.detalles}")

