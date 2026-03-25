# Seguimiento 1 — BVC Analytics

**Universidad del Quindío**  
**Programa de Ingeniería de Sistemas y Computación**  
**Análisis de Algoritmos — Proyecto Final**

---

## Verificación de cumplimiento con el enunciado

### Restricciones generales

| Restricción | Estado | Evidencia |
|---|---|---|
| Sin yfinance ni pandas_datareader | CUMPLE | `requirements.txt` solo tiene `psycopg2-binary==2.9.9`. Descarga via `urllib.request` directo. |
| Sin pandas, numpy, scipy, sklearn | CUMPLE | Ningún import de estas librerías en todo el proyecto. |
| Sin datasets estáticos | CUMPLE | Los datos se descargan en tiempo de ejecución con `python main.py etl`. |
| Algoritmos implementados explícitamente | CUMPLE | Cada algoritmo tiene su lógica completa en código, sin llamadas a funciones de alto nivel. |
| Reproducibilidad | CUMPLE | `python main.py etl` reconstruye el dataset desde cero. |
| Declaración de uso de IA | CUMPLE | Declarada en `README.md` y en este documento. |

---

## Requerimiento 1 — ETL automatizado

**Veredicto: CUMPLE**

### Dónde está

| Componente | Archivo |
|---|---|
| Descarga HTTP | `etl/downloader.py` |
| Limpieza de datos | `etl/cleaner.py` |
| Almacenamiento PostgreSQL | `etl/database.py` |
| Orquestación del pipeline | `main.py` → `pipeline_etl()` |
| Schema de la BD | `database/init.sql` |
| Configuración de activos | `config.py` |

### Cómo funciona

**Descarga (`etl/downloader.py`)**

Se construye la URL de Yahoo Finance manualmente con `urllib.parse.urlencode()`:

```
https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?period1=...&period2=...&interval=1d
```

Los parámetros `period1` y `period2` son Unix timestamps calculados con `datetime.timestamp()`. La respuesta JSON se parsea con `json.loads()` de stdlib. Los timestamps Unix de cada día se convierten a fecha con `datetime.utcfromtimestamp()`. Se implementan 3 reintentos con pausa de 1 segundo entre peticiones para no ser bloqueado.

**Activos descargados (20):**  
EC, CIB, GXG, ILF, EWZ, EWW, SPY, QQQ, DIA, EEM, VT, IEMG, GLD, SLV, USO, TLT, XLE, XLF, XLK, VNQ

**Horizonte:** 5 años (`FECHA_INICIO = datetime.today() - timedelta(days=5*365)`)

**Campos por registro:** fecha, apertura, maximo, minimo, cierre, volumen — todos los requeridos por el enunciado.

**Limpieza (`etl/cleaner.py`)**

Algoritmo 1 — Interpolación lineal — O(n):
```
V[i] = V[izq] + (V[der] - V[izq]) × (i - izq) / (der - izq)
```
Rellena valores `None` entre dos puntos conocidos. Si hay `None` al inicio usa backward fill; al final usa forward fill. Esto maneja diferencias de calendarios bursátiles entre mercados (NYSE vs NASDAQ vs días festivos).

Algoritmo 2 — Detección de outliers Z-Score — O(n):
```
z = (x - μ) / σ    →    descarta si |z| > 3.5
```
Calcula media y desviación estándar muestral manualmente. El umbral 3.5 es más conservador que el estándar (3.0) para no eliminar movimientos extremos legítimos en mercados financieros.

**Almacenamiento (`etl/database.py`)**

- Tabla `activos`: catálogo de los 20 instrumentos con ticker, nombre, tipo, mercado.
- Tabla `precios`: datos OHLCV con `UNIQUE(activo_id, fecha)` para evitar duplicados.
- `ON CONFLICT DO NOTHING` hace el proceso idempotente (re-ejecutable sin duplicar).
- `executemany()` para inserción en lote eficiente.

---

## Requerimiento 2 — Algoritmos de ordenamiento

**Veredicto: CUMPLE**

### Dónde está

