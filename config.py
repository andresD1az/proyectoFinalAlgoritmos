# config.py — Configuración Global del Proyecto BVC Analytics
# Universidad del Quindío — Análisis de Algoritmos
#
# Este archivo centraliza TODOS los parámetros del sistema:
#   - Activos financieros a analizar (20 instrumentos)
#   - Parámetros de los algoritmos (ventanas, umbrales)
#   - Conexión a la base de datos PostgreSQL
#   - Configuración del servidor HTTP
#
# PRINCIPIO: Un solo lugar para cambiar cualquier parámetro.

import os
from datetime import datetime, timedelta

# PARÁMETROS TEMPORALES
# Horizonte de análisis: 5 años hacia atrás desde hoy.
# El enunciado exige "al menos cinco años" de datos históricos.
FECHA_FIN    = datetime.today()
FECHA_INICIO = FECHA_FIN - timedelta(days=5 * 365)   # ~1826 días

# Formato de fecha usado en todo el sistema (ISO 8601)
DATE_FORMAT = "%Y-%m-%d"

# PORTAFOLIO DE 25 ACTIVOS
#
# Composición:
#   - 2 acciones colombianas cotizadas en NYSE (ADRs): EC, CIB
#   - 1 ETF de Colombia: GXG
#   - 4 ETFs de Latinoamérica: ILF, EWZ, EWW, ECH
#   - 7 ETFs globales de referencia: SPY, QQQ, DIA, EEM, VT, IEMG, VEA
#   - 11 ETFs sectoriales y de commodities: GLD, SLV, USO, TLT, XLE, XLF, XLK, VNQ, XLV, XLI, XLP
#
# Todos cotizan en NYSE o NASDAQ y tienen datos disponibles en Yahoo Finance.
ACTIVOS = [
    # ── BVC / Colombia ADRs (cotizados en NYSE) ──────────────────
    # EC: Ecopetrol es la principal empresa petrolera de Colombia.
    #     Su ADR cotiza en NYSE bajo el símbolo EC.
    {"ticker": "EC",   "nombre": "Ecopetrol S.A.",          "tipo": "accion", "mercado": "NYSE"},

    # CIB: Bancolombia es el banco más grande de Colombia.
    #      Su ADR cotiza en NYSE bajo el símbolo CIB.
    {"ticker": "CIB",  "nombre": "Bancolombia S.A.",         "tipo": "accion", "mercado": "NYSE"},

    # GXG: ETF que replica el índice MSCI Colombia.
    #      Incluye las principales empresas colombianas.
    {"ticker": "GXG",  "nombre": "iShares MSCI Colombia",    "tipo": "etf",    "mercado": "NYSE"},

    # ── ETFs Latinoamérica ────────────────────────────────────────
    # ILF: Replica el índice S&P Latin America 40 (40 mayores empresas de LATAM).
    {"ticker": "ILF",  "nombre": "iShares Latin America 40", "tipo": "etf",    "mercado": "NYSE"},

    # EWZ: Replica el índice MSCI Brazil. Brasil es el mayor mercado de LATAM.
    {"ticker": "EWZ",  "nombre": "iShares MSCI Brazil",      "tipo": "etf",    "mercado": "NYSE"},

    # EWW: Replica el índice MSCI Mexico. México es el segundo mercado de LATAM.
    {"ticker": "EWW",  "nombre": "iShares MSCI Mexico",      "tipo": "etf",    "mercado": "NYSE"},

    # ECH: Replica el índice MSCI Chile. Chile es un mercado desarrollado de LATAM.
    {"ticker": "ECH",  "nombre": "iShares MSCI Chile",       "tipo": "etf",    "mercado": "NYSE"},

    # ── ETFs Globales de Referencia ───────────────────────────────
    # SPY: El ETF más negociado del mundo. Replica el S&P 500 (500 mayores empresas de EE.UU.).
    {"ticker": "SPY",  "nombre": "S&P 500 ETF",              "tipo": "etf",    "mercado": "NYSE"},

    # QQQ: Replica el Nasdaq 100 (100 mayores empresas tecnológicas de EE.UU.).
    {"ticker": "QQQ",  "nombre": "Nasdaq 100 ETF",           "tipo": "etf",    "mercado": "NASDAQ"},

    # DIA: Replica el Dow Jones Industrial Average (30 empresas industriales de EE.UU.).
    {"ticker": "DIA",  "nombre": "Dow Jones ETF",            "tipo": "etf",    "mercado": "NYSE"},

    # EEM: Replica el índice MSCI Emerging Markets (mercados emergentes globales).
    {"ticker": "EEM",  "nombre": "Emerging Markets ETF",     "tipo": "etf",    "mercado": "NYSE"},

    # VT: Replica el índice FTSE Global All Cap (mercado accionario mundial completo).
    {"ticker": "VT",   "nombre": "Vanguard Total World",     "tipo": "etf",    "mercado": "NYSE"},

    # IEMG: Versión de bajo costo del EEM. Mercados emergentes con más cobertura.
    {"ticker": "IEMG", "nombre": "Core Emerging Markets",    "tipo": "etf",    "mercado": "NYSE"},

    # VEA: Replica el índice FTSE Developed Markets (mercados desarrollados ex-US).
    {"ticker": "VEA",  "nombre": "Vanguard Developed Markets", "tipo": "etf",  "mercado": "NYSE"},

    # ── Sectores y Commodities ────────────────────────────────────
    # GLD: Replica el precio del oro físico. Activo refugio en crisis.
    {"ticker": "GLD",  "nombre": "SPDR Gold Shares",         "tipo": "etf",    "mercado": "NYSE"},

    # SLV: Replica el precio de la plata física.
    {"ticker": "SLV",  "nombre": "iShares Silver Trust",     "tipo": "etf",    "mercado": "NYSE"},

    # USO: Replica el precio del petróleo crudo WTI (West Texas Intermediate).
    #      Relevante para Colombia por su economía petrolera.
    {"ticker": "USO",  "nombre": "US Oil Fund",              "tipo": "etf",    "mercado": "NYSE"},

    # TLT: Replica bonos del Tesoro de EE.UU. a 20+ años. Activo de renta fija.
    {"ticker": "TLT",  "nombre": "iShares 20Y Treasury",     "tipo": "etf",    "mercado": "NASDAQ"},

    # XLE: Sector energético del S&P 500 (Exxon, Chevron, etc.).
    {"ticker": "XLE",  "nombre": "Energy Select Sector",     "tipo": "etf",    "mercado": "NYSE"},

    # XLF: Sector financiero del S&P 500 (JPMorgan, Bank of America, etc.).
    {"ticker": "XLF",  "nombre": "Financial Select Sector",  "tipo": "etf",    "mercado": "NYSE"},

    # XLK: Sector tecnológico del S&P 500 (Apple, Microsoft, Nvidia, etc.).
    {"ticker": "XLK",  "nombre": "Technology Select Sector", "tipo": "etf",    "mercado": "NYSE"},

    # VNQ: Sector inmobiliario (REITs). Replica el índice MSCI US REIT.
    {"ticker": "VNQ",  "nombre": "Vanguard Real Estate",     "tipo": "etf",    "mercado": "NYSE"},

    # XLV: Sector salud del S&P 500 (Johnson & Johnson, Pfizer, UnitedHealth, etc.).
    {"ticker": "XLV",  "nombre": "Health Care Select Sector", "tipo": "etf",   "mercado": "NYSE"},

    # XLI: Sector industrial del S&P 500 (Boeing, Caterpillar, 3M, etc.).
    {"ticker": "XLI",  "nombre": "Industrial Select Sector", "tipo": "etf",    "mercado": "NYSE"},

    # XLP: Sector consumo básico del S&P 500 (Procter & Gamble, Coca-Cola, Walmart, etc.).
    {"ticker": "XLP",  "nombre": "Consumer Staples Sector",  "tipo": "etf",    "mercado": "NYSE"},
]

