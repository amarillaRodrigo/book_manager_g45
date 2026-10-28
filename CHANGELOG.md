# CHANGELOG

## Sprint 3

[Ejercicio 07]
- Incorporación al menú principal de las tres opciones del Sprint 3: **9. Ejecutar scraping**, **10. Generar reporte** y **11. Ver historial de auditoría**.
- La opción *Ejecutar scraping* pide el umbral de diferencia de precio antes de la corrida, lanza el crawler en un subproceso y genera el archivo de alertas con los precios comparados.
- La opción *Generar reporte* pide el umbral, genera el reporte en Excel con la comparación de precios y muestra la ruta del archivo.
- La opción *Ver historial de auditoría* lista los últimos 50 registros con su identificador, fecha, acción y detalle.
- Blindaje de la lectura de las opciones del menú: ante el fin de la entrada (por ejemplo, al ejecutar el notebook con "Run all") la consola sale del menú en lugar de cortar la ejecución.
- Modo demostración: cuando la entrada no es interactiva (por ejemplo, al ejecutar el notebook con "Run all") la aplicación recorre sola el listado y el alta de cada modelo y las tres opciones del Sprint 3, y termina sin esperar una pulsación.

[Ejercicio 06]
- Creación de la tabla de auditorías `auditorias` (`AuditoriaModel`) con las columnas **acción**, **fecha** y **detalles**, junto con la entidad de dominio `Auditoria` y el repositorio `RepositorioAuditoria`.
- Implementación del decorador `auditable` en la capa de servicios: envuelve los métodos que modifican los datos y escribe un registro con la acción ejecutada, la fecha y el detalle de la operación.
- Aplicación del decorador a las diez operaciones de alta, modificación y baja del sistema (`ServicioBase.crear`, `.actualizar` y `.eliminar`, `ServicioLibro.eliminar`, `ServicioCotizacionDolar.registrar`, `.actualizar` y `.eliminar`, y `ServicioStock.crear`, `.actualizar` y `.eliminar`).
- Incorporación del mixin `ServicioAuditable` y del servicio `ServicioAuditoria`, que se inyecta en los servicios desde `crear_servicios` para que cada uno registre sus operaciones sin que la capa de servicios necesite conocer la base de datos.
- La auditoría solo registra las operaciones que terminan bien: una operación que falla por una regla de negocio no deja rastro.
- Renombrado de los modelos ORM con el sufijo `Model` (`GeneroModel`, `EditorialModel`, `MonedaModel`, `TipoCotizacionModel`, `LibroModel`, `PrecioModel`, `StockModel`, `CotizacionDolarModel`, `PrecioWebModel`) para distinguirlos de las entidades de dominio, actualizando los imports de los repositorios y de las migraciones.

[Ejercicio 05]
- Generación del reporte en Excel `reportes/reporte_precios_<fecha>.xlsx` con `openpyxl`, a partir de la comparación entre los precios internos y los precios publicados en Cúspide.
- Hoja `Comparación` con una fila por libro y las columnas pedidas (Libro, Precio interno, Precio web, Diferencia y Fecha de extracción),ampliadas con ISBN, Diferencia % y Estado.
- Hoja `Alertas` con los libros que superan el umbral de diferencia, destacada en rojo.
- Formato del reporte: encabezado con fondo y negrita, paneles congelados, números con formato `#,##0.00` y ancho de columnas según el contenido.

## Sprint 2

[Ejercicio 04]
- Implementación del `ServicioComparacionPrecios` (`book_manager/services/services.py`), que contrasta el precio interno de cada libro con el precio publicado en Cúspide y calcula la diferencia absoluta y porcentual.
- El umbral de diferencia de precio se le pide al usuario antes de cada ejecución del scraper (`pedir_umbral_diferencia`), tal como pide el enunciado, y es el que define qué diferencias se consideran alerta.
- Generación del archivo de alertas `reportes/alertas_precios_<fecha>.csv` con los libros que superan el umbral y las columnas Libro, ISBN, Precio interno, Precio web, Diferencia, Diferencia %, Fecha de extracción y Estado.
- Función `ejecutar_scraping_con_alertas` (`book_manager/scraper/bookmanager_scraper/runner.py`) que encadena el scraping, la comparación y la generación del archivo de alertas, devolviendo un resumen de la corrida.
- El servicio de comparación se incorpora al contenedor `Servicios` y a la fábrica `crear_servicios`, junto con el repositorio de las extracciones de la web.

