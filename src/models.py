"""Modelos de datos para el sistema de rastreo de convocatorias."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class TipoConvocatoria(Enum):
    BECA = "Beca"
    MOVILIDAD = "Movilidad"
    INVESTIGACION = "Investigacion"
    PASANTIA = "Pasantia"
    EXTENSION = "Extension"
    REPRESENTACION = "Representacion"
    OTRO = "Otro"


class Relevancia(Enum):
    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"


class Estado(Enum):
    NUEVA = "Nueva"
    REVISADA = "Revisada"
    EN_PREPARACION = "En preparacion"
    APLICADA = "Aplicada"
    DESCARTADA = "Descartada"
    VENCIDA = "Vencida"
    EN_PROCESO = "En proceso"


# Column order matching the Excel structure
COLUMNAS = [
    "ID", "Fecha_deteccion", "Nombre", "Entidad", "Tipo", "Fuente",
    "URL", "Fecha_apertura", "Fecha_cierre", "Monto", "Requisitos_clave",
    "Documentos_necesarios", "Relevancia", "Estado", "Notas",
]


@dataclass
class Oportunidad:
    id: Optional[int] = None
    fecha_deteccion: Optional[date] = field(default_factory=date.today)
    nombre: str = ""
    entidad: str = ""
    tipo: str = "Otro"
    fuente: str = ""
    url: str = ""
    fecha_apertura: Optional[date] = None
    fecha_cierre: Optional[date] = None
    monto: str = ""
    requisitos_clave: str = ""
    documentos_necesarios: str = ""
    relevancia: str = "Media"
    estado: str = "Nueva"
    notas: str = ""

    def to_row(self) -> list:
        """Convert to a list matching the Excel column order."""
        return [
            self.id,
            self.fecha_deteccion,
            self.nombre,
            self.entidad,
            self.tipo,
            self.fuente,
            self.url,
            self.fecha_apertura,
            self.fecha_cierre,
            self.monto,
            self.requisitos_clave,
            self.documentos_necesarios,
            self.relevancia,
            self.estado,
            self.notas,
        ]

    @classmethod
    def from_row(cls, row: list) -> "Oportunidad":
        """Construct from an Excel row (list of cell values)."""
        def parse_date(val):
            if val is None:
                return None
            if isinstance(val, date):
                return val
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, str) and val.strip():
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                    try:
                        return datetime.strptime(val.strip(), fmt).date()
                    except ValueError:
                        continue
            return None

        return cls(
            id=int(row[0]) if row[0] is not None else None,
            fecha_deteccion=parse_date(row[1]),
            nombre=str(row[2] or ""),
            entidad=str(row[3] or ""),
            tipo=str(row[4] or "Otro"),
            fuente=str(row[5] or ""),
            url=str(row[6] or ""),
            fecha_apertura=parse_date(row[7]),
            fecha_cierre=parse_date(row[8]),
            monto=str(row[9] or ""),
            requisitos_clave=str(row[10] or ""),
            documentos_necesarios=str(row[11] or ""),
            relevancia=str(row[12] or "Media"),
            estado=str(row[13] or "Nueva"),
            notas=str(row[14] or ""),
        )

    def is_expired(self) -> bool:
        """Check if fecha_cierre has passed."""
        if self.fecha_cierre and self.fecha_cierre < date.today():
            return True
        return False

    def dedup_key(self) -> str:
        """Key for deduplication: lowercase nombre + entidad."""
        return f"{self.nombre.lower().strip()}|{self.entidad.lower().strip()}"
