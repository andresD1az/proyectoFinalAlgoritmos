# BVC Analytics

Plataforma de análisis financiero cuantitativo sobre datos históricos de la Bolsa de Valores de Colombia (BVC) y ETFs globales.

Proyecto académico — Universidad del Quindío  
Ingeniería de Sistemas y Computación — Análisis de Algoritmos

**Restricción académica:** cero uso de pandas, numpy, scipy, sklearn, yfinance o equivalentes.  
Solo Python 3.11 stdlib + psycopg2-binary como driver de BD.

---

## Demo en producción

```
https://bvc-analytics-api.onrender.com
```

---

## Stack

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.11 (stdlib pura para toda la lógica) |
| Base de datos | PostgreSQL 15 |
| Servidor HTTP | `http.server` (stdlib) |
| Frontend | HTML5 + CSS3 + JS vanilla (SVG + Canvas API) |
| Driver BD | psycopg2-binary (única dependencia externa) |
| Despliegue | Render (Python nativo) |

---

## Cómo ejecutar

### Local con Docker

```bash
cp .env.example .env
# edita .env con tus credenciales
docker compose -f docker-compose.local.yml up --build
```

### Local sin Docker

```bash
pip install -r requirements.txt
cp .env.example .env
psql -U postgres -f database/init.sql
python main.py etl        # descarga y carga datos
python main.py api        # inicia servidor en :8001
```

### Comandos disponibles

```bash
python main.py etl            # ETL completo
python main.py similitud      # 4 algoritmos de similitud
python main.py volatilidad    # métricas de riesgo
python main.py ordenamiento   # benchmark 12 algoritmos
python main.py api            # servidor HTTP en :8001
python main.py todo           # todo en secuencia
```

---

## Activos analizados (20, 5 años de historia)

| Ticker | Nombre | Tipo |
|---|---|---|
| EC | Ecopetrol S.A. | Acción NYSE |
| CIB | Bancolombia S.A. | Acción NYSE |
| GXG | iShares MSCI Colombia | ETF NYSE |
| ILF | iShares Latin America 40 | ETF NYSE |
| EWZ | iShares MSCI Brazil | ETF NYSE |
| EWW | iShares MSCI Mexico | ETF NYSE |
| SPY | S&P 500 ETF | ETF NYSE |
| QQQ | Nasdaq 100 ETF | ETF NASDAQ |
| DIA | Dow Jones ETF | ETF NYSE |
| EEM | Emerging Markets ETF | ETF NYSE |
| VT | Vanguard Total World | ETF NYSE |
| IEMG | Core Emerging Markets | ETF NYSE |
| GLD | SPDR Gold Shares | ETF NYSE |
| SLV | iShares Silver Trust | ETF NYSE |
| USO | US Oil Fund | ETF NYSE |
| TLT | iShares 20Y Treasury | ETF NASDAQ |
| XLE | Energy Select Sector | ETF NYSE |
| XLF | Financial Select Sector | ETF NYSE |
| XLK | Technology Select Sector | ETF NYSE |
| VNQ | Vanguard Real Estate | ETF NYSE |

---

## Requerimiento 1 — ETL automatizado (`etl/`)

El pipeline descarga, limpia y carga datos sin ninguna librería de alto nivel.

### Descarga (`etl/downloader.py`)

Peticiones HTTP directas con `urllib.request` a la API pública de Yahoo Finance. Por cada ticker construye la URL manualmente con los timestamps Unix del rango de 5 años, parsea la respuesta JSON con `json.loads()` de stdlib y convierte los timestamps a fechas con `datetime.fromtimestamp()`. Implementa 3 reintentos con backoff exponencial ante errores de red.

### Limpieza (`etl/cleaner.py`)

**Interpolación lineal** — O(n)  
Rellena valores `None` entre dos puntos conocidos:
```
V[i] = V[izq] + (V[der] - V[izq]) × (i - izq) / (der - izq)
```

**Detección de outliers Z-Score** — O(n)  
Calcula media y desviación estándar muestral de la serie, descarta registros donde:
```
z = (x - μ) / σ    →    |z| > 3.5
```

### Almacenamiento (`etl/database.py`)

Inserta en PostgreSQL con `psycopg2` usando `executemany()` para lotes. Usa `ON CONFLICT DO NOTHING` para ser idempotente (se puede re-ejecutar sin duplicar datos). La función `init_schema()` crea todas las tablas al arrancar si no existen.

---

## Requerimiento 2 — Ordenamiento (`algorithms/sorting.py`)

