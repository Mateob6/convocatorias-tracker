"""Orquestador de scraping de portales web."""

import logging
import time
from typing import Dict, List, Type

from src.models import Oportunidad
from src.portal_scrapers.base import BasePortalScraper, GenericScraper

logger = logging.getLogger(__name__)

# Registry of portal-specific scrapers
SCRAPER_REGISTRY: Dict[str, Type[BasePortalScraper]] = {}


def _load_scrapers():
    """Load portal-specific scrapers into the registry."""
    global SCRAPER_REGISTRY
    try:
        from src.portal_scrapers.minciencias import MincienciasScraper
        SCRAPER_REGISTRY["Minciencias"] = MincienciasScraper
    except ImportError:
        pass
    try:
        from src.portal_scrapers.icetex import IcetexScraper
        SCRAPER_REGISTRY["ICETEX"] = IcetexScraper
    except ImportError:
        pass
    try:
        from src.portal_scrapers.fulbright import FulbrightScraper
        SCRAPER_REGISTRY["Fulbright Colombia"] = FulbrightScraper
    except ImportError:
        pass
    try:
        from src.portal_scrapers.univalle import UnivalleScraper
        SCRAPER_REGISTRY["Univalle - DGP"] = UnivalleScraper
        SCRAPER_REGISTRY["Univalle - Extension"] = UnivalleScraper
        SCRAPER_REGISTRY["Univalle - Investigaciones"] = UnivalleScraper
    except ImportError:
        pass


_load_scrapers()


class WebScraperOrchestrator:
    """Coordinates scraping across all configured portals."""

    DELAY_BETWEEN_PORTALS = 2  # seconds

    def __init__(self, portal_configs: List[dict]):
        self.portal_configs = [p for p in portal_configs if p.get("activo", True)]

    def _get_scraper(self, portal_name: str, url: str) -> BasePortalScraper:
        """Returns the appropriate scraper instance for the portal."""
        scraper_class = SCRAPER_REGISTRY.get(portal_name, GenericScraper)
        return scraper_class(portal_name, url)

    def scrape_all(self) -> List[Oportunidad]:
        """
        Iterate over all active portals, scrape each, collect results.
        Continues on individual portal failures.
        """
        all_results = []

        for i, portal in enumerate(self.portal_configs):
            name = portal["nombre"]
            url = portal["url"]

            logger.info(f"Scraping [{i+1}/{len(self.portal_configs)}]: {name}")

            try:
                results = self.scrape_portal(name, url)
                all_results.extend(results)
                logger.info(f"  -> {len(results)} opportunities found")
            except Exception as e:
                logger.error(f"  -> Failed: {e}")

            # Be polite: delay between requests
            if i < len(self.portal_configs) - 1:
                time.sleep(self.DELAY_BETWEEN_PORTALS)

        logger.info(f"Web scraping complete: {len(all_results)} total opportunities")
        return all_results

    def scrape_portal(self, portal_name: str, url: str) -> List[Oportunidad]:
        """Scrape a single portal."""
        scraper = self._get_scraper(portal_name, url)
        return scraper.extract_opportunities()
