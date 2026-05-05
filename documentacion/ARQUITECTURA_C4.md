# Arquitectura C4 — Algorit Finance

**Universidad del Quindio — Ingenieria de Sistemas y Computacion — Analisis de Algoritmos 2026-1**
**Autores:** Sarita Londono Perdomo (1091884459) · Eyner Andres Diaz Diaz (1128544093)
**Profesor:** Sergio Augusto Cardona Torres

---

## NIVEL 1 — Diagrama de Contexto

Muestra el sistema Algorit Finance en relacion con los actores externos.

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                   CONTEXTO DEL SISTEMA                  │
                    └─────────────────────────────────────────────────────────┘

  ┌──────────────────┐                                  ┌──────────────────────┐
  │     USUARIO      │                                  │  Yahoo Finance API v8 │
  │  (Estudiante /   │                                  │  (Sistema externo)    │
  │   Evaluador)     │                                  │  Acceso publico       │
  └────────┬─────────┘                                  │  Sin autenticacion    │
           │                                            └──────────┬────────────┘
           │ Accede via                                            │
           │ bvc.andresdiazd.com                                   │ HTTP GET
           │ (navegador web)                                       │ urllib.request
           │                                                       │
           ▼                                                       ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                                                                             │
  │                         ALGORIT FINANCE                                    │
  │                                                                             │
  │   Sistema de analisis financiero cuantitativo.                              │
  │   Descarga, procesa y analiza series de tiempo de 20 activos financieros    │
  │   con 5 anos de historia diaria (OHLCV).                                    │
  │                                                                             │
  │   28 algoritmos implementados desde cero en Python 3.11 stdlib puro.        │
  │   Sin pandas, numpy, scipy, sklearn, yfinance, Flask ni FastAPI.            │
  │                                                                             │
  │   URL: https://bvc.andresdiazd.com                                          │
  │                                                                             │
  └─────────────────────────────────────────────────────────────────────────────┘
           │
           │ Lee / Escribe (psycopg2 TCP:5432)
           │
           ▼
  ┌──────────────────────────┐
  │     PostgreSQL 15        │
  │     (Base de datos)      │
  │     VPS Contabo          │
  │     38.242.225.58        │
  └──────────────────────────┘
```

**Actores y sistemas externos:**

| Actor / Sistema | Tipo | Descripcion |
|---|---|---|
| Usuario | Persona | Estudiante o evaluador que accede al dashboard via navegador |
| Yahoo Finance API v8 | Sistema externo | Fuente de datos OHLCV historicos. URL publica sin autenticacion |
| PostgreSQL 15 | Sistema de datos | Persiste todos los datos y resultados algoritmicos en el VPS |


---

## NIVEL 2 — Diagrama de Contenedores

Muestra los contenedores Docker en el VPS y como se comunican.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  VPS CONTABO — Ubuntu 24.04 LTS                                                  │
│  IP: 38.242.225.58   Dominio: bvc.andresdiazd.com                                │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │  NGINX (reverse proxy)                                                     │  │
│  │  Puerto 80 / 443 → proxy_pass http://localhost:8001                        │  │
│  │  Certificado SSL: bvc.andresdiazd.com                                      │  │
│  └──────────────────────────────────┬─────────────────────────────────────────┘  │
│                                     │ :8001                                      │
│  ┌──────────────────────────────────▼─────────────────────────────────────────┐  │
│  │  Red Docker: bvc-analytics_bvc_network                                     │  │
│  │                                                                            │  │
│  │  ┌──────────────────────────────────┐   ┌──────────────────────────────┐  │  │
│  │  │         bvc_api                  │   │          bvc_db              │  │  │
│  │  │                                  │   │                              │  │  │
│  │  │  Imagen:                         │   │  Imagen:                     │  │  │
│  │  │  bvc-analytics-bvc_api:latest    │   │  postgres:15-alpine          │  │  │
│  │  │                                  │   │                              │  │  │
│  │  │  Runtime: Python 3.11            │   │  PostgreSQL 15               │  │  │
│  │  │  Cmd: python main.py api         │◄──►  Puerto: 5432 (interno)     │  │  │
│  │  │  Puerto: 8001 (expuesto)         │   │  DB: bvc_analytics           │  │  │
│  │  │  /app/ → codigo del proyecto     │   │  User: bvc_user              │  │  │
│  │  │                                  │   │  Volumen: datos persistentes │  │  │
│  │  └──────────────────────────────────┘   └──────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  Directorio del proyecto: /opt/bvc-analytics/                                    │
│  Compose file: /opt/bvc-analytics/docker-compose.yml                            │
└──────────────────────────────────────────────────────────────────────────────────┘
         ▲
         │ HTTPS (443) / HTTP (80)
         │
┌────────┴────────┐
│    Navegador    │
│    del usuario  │
│  bvc.andresdiazd│
│      .com       │
└─────────────────┘
```

