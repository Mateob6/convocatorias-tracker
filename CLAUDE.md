# Sistema de Rastreo de Convocatorias Academicas

Sistema automatizado que busca mensualmente becas, movilidades, convocatorias y concursos en portales web, los consolida en un Excel actualizable, y envia un reporte por correo electronico.

## Perfil del candidato

- **Nombre:** Mateo Belalcazar
- **Nivel:** Doctorado en Psicologia
- **Universidad:** Universidad del Valle (CIDEAS - Cognicion cientifica y matematica)
- **Pregrado:** Estadistica, Filosofia
- **Areas:** psicologia computacional, psicometria, filosofia de la ciencia, ciencias cognitivas

## Estructura del proyecto

```
convocatorias_scan.py          # Punto de entrada principal (CLI)
config.py                      # Configuracion centralizada
requirements.txt               # Dependencias pip
src/
  models.py                    # Dataclass Oportunidad (15 campos)
  excel_manager.py             # CRUD Excel + hoja Resumen
  web_scraper.py               # Orquestador de scraping
  pdf_parser.py                # Extraccion de fechas/montos de texto y PDFs
  relevance_scorer.py          # Puntuacion por perfil academico
  email_sender.py              # Envio de email con Excel adjunto
  portal_scrapers/
    base.py                    # BasePortalScraper + GenericScraper (fallback)
    minciencias.py
    icetex.py
    fulbright.py
    univalle.py                # DGP, Extension, Investigaciones
data/
  convocatorias.xlsx           # Excel de salida (generado)
  seed_data.json               # Oportunidades iniciales
logs/
  scanner.log                  # Log rotativo
com.convocatorias.scanner.plist  # launchd para automatizacion mensual
```

## Uso

```bash
pip3 install -r requirements.txt

# Ejecucion completa (scraping + Excel + email)
python3 convocatorias_scan.py

# Solo scraping web, sin email
python3 convocatorias_scan.py --no-email

# Solo actualizar Excel existente (estados, formato, resumen)
python3 convocatorias_scan.py --update-only

# Solo scraping web
python3 convocatorias_scan.py --web-only
```

## Automatizacion

Configurado con launchd para ejecutarse el 1ro de cada mes a las 10:00 AM:

```bash
# Activar
cp com.convocatorias.scanner.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.convocatorias.scanner.plist

# Desactivar
launchctl unload ~/Library/LaunchAgents/com.convocatorias.scanner.plist
```

## Portales monitoreados

ICETEX, Minciencias, Fulbright Colombia, DAAD, Erasmus Mundus, OEA, Fundacion Carolina, CLACSO, La Rabida, Univalle (DGP, Extension, Investigaciones), ICFES.

## Configuracion de email

Requiere variables de entorno `SMTP_USER` y `SMTP_PASSWORD` (Gmail App Password). El reporte se envia a mateo.belalcazar@correounivalle.edu.co.

## Arquitectura

- **Deduplicacion:** por nombre+entidad, evita duplicados entre ejecuciones mensuales
- **Relevancia automatica:** Alta/Media/Baja segun match con perfil academico
- **Estados:** Nueva, Vencida, Aplicada, En proceso, Descartada (auto-expiracion por fecha)
- **Scraping:** abstract base + GenericScraper fallback, falla un portal y sigue con el resto
- **Excel:** formato condicional (rojo=vencida, verde=alta, amarillo=urgente <15 dias)

## Pendiente

- Integracion con Gmail API para buscar convocatorias en correos
- Mejorar scrapers especificos para portales que cambian estructura