Los 12 algoritmos ordenan el dataset unificado con criterio compuesto:
- Primario: `fecha ASC` (string ISO, comparable lexicográficamente)
- Secundario: `cierre ASC` (float)

Ninguno usa `sorted()` ni `.sort()`. Cada función retorna `(lista_ordenada, tiempo_segundos)` medido con `time.perf_counter()`.

### 1. TimSort — O(n log n)

Divide el arreglo en bloques de 32 elementos (`RUN = 32`), los ordena con Insertion Sort, luego los fusiona con Merge Sort duplicando el tamaño del bloque en cada pasada. Es el algoritmo interno de Python, pero aquí implementado explícitamente.

### 2. Comb Sort — O(n log n)

Mejora de Bubble Sort. En lugar de comparar elementos adyacentes, usa una brecha (`gap`) que empieza en `n` y se reduce con factor `1.3` en cada pasada. Elimina eficientemente los "tortugas" (valores pequeños atrapados al final). Cuando `gap` llega a 1, hace una pasada final de Bubble Sort.

### 3. Selection Sort — O(n²)

En cada iteración `i`, recorre `arr[i..n-1]` para encontrar el mínimo y lo intercambia con `arr[i]`. Siempre hace exactamente `n(n-1)/2` comparaciones sin importar el estado inicial del arreglo.

### 4. Tree Sort — O(n log n) promedio

Inserta cada registro en un Árbol Binario de Búsqueda (BST) manual con nodos `_NodoBST`. El recorrido in-orden (izquierda → raíz → derecha) produce los elementos en orden ascendente. Peor caso O(n²) si el árbol degenera (datos ya ordenados).

### 5. Pigeonhole Sort — O(n + k)

Convierte cada fecha a entero `YYYYMMDD` y crea un "palomar" (lista) por cada valor entero en el rango `[min_fecha, max_fecha]`. Distribuye los registros en sus palomares y los concatena. Dentro de cada palomar (misma fecha) ordena por cierre con Insertion Sort. Eficiente porque `k ≈ 1826 días` y `n ≈ 25200 registros`.

### 6. Bucket Sort — O(n + k)

Normaliza la fecha al rango `[0, 1]` y distribuye los registros en `n` cubetas según esa normalización. Cada cubeta se ordena internamente con Insertion Sort. Eficiente cuando los datos están distribuidos uniformemente en el rango.

### 7. QuickSort — O(n log n) promedio

Partición de Lomuto con pivote **mediana-de-tres** (compara primero, medio y último elemento para elegir el pivote). Esto evita el peor caso O(n²) en datos ya ordenados. Recursión sobre ambas mitades del arreglo.

### 8. HeapSort — O(n log n)

**Fase 1 — Build Max-Heap:** convierte el arreglo en un max-heap de abajo hacia arriba en O(n). El nodo `i` tiene hijos en `2i+1` y `2i+2`.  
**Fase 2 — Extract:** intercambia la raíz (máximo) con el último elemento, reduce el tamaño del heap en 1 y restaura la propiedad heap con `_heapify()`. Repite n veces → O(n log n).

### 9. Bitonic Sort — O(n log²n)

Requiere que `n` sea potencia de 2. Si no lo es, rellena con un centinela `{"fecha": "9999-99-99"}` y lo elimina al final. Genera secuencias bitónicas (primero creciente, luego decreciente) recursivamente y las fusiona. Diseñado para hardware paralelo (GPU/FPGA), aquí implementado secuencialmente.

### 10. Gnome Sort — O(n²)

El "gnomo" avanza si `arr[i] >= arr[i-1]`, retrocede e intercambia si `arr[i] < arr[i-1]`. Sin bucle interno explícito. Equivalente a Insertion Sort pero con un solo índice que sube y baja.

### 11. Binary Insertion Sort — O(n²)

Mejora Insertion Sort usando **búsqueda binaria** para encontrar la posición de inserción correcta en O(log n) comparaciones en lugar de O(n). Sin embargo, el desplazamiento de elementos sigue siendo O(n), por lo que la complejidad total permanece en O(n²). Reduce el número de comparaciones a la mitad en promedio.

### 12. RadixSort — O(nk)

Ordena por la clave entera `YYYYMMDD` (8 dígitos, `k=8`). Aplica **Counting Sort estable** dígito a dígito del menos al más significativo (LSD). El Counting Sort estable garantiza que el orden de pasadas anteriores se preserve. Después de ordenar por fecha, aplica Insertion Sort dentro de cada grupo de misma fecha para el criterio secundario (cierre).

