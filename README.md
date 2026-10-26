# Book Manager - Sprint 3

## Introducción y Contexto
En esta tercera entrega se amplía el sistema de gestión de inventario y cotizaciones de la librería **Cúspide**, incorporando la obtención de datos desde la web para poder compararnos con los competidores.

El sistema ya persiste su información en una base de datos relacional mediante el ORM **SQLAlchemy** (Sprint 2) y consulta en tiempo real las cotizaciones del dólar a través de una **API externa** configurada con `python-dotenv`. En este sprint se suma un **scraper desarrollado con Scrapy** que recorre el sitio de Cúspide y extrae los datos públicos de los libros que ya tenemos en nuestro catálogo: precio, imagen, formas de pago y precio de cada título, y descripción detallada.

Sobre esa información el sistema genera **alertas de diferencia de precios** contra nuestro precio interno, un **reporte en Excel** con la comparación y un **historial de auditoría** de todas las operaciones realizadas.

## Objetivo
El objetivo principal de este sprint es aplicar los conocimientos adquiridos en programación orientada a objetos, persistencia relacional e integración de servicios externos, extendiendo el sistema con:

- Un **scraper Scrapy** (`CuspideSpider`) que consulta Cúspide una vez por cada título de nuestro catálogo, quedándose únicamente con los diez primeros resultados de cada búsqueda, e implementa **loaders** y **pipelines**.
- Una **capa de comparación de precios** que contrasta el precio web contra nuestro precio interno y genera un archivo de **alertas CSV** con el umbral de diferencia ingresado por el usuario antes de cada ejecución.
- Un **reporte Excel** con los campos Libro, Precio interno, Precio web, Diferencia y Fecha de extracción.
- Un **decorador de auditoría** que registra cada operación del sistema en una tabla de auditorías (acción, fecha y detalles).
- Las nuevas **opciones de menú**: ejecutar scraping, generar reporte y ver el historial de auditoría.

## Estructura del Proyecto
```
book_manager/
├── src/
│   └── book_manager/
│       ├── database/
│       │   └── connection.py
│       ├── entities/
│       │   └── entities.py
│       ├── models/
│       │   └── models.py
│       ├── preload_data/
│       │   └── preload_data.py
│       ├── repositories/
│       │   └── repositories.py
│       ├── scraper/
│       │   ├── scrapy.cfg
│       │   └── bookmanager_scraper/
│       │       ├── items.py
│       │       ├── pipelines.py
│       │       ├── settings.py
│       │       └── spiders/
│       │           └── cuspide_spider.py
│       ├── services/
│       │   └── services.py
│       ├── migrations/
│       │   ├── csv/
│       │   └── sql/
│       ├── reportes/
│       ├── ui/
│       │   └── console.py
│       └── main.py
├── .env
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

## Dependencias
Las dependencias requeridas se encuentran en `requirements.txt`:
- `sqlalchemy>=2.0.0`
- `python-dotenv>=1.0.0`
- `requests>=2.31.0`
- `scrapy>=2.11.0`
- `openpyxl>=3.1.0`

## Configuración
Las variables de entorno se definen en el archivo `.env` de la raíz del proyecto:

| Variable | Descripción |
|---|---|
| `API_URL` | Endpoint de la API de cotizaciones del dólar. |
| `DATABASE_URL` | Cadena de conexión a la base de datos (SQLite por defecto). |
| `CUSPIDE_URL` | Sitio web objetivo del scraper. |
| `SCRAPY_USER_AGENT` | User-Agent utilizado por el crawler. |
| `SCRAPY_DELAY` | Segundos de espera entre peticiones. |
| `SCRAPY_CONCURRENT_REQUESTS` | Número de peticiones simultáneas. |
| `SCRAPY_TIMEOUT` | Tiempo máximo de espera por respuesta. |
| `SCRAPY_RETRY_TIMES` | Cantidad de reintentos ante errores de red. |
| `SCRAPY_LOG_LEVEL` | Nivel de detalle del log del crawler. |

## Ejecución
Para ejecutar el sistema desde la raíz del código fuente:
```bash
python -m book_manager.main
```

Para ejecutar el scraper de forma aislada:
```bash
cd src/book_manager/scraper
scrapy crawl cuspide
```