| Componente | Archivo |
|---|---|
| 12 algoritmos de ordenamiento | `algorithms/sorting.py` |
| Benchmark (Tabla 1) | `algorithms/sorting.py` → `ejecutar_benchmark()` |
| Top-15 mayor volumen | `algorithms/sorting.py` → `top15_mayor_volumen()` |
| Pipeline que lo ejecuta | `main.py` → `pipeline_ordenamiento()` |
| Endpoint API Tabla 1 | `api/server.py` → `GET /ordenamiento/benchmark` |
| Endpoint top-15 | `api/server.py` → `GET /ordenamiento/top-volumen` |
| Diagrama de barras | `frontend/index.html` (Canvas API) |

### Criterio de ordenamiento

Clave compuesta implementada en `_clave(registro)`:
- Primario: `fecha` como string ISO `YYYY-MM-DD` (comparable lexicográficamente)
- Secundario: `cierre` como float

Ningún algoritmo usa `sorted()` ni `.sort()` de Python. Cada uno retorna `(lista_ordenada, tiempo_segundos)` medido con `time.perf_counter()`.

### Los 12 algoritmos — cómo funciona cada uno

**1. TimSort — O(n log n)**  
Archivo: `algorithms/sorting.py` → `timsort()`  
Divide el arreglo en bloques de 32 elementos (`_TIM_RUN = 32`). Ordena cada bloque con Insertion Sort (`_insertion_run()`). Luego fusiona los bloques con Merge Sort (`_merge_tim()`), duplicando el tamaño del bloque en cada pasada. Es el algoritmo interno de Python, implementado aquí de forma explícita.

**2. Comb Sort — O(n log n)**  
Archivo: `algorithms/sorting.py` → `comb_sort()`  
Mejora de Bubble Sort. La brecha `gap` empieza en `n` y se reduce con factor `1.3` en cada pasada (`gap = int(gap / 1.3)`). Cuando `gap == 1` hace una pasada final de Bubble Sort. Elimina eficientemente los "tortugas" (valores pequeños atrapados al final del arreglo).

**3. Selection Sort — O(n²)**  
Archivo: `algorithms/sorting.py` → `selection_sort()`  
En cada iteración `i` recorre `arr[i..n-1]` para encontrar el índice del mínimo y lo intercambia con `arr[i]`. Siempre hace exactamente `n(n-1)/2` comparaciones sin importar el estado inicial.

**4. Tree Sort — O(n log n) promedio**  
Archivo: `algorithms/sorting.py` → `tree_sort()`, clase `_NodoBST`  
Inserta cada registro en un Árbol Binario de Búsqueda (BST) implementado con la clase `_NodoBST` (campos: `registro`, `izq`, `der`). El recorrido in-orden (`_bst_inorden()`) produce los elementos en orden ascendente. Peor caso O(n²) si el árbol degenera con datos ya ordenados.

**5. Pigeonhole Sort — O(n + k)**  
Archivo: `algorithms/sorting.py` → `pigeonhole_sort()`  
Convierte cada fecha a entero `YYYYMMDD`. Crea una lista de "palomares" de tamaño `max_fecha - min_fecha + 1`. Distribuye cada registro en su palomar según su fecha. Dentro de cada palomar (misma fecha) ordena por cierre con Insertion Sort. Para 5 años: `k ≈ 1826` y `n ≈ 25200`.

**6. Bucket Sort — O(n + k)**  
Archivo: `algorithms/sorting.py` → `bucket_sort()`  
Normaliza la fecha al rango `[0, 1]` y distribuye los registros en `n` cubetas. Cada cubeta se ordena con Insertion Sort. Eficiente cuando los datos están distribuidos uniformemente.

**7. QuickSort — O(n log n) promedio**  
Archivo: `algorithms/sorting.py` → `quicksort()`, `_quicksort_rec()`, `_particionar()`  
Partición de Lomuto con pivote **mediana-de-tres** (`_mediana_tres()`): compara el primero, el medio y el último elemento para elegir el pivote. Esto evita el peor caso O(n²) en datos ya ordenados. Recursión sobre ambas mitades.

**8. HeapSort — O(n log n)**  
Archivo: `algorithms/sorting.py` → `heapsort()`, `_heapify()`  
Fase 1: construye un max-heap de abajo hacia arriba en O(n). El nodo `i` tiene hijos en `2i+1` y `2i+2`. Fase 2: intercambia la raíz (máximo) con el último elemento, reduce el heap en 1 y restaura con `_heapify()`. Repite n veces.

