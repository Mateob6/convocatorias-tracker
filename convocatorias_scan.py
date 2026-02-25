#!/usr/bin/env python3
"""
Sistema de Rastreo de Convocatorias Academicas
Busca becas, movilidades, convocatorias y concursos en portales web,
los consolida en un Excel y envia un reporte por correo.

Uso:
    python3 convocatorias_scan.py                    # Ejecucion completa
    python3 convocatorias_scan.py --web-only         # Solo scraping web
    python3 convocatorias_scan.py --update-only      # Solo actualizar Excel existente
    python3 convocatorias_scan.py --no-email         # No enviar correo
"""

import argparse
import json
import logging
import sys
from datetime import date, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import CONFIG
from src.email_sender import EmailSender
from src.excel_manager import ExcelManager
from src.models import Oportunidad
from src.relevance_scorer import RelevanceScorer
from src.web_scraper import WebScraperOrchestrator


def setup_logging() -> logging.Logger:
    """Configure rotating file handler + console handler."""
    log_config = CONFIG["logging"]
    log_path = Path(log_config["archivo"])
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_config["nivel"], logging.INFO))

    # File handler
    file_handler = RotatingFileHandler(
        str(log_path),
        maxBytes=log_config["max_bytes"],
        backupCount=log_config["backup_count"],
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                          datefmt="%H:%M:%S")
    )
    logger.addHandler(console_handler)

    return logger


def load_seed_data(path: str) -> list:
    """Load initial opportunities from seed_data.json."""
    seed_path = Path(path)
    if not seed_path.exists():
        return []

    try:
        with open(seed_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        opportunities = []
        for item in data:
            op = Oportunidad(
                nombre=item.get("nombre", ""),
                entidad=item.get("entidad", ""),
                tipo=item.get("tipo", "Otro"),
                fuente=item.get("fuente", ""),
                url=item.get("url", ""),
                monto=item.get("monto", ""),
                requisitos_clave=item.get("requisitos_clave", ""),
                documentos_necesarios=item.get("documentos_necesarios", ""),
                relevancia=item.get("relevancia", "Media"),
                estado=item.get("estado", "Nueva"),
                notas=item.get("notas", ""),
            )

            # Parse dates
            det = item.get("fecha_deteccion")
            if det:
                op.fecha_deteccion = datetime.strptime(det, "%Y-%m-%d").date()

            apertura = item.get("fecha_apertura")
            if apertura:
                op.fecha_apertura = datetime.strptime(apertura, "%Y-%m-%d").date()

            cierre = item.get("fecha_cierre")
            if cierre:
                op.fecha_cierre = datetime.strptime(cierre, "%Y-%m-%d").date()

            opportunities.append(op)

        return opportunities
    except Exception as e:
        logging.getLogger(__name__).error(f"Error loading seed data: {e}")
        return []


def print_summary(new_ops: list, all_ops: list):
    """Print a summary to the console."""
    print("\n" + "=" * 60)
    print(f"  RESUMEN DE ESCANEO - {date.today().strftime('%d/%m/%Y')}")
    print("=" * 60)
    print(f"  Convocatorias nuevas encontradas: {len(new_ops)}")
    print(f"  Total en el tracker:              {len(all_ops)}")

    # Count by relevancia
    alta = sum(1 for op in all_ops if op.relevancia == "Alta")
    media = sum(1 for op in all_ops if op.relevancia == "Media")
    baja = sum(1 for op in all_ops if op.relevancia == "Baja")
    print(f"\n  Relevancia: Alta={alta} | Media={media} | Baja={baja}")

    # Count by estado
    activas = sum(1 for op in all_ops if op.estado not in ("Vencida", "Descartada"))
    vencidas = sum(1 for op in all_ops if op.estado == "Vencida")
    print(f"  Estado: Activas={activas} | Vencidas={vencidas}")

    # Upcoming deadlines
    upcoming = []
    for op in all_ops:
        if op.fecha_cierre and op.estado not in ("Vencida", "Aplicada"):
            days = (op.fecha_cierre - date.today()).days
            if 0 <= days <= 15:
                upcoming.append((op, days))
    upcoming.sort(key=lambda x: x[1])

    if upcoming:
        print(f"\n  PROXIMAS A VENCER:")
        for op, days in upcoming:
            cierre = op.fecha_cierre.strftime("%d/%m/%Y")
            print(f"    [{days}d] {op.nombre[:50]} - Cierre: {cierre}")

    if new_ops:
        print(f"\n  NUEVAS CONVOCATORIAS:")
        for op in new_ops[:10]:
            print(f"    + [{op.relevancia}] {op.nombre[:55]} ({op.entidad})")
        if len(new_ops) > 10:
            print(f"    ... y {len(new_ops) - 10} mas")

    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Sistema de Rastreo de Convocatorias Academicas"
    )
    parser.add_argument(
        "--web-only", action="store_true",
        help="Solo ejecutar scraping web"
    )
    parser.add_argument(
        "--update-only", action="store_true",
        help="Solo actualizar estados y resumen del Excel existente"
    )
    parser.add_argument(
        "--no-email", action="store_true",
        help="No enviar correo electronico"
    )
    args = parser.parse_args()

    logger = setup_logging()
    logger.info(f"=== Scan started: {date.today()} ===")

    # Step 1: Open or create Excel
    excel = ExcelManager(CONFIG["excel"]["ruta"])
    excel.open_or_create()

    # Step 2: Seed data if Excel is brand new
    is_new_excel = excel.get_next_id() == 1
    if is_new_excel:
        seed = load_seed_data(CONFIG["rutas"]["seed_data"])
        if seed:
            added = excel.add_oportunidades(seed)
            logger.info(f"Seeded {added} initial opportunities")

    new_ops = []

    # Step 3: Web scraping
    if not args.update_only:
        try:
            scraper = WebScraperOrchestrator(CONFIG["portales"])
            web_ops = scraper.scrape_all()

            # Score relevance
            scorer = RelevanceScorer(CONFIG["perfil"])
            scored = scorer.score_all(web_ops)

            # Add to Excel (deduplication handled internally)
            added = excel.add_oportunidades(scored)
            new_ops = scored[:added] if added > 0 else []
            logger.info(f"Web: {len(web_ops)} found, {added} new added")
        except Exception as e:
            logger.error(f"Web scraping failed: {e}", exc_info=True)

    # Step 4: Update expired entries
    updated = excel.update_estados()

    # Step 5: Sort and format
    excel.sort_by_fecha_cierre()
    excel.apply_conditional_formatting()

    # Step 6: Update summary
    excel.update_summary_sheet()

    # Step 7: Save
    excel.save()

    # Get all ops for reporting
    all_ops = excel.get_all_oportunidades()

    # Step 8: Print console summary
    print_summary(new_ops, all_ops)

    # Step 9: Send email
    if not args.no_email:
        email_config = CONFIG["email"]
        sender = EmailSender(
            smtp_server=email_config["smtp_server"],
            smtp_port=email_config["smtp_port"],
            sender=email_config["sender"],
            password=email_config["password"],
            recipient=email_config["recipient"],
        )
        sender.send_report(CONFIG["excel"]["ruta"], new_ops, all_ops)

    logger.info(f"=== Scan complete: {date.today()} ===")


if __name__ == "__main__":
    main()
