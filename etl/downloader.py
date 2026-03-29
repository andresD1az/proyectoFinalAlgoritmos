"""
etl/downloader.py — Descarga HTTP de datos financieros históricos
Universidad del Quindío — Análisis de Algoritmos — Requerimiento 1

PROPÓSITO:
    Implementa la descarga automática de datos OHLCV (Open, High, Low, Close, Volume)
    desde Yahoo Finance usando peticiones HTTP directas con urllib (stdlib de Python).

RESTRICCIONES DEL ENUNCIADO CUMPLIDAS:
    - NO usa yfinance, pandas_datareader ni ninguna librería de alto nivel.
    - Construye la URL manualmente con urllib.parse.urlencode().
    - Parsea la respuesta JSON manualmente con json.loads() de stdlib.
    - Implementa manejo de errores y reintentos explícitamente.
    - Convierte timestamps Unix a fechas manualmente con datetime.utcfromtimestamp().

FUENTE DE DATOS:
    Yahoo Finance API v8 (pública, sin autenticación requerida):
    https://query1.finance.yahoo.com/v8/finance/chart/{ticker}

    Parámetros de la petición:
        period1:  Unix timestamp de inicio (5 años atrás)
        period2:  Unix timestamp de fin (hoy)
        interval: "1d" = datos diarios
        events:   "history" = solo precios históricos (sin dividendos ni splits)

ESTRUCTURA DE LA RESPUESTA JSON:
    {
      "chart": {
        "result": [{
          "timestamp": [1609459200, 1609545600, ...],  <- Unix timestamps
          "indicators": {
            "quote": [{
              "open":   [123.45, ...],
              "high":   [125.00, ...],
              "low":    [122.00, ...],
              "close":  [124.50, ...],
              "volume": [1234567, ...]
            }]
          }
        }]
      }
    }
"""

import urllib.request
import urllib.parse
import json
import time
from datetime import datetime
from config import ACTIVOS, FECHA_INICIO, FECHA_FIN, DATE_FORMAT


# ------------------------------------------------------------------
# CONSTANTES DE CONFIGURACIÓN HTTP
# ------------------------------------------------------------------

# URL base de la API de Yahoo Finance (versión 8, retorna JSON crudo)
_YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

# Headers HTTP necesarios para que Yahoo Finance no rechace la petición.
# Sin User-Agent, Yahoo Finance devuelve error 429 (Too Many Requests).
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _timestamp(fecha: datetime) -> int:
    """
    Convierte un objeto datetime a Unix timestamp (segundos desde 1970-01-01).

    Yahoo Finance requiere las fechas en este formato para los parámetros
    period1 y period2 de la URL.

    Ejemplo:
        datetime(2020, 1, 1) → 1577836800

    Args:
        fecha: Objeto datetime a convertir

    Returns:
        Entero con el Unix timestamp
    """
    return int(fecha.timestamp())


