"""Ejecución del scraper de Cúspide desde la aplicación.

Scrapy no puede ejecutarse dos veces dentro del mismo proceso: el reactor de
Twisted queda inicializado y la segunda ejecución falla con el error
`cannot re-initialize reactor`. Por eso el crawler se lanza siempre como un
subproceso independiente, que además permite capturar su salida y su código
de retorno.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Carpeta del proyecto Scrapy (src/book_manager/scraper).
DIRECTORIO_SCRAPER = Path(__file__).resolve().parents[1]

# Carpeta `src` del proyecto y raíz del repositorio.
CARPETA_SRC = Path(__file__).resolve().parents[3]
RAIZ_PROYECTO = Path(__file__).resolve().parents[4]


def ruta_base_datos() -> str:
    """Devuelve la URL de la base de datos como ruta absoluta.

    La URL del `.env` es relativa (`sqlite:///book_manager.db`) y SQLite la
    resuelve contra el directorio de trabajo, que cambia al correr el crawler
    en su propia carpeta. Se resuelve acá, en el proceso principal, para que el
    scraper trabaje sobre la misma base que el resto del sistema.

    Returns:
        str: URL de conexión a la base de datos.
    """
    url = os.getenv("DATABASE_URL") or "sqlite:///book_manager.db"
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        relativa = url[len("sqlite:///") :]
        absoluta = (Path.cwd() / relativa).resolve()
        return "sqlite:///" + str(absoluta).replace("\\", "/")
    return url


def entorno_del_crawler() -> Dict[str, str]:
    """Arma el entorno de variables para el subproceso del crawler.

    Returns:
        Dict[str, str]: Variables de entorno del subproceso.
    """
    entorno = dict(os.environ)
    entorno["PYTHONPATH"] = os.pathsep.join(
        [str(CARPETA_SRC), *[p for p in [entorno.get("PYTHONPATH", "")] if p]]
    )
    entorno["DATABASE_URL"] = ruta_base_datos()
    return entorno


def ejecutar_scraping(
    titulo: Optional[str] = None,
    timeout: Optional[int] = None,
    silencioso: bool = False,
) -> Dict[str, object]:
    """Ejecuta el spider `Cuspide` en un subproceso.

    Args:
        titulo (Optional[str]): Si se indica, solo se consulta ese título del
            catálogo en lugar de todos.
        timeout (Optional[int]): Segundos máximos de espera del subproceso.
        silencioso (bool): Si es True, no muestra la salida del crawler.

    Returns:
        Dict[str, object]: Código de retorno, salida del crawler y un resumen
            con la cantidad de items extraídos y alertas registradas.
    """
    comando: List[str] = [sys.executable, "-m", "scrapy", "crawl", "cuspide"]
    if titulo:
        comando += ["-a", f"titulo={titulo}"]

    proceso = subprocess.run(
        comando,
        cwd=str(DIRECTORIO_SCRAPER),
        env=entorno_del_crawler(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )

    salida = (proceso.stdout or "") + (proceso.stderr or "")
    if not silencioso and salida:
        print(salida)

    resumen: Dict[str, object] = {
        "codigo_retorno": proceso.returncode,
        "comando": " ".join(comando),
        "items_extraidos": _contar(salida, "'item_scraped_count': "),
        "items_descartados": _contar(salida, "'item_dropped_count': "),
        "errores": _contar(salida, "'log_count/ERROR': "),
        "salida": salida,
    }

    return resumen


def _contar(salida: str, etiqueta: str) -> int:
    """Cuenta apariciones de una etiqueta en la salida del crawler.

    Args:
        salida (str): Salida del crawler.
        etiqueta (str): Etiqueta a buscar.

    Returns:
        int: Cantidad de apariciones de la etiqueta.
    """
    return salida.count(etiqueta)


if __name__ == "__main__":
    resultado = ejecutar_scraping(silencioso=True)
    print(resultado.get("salida", ""))
    print(f"Código de retorno: {resultado['codigo_retorno']}")
