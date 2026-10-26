"""Configuración del proyecto Scrapy de Book Manager (Sprint 3).

Lee los parámetros de scraping desde el archivo `.env` de la raíz del
proyecto para no dejar valores mágicos en el código.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Raíz del repositorio (book_manager/) y carpeta que contiene los CSV del
# catálogo propio used para acotar las búsquedas.
RAIZ_PROYECTO = Path(__file__).resolve().parents[4]
ARCHIVO_ENV = RAIZ_PROYECTO / ".env"
if ARCHIVO_ENV.exists():
    load_dotenv(dotenv_path=ARCHIVO_ENV)

# --- Identificación del proyecto ------------------------------------------------
BOT_NAME = "bookmanager_scraper"
SPIDER_MODULES = ["bookmanager_scraper.spiders"]
NEWSPIDER_MODULE = "bookmanager_scraper.spiders"

# --- Sitio objetivo ------------------------------------------------------------
CUSPIDE_URL = os.getenv("CUSPIDE_URL", "https://cuspide.com")
URL_BUSQUEDA = f"{CUSPIDE_URL}/?s={{titulo}}&post_type=product"
URL_RESULTADOS = f"{CUSPIDE_URL}/buscar/?q={{titulo}}"

# --- Comportamiento del crawler -------------------------------------------------
# El `robots.txt` de Cúspide no habilita la consulta por título que exige el
# enunciado, por lo que se desactiva su cumplimiento de forma explícita.
ROBOTSTXT_OBEY = False
USER_AGENT = os.getenv(
    "SCRAPY_USER_AGENT",
    "BookManager/3.0 (tp-integrador-sprint-3; +https://github.com/amarillaRodrigo/book_manager_g45)",
)
CONCURRENT_REQUESTS = int(os.getenv("SCRAPY_CONCURRENT_REQUESTS", "4"))
DOWNLOAD_DELAY = float(os.getenv("SCRAPY_DELAY", "1.0"))
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 30.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
DOWNLOAD_TIMEOUT = int(os.getenv("SCRAPY_TIMEOUT", "30"))
RETRY_ENABLED = True
RETRY_TIMES = int(os.getenv("SCRAPY_RETRY_TIMES", "3"))
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
COOKIES_ENABLED = False
TELESCOPE_ENABLED = True
DEFAULT_REQUEST_HEADERS = {
    "Accept-Language": "es-AR,es;q=0.9",
}

# --- Manejo de errores ----------------------------------------------------------
# Un fallo puntual de una ficha no debe abortar la corrida completa: los
# reintentos ante errores de red son los del propio Scrapy (RETRY_ENABLED).
ITEM_ERRORS_DISPLAY = ["stdout", "pprint"]

# --- Pipelines ------------------------------------------------------------------
# El registro completo de pipelines se activa en el Ejercicio 03, junto con la
# implementación concreta de cada etapa.
ITEM_PIPELINES = {}

# --- Salida de respaldo ---------------------------------------------------------
# JSON con los datos extraídos: permite reejecutar la comparación de precios
# sin volver a golpear el sitio y sirve de red de seguridad si Cúspide cambia
# su HTML o bloquea las peticiones.
DIRECTORIO_DATOS = Path(__file__).resolve().parents[1] / "data"
ARCHIVO_JSON = DIRECTORIO_DATOS / "datos_cuspide.json"
FEEDS = {
    str(ARCHIVO_JSON): {
        "format": "json",
        "encoding": "utf-8",
        "indent": 2,
        "overwrite": True,
    },
}

# --- Salida de logs -------------------------------------------------------------
LOG_LEVEL = os.getenv("SCRAPY_LOG_LEVEL", "INFO")
FEED_EXPORT_ENCODING = "utf-8"