def descargar_ticker(ticker: str) -> list[dict] | None:
    """
    Descarga los datos OHLCV históricos de un activo desde Yahoo Finance.

    PROCESO:
        1. Construir la URL con los parámetros de fecha y frecuencia
        2. Realizar la petición HTTP con urllib.request (hasta 3 intentos)
        3. Parsear la respuesta JSON manualmente
        4. Convertir cada timestamp Unix a fecha string 'YYYY-MM-DD'
        5. Construir y retornar la lista de registros OHLCV

    MANEJO DE ERRORES:
        - Reintenta hasta 3 veces ante errores de red (timeout, conexión)
        - Pausa 1 segundo entre reintentos para no saturar el servidor
        - Retorna None si todos los intentos fallan

    Args:
        ticker: Símbolo del activo (ej: "SPY", "EC", "GLD")

    Returns:
        Lista de dicts con keys: fecha, apertura, maximo, minimo, cierre, volumen
        None si la descarga falla completamente
    """
    # Construir parámetros de la URL
    params = urllib.parse.urlencode({
        "period1":  _timestamp(FECHA_INICIO),  # inicio del rango (Unix timestamp)
        "period2":  _timestamp(FECHA_FIN),     # fin del rango (Unix timestamp)
        "interval": "1d",                       # frecuencia diaria
        "events":   "history",                  # solo precios históricos
    })
    url = _YAHOO_BASE.format(ticker=ticker) + "?" + params

    # Crear objeto Request con headers personalizados
    req = urllib.request.Request(url, headers=_HEADERS)

    # Intentar la descarga hasta 3 veces
    intentos = 3
    for intento in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                # Leer y parsear la respuesta JSON
                raw = json.loads(resp.read().decode("utf-8"))
            break  # Éxito: salir del bucle de reintentos
        except Exception as e:
            if intento == intentos - 1:
                # Último intento fallido: reportar error y retornar None
                print(f"[DOWNLOAD] Error descargando {ticker} (intento {intento+1}/{intentos}): {e}")
                return None
            # Pausa antes de reintentar (evita bloqueo por rate limiting)
            time.sleep(1)

    # Parsear la estructura JSON de Yahoo Finance
    try:
        result      = raw["chart"]["result"][0]
        tss         = result["timestamp"]                    # lista de Unix timestamps
        indicadores = result["indicators"]["quote"][0]       # dict con listas OHLCV

        filas = []
        for i, ts in enumerate(tss):
            # Convertir Unix timestamp a fecha string 'YYYY-MM-DD'
            fecha_str = datetime.utcfromtimestamp(ts).strftime(DATE_FORMAT)

            cierre = indicadores["close"][i]
            if cierre is None:
                # Días sin negociación (festivos, fines de semana en algunos mercados)
                # Se omiten aquí; la interpolación lineal en cleaner.py los maneja
                continue

            filas.append({
                "fecha":    fecha_str,
                "apertura": indicadores["open"][i],    # precio de apertura
                "maximo":   indicadores["high"][i],    # precio máximo del día
                "minimo":   indicadores["low"][i],     # precio mínimo del día
                "cierre":   cierre,                    # precio de cierre (ajustado)
                "volumen":  indicadores["volume"][i],  # volumen de negociación
            })

        print(f"[DOWNLOAD] {ticker}: {len(filas)} días descargados.")
        return filas

    except (KeyError, IndexError, TypeError) as e:
        # Error al parsear la respuesta (estructura inesperada del JSON)
        print(f"[DOWNLOAD] Error parseando respuesta de {ticker}: {e}")
        return None


def descargar_todos(pausa_segundos: float = 1.0) -> dict[str, list[dict]]:
    """
    Descarga los datos históricos de los 20 activos definidos en config.py.

    ESTRATEGIA:
        Descarga secuencial (uno a uno) con pausa entre peticiones.
        Esto respeta las políticas de uso de Yahoo Finance y evita
        ser bloqueado por rate limiting.

        Una descarga paralela sería más rápida pero viola las buenas
        prácticas de scraping ético mencionadas en el enunciado.

    Args:
        pausa_segundos: Tiempo de espera entre peticiones (default: 1 segundo)

    Returns:
        Dict {ticker: [filas_ohlcv]} con los activos descargados exitosamente.
        Los activos que fallaron no aparecen en el resultado.
    """
    resultados = {}
    total = len(ACTIVOS)

    for i, activo in enumerate(ACTIVOS, 1):
        ticker = activo["ticker"]
        print(f"[DOWNLOAD] ({i}/{total}) Descargando {ticker} — {activo['nombre']} ...")
        filas = descargar_ticker(ticker)
        if filas:
            resultados[ticker] = filas
        # Pausa cortés entre peticiones (scraping ético)
        time.sleep(pausa_segundos)

    exitosos = len(resultados)
    fallidos  = total - exitosos
    print(f"\n[DOWNLOAD] Completado: {exitosos}/{total} activos descargados."
          f"{f' ({fallidos} fallaron)' if fallidos else ''}")
    return resultados
