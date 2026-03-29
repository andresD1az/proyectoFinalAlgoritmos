# Documento de Arquitectura — BVC Analytics

**Universidad del Quindío**  
**Programa de Ingeniería de Sistemas y Computación**  
**Análisis de Algoritmos — Proyecto Final**

---

## 1. Visión General del Sistema

BVC Analytics es una plataforma web de análisis financiero cuantitativo que procesa datos históricos de 20 activos de la Bolsa de Valores de Colombia (BVC) y ETFs globales. El sistema implementa desde cero (sin librerías de alto nivel) los algoritmos exigidos por el enunciado del proyecto.

**Principio fundamental:** toda la lógica algorítmica está implementada con estructuras básicas de Python. La única dependencia externa es `psycopg2-binary` como driver de conexión a PostgreSQL.

---

## 2. Estructura de Carpetas

```
proyectoFinalAlgoritmos/
│
├── algoritmos/                  ← Núcleo algorítmico (Reqs 1, 2, 3)
│   ├── ordenamiento.py          ← 12 algoritmos de ordenamiento
│   ├── similitud.py             ← 4 algoritmos de similitud
│   ├── patrones.py              ← Ventana deslizante + Golden/Death Cross
│   ├── volatilidad.py           ← VaR, Sharpe, Drawdown, volatilidad
│   └── __init__.py
│
├── etl/                         ← Pipeline de datos (Req 1)
│   ├── descargador.py           ← Descarga HTTP desde Yahoo Finance
│   ├── limpieza.py              ← Interpolación lineal + Z-Score
│   ├── database.py              ← CRUD PostgreSQL con psycopg2
│   └── __init__.py
│
├── api/                         ← Servidor HTTP (Req 5)
│   ├── server.py                ← 18 endpoints REST con http.server
│   └── __init__.py
│
├── interfaz/                    ← Dashboard visual (Req 4)
│   └── index.html               ← SPA: HTML5 + CSS3 + JS vanilla
│
├── reportes/                    ← Generación de reportes (Req 4)
│   ├── generador.py             ← Reporte JSON y texto plano
│   └── __init__.py
│
├── basedatos/                   ← Schema SQL
│   ├── init.sql                 ← Creación de tablas
│   ├── migrate_auth.sql         ← Migraciones
│   └── migrate_v2.sql
│
├── autenticacion/               ← Módulo de autenticación
│   ├── auth.py                  ← SHA-256 + salt + sesiones
│   └── __init__.py
│
├── scripts/                     ← Utilidades de administración
│   ├── crear_superadmin.py
│   └── deploy_vps.py
│
├── config.py                    ← Configuración global centralizada
├── main.py                      ← Orquestador de pipelines
├── requirements.txt             ← psycopg2-binary==2.9.9 (única dep.)
├── render.yaml                  ← Despliegue en Render (Req 5)
├── Dockerfile.local             ← Imagen Docker para desarrollo local
├── docker-compose.local.yml     ← Orquestación local (API + BD)
└── .env                         ← Variables de entorno (no en git)
```

---

## 3. Arquitectura en Capas

```
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                  │
│              interfaz/index.html                         │
│         HTML5 + CSS3 + JavaScript vanilla                │
│    SVG (heatmap) + Canvas API (velas, barras)            │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP (fetch API)
┌──────────────────────▼──────────────────────────────────┐
│                    CAPA DE API                           │
│              api/server.py                               │
│         http.server (stdlib) — ThreadingHTTPServer       │
│         18 endpoints REST — CORS habilitado              │
└──────────┬───────────────────────────┬──────────────────┘
           │                           │
┌──────────▼──────────┐   ┌────────────▼────────────────┐
│  CAPA ALGORÍTMICA   │   │     CAPA DE DATOS (ETL)      │
│  algoritmos/        │   │     etl/                     │
│                     │   │                              │
│  ordenamiento.py    │   │  descargador.py              │
│  similitud.py       │   │  → urllib.request            │
│  patrones.py        │   │  → Yahoo Finance API v8      │
│  volatilidad.py     │   │                              │
│                     │   │  limpieza.py                 │
│  28 algoritmos      │   │  → Interpolación lineal      │
│  implementados      │   │  → Z-Score                   │
│  desde cero         │   │                              │
└──────────┬──────────┘   │  database.py                 │
           │              │  → psycopg2 (driver)         │
           └──────────────┴────────────┬─────────────────┘
                                       │
┌──────────────────────────────────────▼─────────────────┐
│                  CAPA DE PERSISTENCIA                    │
│              PostgreSQL 15                               │
│                                                          │
│  activos          precios           resultados_similitud │
│  resultados_      resultados_       top_volumen          │
│  volatilidad      sorting                                │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Flujo de Datos

```
Yahoo Finance (HTTPS)
        │
        ▼
