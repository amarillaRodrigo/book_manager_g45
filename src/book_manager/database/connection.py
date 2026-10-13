"""Módulo de conexión y sesiones para la base de datos con SQLAlchemy."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Cargar variables de entorno desde .env si existe en la raíz del proyecto
_env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    load_dotenv()


class ConexionDB:
    """Administra la conexión y la fábrica de sesiones con SQLAlchemy.

    Permite configurar la URL de conexión a la base de datos mediante parámetro,
    variable de entorno DATABASE_URL o utilizando SQLite por defecto.
    """

    DEFAULT_DATABASE_URL = "sqlite:///book_manager.db"

    def __init__(self, url: Optional[str] = None, echo: bool = False) -> None:
        """Inicializa la conexión configurando el motor y la fábrica de sesiones.

        Args:
            url (Optional[str]): Cadena de conexión para SQLAlchemy. Si no se
                especifica, se consulta la variable de entorno DATABASE_URL o
                se utiliza el valor por defecto (SQLite local).
            echo (bool): Si es True, SQLAlchemy emitirá las consultas SQL en consola.
        """
        self._url = url or os.getenv("DATABASE_URL") or self.DEFAULT_DATABASE_URL
        self._echo = echo
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._inicializar_motor()

    def _inicializar_motor(self) -> None:
        """Configura el motor (Engine) y la fábrica de sesiones de SQLAlchemy."""
        connect_args = {}
        if self._url.startswith("sqlite"):
            # En SQLite permitimos múltiples hilos para compatibilidad en entornos interactivos
            connect_args["check_same_thread"] = False

        self._engine = create_engine(
            self._url,
            echo=self._echo,
            connect_args=connect_args,
        )
        self._session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
        )

    @property
    def url(self) -> str:
        """Cadena de conexión utilizada."""
        return self._url

    @property
    def engine(self) -> Engine:
        """Instancia del motor (Engine) de SQLAlchemy."""
        if self._engine is None:
            self._inicializar_motor()
        return self._engine  # type: ignore[return-value]

    @property
    def session_factory(self) -> sessionmaker:
        """Fábrica de sesiones (sessionmaker) configurada."""
        if self._session_factory is None:
            self._inicializar_motor()
        return self._session_factory  # type: ignore[return-value]

    def obtener_sesion(self) -> Session:
        """Crea y retorna una nueva sesión de base de datos."""
        return self.session_factory()

    @contextmanager
    def transaccion(self) -> Iterator[Session]:
        """Context manager para ejecutar operaciones dentro de una transacción.

        Abre una nueva sesión y la expone al bloque `with`. Si el bloque
        finaliza sin errores, confirma los cambios (`commit`); si ocurre una
        excepción, revierte los cambios (`rollback`) y relanza la excepción
        original. La sesión se cierra siempre al finalizar, haya o no error.

        Yields:
            Session: sesión de SQLAlchemy activa durante la transacción.
        """
        sesion = self.obtener_sesion()
        try:
            yield sesion
            sesion.commit()
        except Exception:
            sesion.rollback()
            raise
        finally:
            sesion.close()

    def crear_tablas(self, base: object) -> None:
        """Crea todas las tablas registradas en el metadata del Base declarativo.

        Args:
            base: Clase Base declarativa de SQLAlchemy cuyos modelos se van a crear.
        """
        if hasattr(base, "metadata") and hasattr(base.metadata, "create_all"):
            base.metadata.create_all(bind=self.engine)
        else:
            raise TypeError("El objeto provisto no posee un atributo metadata válido de SQLAlchemy.")

    def desconectar(self) -> None:
        """Cierra el pool de conexiones del motor si está activo."""
        if self._engine is not None:
            self._engine.dispose()


# Instancia global compartida opcional
_conexion_global: Optional[ConexionDB] = None


def obtener_conexion(url: Optional[str] = None, echo: bool = False) -> ConexionDB:
    """Retorna una instancia compartida de ConexionDB.

    Si se proporciona una URL distinta o aún no fue creada, se inicializa una nueva.
    """
    global _conexion_global
    if _conexion_global is None or (url is not None and url != _conexion_global.url):
        _conexion_global = ConexionDB(url=url, echo=echo)
    return _conexion_global


@contextmanager
def transaccion(url: Optional[str] = None, echo: bool = False) -> Iterator[Session]:
    """Atajo para ejecutar una transacción sobre la conexión global compartida.

    Equivale a `obtener_conexion(url, echo).transaccion()`.
    """
    with obtener_conexion(url=url, echo=echo).transaccion() as sesion:
        yield sesion