### Benchmark

`ejecutar_benchmark()` ejecuta los 12 algoritmos sobre el dataset completo y retorna la Tabla 1 ordenada por tiempo ascendente. `top15_mayor_volumen()` usa HeapSort manual para extraer los 15 días con mayor volumen en O(n log n).

---

## Requerimiento 3 — Similitud (`algorithms/similarity.py`)

Compara pares de series de precios de cierre. Antes de calcular distancias, normaliza con **Min-Max Scaling** cuando las escalas difieren (ej. EC en USD vs SPY en USD pero rangos distintos):
```
x_norm = (x - min) / (max - min)
```

### Distancia Euclidiana — O(n)

Trata cada serie como un vector en ℝⁿ y mide la distancia geométrica:
```
d(A, B) = √( Σᵢ (Aᵢ - Bᵢ)² )
```
Valor 0 = series idénticas. Mayor valor = más diferentes. Requiere normalización previa.

### Correlación de Pearson — O(n)

Mide la relación lineal entre dos series. No requiere normalización porque trabaja con desviaciones respecto a la media:
```
r = Σ((Aᵢ - Ā)(Bᵢ - B̄)) / √(Σ(Aᵢ - Ā)² · Σ(Bᵢ - B̄)²)
```
Rango [-1, 1]. `r = 1` correlación perfecta positiva, `r = -1` inversa perfecta, `r = 0` sin relación lineal.

### Similitud por Coseno — O(n)

Mide el ángulo entre dos vectores. Invariante a la magnitud (escala de precios):
```
cos(θ) = (A · B) / (‖A‖ · ‖B‖) = Σ(Aᵢ·Bᵢ) / (√Σ(Aᵢ²) · √Σ(Bᵢ²))
```
Útil cuando importa la dirección del movimiento, no la magnitud.

### DTW — Dynamic Time Warping — O(n²)

Alinea dos series temporales que pueden estar desfasadas en el tiempo. Llena una matriz de programación dinámica donde `matriz[i][j]` es el costo mínimo de alinear `A[0..i]` con `B[0..j]`:
```
matriz[i][j] = |A[i] - B[j]| + min(matriz[i-1][j], matriz[i][j-1], matriz[i-1][j-1])
```
Optimizado con **ventana de Sakoe-Chiba** (10% de la longitud) para reducir el costo de O(n²) a O(n·k).

La función `matriz_similitud()` calcula todos los pares posibles entre los 20 activos (190 pares) para un algoritmo dado.

---

## Requerimiento 4 — Patrones y Volatilidad

### Patrones (`algorithms/patterns.py`)

**Ventana deslizante — O(n·k)**  
Recorre la serie con una ventana de 20 días (configurable). Para cada segmento cuenta días de alza y baja:
- Si ≥75% días positivos → `N_dias_alza`
- Si ≥75% días negativos → `N_dias_baja`
- Si primera mitad baja y segunda sube → `rebote`
- Caso contrario → `neutro`

Solo guarda patrones no neutros o con variación porcentual ≥1%.

**Detección de picos y valles — O(n)**  
Un punto `i` es pico si `precios[i] > precios[j]` para todo `j` en una vecindad de ±3 días. Análogo para valles.

**Media Móvil Simple (SMA) — O(n·k)**  
```
SMA[i] = (P[i] + P[i-1] + ... + P[i-k+1]) / k
```
Implementada de forma directa (sin suma rodante) para mayor claridad académica.

**Golden/Death Cross — O(n)**  
Calcula SMA corta (10 días) y SMA larga (30 días). Detecta cruces:
- Golden Cross: SMA corta pasa de debajo a arriba de SMA larga → señal alcista
- Death Cross: SMA corta pasa de arriba a abajo → señal bajista

### Volatilidad y Riesgo (`algorithms/volatility.py`)

**Retornos logarítmicos — O(n)**
```
rᵢ = ln(Pᵢ / Pᵢ₋₁)
```
Preferidos sobre retornos simples porque son aditivos en el tiempo y tienen distribución más cercana a la normal.

**Volatilidad histórica — O(n)**  
Desviación estándar muestral de los retornos en ventana de 30 días, anualizada:
```
σ_anual = σ_diaria × √252
```
Usa corrección de Bessel (denominador `k-1`) para estimación insesgada.

**Máximo Drawdown — O(n)**  
Mantiene el pico máximo visto hasta cada punto y calcula la caída:
```
MDD = (valle - pico) / pico × 100
```
Recorre la serie una sola vez.

