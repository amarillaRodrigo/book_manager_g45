# Book Manager - Sprint 1

## Introducción y Contexto
Una librería con venta al público necesita modernizar su sistema de gestión de inventario de libros. Debido a la fluctuación en los costos de importación de material bibliográfico, el sistema debe gestionar precios en diferentes monedas y seguir de cerca la cotización del dólar para actualizar sus valores en tiempo real.

## Objetivo
El objetivo principal de este proyecto es aplicar los conocimientos adquiridos en programación orientada a objetos (POO) y almacenamiento de datos en archivos para su persistencia, construyendo una aplicación de consola (CLI) en Python.

## Estructura del Proyecto
```
book_manager/
├── src/
│   └── book_manager/
│       ├── entities/
│       │   └── entities.py
│       ├── preload_data/
│       │   └── preload_data.py
│       ├── repositories/
│       │   └── repositories.py
│       ├── services/
│       │   └── services.py
│       ├── migrations/
│       │   └── csv/
│       ├── ui/
│       │   └── console.py
│       └── main.py
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

## Ejecución
Para ejecutar el sistema desde la raíz del código fuente:
```bash
python -m book_manager.main
```
