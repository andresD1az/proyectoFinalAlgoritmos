# Arquitectura del Sistema — BVC Analytics

## Visión General

BVC Analytics es una aplicación web de análisis financiero cuantitativo construida sobre una arquitectura de capas. Cada capa tiene responsabilidades bien definidas y se comunica con las adyacentes a través de interfaces explícitas.

```
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                  │
│              interfaz/index.html (SPA vanilla)           │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/JSON
┌────────────────────────▼────────────────────────────────┐
│                      CAPA DE API                         │
│           api/server.py (http.server stdlib)             │
│                    20+ endpoints                         │
└──────┬──────────┬──────────┬──────────┬─────────────────┘
       │          │          │          │
┌──────▼──┐ ┌────▼────┐ ┌───▼────┐ ┌──▼──────────────────┐
│  ETL    │ │Similitud│ │Patrones│ │    Volatilidad        │
│ etl/    │ │algoritm.│ │algoritm│ │    algoritmos/        │
│         │ │similitud│ │patrones│ │    volatilidad.py     │
└──────┬──┘ └────┬────┘ └───┬────┘ └──┬──────────────────┘
       │         │           │         │
┌──────▼─────────▼───────────▼─────────▼──────────────────┐
│                   CAPA DE DATOS                           │
│              etl/database.py (psycopg2)                  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   POSTGRESQL 15                           │
│   activos | precios | resultados_similitud               │
│   resultados_volatilidad | resultados_sorting            │
│   resultados_patrones | top_volumen                      │
└─────────────────────────────────────────────────────────┘
```

---

## Flujo de Datos

```
Yahoo Finance API v8
        │
        │ urllib.request (HTTP directo)
        ▼
etl/descargador.py
  descargar_ticker()     → JSON crudo por activo
  descargar_todos()      → Dict {ticker: [filas_OHLCV]}
        │
        ▼
etl/limpieza.py
  limpiar_dataset()      → Ordena, elimina inválidos
  interpolar_linealmente() → Rellena Nones (O(n))
  detectar_outliers_zscore() → Marca anomalías (O(n))
        │
        ▼
etl/database.py
  insertar_activos()     → tabla activos (20 filas)
  insertar_precios_lote() → tabla precios (~25,200 filas)
        │
        ├──────────────────────────────────────────────────┐
        │                                                  │
        ▼                                                  ▼
algoritmos/similitud.py                    algoritmos/volatilidad.py
  obtener_series_alineadas()                 calcular_retornos_log()
  matriz_similitud()                         calcular_volatilidad()
  → 190 pares × 4 algoritmos                calcular_var_historico()
  → tabla resultados_similitud               calcular_sharpe()
                                             calcular_max_drawdown()
                                             → tabla resultados_volatilidad
        │
        ▼
algoritmos/patrones.py
  detectar_patrones()    → ventana deslizante
  detectar_picos_valles()
  detectar_cruces_medias()
  → tabla resultados_patrones

algoritmos/ordenamiento.py
  ejecutar_benchmark()   → 12 algoritmos × 5000 registros
  top15_mayor_volumen()
  → tablas resultados_sorting, top_volumen
        │
        ▼
api/server.py
  BVCHandler             → 20+ endpoints HTTP
  ThreadingHTTPServer    → Concurrencia por hilos
        │
        ▼
reportes/generador.py
  generar_reporte_json() → Agrega todas las secciones
  generar_reporte_html() → HTML para exportar a PDF
        │
        ▼
interfaz/index.html
  Dashboard SPA          → Gráficos SVG + Canvas
  Portafolio             → 20 gráficos individuales
  Comparar Activos       → 4 algoritmos de similitud
  Mapa de Calor          → Heatmap 20×20
  Patrones               → Ventana deslizante
  Clasificación Riesgo   → Ranking por volatilidad
  Velas OHLC             → Candlestick + SMA
  Reporte / PDF          → Exportación
```

---

## Módulos del Sistema

### config.py

Centraliza todos los parámetros del sistema. Ningún módulo tiene valores hardcodeados.

| Parámetro | Valor | Descripción |
|---|---|---|
| `ACTIVOS` | 20 instrumentos | Portafolio completo |
| `TICKERS` | Lista de 20 strings | Acceso rápido a símbolos |
| `FECHA_INICIO` | hoy − 1826 días | 5 años de historia |
| `FECHA_FIN` | hoy | Fecha de corte |
| `VENTANA_DESLIZANTE_DIAS` | 20 | Tamaño de ventana para patrones |
| `DIAS_VOLATILIDAD` | 30 | Ventana para volatilidad rodante |
| `MIN_SIMILITUD_THRESHOLD` | 0.75 | Umbral de reporte |
| `DB_CONFIG` | Dict psycopg2 | Conexión PostgreSQL |
| `API_HOST` | 0.0.0.0 | Escucha en todas las interfaces |
| `API_PORT` | 8001 | Puerto del servidor HTTP |