**VaR Histórico (95%) — O(n log n)**  
Ordena todos los retornos logarítmicos ascendentemente y toma el percentil 5%:
```
VaR₀.₉₅ = retorno en el percentil 5 de la distribución histórica
```
Interpretación: "Solo en el 5% de los días la pérdida supera este valor."

**Sharpe Ratio — O(n)**
```
Sharpe = (R_portfolio - R_libre_riesgo) / σ_portfolio
```
Donde `R_portfolio` es el retorno anualizado y `σ_portfolio` la volatilidad anualizada. Tasa libre de riesgo: 5% anual. Sharpe > 1 indica buena relación riesgo/retorno.

**Clasificación de riesgo — O(1)**  
Basada en la volatilidad anualizada:
- Conservador: σ < 15%
- Moderado: 15% ≤ σ < 30%
- Agresivo: σ ≥ 30%

---

## API — Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del sistema |
| GET | `/activos` | Catálogo de 20 activos |
| GET | `/precios?ticker=SPY` | Precios históricos |
| GET | `/precios/ohlcv?ticker=SPY` | Datos OHLCV completos |
| GET | `/similitud?algoritmo=pearson` | Resultados de similitud |
| GET | `/volatilidad?ticker=SPY` | Métricas de riesgo |
| GET | `/patrones?ticker=SPY` | Patrones detectados |
| GET | `/patrones/cruces?ticker=SPY&corta=10&larga=30` | Golden/Death Cross |
| GET | `/riesgo/clasificacion` | Ranking de riesgo de los 20 activos |
| GET | `/correlacion/matriz` | Matriz de correlación 20×20 |
| GET | `/ordenamiento/benchmark` | Tabla 1: tiempos de los 12 algoritmos |
| GET | `/ordenamiento/top-volumen` | Top-15 días con mayor volumen |
| GET | `/ordenamiento/dataset?algoritmo=quicksort` | Dataset ordenado |
| GET | `/reporte` | Reporte técnico completo (JSON) |
| GET | `/etl/status` | Registros en BD |
| POST | `/etl/iniciar` | Dispara el ETL en segundo plano |
| POST | `/auth/register` | Registro de usuario |
| POST | `/auth/login` | Inicio de sesión |
| GET | `/simulador/portafolio` | Portafolio virtual (paper trading) |
| POST | `/simulador/comprar` | Comprar activo |
| POST | `/simulador/vender` | Vender activo |
| GET | `/monedas/tasa` | Tasa USD/COP en tiempo real |
| GET | `/academia/lecciones` | Lecciones financieras |

---

## Variables de entorno

```env
# Render provee DATABASE_URL automáticamente
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Para desarrollo local
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bvc_analytics
DB_USER=bvc_user
DB_PASSWORD=tu_password
API_HOST=0.0.0.0
API_PORT=8001
```

---

## Estructura del proyecto

```
bvc-analytics/
├── etl/
│   ├── downloader.py       # HTTP pura con urllib, 3 reintentos
│   ├── cleaner.py          # Interpolación lineal + Z-Score
│   └── database.py         # CRUD PostgreSQL + init_schema()
├── algorithms/
│   ├── sorting.py          # 12 algoritmos de ordenamiento
│   ├── similarity.py       # 4 algoritmos de similitud
│   ├── patterns.py         # Ventana deslizante + Golden/Death Cross
│   └── volatility.py       # VaR, Sharpe, Drawdown, volatilidad
├── api/server.py           # Servidor HTTP con 25+ endpoints
├── auth/auth.py            # SHA-256 + salt + sesiones
├── cms/content.py          # Lecciones + paper trading
├── reports/generator.py    # Reportes JSON y texto plano
├── frontend/index.html     # SPA completa sin frameworks
├── database/init.sql       # Schema PostgreSQL
├── main.py                 # Orquestador de pipelines
├── config.py               # 20 activos + parámetros
├── render.yaml             # Despliegue nativo Render
└── requirements.txt        # psycopg2-binary==2.9.9
```

---

## Declaración de uso de IA

Este proyecto utilizó herramientas de inteligencia artificial generativa (Kiro/Claude) como apoyo en el desarrollo. El diseño algorítmico, la formulación matemática, la implementación explícita de cada algoritmo y el análisis de complejidad fueron realizados y verificados por los estudiantes. Las herramientas de IA se usaron como soporte de codificación y revisión, no como sustituto del análisis formal requerido por el curso.

---

*Universidad del Quindío — Análisis de Algoritmos — 2025*
