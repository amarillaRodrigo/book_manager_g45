"""Ejecución del scraper de Cúspide desde la aplicación.

Scrapy no puede ejecutarse dos veces dentro del mismo proceso: el reactor de
Twisted queda inicializado y la segunda ejecución falla con el error
`cannot re-initialize reactor`. Por eso el crawler se lanza siempre como un
subproceso independiente, que además permite capturar su salida y su código
de retorno.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Carpeta del proyecto Scrapy (src/book_manager/scraper).
DIRECTORIO_SCRAPER = Path(__file__).resolve().parents[1]

# Carpeta `src` del proyecto y raíz del repositorio.
CARPETA_SRC = Path(__file__).resolve().parents[3]
RAIZ_PROYECTO = Path(__file__).resolve().parents[4]

# Umbral de diferencia de precio que se usa si el usuario no indica otro.
UMBRAL_ALERTA_POR_DEFECTO = 10.0


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
        print(texto_para_consola(salida))

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
    """Extrae el valor de una estadística del resumen de Scrapy.

    Args:
        salida (str): Salida del crawler.
        etiqueta (str): Etiqueta de la estadística, con su formato original.

    Returns:
        int: El valor de la estadística, o 0 si no aparece.
    """
    coincidencia = re.search(re.escape(etiqueta) + r"\s*(\d+)", salida)
    return int(coincidencia.group(1)) if coincidencia else 0


def texto_para_consola(texto: str) -> str:
    """Sustituye los caracteres que la consola no puede representar.

    La salida del crawler puede traer caracteres del sitio que la consola de
    Windows (cp1252) no sabe mostrar, y eso cortaría la ejecución.

    Args:
        texto (str): Texto a mostrar.

    Returns:
        str: El texto, con los caracteres no representables reemplazados.
    """
    codificacion = getattr(sys.stdout, "encoding", None) or "utf-8"
    return texto.encode(codificacion, errors="replace").decode(codificacion, errors="replace")


def ejecutar_scraping_con_alertas(
    servicios: Any,
    umbral_porcentaje: Optional[float] = None,
    preguntar_umbral: bool = True,
    titulo: Optional[str] = None,
    timeout: Optional[int] = None,
) -> Dict[str, object]:
    """Ejecuta el scraping, compara los precios y genera el archivo de alertas.

    El umbral de diferencia de precio se pide al usuario **antes** de cada
    ejecución del scraper, tal como pide el enunciado, y es el que define qué
    diferencias se consideran alerta.

    Args:
        servicios (Any): Contenedor `Servicios` del sistema.
        umbral_porcentaje (Optional[float]): Umbral a utilizar. Si es None y
            `preguntar_umbral` es True, se le pregunta al usuario.
        preguntar_umbral (bool): Si es True, pide el umbral al usuario.
        titulo (Optional[str]): Si se indica, solo se consulta ese título.
        timeout (Optional[int]): Segundos máximos de espera del subproceso.

    Returns:
        Dict[str, object]: Resumen de la corrida con el umbral utilizado, la
            cantidad de comparaciones y de alertas, y la ruta del CSV.
    """
    from book_manager.services.services import pedir_umbral_diferencia

    if umbral_porcentaje is None and preguntar_umbral:
        umbral_porcentaje = pedir_umbral_diferencia()
    if umbral_porcentaje is None:
        umbral_porcentaje = UMBRAL_ALERTA_POR_DEFECTO

    print("\n--- Ejecutando el scraping en Cúspide ---")
    resultado = ejecutar_scraping(titulo=titulo, timeout=timeout)

    comparaciones = servicios.comparacion_precios.comparar(umbral_porcentaje)
    alertas = [c for c in comparaciones if c.en_alerta]

    resumen: Dict[str, object] = {
        "umbral_porcentaje": umbral_porcentaje,
        "codigo_retorno": resultado.get("codigo_retorno"),
        "items_extraidos": resultado.get("items_extraidos", 0),
        "comparaciones": len(comparaciones),
        "alertas": len(alertas),
        "archivo_alertas": None,
    }

    if alertas:
        try:
            ruta = servicios.comparacion_precios.generar_alertas_csv(umbral_porcentaje)
            resumen["archivo_alertas"] = str(ruta)
            print(f"\nArchivo de alertas generado en: {ruta}")
        except Exception as error:  # pragma: no cover - depende del entorno
            print(f"\nNo se pudo generar el archivo de alertas: {error}")
    else:
        print(
            f"\nNo hay diferencias de precio superiores al {umbral_porcentaje:g}% "
            "entre nuestro precio y el de Cúspide."
        )

    return resumen


if __name__ == "__main__":
    resultado = ejecutar_scraping(silencioso=True)
    print(resultado.get("salida", ""))
    print(f"Código de retorno: {resultado['codigo_retorno']}")