etl/descargador.py
  urllib.request.urlopen()
  json.loads() → parseo manual
  datetime.utcfromtimestamp() → conversión timestamps
        │
        ▼
etl/limpieza.py
  interpolar_linealmente() → rellena None con fórmula lineal
  detectar_outliers_zscore() → identifica anomalías
        │
        ▼
etl/database.py
  insertar_precios_lote() → PostgreSQL via psycopg2
        │
        ▼
algoritmos/ (procesamiento)
  ordenamiento.py  → 12 algoritmos sobre dataset unificado
  similitud.py     → 190 pares × 4 algoritmos
  patrones.py      → ventana deslizante sobre cada activo
  volatilidad.py   → VaR, Sharpe, Drawdown por activo
        │
        ▼
etl/database.py
  guardar_similitud()   → tabla resultados_similitud
  guardar_volatilidad() → tabla resultados_volatilidad
  (ordenamiento)        → tablas resultados_sorting, top_volumen
        │
        ▼
api/server.py
  ThreadingHTTPServer → sirve endpoints REST
  _app() → sirve interfaz/index.html
        │
        ▼
interfaz/index.html
  fetch() → consume endpoints
  SVG → mapa de calor de correlaciones
  Canvas API → velas OHLC, diagrama de barras
```

---

## 5. Modelo de Datos (PostgreSQL)

```sql
activos
  id        SERIAL PK
  ticker    VARCHAR(10) UNIQUE   -- "SPY", "EC", "GLD"
  nombre    VARCHAR(100)         -- "S&P 500 ETF"
  tipo      VARCHAR(20)          -- "etf" | "accion"
  mercado   VARCHAR(20)          -- "NYSE" | "NASDAQ"

precios
  id        SERIAL PK
  activo_id INTEGER FK → activos.id
  fecha     DATE
  apertura  NUMERIC(12,4)
  maximo    NUMERIC(12,4)
  minimo    NUMERIC(12,4)
  cierre    NUMERIC(12,4)
  volumen   BIGINT
  UNIQUE(activo_id, fecha)       -- evita duplicados

resultados_similitud
  id         SERIAL PK
  activo1_id INTEGER FK → activos.id
  activo2_id INTEGER FK → activos.id
  algoritmo  VARCHAR(30)         -- "pearson" | "coseno" | "euclidiana" | "dtw"
  valor      NUMERIC(10,6)
  calculado_en TIMESTAMP

resultados_volatilidad
  id           SERIAL PK
  activo_id    INTEGER FK → activos.id
  fecha        DATE
  ventana_dias INTEGER
  volatilidad  NUMERIC(12,6)    -- volatilidad anualizada
  retorno_medio NUMERIC(12,6)
  UNIQUE(activo_id, fecha, ventana_dias)

resultados_sorting
  id          SERIAL PK
  algoritmo   VARCHAR(50)        -- "TimSort", "QuickSort", etc.
  complejidad VARCHAR(20)        -- "O(n log n)", "O(n²)", etc.
  tamanio     INTEGER            -- n = 5000 registros
  tiempo_ms   NUMERIC(12,6)      -- tiempo de ejecución en ms

top_volumen
  id      SERIAL PK
  ticker  VARCHAR(10)
  fecha   DATE
  volumen BIGINT
  cierre  NUMERIC(12,4)
