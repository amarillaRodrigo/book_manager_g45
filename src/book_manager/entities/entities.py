"""Módulo para las entidades de dominio de Book Manager.

Contiene las clases base y de dominio utilizando POO pura, encapsulamiento
y type hints, sin dependencias externas fuera de la librería estándar.
"""

import datetime
from typing import Any, Dict, Optional


class EntidadBase:
    """Clase base abstracta para todas las entidades del dominio."""

    def __init__(self, id: Optional[int] = None) -> None:
        self._id: Optional[int] = id

    @property
    def id(self) -> Optional[int]:
        """Obtiene el ID de la entidad."""
        return self._id

    @id.setter
    def id(self, value: Optional[int]) -> None:
        """Establece el ID de la entidad validando que sea mayor a 0 si existe."""
        if value is not None and value <= 0:
            raise ValueError("El ID debe ser un número entero positivo.")
        self._id = value

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la entidad a un diccionario serializable."""
        raise NotImplementedError("Debe implementar to_dict() en la subclase.")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntidadBase":
        """Crea una instancia de la entidad desde un diccionario."""
        raise NotImplementedError("Debe implementar from_dict() en la subclase.")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.id is not None and self.id == other.id


class Genero(EntidadBase):
    """Representa la categoría o género literario de un libro."""

    def __init__(self, nombre: str, descripcion: str = "", id: Optional[int] = None) -> None:
        super().__init__(id)
        self.nombre = nombre
        self._descripcion = descripcion

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("El nombre del género no puede estar vacío.")
        self._nombre = value.strip()

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @descripcion.setter
    def descripcion(self, value: str) -> None:
        self._descripcion = value.strip() if value else ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id is not None else "",
            "nombre": self.nombre,
            "descripcion": self.descripcion,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Genero":
        raw_id = data.get("id")
        obj_id = int(raw_id) if raw_id and str(raw_id).strip() else None
        return cls(
            id=obj_id,
            nombre=data.get("nombre", ""),
            descripcion=data.get("descripcion", ""),
        )

    def __repr__(self) -> str:
        return f"Genero(id={self.id}, nombre='{self.nombre}')"


class Editorial(EntidadBase):
    """Representa a la editorial o distribuidora que provee los libros."""

    def __init__(
        self, nombre: str, contacto: str = "", direccion: str = "", id: Optional[int] = None
    ) -> None:
        super().__init__(id)
        self.nombre = nombre
        self._contacto = contacto
        self._direccion = direccion

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("El nombre de la editorial no puede estar vacío.")
        self._nombre = value.strip()

    @property
    def contacto(self) -> str:
        return self._contacto

    @contacto.setter
    def contacto(self, value: str) -> None:
        self._contacto = value.strip() if value else ""

    @property
    def direccion(self) -> str:
        return self._direccion

    @direccion.setter
    def direccion(self, value: str) -> None:
        self._direccion = value.strip() if value else ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id is not None else "",
            "nombre": self.nombre,
            "contacto": self.contacto,
            "direccion": self.direccion,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Editorial":
        raw_id = data.get("id")
        obj_id = int(raw_id) if raw_id and str(raw_id).strip() else None
        return cls(
            id=obj_id,
            nombre=data.get("nombre", ""),
            contacto=data.get("contacto", ""),
            direccion=data.get("direccion", ""),
        )

    def __repr__(self) -> str:
        return f"Editorial(id={self.id}, nombre='{self.nombre}')"


class Moneda(EntidadBase):
    """Representa una moneda en la que se expresa un precio (ARS, USD, etc.)."""

    def __init__(
        self, codigo: str, nombre: str, simbolo: str = "$", id: Optional[int] = None
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.nombre = nombre
        self._simbolo = simbolo

    @property
    def codigo(self) -> str:
        return self._codigo

    @codigo.setter
    def codigo(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("El código de moneda no puede estar vacío.")
        self._codigo = value.strip().upper()

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("El nombre de moneda no puede estar vacío.")
        self._nombre = value.strip()

    @property
    def simbolo(self) -> str:
        return self._simbolo

    @simbolo.setter
    def simbolo(self, value: str) -> None:
        self._simbolo = value.strip() if value else "$"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id is not None else "",
            "codigo": self.codigo,
            "nombre": self.nombre,
            "simbolo": self.simbolo,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Moneda":
        raw_id = data.get("id")
        obj_id = int(raw_id) if raw_id and str(raw_id).strip() else None
        return cls(
            id=obj_id,
            codigo=data.get("codigo", ""),
            nombre=data.get("nombre", ""),
            simbolo=data.get("simbolo", "$"),
        )

    def __repr__(self) -> str:
        return f"Moneda(id={self.id}, codigo='{self.codigo}', simbolo='{self.simbolo}')"


class TipoCotizacion(EntidadBase):
    """Representa el tipo de cotización del dólar (Oficial, Blue, MEP, CCL)."""

    def __init__(self, nombre: str, descripcion: str = "", id: Optional[int] = None) -> None:
        super().__init__(id)
        self.nombre = nombre
        self._descripcion = descripcion

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("El nombre de la cotización no puede estar vacío.")
        self._nombre = value.strip()

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @descripcion.setter
    def descripcion(self, value: str) -> None:
        self._descripcion = value.strip() if value else ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id is not None else "",
            "nombre": self.nombre,
            "descripcion": self.descripcion,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TipoCotizacion":
        raw_id = data.get("id")
        obj_id = int(raw_id) if raw_id and str(raw_id).strip() else None
        return cls(
            id=obj_id,
            nombre=data.get("nombre", ""),
            descripcion=data.get("descripcion", ""),
        )

    def __repr__(self) -> str:
        return f"TipoCotizacion(id={self.id}, nombre='{self.nombre}')"


class Libro(EntidadBase):
    """Representa cada título del catálogo de la librería."""

    def __init__(
        self,
        isbn: str,
        titulo: str,
        autor: str,
        genero_id: int,
        editorial_id: int,
        anio_publicacion: int = 2024,
        id: Optional[int] = None,
    ) -> None:
        super().__init__(id)
        self.isbn = isbn
        self.titulo = titulo
        self.autor = autor
        self.genero_id = genero_id
        self.editorial_id = editorial_id
        self.anio_publicacion = anio_publicacion

    @property
    def isbn(self) -> str:
        return self._isbn

    @isbn.setter
    def isbn(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("El ISBN no puede estar vacío.")
        self._isbn = value.strip()

    @property
    def titulo(self) -> str:
        return self._titulo

    @titulo.setter
    def titulo(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("El título no puede estar vacío.")
        self._titulo = value.strip()

    @property
    def autor(self) -> str:
        return self._autor

    @autor.setter
    def autor(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("El autor no puede estar vacío.")
        self._autor = value.strip()

    @property
    def genero_id(self) -> int:
        return self._genero_id

    @genero_id.setter
    def genero_id(self, value: int) -> None:
        if value <= 0:
            raise ValueError("El ID de género debe ser mayor a 0.")
        self._genero_id = value

    @property
    def editorial_id(self) -> int:
        return self._editorial_id

    @editorial_id.setter
    def editorial_id(self, value: int) -> None:
        if value <= 0:
            raise ValueError("El ID de editorial debe ser mayor a 0.")
        self._editorial_id = value

    @property
    def anio_publicacion(self) -> int:
        return self._anio_publicacion

    @anio_publicacion.setter
    def anio_publicacion(self, value: int) -> None:
        if value <= 0:
            raise ValueError("El año de publicación debe ser un año válido.")
        self._anio_publicacion = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id is not None else "",
            "isbn": self.isbn,
            "titulo": self.titulo,
            "autor": self.autor,
            "genero_id": str(self.genero_id),
            "editorial_id": str(self.editorial_id),
            "anio_publicacion": str(self.anio_publicacion),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Libro":
        raw_id = data.get("id")
        obj_id = int(raw_id) if raw_id and str(raw_id).strip() else None
        return cls(
            id=obj_id,
            isbn=data.get("isbn", ""),
            titulo=data.get("titulo", ""),
            autor=data.get("autor", ""),
            genero_id=int(data.get("genero_id", 1)),
            editorial_id=int(data.get("editorial_id", 1)),
            anio_publicacion=int(data.get("anio_publicacion", 2024)),
        )

    def __repr__(self) -> str:
        return f"Libro(id={self.id}, isbn='{self.isbn}', titulo='{self.titulo}')"


class Precio(EntidadBase):
    """Representa el valor monetario asociado a un libro en una moneda determinada."""

    def __init__(
        self, libro_id: int, monto: float, moneda_id: int, id: Optional[int] = None
    ) -> None:
        super().__init__(id)
        self.libro_id = libro_id
        self.monto = monto
        self.moneda_id = moneda_id

    @property
    def libro_id(self) -> int:
        return self._libro_id

    @libro_id.setter
    def libro_id(self, value: int) -> None:
        if value <= 0:
            raise ValueError("El ID del libro debe ser mayor a 0.")
        self._libro_id = value

    @property
    def monto(self) -> float:
        return self._monto

    @monto.setter
    def monto(self, value: float) -> None:
        if value <= 0:
            raise ValueError("El monto del precio debe ser mayor a 0.")
        self._monto = float(value)

    @property
    def moneda_id(self) -> int:
        return self._moneda_id

    @moneda_id.setter
    def moneda_id(self, value: int) -> None:
        if value <= 0:
            raise ValueError("El ID de moneda debe ser mayor a 0.")
        self._moneda_id = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id is not None else "",
            "libro_id": str(self.libro_id),
            "monto": str(self.monto),
            "moneda_id": str(self.moneda_id),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Precio":
        raw_id = data.get("id")
        obj_id = int(raw_id) if raw_id and str(raw_id).strip() else None
        return cls(
            id=obj_id,
            libro_id=int(data.get("libro_id", 1)),
            monto=float(data.get("monto", 0.0)),
            moneda_id=int(data.get("moneda_id", 1)),
        )

    def __repr__(self) -> str:
        return f"Precio(id={self.id}, libro_id={self.libro_id}, monto={self.monto})"


class Stock(EntidadBase):
    """Representa la cantidad disponible de cada libro."""

    def __init__(
        self, libro_id: int, cantidad: int, ubicacion: str = "Depósito", id: Optional[int] = None
    ) -> None:
        super().__init__(id)
        self.libro_id = libro_id
        self.cantidad = cantidad
        self._ubicacion = ubicacion

    @property
    def libro_id(self) -> int:
        return self._libro_id

    @libro_id.setter
    def libro_id(self, value: int) -> None:
        if value <= 0:
            raise ValueError("El ID del libro debe ser mayor a 0.")
        self._libro_id = value

    @property
    def cantidad(self) -> int:
        return self._cantidad

    @cantidad.setter
    def cantidad(self, value: int) -> None:
        if value < 0:
            raise ValueError("La cantidad en stock no puede ser negativa.")
        self._cantidad = int(value)

    @property
    def ubicacion(self) -> str:
        return self._ubicacion

    @ubicacion.setter
    def ubicacion(self, value: str) -> None:
        self._ubicacion = value.strip() if value else "Depósito"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id is not None else "",
            "libro_id": str(self.libro_id),
            "cantidad": str(self.cantidad),
            "ubicacion": self.ubicacion,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Stock":
        raw_id = data.get("id")
        obj_id = int(raw_id) if raw_id and str(raw_id).strip() else None
        return cls(
            id=obj_id,
            libro_id=int(data.get("libro_id", 1)),
            cantidad=int(data.get("cantidad", 0)),
            ubicacion=data.get("ubicacion", "Depósito"),
        )

    def __repr__(self) -> str:
        return f"Stock(id={self.id}, libro_id={self.libro_id}, cantidad={self.cantidad})"


class CotizacionDolar(EntidadBase):
    """Registro histórico de las cotizaciones del dólar por tipo y fecha."""

    def __init__(
        self,
        tipo_id: int,
        fecha: datetime.date,
        valor_compra: float,
        valor_venta: float,
        id: Optional[int] = None,
    ) -> None:
        super().__init__(id)
        self.tipo_id = tipo_id
        self.fecha = fecha
        self.valor_compra = valor_compra
        self.valor_venta = valor_venta

    @property
    def tipo_id(self) -> int:
        return self._tipo_id

    @tipo_id.setter
    def tipo_id(self, value: int) -> None:
        if value <= 0:
            raise ValueError("El ID de tipo de cotización debe ser mayor a 0.")
        self._tipo_id = value

    @property
    def fecha(self) -> datetime.date:
        return self._fecha

    @fecha.setter
    def fecha(self, value: datetime.date) -> None:
        if not isinstance(value, datetime.date):
            raise TypeError("La fecha debe ser un objeto datetime.date.")
        self._fecha = value

    @property
    def valor_compra(self) -> float:
        return self._valor_compra

    @valor_compra.setter
    def valor_compra(self, value: float) -> None:
        if value <= 0:
            raise ValueError("El valor de compra debe ser mayor a 0.")
        self._valor_compra = float(value)

    @property
    def valor_venta(self) -> float:
        return self._valor_venta

    @valor_venta.setter
    def valor_venta(self, value: float) -> None:
        if value <= 0:
            raise ValueError("El valor de venta debe ser mayor a 0.")
        self._valor_venta = float(value)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id) if self.id is not None else "",
            "tipo_id": str(self.tipo_id),
            "fecha": self.fecha.isoformat(),
            "valor_compra": str(self.valor_compra),
            "valor_venta": str(self.valor_venta),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CotizacionDolar":
        raw_id = data.get("id")
        obj_id = int(raw_id) if raw_id and str(raw_id).strip() else None

        fecha_raw = data.get("fecha", "")
        if isinstance(fecha_raw, datetime.date):
            fecha_obj = fecha_raw
        elif isinstance(fecha_raw, str) and fecha_raw.strip():
            fecha_obj = datetime.date.fromisoformat(fecha_raw.strip())
        else:
            fecha_obj = datetime.date.today()

        return cls(
            id=obj_id,
            tipo_id=int(data.get("tipo_id", 1)),
            fecha=fecha_obj,
            valor_compra=float(data.get("valor_compra", 1.0)),
            valor_venta=float(data.get("valor_venta", 1.0)),
        )

    def __repr__(self) -> str:
        return (
            f"CotizacionDolar(id={self.id}, tipo_id={self.tipo_id}, "
            f"fecha={self.fecha}, compra={self.valor_compra}, venta={self.valor_venta})"
        )