**Contenedores:**

| Contenedor | Imagen | Puerto | Responsabilidad |
|---|---|---|---|
| vc_api | vc-analytics-bvc_api:latest | 8001 (expuesto) | Servidor HTTP + todos los algoritmos + ETL |
| vc_db | postgres:15-alpine | 5432 (solo interno) | Persistencia de datos y resultados |

**Infraestructura de red:**

| Componente | Detalle |
|---|---|
| VPS | Contabo, Ubuntu 24.04, 38.242.225.58 |
| Dominio | bvc.andresdiazd.com (subdominio) |
| Reverse proxy | Nginx → localhost:8001 |
| SSL | Certificado para bvc.andresdiazd.com |
| Red Docker | bvc-analytics_bvc_network (bridge) |


---

## NIVEL 3 — Diagrama de Componentes (bvc_api)

Muestra los modulos Python dentro del contenedor bvc_api organizados en capas.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          CONTENEDOR: bvc_api                                    │
│                          Python 3.11 — /app/                                   │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  CAPA 1 — PRESENTACION                                                    │  │
│  │                                                                           │  │
│  │  interfaz/index.html                                                      │  │
│  │  SPA — HTML5 + CSS3 + JavaScript vanilla                                  │  │
│  │  Graficos: SVG puro + Canvas 2D API (sin Chart.js, D3, Plotly)            │  │
│  │  Sin React, Vue, Angular, jQuery                                          │  │
│  │                                                                           │  │
│  │  Secciones: Overview | Portafolio | Comparar Activos | Mapa de Calor      │  │
│  │             Patrones | Clasificacion Riesgo | Ordenamiento | Velas OHLC   │  │
│  │             Reporte/PDF | Tasa USD/COP                                    │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                              ▲ HTTP/JSON                                        │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  CAPA 2 — API                                                             │  │
│  │                                                                           │  │
│  │  api/server.py                                                            │  │
│  │  ThreadingHTTPServer (http.server stdlib) — Sin Flask, FastAPI, Django    │  │
│  │  18 endpoints GET/POST — CORS habilitado                                  │  │
│  │                                                                           │  │
│  │  GET /activos          GET /precios         GET /precios/ohlcv            │  │
│  │  GET /similitud        GET /correlacion/matriz                            │  │
│  │  GET /patrones         GET /patrones/cruces                               │  │
│  │  GET /riesgo/clasificacion                                                │  │
│  │  GET /ordenamiento/benchmark  GET /ordenamiento/top-volumen               │  │
│  │  GET /reporte          GET /reporte/txt     GET /monedas/tasa             │  │
│  │  GET /etl/status       POST /etl/iniciar    GET /health                   │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                              ▲ llamadas Python directas                         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  CAPA 3 — ALGORITMICA                                                     │  │
│  │                                                                           │  │
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐  │  │
│  │  │ algoritmos/         │  │ algoritmos/         │  │ algoritmos/      │  │  │
│  │  │ similitud.py        │  │ patrones.py         │  │ volatilidad.py   │  │  │
│  │  │                     │  │                     │  │                  │  │  │
│  │  │ distancia_          │  │ detectar_patrones() │  │ calcular_        │  │  │
│  │  │  euclidiana() O(n)  │  │  O(n·k) — ventana  │  │  retornos_log()  │  │  │
│  │  │ correlacion_        │  │  20 dias            │  │  O(n)            │  │  │
│  │  │  pearson() O(n)     │  │ detectar_picos_     │  │ calcular_        │  │  │
│  │  │ similitud_          │  │  valles() O(n)      │  │  volatilidad()   │  │  │
│  │  │  coseno() O(n)      │  │ media_movil_        │  │  O(n) — σ×√252  │  │  │
│  │  │ dtw() O(n²)         │  │  simple() O(n·k)    │  │ calcular_var_   │  │  │
│  │  │  +Sakoe-Chiba 10%   │  │ detectar_cruces_    │  │  historico()     │  │  │
│  │  │ matriz_similitud()  │  │  medias() O(n·k)    │  │  O(n log n)      │  │  │
│  │  │  190 pares C(20,2)  │  │  Golden/Death Cross │  │ calcular_sharpe()│  │  │
│  │  │                     │  │                     │  │  O(n)            │  │  │
│  │  │                     │  │ Patron 1: N_dias_   │  │ calcular_max_   │  │  │
│  │  │                     │  │  alza (>=75%)       │  │  drawdown() O(n) │  │  │
│  │  │                     │  │ Patron 2: rebote    │  │                  │  │  │
│  │  │                     │  │  V-shape            │  │                  │  │  │
│  │  └─────────────────────┘  └─────────────────────┘  └──────────────────┘  │  │
│  │                                                                           │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐   │  │
│  │  │ algoritmos/ordenamiento.py — 12 algoritmos sin sorted() ni .sort()│   │  │
│  │  │                                                                   │   │  │
│  │  │ TimSort O(n logn)  | Comb Sort O(n logn)  | Selection Sort O(n²) │   │  │
│  │  │ Tree Sort O(n logn)| Pigeonhole O(n+k)    | Bucket Sort O(n+k)   │   │  │
│  │  │ QuickSort O(n logn)| HeapSort O(n logn)   | Bitonic O(n log²n)   │   │  │
│  │  │ Gnome Sort O(n²)   | Bin.Insertion O(n²)  | RadixSort O(nk)      │   │  │
│  │  │                                                                   │   │  │
│  │  │ Criterio: fecha ASC (primario), cierre ASC (secundario)           │   │  │
│  │  │ Benchmark: n=5000 registros con time.perf_counter()               │   │  │
│  │  └───────────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                              ▲ llamadas Python directas                         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  CAPA 4 — ETL                                                             │  │
│  │                                                                           │  │
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐  │  │
│  │  │ etl/                │  │ etl/                │  │ etl/             │  │  │
│  │  │ descargador.py      │  │ limpieza.py         │  │ database.py      │  │  │
│  │  │                     │  │                     │  │                  │  │  │
│  │  │ urllib.request      │  │ interpolar_         │  │ psycopg2 puro    │  │  │
│  │  │ urllib.parse        │  │  linealmente() O(n) │  │ Sin ORM          │  │  │
│  │  │ json.loads()        │  │  V[k]=V[izq]+       │  │                  │  │  │
│  │  │ 3 reintentos        │  │  (V[der]-V[izq])×   │  │ insertar_activos │  │  │
│  │  │ 1s pausa cortés     │  │  (k-izq)/(der-izq)  │  │ insertar_precios │  │  │
│  │  │ 20 activos          │  │                     │  │  _lote()         │  │  │
│  │  │ 5 años historia     │  │ detectar_outliers_  │  │ obtener_series_  │  │  │
│  │  │ ~1255 dias/activo   │  │  zscore() O(n)      │  │  alineadas()     │  │  │
│  │  │                     │  │  z=(x-μ)/σ >3.5     │  │  interseccion de │  │  │
│  │  │ Yahoo Finance API   │  │                     │  │  calendarios     │  │  │
│  │  │ v8 (sin yfinance)   │  │ limpiar_dataset()   │  │                  │  │  │
│  │  └─────────────────────┘  └─────────────────────┘  └──────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                              ▲ llamadas Python directas                         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  CAPA 5 — CONFIGURACION Y REPORTES                                        │  │
│  │                                                                           │  │
│  │  config.py              main.py               reportes/generador.py      │  │
│  │  20 activos             pipeline_etl()        generar_reporte_html()     │  │
│  │  FECHA_INICIO/FIN       pipeline_similitud()  Portada + 7 secciones      │  │
│  │  VENTANA=20 dias        pipeline_volatilidad()5 graficos SVG inline      │  │
│  │  DIAS_VOL=30            pipeline_ordenamiento()Exportable a PDF          │  │
│  │  DB_CONFIG              iniciar_api()                                    │  │
│  │  API_PORT=8001                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                              │ psycopg2 TCP:5432                                │
└──────────────────────────────┼──────────────────────────────────────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │  bvc_db              │
                    │  PostgreSQL 15       │
                    │  bvc_analytics DB    │
                    └──────────────────────┘
