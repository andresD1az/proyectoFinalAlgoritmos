# BVC Analytics

Plataforma de análisis financiero cuantitativo sobre datos históricos de la Bolsa de Valores de Colombia (BVC) y ETFs globales.

Proyecto académico — Universidad del Quindío  
Ingeniería de Sistemas y Computación — Análisis de Algoritmos

---

## Qué hace este proyecto

Descarga, limpia y analiza 5 años de datos históricos de 20 activos financieros. Implementa desde cero (sin librerías de alto nivel) 28 algoritmos de ordenamiento, similitud, detección de patrones y análisis de riesgo. Expone todo a través de una API HTTP y un dashboard visual interactivo.

**Restricción académica:** cero uso de pandas, numpy, scipy, sklearn, yfinance o equivalentes. Solo Python 3.11 stdlib + psycopg2 como driver de BD.

---

## Stack

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.11 (stdlib pura para toda la lógica) |
| Base de datos | PostgreSQL 15 |
| Servidor HTTP | `http.server` (stdlib) |
| Frontend | HTML5 + CSS3 + JS vanilla (SVG + Canvas API) |
| Driver BD | psycopg2-binary (única dependencia externa) |
| Despliegue | Render (Python nativo) / Docker Compose (local) |

---

## Activos analizados (20)

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

## Estructura del proyecto

```
bvc-analytics/
├── etl/
│   ├── downloader.py       # Descarga HTTP pura (urllib) con reintentos
│   ├── cleaner.py          # Interpolación lineal + detección outliers Z-Score
│   └── database.py         # CRUD PostgreSQL con psycopg2
├── algorithms/
│   ├── sorting.py          # 12 algoritmos de ordenamiento (Req. 2)
│   ├── similarity.py       # 4 algoritmos de similitud (Req. 3)
│   ├── patterns.py         # Ventana deslizante + Golden/Death Cross (Req. 4)
│   └── volatility.py       # VaR, Sharpe, Drawdown, clasificación riesgo (Req. 4)
├── api/
│   └── server.py           # Servidor HTTP con 25+ endpoints
├── auth/
│   └── auth.py             # Autenticación SHA-256 + sesiones
├── cms/
│   └── content.py          # Lecciones financieras + paper trading
├── reports/
│   └── generator.py        # Reportes JSON y texto plano
├── frontend/
│   └── index.html          # SPA completa (sin frameworks)
├── database/
│   ├── init.sql            # Schema inicial PostgreSQL
│   └── migrate_*.sql       # Migraciones
├── main.py                 # Orquestador de pipelines
├── config.py               # 20 activos + parámetros algorítmicos
├── render.yaml             # Despliegue nativo en Render
├── Dockerfile.local        # Imagen Docker (solo uso local)
├── docker-compose.local.yml
├── .python-version         # Python 3.11.0 (fijado para Render)
└── requirements.txt        # Solo psycopg2-binary==2.9.9
```

---

## Cómo ejecutar

### Local con Docker (recomendado)

```bash
cp .env.example .env
# Edita .env con tus credenciales
docker compose -f docker-compose.local.yml up --build
```

La API queda disponible en `http://localhost:8001`.

### Local sin Docker

Requiere PostgreSQL corriendo localmente.

```bash
pip install -r requirements.txt
cp .env.example .env
# Edita .env con DB_HOST=localhost y tus credenciales
psql -U postgres -f database/init.sql
python main.py etl
python main.py api
```

### Comandos disponibles

```bash
python main.py etl            # Descarga + limpieza + carga en BD
python main.py similitud      # Calcula los 4 algoritmos de similitud
python main.py volatilidad    # Calcula métricas de riesgo
python main.py ordenamiento   # Benchmark 12 algoritmos + top-15 volumen
python main.py api            # Inicia el servidor HTTP en :8001
python main.py todo           # Ejecuta todo en secuencia
```

---

## Algoritmos implementados (28)

### ETL — `etl/cleaner.py`

| Algoritmo | Complejidad | Descripción |
|---|---|---|
| Interpolación lineal | O(n) | Rellena valores faltantes: `V[i] = V[izq] + (V[der]-V[izq]) * (i-izq)/(der-izq)` |
| Detección outliers Z-Score | O(n) | `z = (x - μ) / σ` — descarta registros con `|z| > 3.5` |

### Ordenamiento — `algorithms/sorting.py` (Requerimiento 2)

| # | Algoritmo | Complejidad |
|---|---|---|
| 1 | TimSort | O(n log n) |
| 2 | Comb Sort | O(n log n) |
| 3 | Selection Sort | O(n²) |
| 4 | Tree Sort | O(n log n) |
| 5 | Pigeonhole Sort | O(n + k) |
| 6 | Bucket Sort | O(n + k) |
| 7 | QuickSort | O(n log n) promedio |
| 8 | HeapSort | O(n log n) |
| 9 | Bitonic Sort | O(n log²n) |
| 10 | Gnome Sort | O(n²) |
| 11 | Binary Insertion Sort | O(n²) |
| 12 | RadixSort | O(nk) |

