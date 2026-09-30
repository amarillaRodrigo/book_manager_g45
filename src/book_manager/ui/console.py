"""Módulo de interfaz de usuario de consola (CLI) con operaciones CRUD integrales."""

class ConsolaUI:
    """Clase encargada de la interfaz interactiva para operar los CRUDs del sistema."""

    def __init__(self, servicios: Servicios) -> None:
        self._s = servicios

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
                    id_lib = int(input("ID: "))
                    isbn = input("ISBN: ").strip()
                    titulo = input("Título: ").strip()
                    autor = input("Autor: ").strip()
                    editorial_id = int(input("ID Editorial: "))
                    genero_id = int(input("ID Género: "))
                    nuevo = Libro(id=id_lib, isbn=isbn, titulo=titulo, autor=autor, editorial_id=editorial_id, genero_id=genero_id)
                    self._s.libros._repo.crear(nuevo)
                    print("¡Libro creado con éxito!")
                elif op == "2":
                    for l in self._s.libros.listar():
                        print(f"ID: {l.id} | ISBN: {l.isbn} | Título: {l.titulo} | Autor: {l.autor}")
                elif op == "3":
                    isbn = input("ISBN: ").strip()
                    l = self._s.libros.buscar_por_isbn(isbn)
                    print(f"Encontrado: {l}" if l else "No encontrado.")
                elif op == "4":
                    id_lib = int(input("ID del libro a actualizar: "))
                    isbn = input("Nuevo ISBN: ").strip()
                    titulo = input("Nuevo Título: ").strip()
                    autor = input("Nuevo Autor: ").strip()
                    editorial_id = int(input("Nuevo ID Editorial: "))
                    genero_id = int(input("Nuevo ID Género: "))
                    act = Libro(id=id_lib, isbn=isbn, titulo=titulo, autor=autor, editorial_id=editorial_id, genero_id=genero_id)
                    self._s.libros._repo.actualizar(act)
                    print("¡Libro actualizado!")
                elif op == "5":
                    id_lib = int(input("ID del libro a eliminar: "))
                    self._s.libros._repo.eliminar(id_lib)
                    print("¡Libro eliminado!")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

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
                    g_id = int(input("ID: "))
                    nombre = input("Nombre del género: ").strip()
                    self._s.generos._repo.crear(Genero(id=g_id, nombre=nombre))
                    print("¡Género creado!")
                elif op == "2":
                    for g in self._s.generos.listar():
                        print(f"ID: {g.id} | Nombre: {g.nombre}")
                elif op == "3":
                    g_id = int(input("ID género a actualizar: "))
                    nombre = input("Nuevo nombre: ").strip()
                    self._s.generos._repo.actualizar(Genero(id=g_id, nombre=nombre))
                    print("¡Género actualizado!")
                elif op == "4":
                    g_id = int(input("ID a eliminar: "))
                    self._s.generos._repo.eliminar(g_id)
                    print("¡Género eliminado!")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

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
                    e_id = int(input("ID: "))
                    nombre = input("Nombre de la editorial: ").strip()
                    self._s.editoriales._repo.crear(Editorial(id=e_id, nombre=nombre))
                    print("¡Editorial creada!")
                elif op == "2":
                    for e in self._s.editoriales.listar():
                        print(f"ID: {e.id} | Nombre: {e.nombre}")
                elif op == "3":
                    e_id = int(input("ID editorial a actualizar: "))
                    nombre = input("Nuevo nombre: ").strip()
                    self._s.editoriales._repo.actualizar(Editorial(id=e_id, nombre=nombre))
                    print("¡Editorial actualizada!")
                elif op == "4":
                    e_id = int(input("ID a eliminar: "))
                    self._s.editoriales._repo.eliminar(e_id)
                    print("¡Editorial eliminada!")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    def _crud_monedas(self) -> None:
        while True:
            print("\n--- GESTIÓN DE MONEDAS (CRUD) ---")
            print("1. Crear moneda")
            print("2. Listar monedas")
            print("3. Actualizar moneda")
            print("4. Eliminar moneda")
            print("0. Volver")
            op = input("Opción: ").strip()
            try:
                if op == "1":
                    m_id = int(input("ID: "))
                    codigo = input("Código (ej. ARS, USD): ").strip().upper()
                    nombre = input("Nombre: ").strip()
                    simbolo = input("Símbolo (ej. $, u$s): ").strip()
                    self._s.monedas._repo.crear(Moneda(id=m_id, codigo=codigo, nombre=nombre, simbolo=simbolo))
                    print("¡Moneda creada!")
                elif op == "2":
                    for m in self._s.monedas.listar():
                        print(f"ID: {m.id} | Código: {m.codigo} | Nombre: {m.nombre} | Símbolo: {m.simbolo}")
                elif op == "3":
                    m_id = int(input("ID a actualizar: "))
                    codigo = input("Nuevo Código: ").strip().upper()
                    nombre = input("Nuevo Nombre: ").strip()
                    simbolo = input("Nuevo Símbolo: ").strip()
                    self._s.monedas._repo.actualizar(Moneda(id=m_id, codigo=codigo, nombre=nombre, simbolo=simbolo))
                    print("¡Moneda actualizada!")
                elif op == "4":
                    m_id = int(input("ID a eliminar: "))
                    self._s.monedas._repo.eliminar(m_id)
                    print("¡Moneda eliminada!")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    def _crud_tipos_cotizacion(self) -> None:
        while True:
            print("\n--- GESTIÓN DE TIPOS DE COTIZACIÓN (CRUD) ---")
            print("1. Crear tipo cotización")
            print("2. Listar tipos de cotización")
            print("3. Actualizar tipo cotización")
            print("4. Eliminar tipo cotización")
            print("0. Volver")
            op = input("Opción: ").strip()
            try:
                if op == "1":
                    t_id = int(input("ID: "))
                    nombre = input("Nombre (ej. Oficial, Blue, MEP): ").strip()
                    self._s.tipos_cotizacion._repo.crear(TipoCotizacion(id=t_id, nombre=nombre))
                    print("¡Tipo de cotización creado!")
                elif op == "2":
                    for t in self._s.tipos_cotizacion.listar():
                        print(f"ID: {t.id} | Nombre: {t.nombre}")
                elif op == "3":
                    t_id = int(input("ID a actualizar: "))
                    nombre = input("Nuevo nombre: ").strip()
                    self._s.tipos_cotizacion._repo.actualizar(TipoCotizacion(id=t_id, nombre=nombre))
                    print("¡Tipo actualizado!")
                elif op == "4":
                    t_id = int(input("ID a eliminar: "))
                    self._s.tipos_cotizacion._repo.eliminar(t_id)
                    print("¡Tipo eliminado!")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    def _crud_cotizaciones(self) -> None:
        while True:
            print("\n--- GESTIÓN DE COTIZACIONES DE DÓLAR (CRUD) ---")
            print("1. Crear cotización")
            print("2. Listar / Ver cotizaciones por tipo")
            print("3. Actualizar cotización")
            print("4. Eliminar cotización")
            print("0. Volver")
            op = input("Opción: ").strip()
            try:
                if op == "1":
                    c_id = int(input("ID: "))
                    tipo_id = int(input("ID Tipo Cotización: "))
                    fecha_str = input("Fecha (YYYY-MM-DD): ").strip()
                    fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
                    compra = float(input("Valor Compra: "))
                    venta = float(input("Valor Venta: "))
                    cot = CotizacionDolar(id=c_id, tipo_cotizacion_id=tipo_id, fecha=fecha, valor_compra=compra, valor_venta=venta)
                    self._s.cotizaciones._repo.crear(cot)
                    print("¡Cotización creada!")
                elif op == "2":
                    tipo_id = int(input("ID Tipo Cotización: "))
                    for c in self._s.cotizaciones.historico(tipo_id):
                        print(f"ID: {c.id} | Fecha: {c.fecha} | Compra: ${c.valor_compra} | Venta: ${c.valor_venta}")
                elif op == "3":
                    c_id = int(input("ID cotización a actualizar: "))
                    tipo_id = int(input("ID Tipo Cotización: "))
                    fecha_str = input("Fecha (YYYY-MM-DD): ").strip()
                    fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
                    compra = float(input("Nuevo Valor Compra: "))
                    venta = float(input("Nuevo Valor Venta: "))
                    cot = CotizacionDolar(id=c_id, tipo_cotizacion_id=tipo_id, fecha=fecha, valor_compra=compra, valor_venta=venta)
                    self._s.cotizaciones._repo.actualizar(cot)
                    print("¡Cotización actualizada!")
                elif op == "4":
                    c_id = int(input("ID cotización a eliminar: "))
                    self._s.cotizaciones._repo.eliminar(c_id)
                    print("¡Cotización eliminada!")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    def _crud_precios(self) -> None:
        while True:
            print("\n--- GESTIÓN DE PRECIOS (CRUD) ---")
            print("1. Crear precio para un libro")
            print("2. Listar todos los precios")
            print("3. Consultar/Convertir precio de un libro")
            print("4. Actualizar precio")
            print("5. Eliminar precio")
            print("0. Volver")
            op = input("Opción: ").strip()
            try:
                if op == "1":
                    p_id = int(input("ID Precio: "))
                    libro_id = int(input("ID Libro: "))
                    moneda_id = int(input("ID Moneda: "))
                    monto = float(input("Monto: "))
                    p = Precio(id=p_id, libro_id=libro_id, moneda_id=moneda_id, monto=monto)
                    self._s.precios._repo.crear(p)
                    print("¡Precio asignado con éxito!")
                elif op == "2":
                    for p in self._s.precios._repo.leer_todos():
                        print(f"ID: {p.id} | Libro ID: {p.libro_id} | Moneda ID: {p.moneda_id} | Monto: {p.monto}")
                elif op == "3":
                    libro_id = int(input("ID Libro: "))
                    cod = input("Moneda destino (ARS/USD): ").strip().upper()
                    t_id = int(input("ID Tipo Cotización (ej: 2 Blue): "))
                    res = self._s.precios.precio_en(libro_id, cod, t_id)
                    print(f"\nPrecio calculated: {res:.2f} {cod}")
                elif op == "4":
                    p_id = int(input("ID Precio a actualizar: "))
                    libro_id = int(input("ID Libro: "))
                    moneda_id = int(input("ID Moneda: "))
                    monto = float(input("Nuevo Monto: "))
                    p = Precio(id=p_id, libro_id=libro_id, moneda_id=moneda_id, monto=monto)
                    self._s.precios._repo.actualizar(p)
                    print("¡Precio actualizado!")
                elif op == "5":
                    p_id = int(input("ID Precio a eliminar: "))
                    self._s.precios._repo.eliminar(p_id)
                    print("¡Precio eliminado!")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")

    def _crud_stock(self) -> None:
        while True:
            print("\n--- GESTIÓN DE STOCK / INVENTARIO (CRUD) ---")
            print("1. Crear registro de stock")
            print("2. Listar registros de stock")
            print("3. Ingresar stock a libro (+)")
            print("4. Retirar stock a libro (-)")
            print("5. Actualizar registro de stock")
            print("6. Eliminar registro de stock")
            print("7. Ver libros sin stock")
            print("0. Volver")
            op = input("Opción: ").strip()
            try:
                if op == "1":
                    s_id = int(input("ID Stock: "))
                    libro_id = int(input("ID Libro: "))
                    cant = int(input("Cantidad inicial: "))
                    self._s.stock._repo.crear(Stock(id=s_id, libro_id=libro_id, cantidad=cant))
                    print("¡Registro de stock creado!")
                elif op == "2":
                    for st in self._s.stock.listar():
                        print(f"ID: {st.id} | Libro ID: {st.libro_id} | Cantidad: {st.cantidad}")
                elif op == "3":
                    libro_id = int(input("ID Libro: "))
                    cant = int(input("Cantidad a sumar: "))
                    self._s.stock.ingresar(libro_id, cant)
                    print("¡Stock ingresado!")
                elif op == "4":
                    libro_id = int(input("ID Libro: "))
                    cant = int(input("Cantidad a restar: "))
                    self._s.stock.retirar(libro_id, cant)
                    print("¡Stock retirado!")
                elif op == "5":
                    s_id = int(input("ID Stock a actualizar: "))
                    libro_id = int(input("ID Libro: "))
                    cant = int(input("Nueva Cantidad: "))
                    self._s.stock._repo.actualizar(Stock(id=s_id, libro_id=libro_id, cantidad=cant))
                    print("¡Registro actualizado!")
                elif op == "6":
                    s_id = int(input("ID Stock a eliminar: "))
                    self._s.stock._repo.eliminar(s_id)
                    print("¡Registro eliminado!")
                elif op == "7":
                    for f in self._s.stock.sin_stock():
                        print(f"Sin stock -> ID Libro: {f.id} | Título: {f.titulo}")
                elif op == "0":
                    break
            except Exception as e:
                print(f"Error: {e}")
