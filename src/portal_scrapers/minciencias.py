"""Scraper para el portal de Minciencias."""

import logging
import time
from typing import List

from src.models import Oportunidad
from src.pdf_parser import find_deadline, extract_amount
from src.portal_scrapers.base import BasePortalScraper

logger = logging.getLogger(__name__)


class MincienciasScraper(BasePortalScraper):
    """Scraper para convocatorias de Minciencias."""

    def extract_opportunities(self) -> List[Oportunidad]:
        soup = self.fetch_page()
        if not soup:
            return []

        results = []

        # Minciencias uses various card/list patterns
        selectors = [
            "article", ".views-row", ".card", ".node--type-convocatoria",
            ".view-content .item-list li", "div.convocatoria",
        ]

        items = []
        for sel in selectors:
            items = soup.select(sel)
            if items:
                break

        if not items:
            # Fallback: look for any links with "convocatoria" in text/href
            for link in soup.find_all("a", href=True):
                text = link.get_text(strip=True)
                href = link.get("href", "")
                if "convocatoria" in text.lower() or "convocatoria" in href.lower():
                    url = self._make_absolute_url(href)
                    op = Oportunidad(
                        nombre=text[:200],
                        entidad="Minciencias",
                        tipo="Investigacion",
                        fuente=f"Web - {self.portal_name}",
                        url=url,
                    )
                    results.append(op)
            logger.info(f"[{self.portal_name}] Fallback found {len(results)} items")
            return results[:20]

        for item in items[:20]:
            title_el = item.select_one("h2 a, h3 a, .title a, .field--name-title a, a")
            if not title_el:
                continue

            text = title_el.get_text(strip=True)
            if not text or len(text) < 5:
                continue

            href = title_el.get("href", "")
            url = self._make_absolute_url(href)

            context = item.get_text()
            deadline = find_deadline(context)
            amount = extract_amount(context)

            # Determine status from badges
            estado = "Nueva"
            badges = item.select(".badge, .label, .status, .estado")
            for badge in badges:
                badge_text = badge.get_text(strip=True).lower()
                if "cerrad" in badge_text or "finaliz" in badge_text:
                    estado = "Vencida"
                elif "abiert" in badge_text:
                    estado = "Nueva"

            op = Oportunidad(
                nombre=text[:200],
                entidad="Minciencias",
                tipo="Investigacion",
                fuente=f"Web - {self.portal_name}",
                url=url,
                fecha_cierre=deadline,
                monto=amount,
                estado=estado,
            )

            detail_text = self.fetch_detail_text(url)
            self.enrich_from_detail(op, detail_text)
            time.sleep(1)

            results.append(op)

        logger.info(f"[{self.portal_name}] Found {len(results)} items")
        return results
