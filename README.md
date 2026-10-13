# Book Manager - Sprint 2

## Introducción y Contexto
En esta segunda entrega se amplía el alcance de la aplicación del sistema de gestión de inventario y cotizaciones de la librería **Cúspide**, haciendo que el sistema persista en una base de datos relacional mediante el ORM **SQLAlchemy**.

Se migran los datos previamente gestionados en archivos planos CSV a tablas relacionales normalizadas, garantizando integridad referencial y transaccional. Asimismo, el sistema incorpora la integración con una **API externa** para la consulta y registro de cotizaciones en tiempo real del dólar, gestionada a través de variables de entorno con `python-dotenv`.

## Objetivo
El objetivo principal de este sprint es consolidar los conocimientos de:
- Modelado de bases de datos relacionales y normalización.
- Mapeo objeto-relacional (ORM) utilizando SQLAlchemy.
- Implementación de conexiones seguras y transacciones atómicas mediante gestores de contexto (*context managers*).
- Migración de datos entre formatos (CSV a SQL relacional) y trazabilidad con scripts `.sql`.
- Consumo e integración de APIs externas seguras a través de variables de entorno (`.env`).
- Ampliación de la interfaz de consola (CLI) con reportes bimonetarios y exportación de datos.

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
│       ├── services/
│       │   └── services.py
│       ├── migrations/
│       │   ├── csv/
│       │   └── sql/
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

## Ejecución
Para ejecutar el sistema desde la raíz del código fuente:
```bash
python -m book_manager.main
```
