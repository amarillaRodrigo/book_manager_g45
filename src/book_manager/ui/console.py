"""Módulo de interfaz de usuario de consola (CLI) con operaciones CRUD integrales."""

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
    """Clase encargada de la interfaz interactiva para operar los CRUDs del sistema."""

    def __init__(self, servicios: Servicios) -> None:
        self._s = servicios
        self.servicios = servicios

    def ejecutar(self) -> None:
        """Alias para mostrar_menu_principal."""
        self.mostrar_menu_principal()

    def mostrar_menu_principal(self) -> None:
        """Menú principal del sistema."""
        while True:
            print("\n" + "=" * 50)
            print("         BOOK MANAGER - SISTEMA DE GESTIÓN")
            print("=" * 50)
            print("1. CRUD Libros")
            print("2. CRUD Géneros")
            print("3. CRUD Editoriales")
            print("4. CRUD Monedas")
            print("5. CRUD Tipos de Cotización")
            print("6. CRUD Cotizaciones del Dólar")
            print("7. CRUD Precios")
            print("8. CRUD Stock / Control de Inventario")
            print("0. Salir")
            print("-" * 50)

            opcion = input("Seleccione una opción: ").strip()
            if opcion == "1":
                self._crud_libros()
            elif opcion == "2":
                self._crud_generos()
            elif opcion == "3":
                self._crud_editoriales()
            elif opcion == "4":
                self._crud_monedas()
            elif opcion == "5":
                self._crud_tipos_cotizacion()
            elif opcion == "6":
                self._crud_cotizaciones()
            elif opcion == "7":
                self._crud_precios()
            elif opcion == "8":
                self._crud_stock()
            elif opcion == "0":
                print("\n¡Sesión finalizada exitosamente!")
                break
            else:
                print("Opción no válida.")

    # ---------------------------------------------------------------------------
    # CRUD Libros
    # ---------------------------------------------------------------------------
    def _crud_libros(self) -> None:
        while True:
            print("\n--- GESTIÓN DE LIBROS (CRUD) ---")
            print("1. Crear nuevo libro")
            print("2. Listar todos los libros")
            print("3. Buscar libro por ISBN")
            print("4. Actualizar libro")
            print("5. Eliminar libro")
            print("0. Volver")

            op = input("Opción: ").strip()
            try:
                if op == "1":
                    isbn = input("ISBN: ").strip()
                    titulo = input("Título: ").strip()
                    autor = input("Autor: ").strip()
                    editorial_id = int(input("ID Editorial: ").strip())
                    genero_id = int(input("ID Género: ").strip())
                    pub_str = input("Año de publicación (opcional, ej: 2024): ").strip()
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
                    print(f"¡Libro creado con éxito con ID {creado.id}!")
                elif op == "2":
                    libros = self._s.libros.listar()
                    if not libros:
                        print("No hay libros registrados.")
                    else:
                        for l in libros:
                            print(
                                f"ID: {l.id} | ISBN: {l.isbn} | Título: {l.titulo} | Autor: {l.autor} | Género ID: {l.genero_id} | Editorial ID: {l.editorial_id}"
                            )
                elif op == "3":
                    isbn = input("ISBN: ").strip()
                    l = self._s.libros.buscar_por_isbn(isbn)
                    print(f"Encontrado: {l}" if l else "No encontrado.")
                elif op == "4":
                    id_lib = int(input("ID del libro a actualizar: ").strip())
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
                    print("¡Libro actualizado!")
                elif op == "5":
                    id_lib = int(input("ID del libro a eliminar: ").strip())
                    if self._s.libros.eliminar(id_lib):
                        print("¡Libro eliminado!")
                    else:
                        print("No se encontró el libro.")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # CRUD Géneros
    # ---------------------------------------------------------------------------
    def _crud_generos(self) -> None:
        while True:
            print("\n--- GESTIÓN DE GÉNEROS (CRUD) ---")
            print("1. Crear género")
            print("2. Listar géneros")
            print("3. Actualizar género")
            print("4. Eliminar género")
            print("0. Volver")

            op = input("Opción: ").strip()
            try:
                if op == "1":
                    nom = input("Nombre género: ").strip()
                    desc = input("Descripción (opcional): ").strip()
                    nuevo = Genero(nombre=nom, descripcion=desc)
                    creado = self._s.generos.crear(nuevo)
                    print(f"¡Género creado con éxito con ID {creado.id}!")
                elif op == "2":
                    generos = self._s.generos.listar()
                    if not generos:
                        print("No hay géneros registrados.")
                    else:
                        for g in generos:
                            print(f"ID: {g.id} | Nombre: {g.nombre} | Descripción: {g.descripcion}")
                elif op == "3":
                    id_g = int(input("ID Género a actualizar: ").strip())
                    g = self._s.generos.obtener(id_g)
                    nom = input(f"Nuevo Nombre (actual: {g.nombre}): ").strip() or g.nombre
                    desc = input(f"Nueva Descripción (actual: {g.descripcion}): ").strip() or g.descripcion
                    g.nombre = nom
                    g.descripcion = desc
                    self._s.generos.actualizar(g)
                    print("¡Género actualizado!")
                elif op == "4":
                    id_g = int(input("ID Género a eliminar: ").strip())
                    if self._s.generos.eliminar(id_g):
                        print("¡Género eliminado!")
                    else:
                        print("No se encontró el género.")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # CRUD Editoriales
    # ---------------------------------------------------------------------------
    def _crud_editoriales(self) -> None:
        while True:
            print("\n--- GESTIÓN DE EDITORIALES (CRUD) ---")
            print("1. Crear editorial")
            print("2. Listar editoriales")
            print("3. Actualizar editorial")
            print("4. Eliminar editorial")
            print("0. Volver")

            op = input("Opción: ").strip()
            try:
                if op == "1":
                    nom = input("Nombre editorial: ").strip()
                    cont = input("Contacto (opcional): ").strip()
                    dire = input("Dirección (opcional): ").strip()
                    nueva = Editorial(nombre=nom, contacto=cont, direccion=dire)
                    creada = self._s.editoriales.crear(nueva)
                    print(f"¡Editorial creada con éxito con ID {creada.id}!")
                elif op == "2":
                    editoriales = self._s.editoriales.listar()
                    if not editoriales:
                        print("No hay editoriales registradas.")
                    else:
                        for e in editoriales:
                            print(f"ID: {e.id} | Nombre: {e.nombre} | Contacto: {e.contacto} | Dirección: {e.direccion}")
                elif op == "3":
                    id_ed = int(input("ID Editorial a actualizar: ").strip())
                    e = self._s.editoriales.obtener(id_ed)
                    nom = input(f"Nuevo Nombre (actual: {e.nombre}): ").strip() or e.nombre
                    cont = input(f"Nuevo Contacto (actual: {e.contacto}): ").strip() or e.contacto
                    dire = input(f"Nueva Dirección (actual: {e.direccion}): ").strip() or e.direccion
                    e.nombre = nom
                    e.contacto = cont
                    e.direccion = dire
                    self._s.editoriales.actualizar(e)
                    print("¡Editorial actualizada!")
                elif op == "4":
                    id_ed = int(input("ID Editorial a eliminar: ").strip())
                    if self._s.editoriales.eliminar(id_ed):
                        print("¡Editorial eliminada!")
                    else:
                        print("No se encontró la editorial.")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # CRUD Monedas
    # ---------------------------------------------------------------------------
    def _crud_monedas(self) -> None:
        while True:
            print("\n--- GESTIÓN DE MONEDAS (CRUD) ---")
            print("1. Crear moneda")
            print("2. Listar monedas")
            print("3. Buscar por código")
            print("4. Actualizar moneda")
            print("5. Eliminar moneda")
            print("0. Volver")

            op = input("Opción: ").strip()
            try:
                if op == "1":
                    cod = input("Código (ej: ARS, USD): ").strip()
                    nom = input("Nombre: ").strip()
                    simb = input("Símbolo (ej: $): ").strip() or "$"
                    nueva = Moneda(codigo=cod, nombre=nom, simbolo=simb)
                    creada = self._s.monedas.crear(nueva)
                    print(f"¡Moneda creada con éxito con ID {creada.id}!")
                elif op == "2":
                    monedas = self._s.monedas.listar()
                    if not monedas:
                        print("No hay monedas registradas.")
                    else:
                        for m in monedas:
                            print(f"ID: {m.id} | Código: {m.codigo} | Nombre: {m.nombre} | Símbolo: {m.simbolo}")
                elif op == "3":
                    cod = input("Código: ").strip()
                    m = self._s.monedas.buscar_por_codigo(cod)
                    print(f"Encontrada: {m}" if m else "No encontrada.")
                elif op == "4":
                    id_m = int(input("ID Moneda a actualizar: ").strip())
                    m = self._s.monedas.obtener(id_m)
                    cod = input(f"Nuevo Código (actual: {m.codigo}): ").strip() or m.codigo
                    nom = input(f"Nuevo Nombre (actual: {m.nombre}): ").strip() or m.nombre
                    simb = input(f"Nuevo Símbolo (actual: {m.simbolo}): ").strip() or m.simbolo
                    m.codigo = cod
                    m.nombre = nom
                    m.simbolo = simb
                    self._s.monedas.actualizar(m)
                    print("¡Moneda actualizada!")
                elif op == "5":
                    id_m = int(input("ID Moneda a eliminar: ").strip())
                    if self._s.monedas.eliminar(id_m):
                        print("¡Moneda eliminada!")
                    else:
                        print("No se encontró la moneda.")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # CRUD Tipos de Cotización
    # ---------------------------------------------------------------------------
    def _crud_tipos_cotizacion(self) -> None:
        while True:
            print("\n--- GESTIÓN DE TIPOS DE COTIZACIÓN (CRUD) ---")
            print("1. Crear tipo de cotización")
            print("2. Listar tipos de cotización")
            print("3. Actualizar tipo de cotización")
            print("4. Eliminar tipo de cotización")
            print("0. Volver")

            op = input("Opción: ").strip()
            try:
                if op == "1":
                    nom = input("Nombre (ej: Oficial, Blue, MEP): ").strip()
                    desc = input("Descripción (opcional): ").strip()
                    nuevo = TipoCotizacion(nombre=nom, descripcion=desc)
                    creado = self._s.tipos_cotizacion.crear(nuevo)
                    print(f"¡Tipo de cotización creado con éxito con ID {creado.id}!")
                elif op == "2":
                    tipos = self._s.tipos_cotizacion.listar()
                    if not tipos:
                        print("No hay tipos de cotización registrados.")
                    else:
                        for t in tipos:
                            print(f"ID: {t.id} | Nombre: {t.nombre} | Descripción: {t.descripcion}")
                elif op == "3":
                    id_t = int(input("ID Tipo de cotización a actualizar: ").strip())
                    t = self._s.tipos_cotizacion.obtener(id_t)
                    nom = input(f"Nuevo Nombre (actual: {t.nombre}): ").strip() or t.nombre
                    desc = input(f"Nueva Descripción (actual: {t.descripcion}): ").strip() or t.descripcion
                    t.nombre = nom
                    t.descripcion = desc
                    self._s.tipos_cotizacion.actualizar(t)
                    print("¡Tipo de cotización actualizado!")
                elif op == "4":
                    id_t = int(input("ID Tipo de cotización a eliminar: ").strip())
                    if self._s.tipos_cotizacion.eliminar(id_t):
                        print("¡Tipo de cotización eliminado!")
                    else:
                        print("No se encontró el tipo de cotización.")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # CRUD Cotizaciones del Dólar
    # ---------------------------------------------------------------------------
    def _crud_cotizaciones(self) -> None:
        while True:
            print("\n--- GESTIÓN DE COTIZACIONES DEL DÓLAR ---")
            print("1. Registrar nueva cotización")
            print("2. Modificar cotización existente")
            print("3. Obtener cotización exacta (Tipo + Fecha)")
            print("4. Ver histórico por tipo de cotización")
            print("5. Ver cotización vigente (última hasta una fecha)")
            print("6. Convertir Dólares a Pesos")
            print("7. Convertir Pesos a Dólares")
            print("8. Eliminar cotización")
            print("0. Volver")

            op = input("Opción: ").strip()
            try:
                if op == "1":
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    fecha_str = input("Fecha (YYYY-MM-DD) [dejar vacío para HOY]: ").strip()
                    fecha = datetime.date.fromisoformat(fecha_str) if fecha_str else datetime.date.today()
                    compra = float(input("Valor Compra: ").strip())
                    venta = float(input("Valor Venta: ").strip())
                    cot = CotizacionDolar(tipo_id=tipo_id, fecha=fecha, valor_compra=compra, valor_venta=venta)
                    self._s.cotizaciones.registrar(cot)
                    print("¡Cotización registrada!")
                elif op == "2":
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    fecha_str = input("Fecha (YYYY-MM-DD): ").strip()
                    fecha = datetime.date.fromisoformat(fecha_str)
                    compra = float(input("Nuevo Valor Compra: ").strip())
                    venta = float(input("Nuevo Valor Venta: ").strip())
                    cot = CotizacionDolar(tipo_id=tipo_id, fecha=fecha, valor_compra=compra, valor_venta=venta)
                    self._s.cotizaciones.actualizar(cot)
                    print("¡Cotización actualizada!")
                elif op == "3":
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    fecha_str = input("Fecha (YYYY-MM-DD): ").strip()
                    fecha = datetime.date.fromisoformat(fecha_str)
                    c = self._s.cotizaciones.obtener(tipo_id, fecha)
                    print(f"Resultado: {c}" if c else "No se encontró cotización.")
                elif op == "4":
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    hist = self._s.cotizaciones.historico(tipo_id)
                    if not hist:
                        print("No hay historial para este tipo.")
                    else:
                        for c in hist:
                            print(f"Fecha: {c.fecha} | Compra: ${c.valor_compra:.2f} | Venta: ${c.valor_venta:.2f}")
                elif op == "5":
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    v = self._s.cotizaciones.vigente(tipo_id)
                    print(f"Vigente: {v}")
                elif op == "6":
                    monto = float(input("Monto en USD: ").strip())
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    res = self._s.cotizaciones.dolares_a_pesos(monto, tipo_id)
                    print(f"USD ${monto:.2f} = ARS ${res:.2f}")
                elif op == "7":
                    monto = float(input("Monto en ARS: ").strip())
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    res = self._s.cotizaciones.pesos_a_dolares(monto, tipo_id)
                    print(f"ARS ${monto:.2f} = USD ${res:.2f}")
                elif op == "8":
                    tipo_id = int(input("ID Tipo de cotización: ").strip())
                    fecha_str = input("Fecha (YYYY-MM-DD): ").strip()
                    fecha = datetime.date.fromisoformat(fecha_str)
                    if self._s.cotizaciones.eliminar(tipo_id, fecha):
                        print("¡Cotización eliminada!")
                    else:
                        print("No se encontró la cotización.")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # CRUD Precios
    # ---------------------------------------------------------------------------
    def _crud_precios(self) -> None:
        while True:
            print("\n--- GESTIÓN DE PRECIOS ---")
            print("1. Crear precio para un libro")
            print("2. Listar todos los precios")
            print("3. Obtener precios de un libro")
            print("4. Obtener precio convertido de un libro (ARS/USD)")
            print("5. Actualizar precio")
            print("6. Eliminar precio")
            print("0. Volver")

            op = input("Opción: ").strip()
            try:
                if op == "1":
                    libro_id = int(input("ID Libro: ").strip())
                    moneda_id = int(input("ID Moneda: ").strip())
                    monto = float(input("Monto: ").strip())
                    nuevo = Precio(libro_id=libro_id, moneda_id=moneda_id, monto=monto)
                    creado = self._s.precios.crear(nuevo)
                    print(f"¡Precio creado con éxito con ID {creado.id}!")
                elif op == "2":
                    precios = self._s.precios.listar()
                    if not precios:
                        print("No hay precios registrados.")
                    else:
                        for p in precios:
                            print(f"ID: {p.id} | Libro ID: {p.libro_id} | Moneda ID: {p.moneda_id} | Monto: ${p.monto:.2f}")
                elif op == "3":
                    libro_id = int(input("ID Libro: ").strip())
                    plist = self._s.precios.precios_de_libro(libro_id)
                    for p in plist:
                        print(f"Precio: {p}")
                elif op == "4":
                    libro_id = int(input("ID Libro: ").strip())
                    cod = input("Código Moneda destino (ARS/USD): ").strip().upper()
                    tipo_id = int(input("ID Tipo de cotización a aplicar: ").strip())
                    val = self._s.precios.precio_en(libro_id, cod, tipo_id)
                    print(f"Precio del libro {libro_id} en {cod}: ${val:.2f}")
                elif op == "5":
                    id_p = int(input("ID Precio a actualizar: ").strip())
                    p = self._s.precios.obtener(id_p)
                    monto = float(input(f"Nuevo Monto (actual: ${p.monto:.2f}): ").strip() or p.monto)
                    p.monto = monto
                    self._s.precios.actualizar(p)
                    print("¡Precio actualizado!")
                elif op == "6":
                    id_p = int(input("ID Precio a eliminar: ").strip())
                    if self._s.precios.eliminar(id_p):
                        print("¡Precio eliminado!")
                    else:
                        print("No se encontró el precio.")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    # ---------------------------------------------------------------------------
    # CRUD Stock
    # ---------------------------------------------------------------------------
    def _crud_stock(self) -> None:
        while True:
            print("\n--- GESTIÓN DE STOCK / INVENTARIO ---")
            print("1. Dar de alta registro de stock inicial para un libro")
            print("2. Listar todo el stock")
            print("3. Consultar stock de un libro")
            print("4. Ingresar unidades a stock")
            print("5. Retirar unidades de stock")
            print("6. Eliminar registro de stock")
            print("7. Ver libros sin stock o faltantes")
            print("0. Volver")

            op = input("Opción: ").strip()
            try:
                if op == "1":
                    libro_id = int(input("ID Libro: ").strip())
                    cant = int(input("Cantidad inicial: ").strip())
                    nuevo = Stock(libro_id=libro_id, cantidad=cant)
                    self._s.stock.crear(nuevo)
                    print("¡Stock creado con éxito!")
                elif op == "2":
                    stocks = self._s.stock.listar()
                    if not stocks:
                        print("No hay registros de stock.")
                    else:
                        for st in stocks:
                            print(f"Libro ID: {st.libro_id} | Cantidad disponible: {st.cantidad}")
                elif op == "3":
                    libro_id = int(input("ID Libro: ").strip())
                    st = self._s.stock.obtener(libro_id)
                    print(f"Stock: {st}" if st else "Sin registro de stock.")
                elif op == "4":
                    libro_id = int(input("ID Libro: ").strip())
                    cant = int(input("Cantidad a ingresar: ").strip())
                    st = self._s.stock.ingresar(libro_id, cant)
                    print(f"¡Stock actualizado! Nuevo total: {st.cantidad}")
                elif op == "5":
                    libro_id = int(input("ID Libro: ").strip())
                    cant = int(input("Cantidad a retirar: ").strip())
                    st = self._s.stock.retirar(libro_id, cant)
                    print(f"¡Stock actualizado! Nuevo total: {st.cantidad}")
                elif op == "6":
                    libro_id = int(input("ID Libro: ").strip())
                    if self._s.stock.eliminar(libro_id):
                        print("¡Registro de stock eliminado!")
                    else:
                        print("No se encontró el registro de stock.")
                elif op == "7":
                    faltantes = self._s.stock.sin_stock()
                    if not faltantes:
                        print("Todos los libros cuentan con stock.")
                    else:
                        for f in faltantes:
                            print(f"Sin stock -> ID Libro: {f.id} | Título: {f.titulo}")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")