**9. Bitonic Sort — O(n log²n)**  
Archivo: `algorithms/sorting.py` → `bitonic_sort()`, `_bitonic_sort_rec()`, `_bitonic_merge()`  
Requiere n potencia de 2. Si no, rellena con centinela `{"fecha": "9999-99-99", "cierre": inf}` y lo elimina al final. Genera secuencias bitónicas recursivamente y las fusiona. Diseñado para hardware paralelo, implementado aquí secuencialmente.

**10. Gnome Sort — O(n²)**  
Archivo: `algorithms/sorting.py` → `gnome_sort()`  
El índice `i` avanza si `arr[i] >= arr[i-1]`, retrocede e intercambia si `arr[i] < arr[i-1]`. Sin bucle interno explícito. Equivalente a Insertion Sort con un solo índice que sube y baja.

**11. Binary Insertion Sort — O(n²)**  
Archivo: `algorithms/sorting.py` → `binary_insertion_sort()`, `_busqueda_binaria_pos()`  
Usa búsqueda binaria (`_busqueda_binaria_pos()`) para encontrar la posición de inserción en O(log n) comparaciones. El desplazamiento de elementos sigue siendo O(n), por lo que la complejidad total es O(n²). Reduce el número de comparaciones a la mitad respecto a Insertion Sort clásico.

**12. RadixSort — O(nk)**  
Archivo: `algorithms/sorting.py` → `radix_sort()`, `_counting_sort_por_digito()`  
Ordena por la clave entera `YYYYMMDD` (8 dígitos, `k=8`). Aplica Counting Sort estable dígito a dígito del menos al más significativo (LSD). La estabilidad garantiza que el orden de pasadas anteriores se preserve. Después aplica Insertion Sort dentro de cada grupo de misma fecha para el criterio secundario (cierre).

### Tabla 1 — cómo se genera

`ejecutar_benchmark()` ejecuta los 12 algoritmos sobre el dataset completo, mide el tiempo con `time.perf_counter()` y retorna la lista ordenada por tiempo ascendente. Se persiste en la tabla `resultados_sorting` de PostgreSQL y se expone en `GET /ordenamiento/benchmark`.

### Top-15 mayor volumen

`top15_mayor_volumen()` usa un max-heap manual (HeapSort) para extraer los 15 registros con mayor volumen en O(n log n). Los reordena ASC por volumen para presentación. Se expone en `GET /ordenamiento/top-volumen`.

### Diagrama de barras

El frontend (`frontend/index.html`) consume `GET /ordenamiento/benchmark` y dibuja el diagrama de barras con Canvas API, ordenado ascendentemente por tiempo.

---

## Requerimiento 3 — Similitud entre activos

**Veredicto: CUMPLE**

### Dónde está

| Componente | Archivo |
|---|---|
| 4 algoritmos de similitud | `algorithms/similarity.py` |
| Matriz de similitud (190 pares) | `algorithms/similarity.py` → `matriz_similitud()` |
| Pipeline | `main.py` → `pipeline_similitud()` |
| Endpoint API | `api/server.py` → `GET /similitud` |
| Mapa de calor | `frontend/index.html` (SVG) |

### Los 4 algoritmos

**Distancia Euclidiana — O(n)**  
Función: `distancia_euclidiana()`  
Normaliza ambas series con Min-Max antes de calcular:
```
d(A, B) = √( Σᵢ (Aᵢ - Bᵢ)² )
```
Valor 0 = series idénticas. Requiere normalización porque compara activos con rangos de precios distintos.

**Correlación de Pearson — O(n)**  
Función: `correlacion_pearson()`  
No requiere normalización. Trabaja con desviaciones respecto a la media:
```
r = Σ((Aᵢ - Ā)(Bᵢ - B̄)) / √(Σ(Aᵢ - Ā)² · Σ(Bᵢ - B̄)²)
```
Rango [-1, 1]. Mide relación lineal entre series.

**Similitud por Coseno — O(n)**  
Función: `similitud_coseno()`  
Trata cada serie como vector en ℝⁿ. Invariante a la magnitud:
```
cos(θ) = (A · B) / (‖A‖ · ‖B‖)
```