# Lista plana de tickers para iterar fácilmente
TICKERS = [a["ticker"] for a in ACTIVOS]

# PARÁMETROS ALGORÍTMICOS
#
# Estos valores controlan el comportamiento de los algoritmos.
# Se pueden modificar para experimentar con diferentes configuraciones.

# Tamaño de la ventana deslizante para detección de patrones (Req 3).
# Con 20 días se capturan tendencias de ~1 mes bursátil.
VENTANA_DESLIZANTE_DIAS = 20

# Ventana para el cálculo de volatilidad histórica (Req 3).
# 30 días = ~1.5 meses bursátiles. Captura volatilidad reciente.
DIAS_VOLATILIDAD = 30

# Umbral mínimo de similitud para reportar un par como "similar" (Req 2).
# Solo se reportan pares con similitud >= 0.75 (75%).
MIN_SIMILITUD_THRESHOLD = 0.75

# CONFIGURACIÓN DE BASE DE DATOS
#
# Estrategia de configuración (en orden de prioridad):
#   1. Si existe DATABASE_URL (formato de Render/Heroku), se parsea manualmente.
#   2. Si no, se usan las variables individuales DB_HOST, DB_PORT, etc.
#   3. Si no hay variables de entorno, se usan los valores por defecto
#      que corresponden al contenedor Docker local (bvc_db).
#
# Para desarrollo local: editar el archivo .env
# Para producción (Render): DATABASE_URL se inyecta automáticamente
_DATABASE_URL = os.getenv("DATABASE_URL", "")

if _DATABASE_URL:
    # Parsear DATABASE_URL manualmente sin dependencias externas.
    # Formato estándar: postgresql://usuario:contraseña@host:puerto/nombre_bd
    # Ejemplo: postgresql://bvc_user:abc123@dpg-xxx.render.com:5432/bvc_analytics
    import re as _re
    _m = _re.match(
        r"postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)",
        _DATABASE_URL
    )
    if _m:
        DB_CONFIG = {
            "host":     _m.group(3),   # hostname del servidor PostgreSQL
            "port":     int(_m.group(4)),  # puerto (normalmente 5432)
            "dbname":   _m.group(5),   # nombre de la base de datos
            "user":     _m.group(1),   # usuario de PostgreSQL
            "password": _m.group(2),   # contraseña
        }
    else:
        raise ValueError(
            f"DATABASE_URL con formato inesperado: {_DATABASE_URL}\n"
            f"Formato esperado: postgresql://usuario:contraseña@host:puerto/bd"
        )
else:
    # Variables individuales (desarrollo local o Docker Compose)
    DB_CONFIG = {
        "host":     os.getenv("DB_HOST",     "bvc_db"),      # nombre del servicio en Docker
        "port":     int(os.getenv("DB_PORT", "5432")),        # puerto PostgreSQL estándar
        "dbname":   os.getenv("DB_NAME",     "bvc_analytics"),
        "user":     os.getenv("DB_USER",     "bvc_user"),
        "password": os.getenv("DB_PASSWORD", "changeme"),
    }

# CONFIGURACIÓN DEL SERVIDOR HTTP
#
# API_HOST: "0.0.0.0" significa "escuchar en todas las interfaces de red".
#           Necesario para que Docker y Render puedan acceder al servidor.
#
# API_PORT: Render asigna el puerto dinámicamente via la variable $PORT.
#           Se lee $PORT primero, luego API_PORT, y por defecto 8001.
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8001")))
