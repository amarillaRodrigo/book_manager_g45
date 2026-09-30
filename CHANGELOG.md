# CHANGELOG

[Ejercicio 04]
[Punto 06]
- Creación de la interfaz de usuario en consola CLI (book_manager/ui/console.py).
- Implementación de menú interactivo con operaciones CRUD completas para cada entidad.

[Punto 05]
- Implementación del script de precarga de datos en preload_data.py.
- Generación de 10 registros de prueba para cada entidad del sistema en migrations/csv.

- Capa de servicios sobre los repositorios, con `ServicioBase[T]` para el CRUD común y validaciones por entidad.
- Reglas de negocio: nombres, códigos e ISBN únicos; libros con género y editorial existentes; un precio por libro y moneda; venta mayor o igual a compra en las cotizaciones.
- Integridad al eliminar: no se borran géneros, editoriales, monedas ni tipos de cotización en uso; al eliminar un libro se eliminan su stock y sus precios.
- Movimientos de stock (`ingresar`, `retirar` sin permitir negativos) y listado de libros sin stock.
- Cotización vigente por tipo y fecha, conversión entre pesos y dólares con el valor de venta y precio de un libro en ARS o USD.
- Fábrica `crear_servicios()` que arma todos los servicios sobre la misma carpeta de datos.

[Ejercicio 03]
- Incorporación de las interfaces provistas `IRepositorio[T]`, `IRepositorioStock` e `IRepositorioCotizacionDolar`.
- Clase `ArchivoCSV` que aísla la lectura y escritura de entidades en CSV mediante `to_dict()`/`from_dict()`, con escritura atómica por archivo temporal.
- Repositorio genérico `RepositorioCSV[T]` con CRUD completo y asignación automática de IDs; repositorios concretos para `Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Libro` y `Precio`.
- `RepositorioStock` con un registro por libro (clave `libro_id`) y `RepositorioCotizacionDolar` con clave tipo + fecha e histórico ordenado por fecha.
- Validaciones: error al crear duplicados o al actualizar registros inexistentes; `eliminar` devuelve `False` si no encuentra el registro.

[Ejercicio 02]
- Definición de la clase base `EntidadBase` con conversiones a diccionario y control de ID.
- Implementación de las entidades `Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Libro`, `Precio`, `Stock` y `CotizacionDolar`.
- Encapsulamiento de atributos con getters/setters (`@property`) y validaciones de datos (precios positivos, stock no negativo, cadenas no vacías).
- Adición de Type Hints y cumplimiento estricto con PEP8 y la librería estándar.

[Ejercicio 01]
- Inicialización del repositorio y estructura básica de directorios.
- Configuración de la rama `Sprint_1`.
- Creación de los archivos `README.md`, `CHANGELOG.md` y `requirements.txt`.
