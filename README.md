# BVC Analytics

Sistema de análisis financiero cuantitativo sobre datos históricos de la Bolsa de Valores de Colombia (BVC) y ETFs globales. Implementa 28 algoritmos desde cero en Python puro para el análisis de 20 activos financieros con cinco años de historia diaria.

**Universidad del Quindío — Ingeniería de Sistemas y Computación — Análisis de Algoritmos 2026-1**

---

## Portafolio

| Grupo | Tickers |
|---|---|
| Colombia ADRs (NYSE) | EC, CIB, GXG |
| ETFs Latinoamérica | ILF, EWZ, EWW |
| ETFs Globales | SPY, QQQ, DIA, EEM, VT, IEMG |
| Sectores y Commodities | GLD, SLV, USO, TLT, XLE, XLF, XLK, VNQ |

25,000+ registros OHLCV — 5 años de historia diaria.

---

## Algoritmos Implementados

| Módulo | Algoritmo | Complejidad |
|---|---|---|
| ETL | Interpolación lineal | O(n) |
| ETL | Detección outliers Z-Score | O(n) |
| Similitud | Distancia Euclidiana | O(n) |
| Similitud | Correlación de Pearson | O(n) |
| Similitud | Similitud por Coseno | O(n) |
| Similitud | Dynamic Time Warping | O(n²) |
| Patrones | Ventana deslizante | O(n·k) |
| Patrones | Detección picos y valles | O(n) |
| Patrones | Media Móvil Simple | O(n·k) |
| Patrones | Golden / Death Cross | O(n·k) |
| Volatilidad | Retornos logarítmicos | O(n) |
| Volatilidad | Volatilidad histórica anualizada | O(n) |
| Volatilidad | Máximo Drawdown | O(n) |
| Volatilidad | VaR Histórico 95% | O(n log n) |
| Volatilidad | Sharpe Ratio | O(n) |
| Ordenamiento | TimSort | O(n log n) |
| Ordenamiento | Comb Sort | O(n log n) |
| Ordenamiento | Selection Sort | O(n²) |
| Ordenamiento | Tree Sort | O(n log n) |
| Ordenamiento | Pigeonhole Sort | O(n + k) |
| Ordenamiento | Bucket Sort | O(n + k) |
| Ordenamiento | QuickSort | O(n log n) |
| Ordenamiento | HeapSort | O(n log n) |
| Ordenamiento | Bitonic Sort | O(n log²n) |
| Ordenamiento | Gnome Sort | O(n²) |
| Ordenamiento | Binary Insertion Sort | O(n²) |
| Ordenamiento | RadixSort | O(nk) |

---

## Estructura del Proyecto

```
├── algoritmos/          # Módulos de algoritmos por requerimiento
├── etl/                 # Extracción, transformación y carga de datos
├── api/                 # Servidor HTTP (stdlib)
├── interfaz/            # Dashboard SPA (HTML5 + JS vanilla)
├── reportes/            # Generador de reporte técnico
├── basedatos/           # Schema y migraciones PostgreSQL
├── documentacion/       # Documentación técnica por requerimiento
├── config.py            # Configuración centralizada
├── main.py              # Orquestador de pipelines
└── requirements.txt     # psycopg2-binary==2.9.9
```

---

## Ejecución

### Docker (recomendado)

```bash
cp .env.example .env
docker compose -f docker-compose.local.yml up --build -d
docker exec bvc_api python main.py etl
docker exec bvc_api python main.py similitud
docker exec bvc_api python main.py volatilidad
docker exec bvc_api python main.py ordenamiento
```

Dashboard disponible en **http://localhost:8001**

### Sin Docker

```bash
pip install psycopg2-binary==2.9.9
cp .env.example .env
python main.py todo
```

---

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/activos` | Catálogo de 20 activos |
| GET | `/precios?ticker=SPY` | Precios históricos |
| GET | `/similitud?algoritmo=pearson` | Resultados de similitud |
| GET | `/correlacion/matriz` | Matriz 20×20 para heatmap |
| GET | `/patrones?ticker=SPY` | Patrones detectados |
| GET | `/riesgo/clasificacion` | Ranking de riesgo |
| GET | `/ordenamiento/benchmark` | Benchmark 12 algoritmos |
| GET | `/reporte/txt` | Reporte técnico HTML/PDF |
| GET | `/monedas/tasa` | Tasa USD/COP en tiempo real |

---

## Stack

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.11 (stdlib) |
| Base de datos | PostgreSQL 15 |
| Servidor HTTP | `http.server` (stdlib) |
| Frontend | HTML5 + CSS3 + JS vanilla |
| Driver BD | psycopg2-binary 2.9.9 |
| Despliegue | Render |

---

## Documentación Técnica

La documentación detallada por requerimiento se encuentra en la carpeta `documentacion/`:

- `documentacion/REQ1_ETL.md` — Extracción, limpieza y carga de datos
- `documentacion/REQ2_SIMILITUD.md` — Algoritmos de similitud
- `documentacion/REQ3_PATRONES_VOLATILIDAD.md` — Patrones y métricas de riesgo
- `documentacion/REQ4_DASHBOARD.md` — Dashboard y reporte
- `documentacion/REQ5_DESPLIEGUE.md` — Despliegue y configuración
- `documentacion/ARQUITECTURA.md` — Arquitectura completa del sistema

---

*Universidad del Quindío — Análisis de Algoritmos — 2026-1*
