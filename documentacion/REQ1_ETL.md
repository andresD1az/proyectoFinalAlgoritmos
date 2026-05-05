# Requerimiento 1 — ETL: Extracción, Transformación y Carga

## Enunciado

> Se deberá implementar un proceso completamente automatizado de extracción, transformación y carga (ETL) de datos financieros. El sistema deberá descargar información histórica diaria de al menos cinco años para un portafolio compuesto por mínimo veinte activos.

---

## Archivos Involucrados

| Archivo | Función |
|---|---|
| `config.py` | Define los 25 activos, fechas y parámetros |
| `etl/descargador.py` | Descarga HTTP desde Yahoo Finance |
| `etl/limpieza.py` | Interpolación lineal + Z-Score + validación |
| `etl/database.py` | CRUD PostgreSQL con psycopg2 |
| `basedatos/init.sql` | Schema de la base de datos |
| `main.py → pipeline_etl()` | Orquestador del proceso completo |

---

## Portafolio de 25 Activos

| Ticker | Nombre | Tipo | Mercado |
|---|---|---|---|
| EC | Ecopetrol S.A. | Acción | NYSE |
| CIB | Bancolombia S.A. | Acción | NYSE |
| GXG | iShares MSCI Colombia | ETF | NYSE |
| ILF | iShares Latin America 40 | ETF | NYSE |
| EWZ | iShares MSCI Brazil | ETF | NYSE |
| EWW | iShares MSCI Mexico | ETF | NYSE |
| SPY | S&P 500 ETF | ETF | NYSE |
| QQQ | Nasdaq 100 ETF | ETF | NASDAQ |
| DIA | Dow Jones ETF | ETF | NYSE |
| EEM | Emerging Markets ETF | ETF | NYSE |
| VT | Vanguard Total World | ETF | NYSE |
| IEMG | Core Emerging Markets | ETF | NYSE |
| GLD | SPDR Gold Shares | ETF | NYSE |
| SLV | iShares Silver Trust | ETF | NYSE |
| USO | US Oil Fund | ETF | NYSE |
| TLT | iShares 20Y Treasury | ETF | NASDAQ |
| XLE | Energy Select Sector | ETF | NYSE |
| XLF | Financial Select Sector | ETF | NYSE |
| XLK | Technology Select Sector | ETF | NYSE |
| VNQ | Vanguard Real Estate | ETF | NYSE |

---

## Descarga de Datos (`etl/descargador.py`)

### Fuente

Yahoo Finance API v8 (pública, sin autenticación):
```
https://query1.finance.yahoo.com/v8/finance/chart/{ticker}
```

### Parámetros de la Petición

| Parámetro | Valor | Descripción |
|---|---|---|
| `period1` | Unix timestamp inicio | 5 años atrás |
| `period2` | Unix timestamp fin | Hoy |
| `interval` | `1d` | Frecuencia diaria |
| `events` | `history` | Solo precios históricos |

### Proceso de Descarga

```
1. Construir URL con urllib.parse.urlencode()
2. Crear Request con User-Agent (evita error 429)
3. Ejecutar urllib.request.urlopen() con timeout=30s
4. Parsear respuesta JSON con json.loads()
5. Convertir timestamps Unix con datetime.utcfromtimestamp()
6. Construir lista de dicts OHLCV
```

### Manejo de Errores

- Hasta 3 reintentos ante errores de red
- Pausa de 1 segundo entre reintentos
- Pausa de 1 segundo entre activos (scraping ético)
- Retorna `None` si todos los intentos fallan

### Estructura de Respuesta JSON

```json
{
  "chart": {
    "result": [{
      "timestamp": [1609459200, ...],
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
```

### Restricciones Cumplidas

- Sin `yfinance`, `pandas_datareader` ni equivalentes
- URL construida manualmente
- JSON parseado manualmente
- Timestamps convertidos manualmente

---

## Limpieza de Datos (`etl/limpieza.py`)

### Algoritmo 1: Interpolación Lineal — O(n)

**Propósito:** Rellenar valores `None` en series de tiempo.

**Fórmula:**
```
Para cada bloque de Nones entre posiciones izq y der:
    V[k] = V[izq] + (V[der] - V[izq]) × (k - izq) / (der - izq)
```