[Ejercicio 03]
- Implementación del `CuspideSpider` (`book_manager/scraper/bookmanager_scraper/spiders/cuspide_spider.py`): consulta el sitio de Cúspide una vez por cada título del catálogo propio y se queda únicamente con los diez primeros resultados de cada búsqueda, tal como pide el enunciado.
- Lectura de los datos de cada ficha de producto mediante `ItemLoader` (`itemloaders`), con los procesadores de normalización de `bookmanager_scraper/items.py`: precio en pesos y en dólares, URL de la imagen, formas de pago, descripción detallada, ISBN y autor.
- Identificación de nuestros libros dentro de los resultados (`bookmanager_scraper/catalogo.py`): se acepta la coincidencia exacta del título o la que incluye la edición entre paréntesis o el año, y se descartan las obras que solo empiezan igual (por ejemplo, `EL DUELO INFANTIL` o `EL ETERNAUTA PARA ARMAR`).
- Implementación de los tres pipelines del scraper: `PrecioInternoPipeline` (identifica el libro del catálogo y suma su precio interno), `ValidacionPipeline` (descarta los items sin precio o ajenos al catálogo) y `PersistenciaPipeline` (guarda la extracción en la tabla `precios_web`, sin duplicar el mismo libro en la misma fecha).
- Incorporación de la entidad `PrecioWeb`, de su modelo ORM `precios_web` y del repositorio `RepositorioPrecioWeb`, con el histórico de extracciones por libro y fecha.
- Módulo `runner.py` que ejecuta el crawler en un subproceso independiente, necesario porque Scrapy no puede inicializar el reactor dos veces en el mismo proceso.
- Actualización de `requirements.txt` con la librería `itemloaders`.

[Ejercicio 02]
- Implementación de `cargar_datos_desde_sql` en `book_manager/migrations/migrations.py`: lee los archivos `.sql` de una carpeta y ejecuta sus sentencias contra la base de datos.
- Orden de carga por prefijo numérico de los archivos (`01_generos.sql` ... `08_cotizaciones.sql`), respetando la dependencia de las claves foráneas entre tablas.
- Ejecución de todas las sentencias dentro de una única transacción: si alguna falla se revierte la carga completa y no queda ningún registro a medias.
- Carga idempotente: si la tabla destino ya contiene filas, su archivo se omite y se informa por pantalla, de modo que la función puede repetirse sin duplicar datos.
- Incorporación del auxiliar `_separar_sentencias`, que divide los scripts `.sql` en sentencias individuales respetando las cadenas entre comillas simples (con el escapado de comillas dobles) y descartando los comentarios de línea y de bloque.
- Activación de `PRAGMA foreign_keys=ON` en las conexiones de SQLite (`book_manager/database/connection.py`): sin ella SQLite no aplicaba las reglas `ondelete="CASCADE"` declaradas en los modelos ni se validaba la integridad referencial al cargar los datos desde SQL.

[Ejercicio 01]
- Inicialización y configuración de la rama de trabajo `Sprint_3`, creada a partir de `Sprint_2`.
- Creación de la estructura de carpetas del Sprint 3: `scraper/` (proyecto Scrapy con `scrapy.cfg`, `settings.py`, `items.py`, `pipelines.py` y `spiders/cuspide_spider.py`) y `reportes/` (destino de los reportes Excel y de las alertas CSV).
- Implementación del `CuspideSpider` base: lectura del catálogo propio desde `migrations/csv/libros.csv` y generación de una petición de búsqueda por cada título, acotada a los diez primeros resultados.
- Configuración del crawler en `scraper/bookmanager_scraper/settings.py` con `ROBOTSTXT_OBEY = False`, user agent propio, `CONCURRENT_REQUESTS`, `DOWNLOAD_DELAY`, auto-throttling y reintentos, todos parametrizables desde el `.env`.
- Actualización del archivo `.env` con las variables `CUSPIDE_URL` y `SCRAPY_*` (user agent, delay, peticiones simultáneas, timeout, reintentos y nivel de log).
- Actualización de `requirements.txt` incorporando las librerías `scrapy` y `openpyxl`.
- Actualización del archivo `README.md` documentando los objetivos, el contexto y la arquitectura del Sprint 3.
- Refactorización de `main.py`: se elimina la duplicación de la fábrica de servicios y se delega en `crear_servicios` de la capa de servicios.

---

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