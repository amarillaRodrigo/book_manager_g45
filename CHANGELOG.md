# CHANGELOG

## Sprint 2

[Ejercicio 07]
- Implementación del servicio `ServicioCotizacionDolar` (y alias `ServicioCotizacion`) en `book_manager/services/services.py` con soporte de variables de entorno mediante `python-dotenv` (`API_URL` en `.env`).
- Creación del método `obtener_cotizaciones` en `ServicioCotizacionDolar` para consultar `https://dolarapi.com/v1/dolares` con `requests`, normalizar tipos de cambio y registrar o actualizar las cotizaciones en la base de datos.
- Actualización de la fábrica `crear_servicios` para conectar todos los servicios y repositorios a la instancia de `ConexionDB`.

[Ejercicio 06]
- Migración de la capa de persistencia en `book_manager/repositories/repositories.py` para operar íntegramente sobre base de datos relacional mediante SQLAlchemy ORM (`ConexionDB` y transacciones).
- Implementación de la clase base genérica `RepositorioSQLAlchemy[T, M]` respetando la interfaz `IRepositorio[T]` y convirtiendo entre modelos ORM y entidades de dominio.
- Adaptación de los repositorios `RepositorioGenero`, `RepositorioEditorial`, `RepositorioMoneda`, `RepositorioTipoCotizacion`, `RepositorioLibro` y `RepositorioPrecio` al motor relacional.
- Reimplementación de `RepositorioStock` (`IRepositorioStock`) y `RepositorioCotizacionDolar` (`IRepositorioCotizacionDolar`) utilizando consultas `select` de SQLAlchemy 2.x y garantizando las reglas de unicidad e histórico ordenado.

[Ejercicio 05]
- Implementación de `migrar_datos` en `book_manager/migrations/migrations.py`: lee los CSV de `migrations/csv` (generos, editoriales, monedas, tipos_cotizacion, libros, precios, stock y cotizaciones) y genera un archivo `.sql` por tabla en `migrations/sql`, numerado según el orden de dependencia de claves foráneas (`01_generos.sql` a `08_cotizaciones.sql`).
- Generación de sentencias `INSERT` con escapado manual de valores (comillas simples duplicadas, `NULL` para vacíos, numéricos sin comillas), sin recurrir a sintaxis específica de un motor en particular.
- Ejecución de esas mismas sentencias dentro de la transacción de `ConexionDB`, creando previamente las tablas con `crear_tablas`, de forma que un error en la migración revierte todos los cambios.
- Migración idempotente: si una tabla ya contiene filas se omite su inserción, evitando duplicados y violaciones de unicidad al volver a ejecutar la migración.

[Ejercicio 04]
- Modelos ORM declarativos de SQLAlchemy 2.x en `book_manager/models/models.py`: clase `Base(DeclarativeBase)` y una tabla por entidad de dominio (`Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Libro`, `Precio`, `Stock`, `CotizacionDolar`).
- Tipos de columna según el dominio (`String` con longitud, `Numeric` para montos y cotizaciones, fechas, enteros) y restricciones `NOT NULL`/`UNIQUE` reflejando las reglas de unicidad de nombre, código e ISBN ya validadas en los servicios.
- Claves foráneas y `relationship()` bidireccionales entre `Libro`↔`Genero`/`Editorial`, `Precio`↔`Libro`/`Moneda`, `Stock`↔`Libro` y `CotizacionDolar`↔`TipoCotizacion`, con restricciones de unicidad compuesta (`libro_id`+`moneda_id`, `tipo_id`+`fecha`).
- Eliminación en cascada de `Precio` y `Stock` al eliminar un `Libro`, consistente con el comportamiento de `ServicioLibro.eliminar`.

[Ejercicio 03]
- Context manager `transaccion` en la clase `ConexionDB` (`book_manager/database/connection.py`): abre una sesión, confirma los cambios si no hay errores y los revierte relanzando la excepción original en caso contrario, cerrando siempre la sesión.
- Función utilitaria `transaccion()` a nivel de módulo como atajo sobre la conexión global compartida, en línea con `obtener_conexion`.

[Ejercicio 02]
- Implementación de la clase `ConexionDB` en `book_manager/database/connection.py` para la gestión centralizada de la base de datos con SQLAlchemy.
- Configuración del motor relacional (`Engine`) y fábrica de sesiones (`sessionmaker`) con URL configurable vía parámetro o `.env` (SQLite por defecto).
- Métodos auxiliares para obtención de sesiones (`obtener_sesion`), creación de tablas (`crear_tablas`) y cierre del pool (`desconectar`).
- Función utilitaria `obtener_conexion` para reutilización segura de la conexión.

[Ejercicio 01]
- Inicialización y configuración de la rama de trabajo `Sprint_2` a partir de `Sprint_1`.
- Creación de la estructura de paquetes para Sprint 2: `database/` (conexión y sesiones), `models/` (modelos ORM), `migrations/sql/` y `migrations/migrations.py`.
- Creación del archivo `.env` con variables de entorno (`API_URL` para la API del dólar y `DATABASE_URL` para la base de datos).
- Actualización de `requirements.txt` incorporando las librerías `sqlalchemy`, `python-dotenv` y `requests`.
- Actualización del archivo `README.md` documentando los objetivos, contexto y arquitectura del Sprint 2.
- Resolución de observaciones de POO en entidades de dominio: vinculación directa de objetos asociados (`genero`, `editorial`, `libro`, `moneda`, `tipo_cotizacion`) en `Libro`, `Precio`, `Stock` y `CotizacionDolar`.
- Actualización de `preload_data.py` para leer los datos iniciales directamente desde los archivos CSV en `migrations/csv/`.
- Refactorización de `main.py` con inyección explícita de dependencias hacia los servicios sin enmascarar excepciones.

---

## Sprint 1

[Ejercicio 07]
- Creación del archivo de ejecución principal (main.py).
- Integración de la capa de servicios con la interfaz gráfica.
- Rediseño estético del menú de consola (ConsolaUI) con encabezados limpios e intuitivos.
- Unificación del directorio de datos a `migrations/csv` y precarga automática de los 10 registros por entidad.

[Ejercicio 06]
- Creación de la interfaz de usuario en consola CLI (book_manager/ui/console.py).
- Implementación de menú interactivo con operaciones CRUD completas para cada entidad.

[Ejercicio 05]
- Precarga de 10 libros y precios reales del catálogo de Cúspide (En agosto nos vemos, Un lugar soleado..., Alas de ónix, El Eternauta, etc.) en preload_data.py y archivos CSV.

[Ejercicio 04]
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