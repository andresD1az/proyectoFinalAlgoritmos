# =============================================================
# config.py — Configuración Global del Proyecto
# Plataforma de Análisis BVC & ETFs Globales
# =============================================================

import os
from datetime import datetime, timedelta

# ------------------------------------------------------------------
# PARÁMETROS TEMPORALES
# ------------------------------------------------------------------
FECHA_FIN   = datetime.today()
FECHA_INICIO = FECHA_FIN - timedelta(days=5 * 365)   # 5 años atrás

DATE_FORMAT = "%Y-%m-%d"

# ------------------------------------------------------------------
# ACTIVOS A ANALIZAR (20 activos: BVC/ADRs colombianos + ETFs globales)
# ------------------------------------------------------------------
ACTIVOS = [
    # --- BVC / Colombia ADRs (cotizados en NYSE) ---
    {"ticker": "EC",   "nombre": "Ecopetrol S.A.",         "tipo": "accion",  "mercado": "NYSE"},
    {"ticker": "CIB",  "nombre": "Bancolombia S.A.",        "tipo": "accion",  "mercado": "NYSE"},
    {"ticker": "GXG",  "nombre": "iShares MSCI Colombia",   "tipo": "etf",     "mercado": "NYSE"},

    # --- ETFs Latinoamérica ---
    {"ticker": "ILF",  "nombre": "iShares Latin America 40","tipo": "etf",     "mercado": "NYSE"},
    {"ticker": "EWZ",  "nombre": "iShares MSCI Brazil",     "tipo": "etf",     "mercado": "NYSE"},
    {"ticker": "EWW",  "nombre": "iShares MSCI Mexico",     "tipo": "etf",     "mercado": "NYSE"},

    # --- ETFs Globales de Referencia ---
    {"ticker": "SPY",  "nombre": "S&P 500 ETF",             "tipo": "etf",     "mercado": "NYSE"},
    {"ticker": "QQQ",  "nombre": "Nasdaq 100 ETF",          "tipo": "etf",     "mercado": "NASDAQ"},
    {"ticker": "DIA",  "nombre": "Dow Jones ETF",           "tipo": "etf",     "mercado": "NYSE"},
    {"ticker": "EEM",  "nombre": "Emerging Markets ETF",    "tipo": "etf",     "mercado": "NYSE"},
    {"ticker": "VT",   "nombre": "Vanguard Total World",    "tipo": "etf",     "mercado": "NYSE"},
    {"ticker": "IEMG", "nombre": "Core Emerging Markets",   "tipo": "etf",     "mercado": "NYSE"},

    # --- Sectores y Commodities ---
    {"ticker": "GLD",  "nombre": "SPDR Gold Shares",        "tipo": "etf",     "mercado": "NYSE"},
    {"ticker": "SLV",  "nombre": "iShares Silver Trust",    "tipo": "etf",     "mercado": "NYSE"},
    {"ticker": "USO",  "nombre": "US Oil Fund",             "tipo": "etf",     "mercado": "NYSE"},
    {"ticker": "TLT",  "nombre": "iShares 20Y Treasury",    "tipo": "etf",     "mercado": "NASDAQ"},
    {"ticker": "XLE",  "nombre": "Energy Select Sector",    "tipo": "etf",     "mercado": "NYSE"},
    {"ticker": "XLF",  "nombre": "Financial Select Sector", "tipo": "etf",     "mercado": "NYSE"},
    {"ticker": "XLK",  "nombre": "Technology Select Sector","tipo": "etf",     "mercado": "NYSE"},
    {"ticker": "VNQ",  "nombre": "Vanguard Real Estate",    "tipo": "etf",     "mercado": "NYSE"},
]

TICKERS = [a["ticker"] for a in ACTIVOS]

# ------------------------------------------------------------------
# PARÁMETROS ALGORÍTMICOS (modificables para experimentación)
# ------------------------------------------------------------------
VENTANA_DESLIZANTE_DIAS  = 20    # Tamaño de ventana para patrones
DIAS_VOLATILIDAD         = 30    # Ventana para cálculo de volatilidad
MIN_SIMILITUD_THRESHOLD  = 0.75  # Umbral mínimo para reportar similitud

# ------------------------------------------------------------------
# BASE DE DATOS (leídos desde variables de entorno con fallback local)
# ------------------------------------------------------------------
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "bvc_db"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "bvc_analytics"),
    "user":     os.getenv("DB_USER",     "bvc_user"),
    "password": os.getenv("DB_PASSWORD", "changeme"),
}

# ------------------------------------------------------------------
# API
# ------------------------------------------------------------------
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8001"))