```

---

## 6. API — Endpoints

| Método | Ruta | Módulo | Descripción |
|--------|------|--------|-------------|
| GET | `/` | `api/server.py` | Sirve el dashboard (interfaz/index.html) |
| GET | `/health` | `api/server.py` | Estado del sistema |
| GET | `/etl/status` | `etl/database.py` | Registros en BD |
| POST | `/etl/iniciar` | `main.py` | Dispara ETL en segundo plano |
| GET | `/activos` | `etl/database.py` | Lista de 20 activos |
| GET | `/precios?ticker=SPY` | `etl/database.py` | Precios históricos |
| GET | `/precios/ohlcv?ticker=SPY` | `etl/database.py` | OHLCV para velas |
| GET | `/similitud?algoritmo=pearson` | `etl/database.py` | Resultados de similitud |
| GET | `/correlacion/matriz` | `etl/database.py` | Matriz 20×20 para heatmap |
| GET | `/patrones?ticker=SPY` | `algoritmos/patrones.py` | Patrones detectados |
| GET | `/patrones/cruces?ticker=SPY` | `algoritmos/patrones.py` | Golden/Death Cross |
| GET | `/riesgo/clasificacion` | `algoritmos/volatilidad.py` | Ranking de riesgo |
| GET | `/ordenamiento/benchmark` | `etl/database.py` | Tabla 1 — 12 algoritmos |
| GET | `/ordenamiento/top-volumen` | `etl/database.py` | Top-15 mayor volumen |
| GET | `/reporte` | `reportes/generador.py` | Reporte JSON |
| GET | `/reporte/txt` | `reportes/generador.py` | Reporte texto plano |
| GET | `/monedas/tasa` | `api/server.py` | Tasa USD/COP en tiempo real |

---

## 7. Stack Tecnológico

| Componente | Tecnología | Justificación |
|---|---|---|
| Lenguaje | Python 3.11 | Requerido por el enunciado |
| Lógica algorítmica | Python stdlib | Restricción del enunciado: sin numpy/pandas |
| Base de datos | PostgreSQL 15 | Persistencia relacional robusta |
| Driver BD | psycopg2-binary 2.9.9 | Única dependencia externa permitida |
| Servidor HTTP | `http.server` (stdlib) | Sin Flask/FastAPI por restricción |
| Descarga de datos | `urllib.request` (stdlib) | Sin yfinance/requests por restricción |
| Frontend | HTML5 + CSS3 + JS vanilla | Sin React/Vue por simplicidad |
| Visualizaciones | SVG + Canvas API | Sin matplotlib/plotly por restricción |
| Contenedores | Docker + Docker Compose | Reproducibilidad del entorno |
| Despliegue | Render (Python nativo) | Plan gratuito, sin Docker en producción |

---

## 8. Decisiones de Diseño

**¿Por qué PostgreSQL y no SQLite?**  
PostgreSQL soporta tipos de datos financieros (`NUMERIC(12,4)`), tiene mejor rendimiento para consultas analíticas sobre 25,000+ registros, y es el estándar en producción. SQLite no soporta concurrencia real.

**¿Por qué `http.server` y no Flask?**  
El enunciado restringe el uso de frameworks. `http.server` es parte de la stdlib de Python y permite implementar un servidor HTTP completo sin dependencias externas.

**¿Por qué retornos logarítmicos y no simples?**  
Los retornos logarítmicos son aditivos en el tiempo (`r_total = r₁ + r₂ + ... + rₙ`) y tienen distribución más cercana a la normal, lo que facilita el cálculo de VaR y Sharpe Ratio.

**¿Por qué ventana de 5,000 registros para el benchmark de ordenamiento?**  
Con 25,579 registros totales, los algoritmos O(n²) tardarían horas. Con 5,000 registros todos los algoritmos terminan en minutos y la diferencia de complejidad es claramente visible en el diagrama de barras.

**¿Por qué Sakoe-Chiba en DTW?**  
La ventana del 10% reduce la complejidad de O(n²) a O(n·k) sin perder precisión significativa. Evita alineaciones "irrazonables" entre puntos muy distantes en el tiempo.

---

## 9. Despliegue

### Desarrollo local (Docker)
```bash
docker compose -f docker-compose.local.yml up --build
# API: http://localhost:8001
```

### Producción (Render)
- URL: `https://bvc-analytics-api.onrender.com`
- Runtime: Python 3.11 nativo (sin Docker)
- BD: PostgreSQL en Render (plan gratuito, 90 días)
- `DATABASE_URL` inyectada automáticamente por Render

### Comandos de pipeline
```bash
python main.py etl           # Req 1: descarga y carga datos
python main.py similitud     # Req 2: calcula 190 pares × 4 algoritmos
python main.py volatilidad   # Req 3: VaR, Sharpe, Drawdown
python main.py ordenamiento  # Req 1: benchmark 12 algoritmos
python main.py api           # Req 5: inicia servidor HTTP
python main.py todo          # Ejecuta todo en secuencia
```

---

## 10. Declaración de Uso de IA

Este proyecto utilizó herramientas de inteligencia artificial generativa (Kiro/Claude) como apoyo en el desarrollo. El diseño algorítmico, la formulación matemática, la implementación explícita de cada algoritmo y el análisis de complejidad fueron realizados y verificados por los estudiantes. Las herramientas de IA se usaron como soporte de codificación y revisión, no como sustituto del análisis formal requerido por el curso.

---

*Universidad del Quindío — Análisis de Algoritmos — 2025*