Criterio: `fecha ASC` (primario), `cierre ASC` (secundario). Ninguno usa `sorted()` ni `.sort()`.

### Similitud — `algorithms/similarity.py` (Requerimiento 3)

| Algoritmo | Complejidad | Fórmula |
|---|---|---|
| Distancia Euclidiana | O(n) | `√Σ(Aᵢ - Bᵢ)²` sobre series normalizadas Min-Max |
| Correlación de Pearson | O(n) | `cov(A,B) / (σ_A · σ_B)` — rango [-1, 1] |
| Similitud por Coseno | O(n) | `(A·B) / (|A|·|B|)` — invariante a escala |
| DTW | O(n²) | Dynamic Time Warping con banda Sakoe-Chiba 10% |

### Patrones — `algorithms/patterns.py` (Requerimiento 4)

| Algoritmo | Complejidad | Descripción |
|---|---|---|
| Ventana deslizante | O(n·k) | Clasifica segmentos: alza, baja, rebote, neutro |
| Detección picos/valles | O(n) | Máximos y mínimos locales en la serie |
| Media Móvil Simple (SMA) | O(n·k) | Promedio de ventana deslizante manual |
| Golden/Death Cross | O(n) | Cruce de SMA corta sobre SMA larga |

### Volatilidad y Riesgo — `algorithms/volatility.py` (Requerimiento 4)

| Algoritmo | Complejidad | Descripción |
|---|---|---|
| Retornos logarítmicos | O(n) | `rᵢ = ln(Pᵢ / Pᵢ₋₁)` |
| Volatilidad histórica | O(n) | Desviación estándar muestral × √252 (anualizada) |
| Máximo Drawdown | O(n) | Mayor caída pico-a-valle en la serie |
| VaR Histórico (95%) | O(n log n) | Percentil 5% de retornos ordenados |
| Sharpe Ratio | O(n) | `(retorno_medio - tasa_libre) / volatilidad` |
| Clasificación de riesgo | O(1) | Conservador (<15%), Moderado (15-30%), Agresivo (>30%) |

---

## API — Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del sistema |
| GET | `/activos` | Catálogo de 20 activos |
| GET | `/precios?ticker=SPY` | Precios históricos |
| GET | `/precios/ohlcv?ticker=SPY` | Datos OHLCV completos |
| GET | `/similitud?algoritmo=pearson` | Resultados de similitud |
| GET | `/volatilidad?ticker=SPY` | Métricas de riesgo |
| GET | `/patrones?ticker=SPY` | Patrones detectados |
| GET | `/patrones/cruces?ticker=SPY` | Golden/Death Cross |
| GET | `/riesgo/clasificacion` | Ranking de riesgo de los 20 activos |
| GET | `/correlacion/matriz` | Matriz de correlación 20×20 |
| GET | `/ordenamiento/benchmark` | Tabla 1: tiempos de los 12 algoritmos |
| GET | `/ordenamiento/top-volumen` | Top-15 días con mayor volumen |
| GET | `/reporte` | Reporte técnico completo (JSON) |
| GET | `/etl/status` | Cuántos registros hay en la BD |
| POST | `/etl/iniciar` | Dispara el pipeline ETL en segundo plano |
| POST | `/auth/login` | Inicio de sesión |
| POST | `/simulador/comprar` | Paper trading — comprar activo |

---

## Variables de entorno

```env
# Render provee DATABASE_URL automáticamente al conectar una BD
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Para desarrollo local (sin DATABASE_URL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bvc_analytics
DB_USER=bvc_user
DB_PASSWORD=tu_password

API_HOST=0.0.0.0
API_PORT=8001
```

---

## Despliegue en Render

El proyecto está desplegado en:  
`https://bvc-analytics-api.onrender.com`

Configurado con `render.yaml` usando runtime Python nativo (sin Docker).  
La BD PostgreSQL es el servicio `bvc-analytics-db` en el mismo workspace de Render.

Para poblar la BD después del primer despliegue:

```javascript
// Desde la consola del navegador (F12)
fetch('https://bvc-analytics-api.onrender.com/etl/iniciar', { method: 'POST' })
  .then(r => r.json()).then(console.log)
```

---

## Declaración de uso de IA

Este proyecto utilizó herramientas de inteligencia artificial generativa (Kiro/Claude) como apoyo en el desarrollo. El diseño algorítmico, la formulación matemática, la implementación explícita de cada algoritmo y el análisis de complejidad fueron realizados y verificados por los estudiantes. Las herramientas de IA se usaron como soporte de codificación y revisión, no como sustituto del análisis formal requerido por el curso.

---

*Universidad del Quindío — Análisis de Algoritmos — 2025*
