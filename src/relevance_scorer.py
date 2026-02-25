"""Puntuacion de relevancia basada en el perfil academico."""

import logging
import re
from typing import List

from src.models import Oportunidad

logger = logging.getLogger(__name__)


class RelevanceScorer:
    """Scores opportunities based on the candidate profile."""

    def __init__(self, profile: dict):
        self.profile = profile
        self.high_keywords = self._build_high_keywords()
        self.medium_keywords = self._build_medium_keywords()

    def _build_high_keywords(self) -> List[str]:
        """Keywords that strongly indicate relevance."""
        base = [
            "doctorado", "doctoral", "phd", "ph.d",
            "psicologia", "psicología", "psychology",
            "colombia", "colombian",
            "latinoamerica", "latinoamérica", "latin america", "iberoamerica",
            "univalle", "universidad del valle",
            "cognitiv", "cognitive",
            "psicometri", "psychometr",
        ]
        areas = [a.lower() for a in self.profile.get("areas", [])]
        return base + areas

    def _build_medium_keywords(self) -> List[str]:
        """Keywords that moderately indicate relevance."""
        return [
            "estadistica", "estadística", "statistics", "statistical",
            "filosofia", "filosofía", "philosophy",
            "investigacion", "investigación", "research",
            "ciencias sociales", "social sciences",
            "posgrado", "postgrado", "graduate",
            "maestria", "maestría", "master",
            "educacion", "educación", "education",
            "cali", "valle del cauca",
            "computacional", "computational",
        ]

    def _count_matches(self, text: str, keywords: List[str]) -> int:
        """Count how many keywords appear in the text."""
        text_lower = text.lower()
        return sum(1 for kw in keywords if kw in text_lower)

    def score(self, op: Oportunidad) -> str:
        """
        Score an opportunity based on keyword matches.
        Returns "Alta", "Media", or "Baja".
        """
        # Build searchable text from all relevant fields
        searchable = " ".join([
            op.nombre, op.entidad, op.requisitos_clave,
            op.notas, op.tipo, op.monto,
        ])

        high_count = self._count_matches(searchable, self.high_keywords)
        medium_count = self._count_matches(searchable, self.medium_keywords)

        if high_count >= 2:
            return "Alta"
        if high_count >= 1 or medium_count >= 2:
            return "Media"
        return "Baja"

    def score_all(self, opportunities: List[Oportunidad]) -> List[Oportunidad]:
        """
        Score a batch of opportunities.
        Only scores if relevancia is still the default "Media" (auto-assigned).
        Does not override manually set relevancia.
        """
        for op in opportunities:
            if op.relevancia in ("Media", "Baja", ""):
                op.relevancia = self.score(op)
        return opportunities
