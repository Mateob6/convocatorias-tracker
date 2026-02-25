"""Scraper para el portal de ICETEX."""

import logging
from typing import List

from src.models import Oportunidad
from src.pdf_parser import find_deadline, extract_amount
from src.portal_scrapers.base import BasePortalScraper

logger = logging.getLogger(__name__)


class IcetexScraper(BasePortalScraper):
    """Scraper para becas de ICETEX."""

    def extract_opportunities(self) -> List[Oportunidad]:
        soup = self.fetch_page()
        if not soup:
            return []

        results = []

        # ICETEX typically uses card/accordion patterns
        selectors = [
            ".card", ".accordion-item", "article", ".beca-item",
            ".views-row", "div[class*='beca']", "li.list-group-item",
        ]

        items = []
        for sel in selectors:
            items = soup.select(sel)
            if items:
                break

        if not items:
            for link in soup.find_all("a", href=True):
                text = link.get_text(strip=True)
                href = link.get("href", "")
                combined = f"{text} {href}".lower()
                if any(kw in combined for kw in ["beca", "scholarship", "convocatoria"]):
                    url = self._make_absolute_url(href)
                    op = Oportunidad(
                        nombre=text[:200],
                        entidad="ICETEX",
                        tipo="Beca",
                        fuente=f"Web - {self.portal_name}",
                        url=url,
                    )
                    results.append(op)
            logger.info(f"[{self.portal_name}] Fallback found {len(results)} items")
            return results[:20]

        for item in items[:20]:
            title_el = item.select_one(
                "h2, h3, h4, .card-title, .accordion-header, "
                ".card-header, a[class*='title']"
            )
            if not title_el:
                continue

            text = title_el.get_text(strip=True)
            if not text or len(text) < 5:
                continue

            link_el = item.select_one("a[href]") or title_el.find_parent("a")
            href = link_el.get("href", "") if link_el else ""
            url = self._make_absolute_url(href)

            context = item.get_text()
            deadline = find_deadline(context)
            amount = extract_amount(context)

            op = Oportunidad(
                nombre=text[:200],
                entidad="ICETEX",
                tipo="Beca",
                fuente=f"Web - {self.portal_name}",
                url=url,
                fecha_cierre=deadline,
                monto=amount,
            )
            results.append(op)

        logger.info(f"[{self.portal_name}] Found {len(results)} items")
        return results