```


---

## NIVEL 4 — Diagrama de Flujo de Datos (Codigo)

Muestra el recorrido completo de los datos desde la fuente hasta la visualizacion.

```
Yahoo Finance API v8
https://query1.finance.yahoo.com/v8/finance/chart/{ticker}
?period1=UNIX_TS&period2=UNIX_TS&interval=1d&events=history
        │
        │  urllib.request.urlopen() — 3 reintentos — 1s pausa entre activos
        │  Respuesta: JSON crudo con timestamps Unix + arrays OHLCV
        ▼
etl/descargador.py — descargar_ticker()
  Construye URL: urllib.parse.urlencode()
  Parsea JSON:   json.loads(resp.read().decode("utf-8"))
  Convierte ts:  datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
  Retorna:       List[Dict{fecha, apertura, maximo, minimo, cierre, volumen}]
        │
        │  ~1,255 filas × 20 activos = ~25,100 filas crudas
        ▼
etl/limpieza.py — limpiar_dataset()
  1. sorted() por fecha ASC
  2. Elimina cierres <= 0
  3. interpolar_linealmente() O(n):
       V[k] = V[izq] + (V[der]-V[izq]) * (k-izq) / (der-izq)
  4. detectar_outliers_zscore() O(n):
       z = (x - media) / std  →  descarta si |z| > 3.5
  5. Rellena volumen None con 0
  Retorna: List[Dict] limpio, ordenado, sin Nones
        │
        │  ~25,100 filas limpias
        ▼
