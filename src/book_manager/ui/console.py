"""Módulo de interfaz de usuario de consola (CLI) para Book Manager."""

import datetime
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
            print("0. Salir")

            opcion = input("Opción: ").strip()
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
            elif opcion == "0":
                print("¡Hasta luego!")
                break
            else:
                print("Opción inválida. Intente de nuevo.")

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

            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    libros = self._s.libros.listar()
                    if not libros:
                        print("No hay registros para mostrar.")
                    else:
                        for l in libros:
                            print(f"{l.id} | {l.isbn} | {l.titulo} | {l.autor}")
                elif opcion == "2":
                    isbn = input("ISBN: ").strip()
                    titulo = input("Título: ").strip()
                    autor = input("Autor: ").strip()
                    editorial_id = int(input("ID Editorial: ").strip())
                    genero_id = int(input("ID Género: ").strip())
                    pub_str = input("Año de publicación (ej: 2024): ").strip()
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
                    id_lib = int(input("ID del libro a modificar: ").strip())
                    libro = self._s.libros.obtener(id_lib)
                    isbn = input(f"Nuevo ISBN (actual: {libro.isbn}): ").strip() or libro.isbn
                    titulo = input(f"Nuevo Título (actual: {libro.titulo}): ").strip() or libro.titulo
                    autor = input(f"Nuevo Autor (actual: {libro.autor}): ").strip() or libro.autor
                    ed_str = input(f"Nuevo ID Editorial (actual: {libro.editorial_id}): ").strip()
                    editorial_id = int(ed_str) if ed_str else libro.editorial_id
                    gen_str = input(f"Nuevo ID Género (actual: {libro.genero_id}): ").strip()
                    genero_id = int(gen_str) if gen_str else libro.genero_id

                    libro.isbn = isbn
                    libro.titulo = titulo
                    libro.autor = autor
                    libro.editorial_id = editorial_id
                    libro.genero_id = genero_id
                    self._s.libros.actualizar(libro)
                    print("Libro modificado exitosamente.")
                elif opcion == "4":
                    id_lib = int(input("ID del libro a eliminar: ").strip())
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

            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    generos = self._s.generos.listar()
                    if not generos:
                        print("No hay registros para mostrar.")
                    else:
                        for g in generos:
                            print(f"{g.id} | {g.nombre}")
                elif opcion == "2":
                    nom = input("Nombre: ").strip()
                    desc = input("Descripción (opcional): ").strip()
                    nuevo = Genero(nombre=nom, descripcion=desc)
                    creado = self._s.generos.crear(nuevo)
                    print(f"Género creado exitosamente con ID {creado.id}.")
                elif opcion == "3":
                    id_g = int(input("ID a modificar: ").strip())
                    g = self._s.generos.obtener(id_g)
                    nom = input(f"Nuevo nombre (actual: {g.nombre}): ").strip() or g.nombre
                    desc = input(f"Nueva descripción (actual: {g.descripcion}): ").strip() or g.descripcion
                    g.nombre = nom
                    g.descripcion = desc
                    self._s.generos.actualizar(g)
                    print("Género modificado exitosamente.")
                elif opcion == "4":
                    id_g = int(input("ID a eliminar: ").strip())
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

            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    editoriales = self._s.editoriales.listar()
                    if not editoriales:
                        print("No hay registros para mostrar.")
                    else:
                        for e in editoriales:
                            print(f"{e.id} | {e.nombre}")
                elif opcion == "2":
                    nom = input("Nombre: ").strip()
                    cont = input("Contacto (opcional): ").strip()
                    dire = input("Dirección (opcional): ").strip()
                    nueva = Editorial(nombre=nom, contacto=cont, direccion=dire)
                    creada = self._s.editoriales.crear(nueva)
                    print(f"Editorial creada exitosamente con ID {creada.id}.")
                elif opcion == "3":
                    id_ed = int(input("ID a modificar: ").strip())
                    e = self._s.editoriales.obtener(id_ed)
                    nom = input(f"Nuevo nombre (actual: {e.nombre}): ").strip() or e.nombre
                    cont = input(f"Nuevo contacto (actual: {e.contacto}): ").strip() or e.contacto
                    dire = input(f"Nueva dirección (actual: {e.direccion}): ").strip() or e.direccion
                    e.nombre = nom
                    e.contacto = cont
                    e.direccion = dire
                    self._s.editoriales.actualizar(e)
                    print("Editorial modificada exitosamente.")
                elif opcion == "4":
                    id_ed = int(input("ID a eliminar: ").strip())
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

            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    monedas = self._s.monedas.listar()
                    if not monedas:
                        print("No hay registros para mostrar.")
                    else:
                        for m in monedas:
                            print(f"{m.id} | {m.codigo} | {m.nombre}")
                elif opcion == "2":
                    cod = input("Código (ej: ARS, USD): ").strip()
                    nom = input("Nombre: ").strip()
                    simb = input("Símbolo (ej: $): ").strip() or "$"
                    nueva = Moneda(codigo=cod, nombre=nom, simbolo=simb)
                    creada = self._s.monedas.crear(nueva)
                    print(f"Moneda creada exitosamente con ID {creada.id}.")
                elif opcion == "3":
                    id_m = int(input("ID a modificar: ").strip())
                    m = self._s.monedas.obtener(id_m)
                    cod = input(f"Nuevo código (actual: {m.codigo}): ").strip() or m.codigo
                    nom = input(f"Nuevo nombre (actual: {m.nombre}): ").strip() or m.nombre
                    simb = input(f"Nuevo símbolo (actual: {m.simbolo}): ").strip() or m.simbolo
                    m.codigo = cod
                    m.nombre = nom
                    m.simbolo = simb
                    self._s.monedas.actualizar(m)
                    print("Moneda modificada exitosamente.")
                elif opcion == "4":
                    id_m = int(input("ID a eliminar: ").strip())
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

            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    tipos = self._s.tipos_cotizacion.listar()
                    if not tipos:
                        print("No hay registros para mostrar.")
                    else:
                        for t in tipos:
                            print(f"{t.id} | {t.nombre}")
                elif opcion == "2":
                    nom = input("Nombre: ").strip()
                    desc = input("Descripción (opcional): ").strip()
                    nuevo = TipoCotizacion(nombre=nom, descripcion=desc)
                    creado = self._s.tipos_cotizacion.crear(nuevo)
                    print(f"Tipo de cotización creado exitosamente con ID {creado.id}.")
                elif opcion == "3":
                    id_t = int(input("ID a modificar: ").strip())
                    t = self._s.tipos_cotizacion.obtener(id_t)
                    nom = input(f"Nuevo nombre (actual: {t.nombre}): ").strip() or t.nombre
                    desc = input(f"Nueva descripción (actual: {t.descripcion}): ").strip() or t.descripcion
                    t.nombre = nom
                    t.descripcion = desc
                    self._s.tipos_cotizacion.actualizar(t)
                    print("Tipo de cotización modificado exitosamente.")
                elif opcion == "4":
                    id_t = int(input("ID a eliminar: ").strip())
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
            print("0. Volver")

            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    precios = self._s.precios.listar()
                    if not precios:
                        print("No hay registros para mostrar.")
                    else:
                        for p in precios:
                            print(f"{p.id} | Libro ID: {p.libro_id} | Moneda ID: {p.moneda_id} | ${p.monto:.2f}")
                elif opcion == "2":
                    libro_id = int(input("ID Libro: ").strip())
                    moneda_id = int(input("ID Moneda: ").strip())
                    monto = float(input("Monto: ").strip())
                    nuevo = Precio(libro_id=libro_id, moneda_id=moneda_id, monto=monto)
                    creado = self._s.precios.crear(nuevo)
                    print(f"Precio creado exitosamente con ID {creado.id}.")
                elif opcion == "3":
                    id_p = int(input("ID a modificar: ").strip())
                    p = self._s.precios.obtener(id_p)
                    monto = float(input(f"Nuevo monto (actual: ${p.monto:.2f}): ").strip() or p.monto)
                    p.monto = monto
                    self._s.precios.actualizar(p)
                    print("Precio modificado exitosamente.")
                elif opcion == "4":
                    id_p = int(input("ID a eliminar: ").strip())
                    if self._s.precios.eliminar(id_p):
                        print("Precio eliminado exitosamente.")
                    else:
                        print("No se encontró el precio.")
                elif opcion == "5":
                    libro_id = int(input("ID Libro: ").strip())
                    cod = input("Moneda destino (ARS / USD): ").strip().upper()
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    val = self._s.precios.precio_en(libro_id, cod, tipo_id)
                    print(f"Precio del libro {libro_id} en {cod}: ${val:.2f}")
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

            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    stocks = self._s.stock.listar()
                    if not stocks:
                        print("No hay registros para mostrar.")
                    else:
                        for st in stocks:
                            print(f"Libro ID: {st.libro_id} | Unidades: {st.cantidad}")
                elif opcion == "2":
                    libro_id = int(input("ID Libro: ").strip())
                    cant = int(input("Cantidad a ingresar: ").strip())
                    st = self._s.stock.ingresar(libro_id, cant)
                    print(f"Stock actualizado. Libro {libro_id} ahora tiene {st.cantidad} unidades.")
                elif opcion == "3":
                    libro_id = int(input("ID Libro: ").strip())
                    cant = int(input("Cantidad a retirar: ").strip())
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
            print("0. Volver")

            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    v = self._s.cotizaciones.vigente(tipo_id)
                    print(f"Vigente al {v.fecha}: Compra = ${v.valor_compra:.2f} | Venta = ${v.valor_venta:.2f}")
                elif opcion == "2":
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    hist = self._s.cotizaciones.historico(tipo_id)
                    if not hist:
                        print("No hay historial para este tipo.")
                    else:
                        for c in hist:
                            print(f"Fecha: {c.fecha} | Compra: ${c.valor_compra:.2f} | Venta: ${c.valor_venta:.2f}")
                elif opcion == "3":
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    fecha_str = input("Fecha (YYYY-MM-DD) [dejar vacío para HOY]: ").strip()
                    fecha = datetime.date.fromisoformat(fecha_str) if fecha_str else datetime.date.today()
                    compra = float(input("Valor Compra: ").strip())
                    venta = float(input("Valor Venta: ").strip())
                    cot = CotizacionDolar(tipo_id=tipo_id, fecha=fecha, valor_compra=compra, valor_venta=venta)
                    self._s.cotizaciones.registrar(cot)
                    print("Cotización registrada exitosamente.")
                elif opcion == "4":
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    fecha_str = input("Fecha (YYYY-MM-DD): ").strip()
                    fecha = datetime.date.fromisoformat(fecha_str)
                    compra = float(input("Nuevo Valor Compra: ").strip())
                    venta = float(input("Nuevo Valor Venta: ").strip())
                    cot = CotizacionDolar(tipo_id=tipo_id, fecha=fecha, valor_compra=compra, valor_venta=venta)
                    self._s.cotizaciones.actualizar(cot)
                    print("Cotización modificada exitosamente.")
                elif opcion == "5":
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    fecha_str = input("Fecha (YYYY-MM-DD): ").strip()
                    fecha = datetime.date.fromisoformat(fecha_str)
                    if self._s.cotizaciones.eliminar(tipo_id, fecha):
                        print("Cotización eliminada exitosamente.")
                    else:
                        print("No se encontró la cotización.")
                elif opcion == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")
