"""Generador de resumenes breves para convocatorias."""

import re

from src.models import Oportunidad

MAX_WORDS = 15


def generate_summary(op: Oportunidad) -> str:
    """
    Generate a max-15-word summary from available Oportunidad fields.
    Uses heuristic extraction from nombre, entidad, tipo, and monto.
    """
    nombre = op.nombre.strip()
    if not nombre:
        return ""

    # Remove the entity name from the title if it's repeated
    entidad_short = op.entidad.split(" - ")[0].strip()
    nombre_clean = re.sub(re.escape(entidad_short), "", nombre, flags=re.IGNORECASE).strip()
    nombre_clean = re.sub(r'^[\s\-:,]+', '', nombre_clean).strip()
    if not nombre_clean:
        nombre_clean = nombre

    # Build prefix from tipo if it's informative and not already in the name
    prefix = ""
    if op.tipo and op.tipo != "Otro":
        tipo_lower = op.tipo.lower()
        if tipo_lower not in nombre_clean.lower():
            prefix = f"{op.tipo}: "

    # Build suffix with monto if available and short
    suffix = ""
    if op.monto and len(op.monto) < 30:
        suffix = f". {op.monto}"

    # Compose and truncate to MAX_WORDS
    summary = f"{prefix}{nombre_clean}{suffix}"
    words = summary.split()
    if len(words) > MAX_WORDS:
        summary = " ".join(words[:MAX_WORDS]) + "..."

    return summary