etl/database.py — insertar_precios_lote()
  psycopg2.executemany()
  INSERT INTO precios ... ON CONFLICT (activo_id, fecha) DO NOTHING
  Idempotente: se puede ejecutar multiples veces sin duplicar
        │
        │  PostgreSQL 15 — tabla precios (~25,100 registros)
        ▼
        ├─────────────────────────────────────────────────────────────────┐
        │                                                                 │
        ▼                                                                 ▼
etl/database.py                                           etl/database.py
obtener_series_alineadas(tickers)                         obtener_precios(ticker)
  1. {ticker: {fecha: cierre}} para cada ticker            Serie de cierre por ticker
  2. Interseccion de fechas: set1 & set2 & ... & set20     Ordenada por fecha ASC
  3. ~1,272 dias comunes
  4. Dict{ticker: List[float]} — igual longitud
        │                                                                 │
        ▼                                                                 ▼
algoritmos/similitud.py                           algoritmos/volatilidad.py
  distancia_euclidiana() O(n)                       calcular_retornos_log() O(n)
    normalizar_minmax() + sqrt(sum((a-b)^2))          r_i = ln(P_i / P_{i-1})
  correlacion_pearson() O(n)                        calcular_volatilidad() O(n)
    r = cov(A,B) / (std_A * std_B)                   s2 = sum((r-r_media)^2)/(k-1)
  similitud_coseno() O(n)                             sigma_anual = sqrt(s2) * sqrt(252)
    cos = (A·B) / (||A|| * ||B||)                  calcular_var_historico() O(n logn)
  dtw() O(n^2) + Sakoe-Chiba 10%                     sorted(retornos)[int(0.05*n)]
    D[i][j] = |A[i]-B[j]| + min(D[i-1][j],         calcular_sharpe() O(n)
               D[i][j-1], D[i-1][j-1])               (R_activo - 0.05) / sigma_anual
  190 pares C(20,2) × 4 algoritmos = 760 resultados calcular_max_drawdown() O(n)
        │                                             (valle - pico) / pico * 100
        ▼                                                                 │
etl/database.py                                                           │
guardar_similitud() → tabla resultados_similitud                          │
guardar_volatilidad() → tabla resultados_volatilidad ◄────────────────────┘
        │
        │
        ▼
