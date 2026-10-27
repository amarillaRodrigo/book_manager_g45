"""Módulo de definición de modelos ORM SQLAlchemy para el dominio de Book Manager.

Define las tablas relacionales y sus relaciones a partir de las entidades de
dominio (`book_manager.entities.entities`), preservando los nombres y las
reglas de integridad usadas por los repositorios y servicios de Sprint 1
(unicidad de nombres/códigos/ISBN, un precio por libro y moneda, una
cotización por tipo y fecha, y la eliminación en cascada de precios y stock
al eliminar un libro).
"""

import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Clase base declarativa de la que heredan todos los modelos ORM del sistema."""


class Genero(Base):
    """Tabla de géneros literarios. El nombre es único."""

    __tablename__ = "generos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    libros: Mapped[List["Libro"]] = relationship(back_populates="genero")


class Editorial(Base):
    """Tabla de editoriales o distribuidoras. El nombre es único."""

    __tablename__ = "editoriales"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    contacto: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    direccion: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    libros: Mapped[List["Libro"]] = relationship(back_populates="editorial")


class Moneda(Base):
    """Tabla de monedas en las que se expresan los precios. El código es único."""

    __tablename__ = "monedas"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    simbolo: Mapped[str] = mapped_column(String(5), nullable=False, default="$")

    precios: Mapped[List["Precio"]] = relationship(back_populates="moneda")


class TipoCotizacion(Base):
    """Tabla de tipos de cotización del dólar (Oficial, Blue, MEP, CCL)."""

    __tablename__ = "tipos_cotizacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    cotizaciones: Mapped[List["CotizacionDolar"]] = relationship(
        back_populates="tipo_cotizacion"
    )


class Libro(Base):
    """Tabla de libros del catálogo. El ISBN es único.

    Relaciona cada libro con su género y su editorial. Al eliminar un libro
    se eliminan en cascada sus precios y su stock, ya que no tienen sentido
    sin el libro al que pertenecen (igual que en `ServicioLibro.eliminar`).
    """

    __tablename__ = "libros"

    id: Mapped[int] = mapped_column(primary_key=True)
    isbn: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    autor: Mapped[str] = mapped_column(String(255), nullable=False)
    anio_publicacion: Mapped[int] = mapped_column(nullable=False)
    genero_id: Mapped[int] = mapped_column(ForeignKey("generos.id"), nullable=False)
    editorial_id: Mapped[int] = mapped_column(ForeignKey("editoriales.id"), nullable=False)

    genero: Mapped["Genero"] = relationship(back_populates="libros")
    editorial: Mapped["Editorial"] = relationship(back_populates="libros")
    precios: Mapped[List["Precio"]] = relationship(
        back_populates="libro", cascade="all, delete-orphan"
    )
    stock: Mapped[Optional["Stock"]] = relationship(
        back_populates="libro", cascade="all, delete-orphan", uselist=False
    )
    precios_web: Mapped[List["PrecioWeb"]] = relationship(
        back_populates="libro", cascade="all, delete-orphan"
    )


class Precio(Base):
    """Tabla de precios de un libro en una moneda determinada.

    Existe a lo sumo un precio por combinación de libro y moneda.
    """

    __tablename__ = "precios"
    __table_args__ = (UniqueConstraint("libro_id", "moneda_id", name="uq_precio_libro_moneda"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id", ondelete="CASCADE"), nullable=False
    )
    moneda_id: Mapped[int] = mapped_column(ForeignKey("monedas.id"), nullable=False)
    monto: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    libro: Mapped["Libro"] = relationship(back_populates="precios")
    moneda: Mapped["Moneda"] = relationship(back_populates="precios")


class Stock(Base):
    """Tabla de stock disponible por libro. Existe a lo sumo un registro por libro."""

    __tablename__ = "stock"

    id: Mapped[int] = mapped_column(primary_key=True)
    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    cantidad: Mapped[int] = mapped_column(nullable=False, default=0)
    ubicacion: Mapped[str] = mapped_column(String(100), nullable=False, default="Depósito")

    libro: Mapped["Libro"] = relationship(back_populates="stock")


class CotizacionDolar(Base):
    """Tabla histórica de cotizaciones del dólar por tipo y fecha.

    Existe a lo sumo una cotización por combinación de tipo y fecha.
    """

    __tablename__ = "cotizaciones"
    __table_args__ = (
        UniqueConstraint("tipo_id", "fecha", name="uq_cotizacion_tipo_fecha"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_id: Mapped[int] = mapped_column(ForeignKey("tipos_cotizacion.id"), nullable=False)
    fecha: Mapped[datetime.date] = mapped_column(nullable=False)
    valor_compra: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    valor_venta: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)

    tipo_cotizacion: Mapped["TipoCotizacion"] = relationship(back_populates="cotizaciones")


class PrecioWeb(Base):
    """Datos públicos de un libro del catálogo extraídos del sitio de Cúspide.

    Almacena el precio publicado en la web (en pesos y en dólares), la imagen,
    las formas de pago y la descripción detallada, junto con el precio interno
    del libro para poder compararlos.

    Existe a lo sumo un registro por combinación de libro y fecha de extracción.
    """

    __tablename__ = "precios_web"
    __table_args__ = (
        UniqueConstraint("libro_id", "fecha_extraccion", name="uq_precio_web_libro_fecha"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id", ondelete="CASCADE"), nullable=False
    )
    isbn: Mapped[str] = mapped_column(String(20), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    autor: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    precio_ars: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    precio_usd: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    precio_interno: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    url_imagen: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    formas_pago: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    descripcion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    url_producto: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    fecha_extraccion: Mapped[datetime.date] = mapped_column(nullable=False)

    libro: Mapped["Libro"] = relationship(back_populates="precios_web")
