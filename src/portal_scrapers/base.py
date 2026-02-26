"""Clases base para los scrapers de portales web."""

import logging
import re
import time
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.models import Oportunidad
from src.pdf_parser import (
    extract_amount, extract_dates, extract_documents,
    extract_requirements, find_deadline, find_opening_date,
)

logger = logging.getLogger(__name__)

CONVOCATORIA_KEYWORDS = [
    "beca", "scholarship", "convocatoria", "movilidad", "mobility",
    "pasantia", "pasantías", "fellowship", "grant", "funding",
    "call for", "estancia", "intercambio", "exchange", "award",
    "doctorado", "doctoral", "investigacion", "research",
]


class BasePortalScraper:
    """Abstract base class for all portal scrapers."""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    }
    TIMEOUT = 30

    def __init__(self, portal_name: str, base_url: str):
        self.portal_name = portal_name
        self.base_url = base_url

    def fetch_page(self, url: Optional[str] = None) -> Optional[BeautifulSoup]:
        """HTTP GET the URL, return parsed BeautifulSoup object."""
        target_url = url or self.base_url
        try:
            response = requests.get(
                target_url, headers=self.HEADERS, timeout=self.TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except requests.exceptions.RequestException as e:
            logger.warning(f"[{self.portal_name}] Failed to fetch {target_url}: {e}")
            return None

    def extract_opportunities(self) -> List[Oportunidad]:
        """Scrape the portal and return a list of Oportunidad objects."""
        raise NotImplementedError

    def _make_absolute_url(self, relative_url: str) -> str:
        """Convert relative URLs to absolute using base_url."""
        if not relative_url:
            return ""
        if relative_url.startswith(("http://", "https://")):
            return relative_url
        return urljoin(self.base_url, relative_url)

    def fetch_detail_text(self, url: str) -> str:
        """Fetch a detail page and return its full text content."""
        if not url:
            return ""
        try:
            response = requests.get(
                url, headers=self.HEADERS, timeout=15,
                allow_redirects=True,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            # Remove nav, header, footer, script, style to get cleaner text
            for tag in soup.select("nav, header, footer, script, style, noscript"):
                tag.decompose()
            return soup.get_text(separator=" ", strip=True)
        except requests.exceptions.RequestException as e:
            logger.debug(f"[{self.portal_name}] Detail fetch failed for {url}: {e}")
            return ""

    def enrich_from_detail(self, op, detail_text: str) -> None:
        """Fill empty fields using data extracted from a detail page."""
        if not detail_text:
            return
        if not op.fecha_apertura:
            op.fecha_apertura = find_opening_date(detail_text)
        if not op.fecha_cierre:
            op.fecha_cierre = find_deadline(detail_text)
        if not op.monto:
            op.monto = extract_amount(detail_text)
        if not op.requisitos_clave:
            op.requisitos_clave = extract_requirements(detail_text)
        if not op.documentos_necesarios:
            op.documentos_necesarios = extract_documents(detail_text)


class GenericScraper(BasePortalScraper):
    """
    Fallback scraper that looks for common patterns:
    - Links containing convocatoria-related keywords
    - Date patterns in surrounding text
    """

    def extract_opportunities(self) -> List[Oportunidad]:
        soup = self.fetch_page()
        if not soup:
            return []

        results = []
        seen_urls = set()

        # Find all links on the page
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            full_url = self._make_absolute_url(href)

            if not text or len(text) < 10 or full_url in seen_urls:
                continue

            # Skip navigation, language selectors, and short generic links
            skip_patterns = [
                "menu", "nav", "footer", "header", "cookie", "privacy",
                "login", "registro", "sign in", "contacto", "about",
                "términos", "condiciones", "politica", "política",
                "facebook", "twitter", "linkedin", "instagram", "youtube",
            ]
            text_lower = text.lower()
            if any(pat in text_lower for pat in skip_patterns):
                continue
            if len(text) < 15 and not any(kw in text_lower for kw in CONVOCATORIA_KEYWORDS):
                continue

            # Check if link text or URL contains relevant keywords
            combined = f"{text} {href}".lower()
            if not any(kw in combined for kw in CONVOCATORIA_KEYWORDS):
                continue

            seen_urls.add(full_url)

            # Try to extract date from surrounding context
            parent = link.find_parent(["div", "li", "article", "tr", "section"])
            context_text = parent.get_text() if parent else text
            deadline = find_deadline(context_text)
            amount = extract_amount(context_text)

            op = Oportunidad(
                nombre=text[:200],
                entidad=self.portal_name,
                tipo="Otro",
                fuente=f"Web - {self.portal_name}",
                url=full_url,
                fecha_cierre=deadline,
                monto=amount,
            )

            # Fetch detail page to fill requisitos, documentos, etc.
            detail_text = self.fetch_detail_text(full_url)
            self.enrich_from_detail(op, detail_text)
            time.sleep(1)

            results.append(op)

        logger.info(f"[{self.portal_name}] GenericScraper found {len(results)} items")
        return results
