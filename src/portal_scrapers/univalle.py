"""Scraper para portales de la Universidad del Valle."""

import logging
from typing import List

from src.models import Oportunidad
from src.pdf_parser import find_deadline, extract_amount
from src.portal_scrapers.base import BasePortalScraper

logger = logging.getLogger(__name__)


class UnivalleScraper(BasePortalScraper):
    """Scraper para portales de Univalle (DGP, Extension, Investigaciones)."""

    PORTAL_TYPES = {
        "DGP": "Beca",
        "Extension": "Extension",
        "Investigaciones": "Investigacion",
    }

    def _detect_portal_type(self) -> str:
        url_lower = self.base_url.lower()
        if "extension" in url_lower:
            return "Extension"
        if "investigacion" in url_lower:
            return "Investigaciones"
        return "DGP"

    def extract_opportunities(self) -> List[Oportunidad]:
        soup = self.fetch_page()
        if not soup:
            return []

        results = []
        portal_type = self._detect_portal_type()
        default_tipo = self.PORTAL_TYPES.get(portal_type, "Otro")

        # Univalle sites use various CMS patterns
        selectors = [
            "article", ".node", ".views-row", ".card",
            "div[class*='convocatoria']", "div[class*='noticia']",
            ".elementor-post", "li.list-group-item",
        ]

        items = []
        for sel in selectors:
            items = soup.select(sel)
            if len(items) > 1:
                break

        # If no structured items found, search all links
        if not items or len(items) <= 1:
            keywords = [
                "convocatoria", "beca", "movilidad", "estancia",
                "pasantia", "investigacion", "extension",
            ]
            for link in soup.find_all("a", href=True):
                text = link.get_text(strip=True)
                href = link.get("href", "")
                combined = f"{text} {href}".lower()
                if any(kw in combined for kw in keywords) and len(text) > 10:
                    url = self._make_absolute_url(href)
                    context = ""
                    parent = link.find_parent(["div", "li", "article", "section"])
                    if parent:
                        context = parent.get_text()

                    op = Oportunidad(
                        nombre=text[:200],
                        entidad=f"Universidad del Valle - {portal_type}",
                        tipo=default_tipo,
                        fuente=f"Web - {self.portal_name}",
                        url=url,
                        fecha_cierre=find_deadline(context) if context else None,
                        monto=extract_amount(context) if context else "",
                    )
                    results.append(op)
            logger.info(f"[{self.portal_name}] Link scan found {len(results)} items")
            return results[:20]

        for item in items[:20]:
            title_el = item.select_one("h2 a, h3 a, h4 a, .title a, a.node-title, a")
            if not title_el:
                continue

            text = title_el.get_text(strip=True)
            if not text or len(text) < 8:
                continue

            href = title_el.get("href", "")
            url = self._make_absolute_url(href)

            context = item.get_text()
            deadline = find_deadline(context)
            amount = extract_amount(context)

            op = Oportunidad(
                nombre=text[:200],
                entidad=f"Universidad del Valle - {portal_type}",
                tipo=default_tipo,
                fuente=f"Web - {self.portal_name}",
                url=url,
                fecha_cierre=deadline,
                monto=amount,
            )
            results.append(op)

        logger.info(f"[{self.portal_name}] Found {len(results)} items")
        return results
