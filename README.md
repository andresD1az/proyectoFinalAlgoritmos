# BVC Analytics

Plataforma de análisis financiero cuantitativo sobre datos históricos de la Bolsa de Valores de Colombia (BVC) y ETFs globales.

**Universidad del Quindío — Ingeniería de Sistemas y Computación — Análisis de Algoritmos**

> Todos los algoritmos están implementados desde cero en Python puro. Sin pandas, numpy, scipy, sklearn ni yfinance. La única dependencia externa es `psycopg2-binary` como driver de PostgreSQL.

---

## Demo

**https://bvc-analytics-api.onrender.com**

---

## Portafolio — 20 Activos

| Grupo | Tickers |
|---|---|
| Colombia (ADRs NYSE) | EC, CIB, GXG |
| ETFs Latinoamérica | ILF, EWZ, EWW |
| ETFs Globales | SPY, QQQ, DIA, EEM, VT, IEMG |
| Sectores y Commodities | GLD, SLV, USO, TLT, XLE, XLF, XLK, VNQ |

5 años de historia diaria — ~25,500 registros OHLCV en total.

---

## Algoritmos Implementados

### ETL (`etl/`)
| Algoritmo | Complejidad | Descripción |
|---|---|---|
| Interpolación lineal | O(n) | Rellena valores faltantes: `V[i] = V[izq] + (V[der]-V[izq])*(i-izq)/(der-izq)` |
| Detección outliers Z-Score | O(n) | `z = (x-μ)/σ`, descarta si `|z| > 3.5` |

### Ordenamiento (`algoritmos/ordenamiento.py`)
| # | Algoritmo | Complejidad |
|---|---|---|
| 1 | TimSort | O(n log n) |
| 2 | Comb Sort | O(n log n) |
| 3 | Selection Sort | O(n²) |
| 4 | Tree Sort | O(n log n) |
| 5 | Pigeonhole Sort | O(n + k) |
| 6 | Bucket Sort | O(n + k) |
| 7 | QuickSort | O(n log n) |
| 8 | HeapSort | O(n log n) |
| 9 | Bitonic Sort | O(n log²n) |
| 10 | Gnome Sort | O(n²) |
| 11 | Binary Insertion Sort | O(n²) |
| 12 | RadixSort | O(nk) |

Criterio: `fecha ASC` (primario), `cierre ASC` (secundario). Ninguno usa `sorted()` ni `.sort()`.

### Similitud (`algoritmos/similitud.py`)
| Algoritmo | Complejidad | Fórmula |
|---|---|---|
| Distancia Euclidiana | O(n) | `√(Σ(Aᵢ-Bᵢ)²)` con normalización Min-Max |
| Correlación de Pearson | O(n) | `Σ((Aᵢ-Ā)(Bᵢ-B̄)) / √(Σ(Aᵢ-Ā)²·Σ(Bᵢ-B̄)²)` |
| Similitud por Coseno | O(n) | `(A·B) / (‖A‖·‖B‖)` |
| DTW | O(n²) | Programación dinámica con ventana Sakoe-Chiba 10% |

### Patrones y Volatilidad (`algoritmos/patrones.py`, `algoritmos/volatilidad.py`)
| Algoritmo | Complejidad |
|---|---|
| Ventana deslizante (20 días) | O(n·k) |
| Detección picos y valles | O(n) |
| Media Móvil Simple (SMA) | O(n·k) |
| Golden / Death Cross | O(n) |
| Retornos logarítmicos | O(n) |
| Volatilidad histórica anualizada | O(n) |
| Máximo Drawdown | O(n) |
| VaR Histórico (95%) | O(n log n) |
| Sharpe Ratio | O(n) |

---

## Estructura del Proyecto

```
├── algoritmos/
│   ├── ordenamiento.py   # 12 algoritmos de ordenamiento
│   ├── similitud.py      # 4 algoritmos de similitud
│   ├── patrones.py       # Ventana deslizante + Golden/Death Cross
│   └── volatilidad.py    # VaR, Sharpe, Drawdown, volatilidad
├── etl/
│   ├── descargador.py    # Descarga HTTP desde Yahoo Finance (urllib)
│   ├── limpieza.py       # Interpolación lineal + Z-Score
│   └── database.py       # CRUD PostgreSQL con psycopg2
├── api/
│   └── server.py         # Servidor HTTP (http.server stdlib) — 18 endpoints
├── interfaz/
│   └── index.html        # Dashboard SPA — HTML5 + CSS3 + JS vanilla
├── reportes/
│   └── generador.py      # Reporte JSON y texto plano
├── basedatos/
│   └── init.sql          # Schema PostgreSQL
├── config.py             # 20 activos + parámetros algorítmicos
├── main.py               # Orquestador de pipelines
├── requirements.txt      # psycopg2-binary==2.9.9
├── render.yaml           # Despliegue en Render
└── docker-compose.local.yml
```

---

## Cómo Ejecutar

### Con Docker (recomendado)

```bash
cp .env.example .env
docker compose -f docker-compose.local.yml up --build -d
```

### Sin Docker

```bash
pip install psycopg2-binary==2.9.9
cp .env.example .env
# Editar .env con credenciales de PostgreSQL local
python main.py api
```

### Pipelines

```bash
python main.py etl           # Descarga y carga 5 años de datos (~10 min)
python main.py similitud     # Calcula 190 pares × 4 algoritmos
python main.py volatilidad   # VaR, Sharpe, Drawdown por activo
python main.py ordenamiento  # Benchmark 12 algoritmos + top-15 volumen
python main.py api           # Inicia servidor en http://localhost:8001
python main.py todo          # Ejecuta todo en secuencia
```

---

## API — Endpoints Principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Dashboard visual |
| GET | `/activos` | Catálogo de 20 activos |
| GET | `/precios?ticker=SPY` | Precios históricos |
| GET | `/similitud?algoritmo=pearson` | Resultados de similitud |
| GET | `/correlacion/matriz` | Matriz 20×20 para heatmap |
| GET | `/patrones?ticker=SPY` | Patrones detectados |
| GET | `/riesgo/clasificacion` | Ranking de riesgo |
| GET | `/ordenamiento/benchmark` | Tabla 1 — 12 algoritmos |
| GET | `/ordenamiento/top-volumen` | Top-15 mayor volumen |
| GET | `/reporte/txt` | Reporte técnico completo |
| GET | `/monedas/tasa` | Tasa USD/COP en tiempo real |
| POST | `/etl/iniciar` | Dispara el ETL en segundo plano |

---

## Stack

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.11 (stdlib para toda la lógica) |
| Base de datos | PostgreSQL 15 |
| Servidor HTTP | `http.server` (stdlib) |
| Frontend | HTML5 + CSS3 + JS vanilla (SVG + Canvas API) |
| Driver BD | psycopg2-binary 2.9.9 |
| Despliegue | Render (Python nativo) |

---

## Declaración de Uso de IA

Este proyecto utilizó herramientas de inteligencia artificial generativa como apoyo puntual en revisión de sintaxis, sugerencia de la optimización Sakoe-Chiba para DTW, corrección de un bug en Tree Sort y formato de documentación. El diseño algorítmico, las fórmulas matemáticas, el análisis de complejidad y la implementación final fueron realizados por el equipo.

---

*Universidad del Quindío — Análisis de Algoritmos — 2025*