algoritmos/patrones.py
  detectar_patrones() O(n·k)  k=20 dias
    Para i en [0, n-k]:
      segmento = precios[i:i+k]
      Patron 1 — N_dias_alza:  dias_alza/(k-1) >= 0.75
      Patron 2 — rebote:       primera_mitad_baja AND segunda_mitad_sube
  detectar_picos_valles() O(n)
  media_movil_simple() O(n·k)
  detectar_cruces_medias() O(n·k)  Golden/Death Cross SMA10 vs SMA30

algoritmos/ordenamiento.py
  ejecutar_benchmark() — 12 algoritmos sobre n=5000 registros
  top15_mayor_volumen() — HeapSort sobre dataset completo
  → tabla resultados_sorting, tabla top_volumen
        │
        │  Todos los resultados en PostgreSQL
        ▼
api/server.py — BVCHandler(BaseHTTPRequestHandler)
  ThreadingHTTPServer("0.0.0.0", 8001)
  Routing manual: dict{ruta: handler_method}
  Respuestas: json.dumps() + headers CORS
        │
        │  JSON responses via HTTP
        ▼
interfaz/index.html — SPA JavaScript vanilla
  fetch(API + "/endpoint") → JSON → render SVG/Canvas
  ┌──────────────────────────────────────────────────────────────────┐
  │  Overview:         KPIs + sparklines 20 activos + heatmap mini  │
  │  Portafolio:       20 graficos precio historico con filtros      │
  │  Comparar Activos: lineas % cambio + 4 valores similitud         │
  │  Mapa de Calor:    SVG 20x20 Pearson con tooltip                 │
  │  Patrones:         ventana deslizante + Golden/Death Cross        │
  │  Riesgo:           ranking 20 activos por volatilidad            │
  │  Ordenamiento:     tabla benchmark + barras SVG                  │
  │  Velas OHLC:       Canvas 2D + SMA configurable                  │
  │  Reporte/PDF:      portada + 7 secciones + 5 graficos SVG        │
  │  Tasa USD/COP:     conversor en tiempo real                      │
  └──────────────────────────────────────────────────────────────────┘
```

---

## Schema de Base de Datos

```
PostgreSQL 15 — bvc_analytics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

activos                              precios
─────────────────────────            ──────────────────────────────────────
id       SERIAL PK              ◄──  activo_id  INTEGER FK → activos.id
ticker   VARCHAR(10) UNIQUE          fecha      DATE NOT NULL
nombre   VARCHAR(100)                apertura   NUMERIC(12,4)
tipo     VARCHAR(20)                 maximo     NUMERIC(12,4)
mercado  VARCHAR(20)                 minimo     NUMERIC(12,4)
                                     cierre     NUMERIC(12,4) NOT NULL
                                     volumen    BIGINT
                                     UNIQUE(activo_id, fecha)
                                     INDEX(activo_id, fecha DESC)

resultados_similitud                 resultados_volatilidad
──────────────────────────────────   ──────────────────────────────────────
id           SERIAL PK               id            SERIAL PK
activo1_id   INTEGER FK              activo_id     INTEGER FK → activos.id
activo2_id   INTEGER FK              fecha         DATE
algoritmo    VARCHAR(20)             ventana_dias  INTEGER
  pearson|coseno|euclidiana|dtw      volatilidad   NUMERIC(12,6)
valor        NUMERIC(10,6)           retorno_medio NUMERIC(12,6)
calculado_en TIMESTAMP               calculado_en  TIMESTAMP
                                     UNIQUE(activo_id, fecha, ventana_dias)