**Casos especiales:**
- Nones al inicio → backward fill (toma el primer valor conocido)
- Nones al final → forward fill (toma el último valor conocido)

**Justificación:** La interpolación lineal preserva la tendencia local de la serie. Es preferible a forward-fill porque no introduce sesgo hacia el pasado, y es apropiada para datos faltantes por diferencias de calendarios bursátiles.

**Impacto algorítmico:** Introduce un sesgo suave hacia la media entre los dos extremos conocidos. Aceptable para días festivos o desalineaciones temporales entre mercados.

### Algoritmo 2: Detección de Outliers (Z-Score) — O(n)

**Propósito:** Identificar valores estadísticamente anómalos.

**Fórmula:**
```
media    = Σ(vᵢ) / n
varianza = Σ(vᵢ - media)² / n
std      = √varianza
zᵢ       = (vᵢ - media) / std

Outlier si |zᵢ| > 3.5
```

**Umbral 3.5:** Más conservador que el estándar 3.0. En finanzas, los retornos tienen "colas pesadas" (fat tails): movimientos extremos legítimos son más frecuentes que en una distribución normal. Con 3.5 se evita eliminar crashes o rallies reales del mercado.

### Algoritmo 3: Validación de Registros

**Reglas:**
- Eliminar filas con `cierre <= 0` (físicamente imposible en acciones y ETFs)
- Rellenar `volumen = None` con `0` (volumen cero es válido en baja negociación)
- No interpolar volumen (es una cantidad discreta sin sentido de interpolación)

### Proceso de Limpieza Completo

```
1. Ordenar por fecha ASC (garantiza consistencia temporal)
2. Eliminar filas con cierre inválido (None, negativo o cero)
3. Interpolar columnas OHLC individualmente
4. Rellenar volumen nulo con 0
```

---

## Carga en Base de Datos (`etl/database.py`)

### Schema Principal

```sql
CREATE TABLE activos (
    id      SERIAL PRIMARY KEY,
    ticker  VARCHAR(10) UNIQUE NOT NULL,
    nombre  VARCHAR(100),
    tipo    VARCHAR(20),
    mercado VARCHAR(20)
);

CREATE TABLE precios (
    id        SERIAL PRIMARY KEY,
    activo_id INTEGER REFERENCES activos(id),
    fecha     DATE NOT NULL,
    apertura  NUMERIC(12,4),
    maximo    NUMERIC(12,4),
    minimo    NUMERIC(12,4),
    cierre    NUMERIC(12,4) NOT NULL,
    volumen   BIGINT,
    UNIQUE (activo_id, fecha)
);

CREATE INDEX idx_precios_activo_fecha ON precios(activo_id, fecha DESC);
```

### Idempotencia

Todas las inserciones usan `ON CONFLICT DO NOTHING`. El pipeline puede ejecutarse múltiples veces sin duplicar datos.

### Alineación de Series

La función `obtener_series_alineadas(tickers)` resuelve el problema de calendarios bursátiles distintos:

```
1. Obtener {ticker: {fecha: cierre}} para todos los tickers
2. Calcular intersección de fechas (días en que TODOS tienen dato)
3. Ordenar fechas ASC
4. Construir series alineadas de igual longitud
```

**Complejidad:** O(n·k) donde n = tickers, k = días comunes

**Resultado:** Todas las series tienen exactamente la misma longitud y cada posición i corresponde al mismo día calendario. Crítico para los algoritmos de similitud.

---

## Resultados

| Métrica | Valor |
|---|---|
| Activos descargados | 20/20 |
| Días por activo | ~1,255 |
| Días comunes (alineados) | ~1,272 |
| Total registros OHLCV | ~25,100 |
| Horizonte temporal | 5 años |

---

## Endpoint API

```
GET /activos              → Lista de 25 activos con días en BD
GET /precios?ticker=SPY   → Serie de precios de cierre
GET /precios/ohlcv?ticker=SPY&n=120 → Últimos 120 días OHLCV
GET /etl/status           → Cuántos registros hay en BD
POST /etl/iniciar         → Dispara el ETL en segundo plano
```