**DTW — Dynamic Time Warping — O(n²)**  
Función: `dtw()`  
Programación dinámica. `matriz[i][j]` = costo mínimo de alinear `A[0..i]` con `B[0..j]`:
```
matriz[i][j] = |A[i] - B[j]| + min(arriba, izquierda, diagonal)
```
Optimizado con ventana de Sakoe-Chiba (10%) para reducir el costo real.

`matriz_similitud()` calcula los 190 pares posibles entre los 20 activos y los ordena por similitud descendente.

---

## Requerimiento 4 — Patrones y Volatilidad

**Veredicto: CUMPLE**

### Dónde está

| Componente | Archivo |
|---|---|
| Ventana deslizante + patrones | `algorithms/patterns.py` → `detectar_patrones()` |
| Picos y valles | `algorithms/patterns.py` → `detectar_picos_valles()` |
| Media Móvil Simple | `algorithms/patterns.py` → `media_movil_simple()` |
| Golden/Death Cross | `algorithms/patterns.py` → `detectar_cruces_medias()` |
| Retornos logarítmicos | `algorithms/volatility.py` → `calcular_retornos_log()` |
| Volatilidad histórica | `algorithms/volatility.py` → `calcular_volatilidad()` |
| Máximo Drawdown | `algorithms/volatility.py` → `calcular_max_drawdown()` |
| VaR Histórico | `algorithms/volatility.py` → `calcular_var_historico()` |
| Sharpe Ratio | `algorithms/volatility.py` → `calcular_sharpe()` |
| Clasificación de riesgo | `api/server.py` → `_clasificacion_riesgo()` |
| Pipeline | `main.py` → `pipeline_volatilidad()` |

### Patrones (`algorithms/patterns.py`)

**Ventana deslizante — O(n·k)**  
Recorre la serie con ventana de 20 días. Para cada segmento:
- Cuenta días de alza (`cierre[j] > cierre[j-1]`) y baja
- Si ≥75% días positivos → `N_dias_alza`
- Si ≥75% días negativos → `N_dias_baja`
- Si primera mitad baja y segunda sube → `rebote`
- Caso contrario → `neutro`
- Solo guarda patrones con variación ≥1%

**Detección de picos y valles — O(n)**  
Un punto `i` es pico si `precios[i] > precios[j]` para todo `j` en vecindad de ±3 días.

**Media Móvil Simple — O(n·k)**  
`SMA[i] = (P[i] + ... + P[i-k+1]) / k`  
Implementada de forma directa (sin suma rodante) para transparencia académica.

**Golden/Death Cross — O(n)**  
Calcula SMA corta (10 días) y SMA larga (30 días). Detecta cruces:
- Golden Cross: SMA corta pasa de debajo a arriba → señal alcista
- Death Cross: SMA corta pasa de arriba a abajo → señal bajista

### Volatilidad (`algorithms/volatility.py`)

**Retornos logarítmicos — O(n)**  
`rᵢ = ln(Pᵢ / Pᵢ₋₁)` — preferidos porque son aditivos en el tiempo.

**Volatilidad histórica — O(n)**  
Desviación estándar muestral (corrección de Bessel, denominador `k-1`) × √252 para anualizar.

**Máximo Drawdown — O(n)**  
Mantiene el pico máximo visto hasta cada punto: `MDD = (valle - pico) / pico × 100`. Una sola pasada.

**VaR Histórico (95%) — O(n log n)**  
Ordena todos los retornos y toma el percentil 5%. "Solo en el 5% de los días la pérdida supera este valor."

**Sharpe Ratio — O(n)**  
`Sharpe = (R_portfolio - R_libre_riesgo) / σ_portfolio`  
Tasa libre de riesgo: 5% anual. Sharpe > 1 = buena relación riesgo/retorno.

**Clasificación de riesgo — O(1)**  
Basada en volatilidad anualizada: Conservador (<15%), Moderado (15-30%), Agresivo (≥30%).

---

## Requerimiento 5 — Dashboard, reporte y despliegue

**Veredicto: CUMPLE**

### Dónde está

| Componente | Archivo |
|---|---|
| Dashboard visual completo | `frontend/index.html` |
| Servidor HTTP | `api/server.py` |
| Generador de reportes | `reports/generator.py` |
| Autenticación | `auth/auth.py` |
| Lecciones financieras | `cms/content.py` |
| Despliegue Render | `render.yaml` |
| Despliegue local Docker | `docker-compose.local.yml` + `Dockerfile.local` |