---

### etl/ — Extracción, Transformación y Carga

| Archivo | Responsabilidad |
|---|---|
| `descargador.py` | Descarga HTTP desde Yahoo Finance API v8 |
| `limpieza.py` | Interpolación lineal + Z-Score + validación |
| `database.py` | CRUD PostgreSQL con psycopg2 puro |

**Restricciones cumplidas:**
- Sin `yfinance`, `pandas_datareader` ni equivalentes
- URL construida manualmente con `urllib.parse.urlencode()`
- JSON parseado manualmente con `json.loads()`
- Timestamps Unix convertidos con `datetime.utcfromtimestamp()`

---

### algoritmos/ — Implementaciones Algorítmicas

| Archivo | Requerimiento | Algoritmos |
|---|---|---|
| `similitud.py` | Req 2 | Euclidiana, Pearson, Coseno, DTW |
| `patrones.py` | Req 3 | Ventana deslizante, Picos/Valles, SMA, Golden/Death Cross |
| `volatilidad.py` | Req 3 | Retornos log, Volatilidad, Drawdown, VaR, Sharpe |
| `ordenamiento.py` | Benchmark | 12 algoritmos de ordenamiento |

**Restricciones cumplidas:**
- Sin `numpy`, `scipy`, `sklearn`, `pandas`
- Cada algoritmo implementado con bucles y operaciones básicas de Python
- Fórmulas matemáticas documentadas en cada función
- Complejidades explícitas en docstrings

---

### api/server.py — Servidor HTTP

Implementado con `http.server.ThreadingHTTPServer` de la stdlib. Sin Flask, FastAPI ni ningún framework externo.

**Patrón de routing:**
```python
rutas = {
    "/activos":              self._activos,
    "/precios":              self._precios,
    "/similitud":            self._similitud,
    "/correlacion/matriz":   self._correlacion_matriz,
    "/patrones":             self._patrones,
    "/riesgo/clasificacion": self._clasificacion_riesgo,
    ...
}
handler = rutas.get(ruta)
if handler:
    handler(params)
```

**Concurrencia:** `ThreadingHTTPServer` crea un hilo por petición. Adecuado para carga académica.

---

### interfaz/index.html — Dashboard SPA

Aplicación de página única (SPA) implementada en HTML5 + CSS3 + JavaScript vanilla. Sin React, Vue, Angular ni ninguna librería de UI.

**Gráficos implementados:**
- Sparklines (SVG path)
- Gráfico de líneas comparativo (SVG)
- Heatmap de correlación (SVG rects)
- Gráfico de velas OHLC (Canvas 2D API)
- Barras horizontales (SVG)
- Gráfico de dona (Canvas 2D API)

---

## Base de Datos

### Schema

```sql
activos (id, ticker, nombre, tipo, mercado)
precios (id, activo_id, fecha, apertura, maximo, minimo, cierre, volumen)
resultados_similitud (id, activo1_id, activo2_id, algoritmo, valor, calculado_en)
resultados_volatilidad (id, activo_id, fecha, ventana_dias, volatilidad, retorno_medio)
resultados_patrones (id, activo_id, fecha_inicio, fecha_fin, patron, variacion_pct)
resultados_sorting (id, algoritmo, complejidad, tamanio, tiempo_ms)
top_volumen (id, ticker, fecha, volumen, cierre)
```

### Índices

```sql
CREATE INDEX idx_precios_activo_fecha ON precios(activo_id, fecha DESC);
```

### Idempotencia

Todas las inserciones usan `ON CONFLICT DO NOTHING` o `ON CONFLICT DO UPDATE`. El sistema puede ejecutarse múltiples veces sin duplicar datos.

---

## Despliegue

### Desarrollo Local (Docker Compose)

```yaml
services:
  bvc_db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: bvc_analytics
      POSTGRES_USER: bvc_user
      POSTGRES_PASSWORD: changeme

  bvc_api:
    build: .
    command: python main.py api
    ports:
      - "8001:8001"
    depends_on:
      bvc_db:
        condition: service_healthy
```

### Producción (Render)

```yaml
services:
  - type: web
    name: bvc-analytics
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py api
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: bvc-db
          property: connectionString
```

---

## Dependencias

```
psycopg2-binary==2.9.9
```

Una sola dependencia externa. Todo lo demás es Python stdlib:
`urllib`, `json`, `http.server`, `datetime`, `math`, `time`, `os`, `re`

---

## Ejecución de Pipelines

```bash
python main.py etl           # Req 1: descarga + limpieza + carga (~10 min)
python main.py similitud     # Req 2: 190 pares × 4 algoritmos (~5 min con DTW)
python main.py volatilidad   # Req 3: volatilidad rodante por activo
python main.py ordenamiento  # Benchmark 12 algoritmos + top-15 volumen
python main.py api           # Req 5: servidor HTTP en puerto 8001
python main.py todo          # Ejecuta todos los pipelines en secuencia
```
