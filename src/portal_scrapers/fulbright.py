"""Scraper para Fulbright Colombia."""

import logging
from typing import List

from src.models import Oportunidad
from src.pdf_parser import find_deadline, extract_amount
from src.portal_scrapers.base import BasePortalScraper

logger = logging.getLogger(__name__)


class FulbrightScraper(BasePortalScraper):
    """Scraper para becas Fulbright Colombia."""

    def extract_opportunities(self) -> List[Oportunidad]:
        soup = self.fetch_page()
        if not soup:
            return []

        results = []

        # Fulbright typically lists programs with cards or sections
        selectors = [
            "article", ".program-card", ".beca-card", ".card",
            ".elementor-widget-container", "div[class*='program']",
        ]

        items = []
        for sel in selectors:
            items = soup.select(sel)
            if len(items) > 1:
                break

        if not items or len(items) <= 1:
            for link in soup.find_all("a", href=True):
                text = link.get_text(strip=True)
                href = link.get("href", "")
                combined = f"{text} {href}".lower()
                if any(kw in combined for kw in ["beca", "scholarship", "program", "grant"]):
                    if len(text) > 10:
                        url = self._make_absolute_url(href)
                        op = Oportunidad(
                            nombre=text[:200],
                            entidad="Fulbright Colombia",
                            tipo="Beca",
                            fuente=f"Web - {self.portal_name}",
                            url=url,
                        )
                        results.append(op)
            logger.info(f"[{self.portal_name}] Fallback found {len(results)} items")
            return results[:20]

        for item in items[:20]:
            title_el = item.select_one("h2, h3, h4, .title, a")
            if not title_el:
                continue

            text = title_el.get_text(strip=True)
            if not text or len(text) < 10:
                continue

            link_el = item.select_one("a[href]")
            href = link_el.get("href", "") if link_el else ""
            url = self._make_absolute_url(href)

            context = item.get_text()
            deadline = find_deadline(context)

            op = Oportunidad(
                nombre=text[:200],
                entidad="Fulbright Colombia",
                tipo="Beca",
                fuente=f"Web - {self.portal_name}",
                url=url,
                fecha_cierre=deadline,
            )
            results.append(op)

        logger.info(f"[{self.portal_name}] Found {len(results)} items")
        return results
