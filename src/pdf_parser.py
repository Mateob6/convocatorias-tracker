"""Extraccion de datos estructurados desde documentos PDF."""

import logging
import re
from datetime import date, datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Spanish month names
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    "ene": 1, "feb": 2, "mar": 3, "abr": 4,
    "may": 5, "jun": 6, "jul": 7, "ago": 8,
    "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}

ENGLISH_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def extract_dates(text: str) -> List[date]:
    """
    Extract all dates from text. Handles multiple formats:
    - dd de mes de yyyy (Spanish)
    - dd/mm/yyyy, dd-mm-yyyy
    - yyyy-mm-dd (ISO)
    - Month dd, yyyy (English)
    Returns sorted list of date objects.
    """
    dates = set()
    text_lower = text.lower()

    # Pattern: dd de mes de yyyy
    for match in re.finditer(
        r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|'
        r'septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?(\d{4})',
        text_lower
    ):
        day, month_name, year = int(match.group(1)), match.group(2), int(match.group(3))
        month = MESES.get(month_name)
        if month:
            try:
                dates.add(date(year, month, day))
            except ValueError:
                pass

    # Pattern: dd/mm/yyyy or dd-mm-yyyy
    for match in re.finditer(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', text):
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31:
            try:
                dates.add(date(year, month, day))
            except ValueError:
                pass

    # Pattern: yyyy-mm-dd (ISO)
    for match in re.finditer(r'(\d{4})-(\d{2})-(\d{2})', text):
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if 2020 <= year <= 2030:
            try:
                dates.add(date(year, month, day))
            except ValueError:
                pass

    # Pattern: Month dd, yyyy (English)
    for month_name, month_num in ENGLISH_MONTHS.items():
        pattern = rf'{month_name}\s+(\d{{1,2}}),?\s+(\d{{4}})'
        for match in re.finditer(pattern, text_lower):
            day, year = int(match.group(1)), int(match.group(2))
            try:
                dates.add(date(year, month_num, day))
            except ValueError:
                pass

    return sorted(dates)


def find_deadline(text: str) -> Optional[date]:
    """Find the most likely closing date near deadline keywords."""
    keywords = [
        r'fecha\s*l[ií]mite', r'cierre', r'deadline', r'hasta\s+el',
        r'closes?', r'vence', r'plazo', r'recepci[oó]n.*hasta',
        r'fecha\s*de\s*cierre', r'closing\s*date',
    ]
    text_lower = text.lower()

    for keyword in keywords:
        for match in re.finditer(keyword, text_lower):
            # Extract a window of text around the keyword
            start = max(0, match.start() - 20)
            end = min(len(text_lower), match.end() + 150)
            window = text_lower[start:end]
            dates = extract_dates(window)
            if dates:
                return dates[-1]  # Take the latest date near the keyword

    # Fallback: return the latest date found in the whole text
    all_dates = extract_dates(text)
    return all_dates[-1] if all_dates else None


def find_opening_date(text: str) -> Optional[date]:
    """Find the most likely opening date."""
    keywords = [r'apertura', r'inicio', r'opens?', r'desde', r'a\s*partir\s*de']
    text_lower = text.lower()

    for keyword in keywords:
        for match in re.finditer(keyword, text_lower):
            start = max(0, match.start() - 20)
            end = min(len(text_lower), match.end() + 150)
            window = text_lower[start:end]
            dates = extract_dates(window)
            if dates:
                return dates[0]

    return None


def extract_amount(text: str) -> str:
    """
    Extract monetary amounts from text.
    Returns formatted string or empty string if not found.
    """
    text_clean = text.replace('\n', ' ')

    # COP patterns: $13.000.000, $4.725.000
    cop_pattern = r'\$\s*([\d.]+(?:\.\d{3})+)'
    for match in re.finditer(cop_pattern, text_clean):
        return f"COP ${match.group(1)}"

    # "X millones de pesos" pattern
    mill_pattern = r'(\d+(?:[.,]\d+)?)\s*millones?\s*(?:de\s*pesos)?'
    match = re.search(mill_pattern, text_clean.lower())
    if match:
        return f"COP ${match.group(1)} millones"

    # USD/EUR patterns
    for currency in ['USD', 'EUR', 'GBP']:
        pattern = rf'{currency}\s*\$?\s*([\d,.\s]+)'
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            return f"{currency} {match.group(1).strip()}"

    return ""


def extract_requirements(text: str) -> str:
    """Extract requirement sections from text."""
    keywords = [
        r'requisitos?', r'requirements?', r'perfil', r'elegibilidad',
        r'who\s+can\s+apply', r'quienes?\s+pueden\s+participar',
        r'destinatarios?', r'dirigid[oa]\s+a',
    ]
    text_lower = text.lower()
    results = []

    for keyword in keywords:
        for match in re.finditer(keyword, text_lower):
            start = match.end()
            end = min(len(text), start + 500)
            chunk = text[start:end].strip()
            # Take up to the next section header or double newline
            section_end = re.search(r'\n\s*\n|\n[A-ZÁÉÍÓÚ][^a-z]{3,}', chunk)
            if section_end:
                chunk = chunk[:section_end.start()]
            chunk = chunk.strip(': \n\t')
            if len(chunk) > 20:
                results.append(chunk[:300])

    return "; ".join(results[:3]) if results else ""


def extract_documents(text: str) -> str:
    """Extract document lists from text."""
    keywords = [
        r'documentos?\s*(?:requeridos?|necesarios?|a\s*presentar)',
        r'adjuntar', r'annexe?s?', r'debe\s*presentar',
        r'documentaci[oó]n', r'se\s*debe\s*enviar',
    ]
    text_lower = text.lower()
    results = []

    for keyword in keywords:
        for match in re.finditer(keyword, text_lower):
            start = match.end()
            end = min(len(text), start + 400)
            chunk = text[start:end].strip()
            section_end = re.search(r'\n\s*\n|\n[A-ZÁÉÍÓÚ][^a-z]{3,}', chunk)
            if section_end:
                chunk = chunk[:section_end.start()]
            chunk = chunk.strip(': \n\t')
            if len(chunk) > 10:
                results.append(chunk[:200])

    return "; ".join(results[:3]) if results else ""


class PDFParser:
    """Extracts structured information from PDF convocatoria documents."""

    def extract_text(self, pdf_path: str) -> str:
        """Extract all text from a PDF file."""
        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed. Run: pip3 install pdfplumber")
            return ""

        try:
            with pdfplumber.open(pdf_path) as pdf:
                texts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        texts.append(page_text)
                return "\n".join(texts)
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""

    def extract_opportunity_data(self, pdf_path: str) -> Dict[str, Optional[str]]:
        """
        High-level extraction from a PDF.
        Returns dict with keys: fecha_apertura, fecha_cierre, monto,
        requisitos, documentos.
        """
        text = self.extract_text(pdf_path)
        if not text:
            return {
                "fecha_apertura": None,
                "fecha_cierre": None,
                "monto": "",
                "requisitos": "",
                "documentos": "",
            }

        return {
            "fecha_apertura": find_opening_date(text),
            "fecha_cierre": find_deadline(text),
            "monto": extract_amount(text),
            "requisitos": extract_requirements(text),
            "documentos": extract_documents(text),
        }