### Dashboard (`frontend/index.html`)

SPA completa sin frameworks. Usa SVG para el mapa de calor de correlaciones y Canvas API para el diagrama de barras de los 12 algoritmos. Incluye:
- Overview con métricas generales
- Comparación de activos (% cambio acumulado)
- Mapa de calor de correlaciones 20×20
- Velas OHLC con SMA rápida y lenta
- Clasificación de riesgo
- Tasa USD/COP en tiempo real
- Lecciones financieras (CMS)
- Simulador de portafolio (paper trading)

### API (`api/server.py`)

Servidor HTTP con `http.server` de stdlib. 25+ endpoints. CORS habilitado para el frontend. Manejo de errores con respuestas JSON estructuradas.

### Reportes (`reports/generator.py`)

Genera reportes técnicos en JSON y texto plano con todos los resultados de los algoritmos. Accesible en `GET /reporte` y `GET /reporte/txt`.

---

## Arquitectura del sistema

```
config.py           ← 20 activos, parámetros algorítmicos
    │
    ├── etl/
    │   ├── downloader.py   ← urllib → Yahoo Finance → JSON crudo
    │   ├── cleaner.py      ← interpolación lineal + Z-Score
    │   └── database.py     ← psycopg2 → PostgreSQL
    │
    ├── algorithms/
    │   ├── sorting.py      ← 12 algoritmos de ordenamiento
    │   ├── similarity.py   ← 4 algoritmos de similitud
    │   ├── patterns.py     ← ventana deslizante + cruces
    │   └── volatility.py   ← VaR, Sharpe, Drawdown
    │
    ├── api/server.py       ← http.server stdlib, 25+ endpoints
    ├── frontend/index.html ← SPA, SVG + Canvas API
    ├── auth/auth.py        ← SHA-256 + salt + sesiones
    ├── cms/content.py      ← lecciones + paper trading
    ├── reports/generator.py← reportes JSON y TXT
    │
    └── main.py             ← orquestador de pipelines
```

**Flujo de datos:**
```
Yahoo Finance (HTTP) → downloader.py → cleaner.py → PostgreSQL
                                                         │
                                              algorithms/ (sorting, similarity,
                                              patterns, volatility)
                                                         │
                                              api/server.py → frontend/index.html
```

---

## Cómo ejecutar el proyecto completo

```bash
# 1. Instalar dependencia
pip install psycopg2-binary==2.9.9

# 2. Configurar variables de entorno
cp .env.example .env
# editar .env con credenciales de PostgreSQL

# 3. Inicializar schema
python -c "from etl.database import init_schema; init_schema()"

# 4. Ejecutar ETL (descarga ~25.000 registros)
python main.py etl

# 5. Calcular algoritmos
python main.py similitud
python main.py volatilidad
python main.py ordenamiento

# 6. Iniciar API
python main.py api
# → http://localhost:8001
```

O todo en un comando:
```bash
python main.py todo
```

Con Docker:
```bash
docker compose -f docker-compose.local.yml up --build
```

---

## Despliegue en producción

URL: `https://bvc-analytics-api.onrender.com`

Configurado con `render.yaml` usando runtime Python 3.11 nativo (sin Docker).  
La BD PostgreSQL es el servicio `bvc-analytics-db` en Render.  
La variable `DATABASE_URL` es inyectada automáticamente por Render.  
El puerto es asignado por Render via `$PORT` y leído en `config.py`.

Para poblar la BD después del primer despliegue:
```javascript
// Consola del navegador (F12)
fetch('https://bvc-analytics-api.onrender.com/etl/iniciar', { method: 'POST' })
  .then(r => r.json()).then(console.log)
```

---

## Declaración de uso de IA

Este proyecto utilizó herramientas de inteligencia artificial generativa (Kiro/Claude) como apoyo en el desarrollo. El diseño algorítmico, la formulación matemática, la implementación explícita de cada algoritmo y el análisis de complejidad fueron realizados y verificados por los estudiantes. Las herramientas de IA se usaron como soporte de codificación y revisión, no como sustituto del análisis formal requerido por el curso.

---

*Universidad del Quindío — Análisis de Algoritmos — 2025*