resultados_sorting                   top_volumen
──────────────────────────────────   ──────────────────────────────────────
id           SERIAL PK               id       SERIAL PK
algoritmo    VARCHAR(50)             ticker   VARCHAR(10)
complejidad  VARCHAR(20)             fecha    DATE
tamanio      INTEGER                 volumen  BIGINT
tiempo_ms    NUMERIC(12,6)           cierre   NUMERIC(12,4)
calculado_en TIMESTAMP               calculado_en TIMESTAMP
```

---

## Despliegue en Produccion

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INFRAESTRUCTURA DE PRODUCCION                                              │
│                                                                             │
│  Proveedor:  Contabo VPS                                                    │
│  SO:         Ubuntu 24.04 LTS (GNU/Linux 6.8.0-100-generic x86_64)         │
│  IP:         38.242.225.58                                                  │
│  Dominio:    bvc.andresdiazd.com                                            │
│  URL:        https://bvc.andresdiazd.com                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  NGINX (reverse proxy)                                              │   │
│  │  /etc/nginx/sites-available/bvc.andresdiazd.com                    │   │
│  │                                                                     │   │
│  │  server {                                                           │   │
│  │      listen 80;                                                     │   │
│  │      server_name bvc.andresdiazd.com;                               │   │
│  │      location / {                                                   │   │
│  │          proxy_pass http://localhost:8001;                          │   │
│  │          proxy_set_header Host $host;                               │   │
│  │      }                                                              │   │
│  │  }                                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Directorio: /opt/bvc-analytics/                                            │
│  Compose:    /opt/bvc-analytics/docker-compose.yml                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Comandos de despliegue

```bash
# Conectarse al VPS
ssh root@38.242.225.58

# Ir al directorio del proyecto
cd /opt/bvc-analytics

# Actualizar codigo desde la maquina local (ejecutar en PC local)
scp -r interfaz/index.html root@38.242.225.58:/opt/bvc-analytics/interfaz/
scp -r reportes/generador.py root@38.242.225.58:/opt/bvc-analytics/reportes/

# Reconstruir imagen y reiniciar (en el VPS)
docker compose up -d --build --no-deps bvc_api

# Verificar estado
docker ps --filter "name=bvc"
docker logs bvc_api --tail 20

