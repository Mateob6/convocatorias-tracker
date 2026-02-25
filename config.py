"""Configuracion centralizada del sistema de rastreo de convocatorias."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

CONFIG = {
    "perfil": {
        "nombre": "Mateo Belalcazar",
        "nivel": "Doctorado",
        "programa": "Psicologia",
        "universidad": "Universidad del Valle",
        "grupo": "CIDEAS - Cognicion cientifica y matematica",
        "pregrado": ["Estadistica", "Filosofia"],
        "areas": [
            "psicologia computacional",
            "psicometria",
            "filosofia de la ciencia",
            "computational psychology",
            "psychometrics",
            "philosophy of science",
            "ciencias cognitivas",
            "cognitive science",
        ],
        "ubicacion": "Cali, Colombia",
        "pais": "Colombia",
    },

    "gmail": {
        "keywords": [
            "beca", "convocatoria", "movilidad", "scholarship",
            "pasantia", "estancia", "funding", "grant",
            "call for proposals", "research award",
        ],
        "max_results": 50,
        "days_lookback": 35,
    },

    "portales": [
        {
            "nombre": "ICETEX",
            "url": "https://web.icetex.gov.co/becas/becas-para-estudios-en-el-exterior",
            "activo": True,
        },
        {
            "nombre": "Minciencias",
            "url": "https://minciencias.gov.co/convocatorias",
            "activo": True,
        },
        {
            "nombre": "Fulbright Colombia",
            "url": "https://fulbright.edu.co/becas/",
            "activo": True,
        },
        {
            "nombre": "DAAD",
            "url": "https://www.daad.co/es/",
            "activo": True,
        },
        {
            "nombre": "Erasmus Mundus",
            "url": "https://www.eacea.ec.europa.eu/scholarships/emjmd-catalogue_en",
            "activo": True,
        },
        {
            "nombre": "OEA",
            "url": "https://www.oas.org/es/becas/",
            "activo": True,
        },
        {
            "nombre": "Fundacion Carolina",
            "url": "https://www.fundacioncarolina.es/convocatoria-de-becas/",
            "activo": True,
        },
        {
            "nombre": "CLACSO",
            "url": "https://www.clacso.org/becas/",
            "activo": True,
        },
        {
            "nombre": "La Rabida",
            "url": "https://grupolarabida.org/",
            "activo": True,
        },
        {
            "nombre": "Univalle - DGP",
            "url": "https://posgrados.univalle.edu.co/",
            "activo": True,
        },
        {
            "nombre": "Univalle - Extension",
            "url": "https://extension.univalle.edu.co/convocatorias-extension/convocatorias-2026/",
            "activo": True,
        },
        {
            "nombre": "Univalle - Investigaciones",
            "url": "https://investigaciones.univalle.edu.co/",
            "activo": True,
        },
        {
            "nombre": "ICFES",
            "url": "https://www.icfes.gov.co/",
            "activo": True,
        },
    ],

    "excel": {
        "ruta": str(PROJECT_ROOT / "data" / "convocatorias.xlsx"),
        "hoja_principal": "Convocatorias",
        "hoja_resumen": "Resumen",
    },

    "email": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "recipient": "mateo.belalcazar@correounivalle.edu.co",
    },

    "logging": {
        "nivel": "INFO",
        "archivo": str(PROJECT_ROOT / "logs" / "scanner.log"),
        "max_bytes": 5_242_880,
        "backup_count": 3,
    },

    "rutas": {
        "seed_data": str(PROJECT_ROOT / "data" / "seed_data.json"),
    },
}
