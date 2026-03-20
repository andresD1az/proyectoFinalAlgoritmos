"""
etl/downloader.py — Descarga HTTP pura de datos financieros
Fuente: Yahoo Finance (query1.finance.yahoo.com) via urllib (stdlib)
SIN yfinance, SIN pandas_datareader, SIN requests
"""

import urllib.request
import urllib.parse
import json
import time
from datetime import datetime
from config import ACTIVOS, FECHA_INICIO, FECHA_FIN, DATE_FORMAT


# ------------------------------------------------------------------
# URL base de Yahoo Finance (API v8 - JSON crudo)
# ------------------------------------------------------------------
_YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _timestamp(fecha: datetime) -> int:
    """Convierte un datetime a Unix timestamp (segundos)."""
    return int(fecha.timestamp())


def descargar_ticker(ticker: str) -> list[dict] | None:
    """
    Descarga datos OHLCV históricos de Yahoo Finance para un ticker dado.
    """
    params = urllib.parse.urlencode({
        "period1":  _timestamp(FECHA_INICIO),
        "period2":  _timestamp(FECHA_FIN),
        "interval": "1d",
        "events":   "history",
    })
    url = _YAHOO_BASE.format(ticker=ticker) + "?" + params

    req = urllib.request.Request(url, headers=_HEADERS)
    
    intentos = 3
    for intento in range(intentos):
        try:
            # Aumentamos timeout a 30s
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            break # Éxito
        except Exception as e:
            if intento == intentos - 1:
                print(f"[DOWNLOAD] Error descargando {ticker} (intento {intento+1}): {e}")
                return None
            time.sleep(1) # Pausa antes de reintentar

    try:
        result   = raw["chart"]["result"][0]
        meta     = result["meta"]
        tss      = result["timestamp"]                      # Lista de Unix timestamps
        indicadores = result["indicators"]["quote"][0]      # OHLCV

        filas = []
        for i, ts in enumerate(tss):
            fecha_str = datetime.utcfromtimestamp(ts).strftime(DATE_FORMAT)
            cierre = indicadores["close"][i]
            if cierre is None:           # Día sin negociación, se limpia en cleaner.py
                continue
            filas.append({
                "fecha":    fecha_str,
                "apertura": indicadores["open"][i],
                "maximo":   indicadores["high"][i],
                "minimo":   indicadores["low"][i],
                "cierre":   cierre,
                "volumen":  indicadores["volume"][i],
            })

        print(f"[DOWNLOAD] {ticker}: {len(filas)} días descargados.")
        return filas

    except (KeyError, IndexError, TypeError) as e:
        print(f"[DOWNLOAD] Error parseando respuesta de {ticker}: {e}")
        return None


def descargar_todos(pausa_segundos: float = 1.0) -> dict[str, list[dict]]:
    """
    Descarga los 20 activos configurados en config.py secuencialmente.
    `pausa_segundos`: tiempo de espera entre peticiones para no ser bloqueado.

    Retorna un dict {ticker: [filas]} solo con los activos exitosos.
    """
    resultados = {}
    total = len(ACTIVOS)

    for i, activo in enumerate(ACTIVOS, 1):
        ticker = activo["ticker"]
        print(f"[DOWNLOAD] ({i}/{total}) Descargando {ticker} ...")
        filas = descargar_ticker(ticker)
        if filas:
            resultados[ticker] = filas
        time.sleep(pausa_segundos)   # Pausa cortés entre peticiones

    print(f"\n[DOWNLOAD] Completado: {len(resultados)}/{total} activos descargados.")
    return resultados
