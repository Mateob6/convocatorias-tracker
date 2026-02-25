"""Envio de email con reporte de convocatorias."""

import logging
import smtplib
from datetime import date
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List

from src.models import Oportunidad

logger = logging.getLogger(__name__)


class EmailSender:
    """Sends email reports with the Excel tracker attached."""

    def __init__(self, smtp_server: str, smtp_port: int, sender: str,
                 password: str, recipient: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender = sender
        self.password = password
        self.recipient = recipient

    def _build_html_summary(self, new_ops: List[Oportunidad],
                             all_ops: List[Oportunidad]) -> str:
        """Build HTML email body with summary of findings."""
        today = date.today().strftime("%d/%m/%Y")

        # Count stats
        total = len(all_ops)
        nuevas = len(new_ops)
        alta_count = sum(1 for op in all_ops if op.relevancia == "Alta")
        vencidas = sum(1 for op in all_ops if op.estado == "Vencida")
        activas = total - vencidas

        # Upcoming deadlines (next 15 days)
        upcoming = []
        for op in all_ops:
            if op.fecha_cierre and op.estado not in ("Vencida", "Aplicada"):
                days_left = (op.fecha_cierre - date.today()).days
                if 0 <= days_left <= 15:
                    upcoming.append((op, days_left))
        upcoming.sort(key=lambda x: x[1])

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; }}
                h1 {{ color: #2F5496; font-size: 22px; }}
                h2 {{ color: #2F5496; font-size: 16px; margin-top: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th {{ background-color: #2F5496; color: white; padding: 8px 12px;
                      text-align: left; font-size: 13px; }}
                td {{ border: 1px solid #ddd; padding: 6px 12px; font-size: 13px; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .stat {{ display: inline-block; margin: 5px 15px 5px 0;
                         padding: 8px 15px; border-radius: 5px; font-weight: bold; }}
                .stat-total {{ background: #E8EEF7; color: #2F5496; }}
                .stat-new {{ background: #C6EFCE; color: #006100; }}
                .stat-alta {{ background: #BDD7EE; color: #1F4E79; }}
                .urgent {{ background: #FFEB9C; color: #9C5700; padding: 2px 6px;
                           border-radius: 3px; font-weight: bold; }}
                .footer {{ margin-top: 20px; font-size: 11px; color: #999;
                           border-top: 1px solid #ddd; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <h1>Reporte de Convocatorias Academicas - {today}</h1>

            <div>
                <span class="stat stat-total">Total: {total}</span>
                <span class="stat stat-new">Nuevas: {nuevas}</span>
                <span class="stat stat-alta">Alta relevancia: {alta_count}</span>
                <span class="stat" style="background:#FFC7CE;color:#9C0006;">
                    Activas: {activas}
                </span>
            </div>
        """

        # Urgent deadlines section
        if upcoming:
            html += """
            <h2>Fechas proximas a vencer</h2>
            <table>
                <tr><th>Convocatoria</th><th>Entidad</th><th>Cierre</th>
                    <th>Dias restantes</th></tr>
            """
            for op, days in upcoming:
                cierre_str = op.fecha_cierre.strftime("%d/%m/%Y")
                urgency = f'<span class="urgent">{days} dias</span>'
                html += f"""
                <tr>
                    <td>{op.nombre}</td>
                    <td>{op.entidad}</td>
                    <td>{cierre_str}</td>
                    <td>{urgency}</td>
                </tr>
                """
            html += "</table>"

        # New opportunities section
        if new_ops:
            html += """
            <h2>Nuevas convocatorias encontradas</h2>
            <table>
                <tr><th>Nombre</th><th>Entidad</th><th>Tipo</th>
                    <th>Relevancia</th><th>Cierre</th></tr>
            """
            for op in new_ops:
                cierre = op.fecha_cierre.strftime("%d/%m/%Y") if op.fecha_cierre else "Por definir"
                html += f"""
                <tr>
                    <td>{op.nombre}</td>
                    <td>{op.entidad}</td>
                    <td>{op.tipo}</td>
                    <td>{op.relevancia}</td>
                    <td>{cierre}</td>
                </tr>
                """
            html += "</table>"
        else:
            html += "<p>No se encontraron convocatorias nuevas en esta busqueda.</p>"

        html += """
            <div class="footer">
                Este correo fue generado automaticamente por el sistema de
                rastreo de convocatorias. El archivo Excel adjunto contiene
                el detalle completo.
            </div>
        </body>
        </html>
        """
        return html

    def send_report(self, excel_path: str, new_ops: List[Oportunidad],
                    all_ops: List[Oportunidad]) -> bool:
        """
        Send email with Excel attached and HTML summary.
        Returns True if sent successfully.
        """
        if not self.sender or not self.password:
            logger.warning(
                "Email not configured. Set SMTP_USER and SMTP_PASSWORD "
                "environment variables."
            )
            return False

        try:
            msg = MIMEMultipart("mixed")
            msg["From"] = self.sender
            msg["To"] = self.recipient
            msg["Subject"] = (
                f"Reporte Convocatorias Academicas - "
                f"{date.today().strftime('%d/%m/%Y')} "
                f"({len(new_ops)} nuevas)"
            )

            # HTML body
            html = self._build_html_summary(new_ops, all_ops)
            msg.attach(MIMEText(html, "html"))

            # Excel attachment
            excel_file = Path(excel_path)
            if excel_file.exists():
                with open(excel_file, "rb") as f:
                    attachment = MIMEApplication(f.read(), Name=excel_file.name)
                    attachment["Content-Disposition"] = (
                        f'attachment; filename="{excel_file.name}"'
                    )
                    msg.attach(attachment)

            # Send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.sender, self.password)
                server.send_message(msg)

            logger.info(f"Email sent to {self.recipient}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(
                "SMTP authentication failed. Verify SMTP_USER and SMTP_PASSWORD. "
                "For Gmail, use an App Password: "
                "https://myaccount.google.com/apppasswords"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