# Ejecutar pipelines (primera vez o actualizacion de datos)
docker exec bvc_api python main.py etl           # ~10 min
docker exec bvc_api python main.py similitud     # ~5 min
docker exec bvc_api python main.py volatilidad   # ~1 min
docker exec bvc_api python main.py ordenamiento  # ~3 min
```

### Variables de entorno en produccion

| Variable | Valor | Descripcion |
|---|---|---|
| `DB_HOST` | `bvc_db` | Nombre del servicio PostgreSQL en Docker |
| `DB_PORT` | `5432` | Puerto PostgreSQL |
| `DB_NAME` | `bvc_analytics` | Nombre de la base de datos |
| `DB_USER` | `bvc_user` | Usuario PostgreSQL |
| `DB_PASSWORD` | `[secreto]` | Contrasena PostgreSQL |
| `API_HOST` | `0.0.0.0` | Escucha en todas las interfaces |
| `API_PORT` | `8001` | Puerto del servidor HTTP |

---

## Decisiones de Arquitectura

| Decision | Alternativa descartada | Justificacion |
|---|---|---|
| `http.server` stdlib | Flask / FastAPI / Django | El enunciado prohibe frameworks externos |
| `urllib.request` | `requests` / `yfinance` | El enunciado prohibe librerias de alto nivel para descarga |
| `psycopg2` puro | SQLAlchemy / Django ORM | Driver minimo sin abstraccion que oculte el SQL |
| SVG inline en Python | matplotlib / plotly / Chart.js | Sin dependencias externas para graficos |
| HTML5 + JS vanilla | React / Vue / Angular | Sin frameworks de frontend |
| PostgreSQL 15 | SQLite / MySQL | Soporte nativo DATE, NUMERIC, concurrencia, indices |
| Docker Compose | Despliegue directo | Reproducibilidad garantizada, aislamiento de dependencias |
| Nginx reverse proxy | Exponer :8001 directamente | Permite SSL, dominio personalizado, headers HTTP correctos |
| Ventana Sakoe-Chiba 10% en DTW | DTW completo O(n^2) | Reduce complejidad practica a O(n*0.1n) sin perder precision |
| Correccion de Bessel (k-1) | Varianza poblacional (k) | Estimador insesgado de la varianza para muestras finitas |
| Factor sqrt(252) para volatilidad | sqrt(365) | 252 = dias bursatiles reales en un ano (sin fines de semana ni festivos) |
| Umbral Z-Score 3.5 | Umbral estandar 3.0 | En finanzas los movimientos extremos son legitimos (fat tails) |
| Interseccion de calendarios | Union o padding | Garantiza que cada posicion i corresponde al mismo dia en todos los activos |

---

## Restricciones Tecnicas — Todas Cumplidas

| Restriccion del enunciado | Estado | Evidencia |
|---|---|---|
| Sin yfinance ni pandas_datareader | CUMPLE | `urllib.request` + `json.loads()` manual |
| Sin pandas, numpy, scipy, sklearn | CUMPLE | `requirements.txt`: solo `psycopg2-binary==2.9.9` |
| Sin frameworks web | CUMPLE | `http.server` stdlib puro |
| Sin librerias de graficos | CUMPLE | SVG puro en Python + Canvas 2D API en JS |
| Algoritmos implementados desde cero | CUMPLE | Bucles Python, sin funciones de alto nivel |
| Datos obtenidos automaticamente | CUMPLE | `python main.py etl` descarga desde cero |
| Reproducibilidad garantizada | CUMPLE | `docker compose up -d` + pipelines automatizados |
| Formulas matematicas documentadas | CUMPLE | Docstrings con notacion matematica en cada funcion |
| Complejidades explicitas | CUMPLE | O(n), O(n^2), O(n*k), O(n log n) en cada algoritmo |
| Patrones adicionales formalizados | CUMPLE | Rebote V-shape con formula matematica explicita |
| Despliegue web funcional | CUMPLE | https://bvc.andresdiazd.com |

---

## Resumen de los 28 Algoritmos Implementados

| Categoria | Algoritmo | Complejidad | Archivo |
|---|---|---|---|
| ETL | Interpolacion Lineal | O(n) | etl/limpieza.py |
| ETL | Deteccion Outliers Z-Score | O(n) | etl/limpieza.py |
| Similitud | Distancia Euclidiana | O(n) | algoritmos/similitud.py |
| Similitud | Correlacion de Pearson | O(n) | algoritmos/similitud.py |
| Similitud | Similitud por Coseno | O(n) | algoritmos/similitud.py |
| Similitud | Dynamic Time Warping | O(n^2) | algoritmos/similitud.py |
| Patrones | Ventana Deslizante | O(n·k) | algoritmos/patrones.py |
| Patrones | Deteccion Picos y Valles | O(n) | algoritmos/patrones.py |
| Patrones | Media Movil Simple (SMA) | O(n·k) | algoritmos/patrones.py |
| Patrones | Golden / Death Cross | O(n·k) | algoritmos/patrones.py |
| Volatilidad | Retornos Logaritmicos | O(n) | algoritmos/volatilidad.py |
| Volatilidad | Volatilidad Historica Anualizada | O(n) | algoritmos/volatilidad.py |
| Volatilidad | Maximo Drawdown | O(n) | algoritmos/volatilidad.py |
| Volatilidad | VaR Historico 95% | O(n log n) | algoritmos/volatilidad.py |
| Volatilidad | Sharpe Ratio | O(n) | algoritmos/volatilidad.py |
| Ordenamiento | TimSort | O(n log n) | algoritmos/ordenamiento.py |
| Ordenamiento | Comb Sort | O(n log n) | algoritmos/ordenamiento.py |
| Ordenamiento | Selection Sort | O(n^2) | algoritmos/ordenamiento.py |
| Ordenamiento | Tree Sort | O(n log n) | algoritmos/ordenamiento.py |
| Ordenamiento | Pigeonhole Sort | O(n + k) | algoritmos/ordenamiento.py |
| Ordenamiento | Bucket Sort | O(n + k) | algoritmos/ordenamiento.py |
| Ordenamiento | QuickSort | O(n log n) | algoritmos/ordenamiento.py |
| Ordenamiento | HeapSort | O(n log n) | algoritmos/ordenamiento.py |
| Ordenamiento | Bitonic Sort | O(n log^2 n) | algoritmos/ordenamiento.py |
| Ordenamiento | Gnome Sort | O(n^2) | algoritmos/ordenamiento.py |
| Ordenamiento | Binary Insertion Sort | O(n^2) | algoritmos/ordenamiento.py |
| Ordenamiento | RadixSort | O(nk) | algoritmos/ordenamiento.py |

---

*Universidad del Quindio — Analisis de Algoritmos — 2026-1*
*Sarita Londono Perdomo · Eyner Andres Diaz Diaz*
*Desplegado en: https://bvc.andresdiazd.com*
