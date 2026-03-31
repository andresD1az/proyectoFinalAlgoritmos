# Seguimiento 1 — BVC Analytics

**Universidad del Quindío**  
**Programa de Ingeniería de Sistemas y Computación**  
**Análisis de Algoritmos — Proyecto Final**

---

## Estado de Implementación

| Requerimiento | Estado | Evidencia |
|---|---|---|
| Req 1 — ETL automatizado | COMPLETO | 25,579 registros en BD, 20 activos, 5 años |
| Req 2 — Similitud | COMPLETO | 190 pares × 4 algoritmos calculados |
| Req 3 — Patrones y Volatilidad | COMPLETO | Ventana deslizante + Golden/Death Cross + VaR + Sharpe |
| Req 4 — Dashboard visual | COMPLETO | Heatmap SVG + Velas Canvas + Reporte PDF |
| Req 5 — Despliegue web | COMPLETO | https://bvc-analytics-api.onrender.com |

---

## Requerimiento 1 — ETL Automatizado

### Dónde está implementado

| Componente | Archivo |
|---|---|
| Descarga HTTP | `etl/descargador.py` |
| Limpieza de datos | `etl/limpieza.py` |
| Almacenamiento PostgreSQL | `etl/database.py` |
| Orquestación | `main.py` → `pipeline_etl()` |
| Schema de BD | `basedatos/init.sql` |
| Configuración activos | `config.py` |

### Cómo funciona

**Descarga (`etl/descargador.py`)**

Se construye la URL de Yahoo Finance manualmente con `urllib.parse.urlencode()`:
```
https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?period1=...&period2=...&interval=1d
```
Los parámetros `period1` y `period2` son Unix timestamps calculados con `datetime.timestamp()`. La respuesta JSON se parsea con `json.loads()` de stdlib. Los timestamps Unix de cada día se convierten a fecha con `datetime.utcfromtimestamp()`. Se implementan 3 reintentos con pausa de 1 segundo entre peticiones.

**Activos descargados (20):**  
EC, CIB, GXG, ILF, EWZ, EWW, SPY, QQQ, DIA, EEM, VT, IEMG, GLD, SLV, USO, TLT, XLE, XLF, XLK, VNQ

**Horizonte:** 5 años — `FECHA_INICIO = datetime.today() - timedelta(days=5*365)`

**Campos por registro:** fecha, apertura, maximo, minimo, cierre, volumen

**Limpieza (`etl/limpieza.py`)**

Algoritmo 1 — Interpolación lineal — O(n):
```
V[i] = V[izq] + (V[der] - V[izq]) × (i - izq) / (der - izq)
```
Rellena valores `None` entre dos puntos conocidos. Maneja diferencias de calendarios bursátiles entre NYSE y NASDAQ.

Algoritmo 2 — Detección de outliers Z-Score — O(n):
```
z = (x - μ) / σ    →    descarta si |z| > 3.5
```
Umbral 3.5 (más conservador que el estándar 3.0) para no eliminar movimientos extremos legítimos en mercados financieros.

**Datos reales en BD:**
- 20 activos registrados
- 25,579 registros de precios OHLCV
- Rango: ~1,260 días por activo (5 años de días bursátiles)

---

## Requerimiento 2 — Algoritmos de Similitud

### Dónde está implementado

| Componente | Archivo |
|---|---|
| 4 algoritmos de similitud | `algoritmos/similitud.py` |
| Matriz de similitud (190 pares) | `algoritmos/similitud.py` → `matriz_similitud()` |
| Pipeline | `main.py` → `pipeline_similitud()` |
| Endpoint comparación | `api/server.py` → `GET /similitud` |
| Endpoint heatmap | `api/server.py` → `GET /correlacion/matriz` |
| Visualización | `interfaz/index.html` → Mapa de Calor SVG |

### Los 4 algoritmos

**Distancia Euclidiana — O(n)**  
Función: `distancia_euclidiana()`  
Normaliza con Min-Max antes de calcular:
```
d(A, B) = √( Σᵢ (Aᵢ - Bᵢ)² )
```
Valor 0 = series idénticas. Requiere normalización porque compara activos con rangos de precios distintos (EC: $5-$15 vs SPY: $300-$500).

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

## Requerimiento 3 — Patrones y Volatilidad

### Dónde está implementado

| Componente | Archivo |
|---|---|
| Ventana deslizante + patrones | `algoritmos/patrones.py` → `detectar_patrones()` |
| Picos y valles | `algoritmos/patrones.py` → `detectar_picos_valles()` |
| Media Móvil Simple | `algoritmos/patrones.py` → `media_movil_simple()` |
| Golden/Death Cross | `algoritmos/patrones.py` → `detectar_cruces_medias()` |
| Retornos logarítmicos | `algoritmos/volatilidad.py` → `calcular_retornos_log()` |
| Volatilidad histórica | `algoritmos/volatilidad.py` → `calcular_volatilidad()` |
| Máximo Drawdown | `algoritmos/volatilidad.py` → `calcular_max_drawdown()` |
| VaR Histórico | `algoritmos/volatilidad.py` → `calcular_var_historico()` |
| Sharpe Ratio | `algoritmos/volatilidad.py` → `calcular_sharpe()` |
| Clasificación de riesgo | `api/server.py` → `GET /riesgo/clasificacion` |
| Pipeline | `main.py` → `pipeline_volatilidad()` |

### Patrones (`algoritmos/patrones.py`)

**Patrón 1 — Días consecutivos al alza/baja — O(n·k)**  
Ventana de 20 días. Si ≥75% de los días son positivos → `N_dias_alza`. Si ≥75% negativos → `N_dias_baja`.

**Patrón 2 — Rebote (V-shape) — O(n·k)**  
Primera mitad de la ventana bajista Y segunda mitad alcista → `rebote`. Este es el patrón adicional definido por el equipo.

**Golden/Death Cross — O(n)**  
SMA corta (10 días) cruza SMA larga (30 días):
- Golden Cross: SMA corta pasa de debajo a arriba → señal alcista
- Death Cross: SMA corta pasa de arriba a abajo → señal bajista

### Volatilidad (`algoritmos/volatilidad.py`)

**Retornos logarítmicos — O(n)**  
`rᵢ = ln(Pᵢ / Pᵢ₋₁)` — preferidos porque son aditivos en el tiempo.

**Volatilidad histórica — O(n)**  
Desviación estándar muestral (corrección de Bessel, denominador `k-1`) × √252 para anualizar.

**Máximo Drawdown — O(n)**  
`MDD = (valle - pico) / pico × 100`. Una sola pasada sobre la serie.

**VaR Histórico (95%) — O(n log n)**  
Ordena todos los retornos y toma el percentil 5%. "Solo en el 5% de los días la pérdida supera este valor."

**Sharpe Ratio — O(n)**  
`Sharpe = (R_portfolio - R_libre_riesgo) / σ_portfolio`  
Tasa libre de riesgo: 5% anual.

**Clasificación de riesgo — O(1)**  
Basada en volatilidad anualizada: Conservador (<15%), Moderado (15-30%), Agresivo (≥30%).

---

## Requerimiento 4 — Dashboard Visual

### Dónde está implementado

| Componente | Archivo |
|---|---|
| Dashboard completo | `interfaz/index.html` |
| Servidor HTTP | `api/server.py` |
| Generador de reportes | `reportes/generador.py` |

### Visualizaciones implementadas

**Mapa de Calor de Correlaciones (SVG)**  
Matriz 20×20 de Pearson. Cada celda es un `<rect>` SVG con color calculado:
- Verde: correlación positiva alta (r → 1)
- Rojo: correlación negativa (r → -1)
- Gris: sin correlación (r → 0)

**Gráfico de Velas OHLC (Canvas API)**  
Dibujado con `canvas.getContext('2d')`. Cada vela tiene:
- Mecha: línea vertical de mínimo a máximo
- Cuerpo: rectángulo de apertura a cierre (verde=alcista, rojo=bajista)
- SMA rápida (azul) y SMA lenta (amarilla) superpuestas

**Diagrama de Barras — Benchmark de Ordenamiento (SVG)**  
Barras horizontales ordenadas ASC por tiempo. Colores:
- Verde: algoritmos rápidos (< 33% del máximo)
- Amarillo: algoritmos medios (33-66%)
- Rojo: algoritmos lentos (> 66%)

**Reporte PDF**  
El endpoint `GET /reporte/txt` genera el reporte en texto plano. El botón "Exportar PDF" usa `window.print()` del navegador.

---

## Requerimiento 5 — Despliegue

### Producción (Render)
- URL: `https://bvc-analytics-api.onrender.com`
- Runtime: Python 3.11 nativo (sin Docker)
- BD: PostgreSQL en Render (plan gratuito)
- Configurado con `render.yaml`

### Desarrollo local (Docker)
```bash
docker compose -f docker-compose.local.yml up --build
# API: http://localhost:8001
```

---

## Detalle de los Algoritmos de Limpieza ETL

### Interpolación Lineal — O(n)

**Idea:** para cada bloque de valores `None` consecutivos entre dos valores conocidos (izquierdo en posición `izq`, derecho en posición `der`), calcula el valor intermedio con la fórmula:

```
V[k] = V[izq] + (V[der] - V[izq]) × (k - izq) / (der - izq)
```

**Tres casos:**
- Nones al inicio → backward fill (toma el primer valor conocido)
- Nones al final → forward fill (toma el último valor conocido)
- Nones en el medio → interpolación lineal entre los dos vecinos

**Por qué lineal y no forward-fill:** la interpolación lineal no introduce sesgo hacia el pasado. Si el precio estaba en $100 el lunes y en $106 el viernes, asume $102 el martes, $103 el miércoles y $104 el jueves — más realista que asumir $100 todos los días.

**Impacto en el análisis:** los valores interpolados son estimaciones. Para el ordenamiento por fecha no importa (la fecha es exacta). Para los algoritmos de similitud y volatilidad introduce un sesgo mínimo que es aceptable dado que los días faltantes son festivos o diferencias de calendarios bursátiles.

**Función:** `interpolar_linealmente()` en `etl/limpieza.py`

---

### Detección de Outliers Z-Score — O(n)

**Idea:** calcula cuántas desviaciones estándar se aleja cada valor de la media:

```
media    = Σ(vᵢ) / n
varianza = Σ(vᵢ - media)² / n
std      = √varianza
zᵢ       = (vᵢ - media) / std
```

Un valor es outlier si `|zᵢ| > 3.5`.

**Por qué umbral 3.5 y no 3.0:** el umbral estándar de 3.0 cubre el 99.7% de una distribución normal. Los retornos financieros tienen "colas pesadas" (fat tails) — eventos extremos como el crash de COVID-19 (marzo 2020) o la crisis de 2022 son legítimos y no deben eliminarse. Con 3.5 se preservan esos movimientos reales.

**Función:** `detectar_outliers_zscore()` en `etl/limpieza.py`

---

## Detalle de los 12 Algoritmos de Ordenamiento

### 1. TimSort — O(n log n)

**Idea:** divide el arreglo en bloques pequeños llamados *runs* (tamaño 32), los ordena con Insertion Sort, y luego los fusiona con Merge Sort duplicando el tamaño del bloque en cada pasada.

**Por qué es eficiente:** combina lo mejor de Insertion Sort (muy rápido en datos pequeños o casi ordenados) con Merge Sort (garantiza O(n log n) en el peor caso). Es el algoritmo interno de Python, aquí implementado explícitamente.

**En nuestros datos:** 67.589 ms. Rápido porque los datos venían parcialmente ordenados por fecha desde la BD.

**Funciones:** `timsort()`, `_insertion_run()`, `_merge_tim()`

---

### 2. Comb Sort — O(n log n)

**Idea:** mejora de Bubble Sort. En lugar de comparar elementos adyacentes (gap=1), usa una brecha que empieza en n y se reduce con factor 1.3 en cada pasada. Cuando gap llega a 1, hace una pasada final de Bubble Sort.

**Por qué es mejor que Bubble Sort:** elimina las "tortugas" — valores pequeños atrapados al final del arreglo que en Bubble Sort tardan muchas pasadas en llegar a su posición correcta.

**En nuestros datos:** 294.347 ms. Más lento que TimSort porque no aprovecha el orden parcial existente.

**Función:** `comb_sort()`

---

### 3. Selection Sort — O(n²)

**Idea:** en cada iteración i, recorre todo el subarreglo `arr[i..n-1]` para encontrar el mínimo y lo intercambia con `arr[i]`.

**Característica clave:** siempre hace exactamente `n(n-1)/2` comparaciones sin importar el estado inicial del arreglo. Con n=5,000: 12,497,500 comparaciones.

**En nuestros datos:** 28,960.340 ms — el segundo más lento. No se beneficia del orden parcial porque siempre recorre todo el subarreglo restante.

**Función:** `selection_sort()`

---

### 4. Tree Sort — O(n log n) promedio / O(n²) peor caso

**Idea:** inserta cada elemento en un Árbol Binario de Búsqueda (BST) y luego extrae los elementos con recorrido in-orden (izquierda → raíz → derecha), que produce la lista ordenada.

**Peor caso:** si los datos ya están ordenados, el BST degenera en una lista enlazada (cada nodo solo tiene hijo derecho). Eso convierte las inserciones en O(n) cada una → O(n²) total.

**En nuestros datos:** 41,604.703 ms — el más lento. Los datos venían ordenados por fecha desde la BD, lo que causó exactamente la degeneración descrita.

**Funciones:** `tree_sort()`, `_NodoBST`, `_bst_insertar()`, `_bst_inorden()`

---

### 5. Pigeonhole Sort — O(n + k)

**Idea:** convierte cada fecha a entero YYYYMMDD y crea un "palomar" (lista) por cada valor entero en el rango [min_fecha, max_fecha]. Distribuye los registros en sus palomares y los concatena. Dentro de cada palomar (misma fecha) ordena por cierre con Insertion Sort.

**Condición de eficiencia:** funciona bien cuando k (rango de valores) es comparable a n. En nuestro caso: k ≈ 1,826 días en 5 años, n = 5,000 registros → eficiente.

**En nuestros datos:** 37.369 ms — segundo más rápido. Explota la distribución uniforme de las fechas bursátiles.

**Función:** `pigeonhole_sort()`

---

### 6. Bucket Sort — O(n + k)

**Idea:** normaliza la fecha al rango [0,1] y distribuye los registros en n cubetas según esa normalización. Cada cubeta se ordena internamente con Insertion Sort y luego se concatenan.

**Diferencia con Pigeonhole:** Pigeonhole crea una cubeta por cada valor posible (rango exacto). Bucket crea exactamente n cubetas y distribuye proporcionalmente. Bucket usa menos memoria cuando el rango es grande.

**En nuestros datos:** 55.524 ms. Ligeramente más lento que Pigeonhole porque tiene overhead de normalización y distribución en n cubetas.

**Función:** `bucket_sort()`

---

### 7. QuickSort — O(n log n) promedio / O(n²) peor caso

**Idea:** elige un pivote, coloca los elementos menores a la izquierda y los mayores a la derecha (partición), y recursa sobre ambas mitades.

**Optimización implementada:** pivote mediana-de-tres — compara el primero, el medio y el último elemento y elige la mediana como pivote. Esto evita el peor caso O(n²) que ocurre con datos ya ordenados si se elige siempre el primer o último elemento.

**En nuestros datos:** 208.022 ms. Más lento de lo esperado porque la mediana-de-tres tiene overhead adicional de comparaciones.

**Funciones:** `quicksort()`, `_quicksort_rec()`, `_particionar()`, `_mediana_tres()`

---

### 8. HeapSort — O(n log n) garantizado

**Idea:**
- Fase 1 — Build Max-Heap: convierte el arreglo en un max-heap (árbol binario donde cada padre es mayor que sus hijos) en O(n).
- Fase 2 — Extract: intercambia la raíz (máximo) con el último elemento, reduce el heap en 1 y restaura la propiedad heap con `_heapify()`. Repite n veces → O(n log n).

**Ventaja sobre QuickSort:** O(n log n) garantizado en todos los casos, sin peor caso O(n²).

**En nuestros datos:** 333.874 ms. Más lento que QuickSort en la práctica por el overhead de mantener la estructura heap.

**Funciones:** `heapsort()`, `_heapify()`

---

### 9. Bitonic Sort — O(n log² n)

**Idea:** genera secuencias bitónicas (primero creciente, luego decreciente) recursivamente y las fusiona. Requiere que n sea potencia de 2 — si no lo es, se rellena con un centinela máximo `{"fecha": "9999-99-99"}` que se elimina al final.

**Origen:** diseñado para hardware paralelo (GPU/FPGA) donde todas las comparaciones se hacen simultáneamente. En implementación secuencial es más lento que O(n log n).

**En nuestros datos:** 730.210 ms. El más lento de los algoritmos O(n log n) porque en implementación secuencial tiene más operaciones que HeapSort o TimSort.

**Funciones:** `bitonic_sort()`, `_bitonic_sort_rec()`, `_bitonic_merge()`, `_bitonic_compare()`

---

### 10. Gnome Sort — O(n²)

**Idea:** el "gnomo" avanza si `arr[i] >= arr[i-1]`, retrocede e intercambia si `arr[i] < arr[i-1]`. Sin bucle interno explícito — un solo índice que sube y baja.

**Equivalencia:** es funcionalmente idéntico a Insertion Sort pero con un solo índice en lugar de dos bucles anidados.

**En nuestros datos:** 10.336 ms — el más rápido de todos. Los datos venían casi ordenados por fecha desde la BD, por lo que el gnomo casi nunca retrocedió. En datos desordenados sería uno de los más lentos.

**Función:** `gnome_sort()`

---

### 11. Binary Insertion Sort — O(n²)

**Idea:** mejora Insertion Sort usando búsqueda binaria para encontrar la posición de inserción correcta en O(log n) comparaciones en lugar de O(n). Sin embargo, el desplazamiento de elementos sigue siendo O(n) → complejidad total O(n²).

**Ventaja real:** reduce el número de comparaciones a la mitad respecto a Insertion Sort clásico, pero no mejora la complejidad asintótica porque el cuello de botella es el desplazamiento, no las comparaciones.

**En nuestros datos:** 131.496 ms. Más rápido que Selection Sort y Gnome Sort (en datos desordenados) gracias a la búsqueda binaria.

**Funciones:** `binary_insertion_sort()`, `_busqueda_binaria_pos()`

---

### 12. RadixSort — O(nk)

**Idea:** ordena por la clave entera YYYYMMDD (8 dígitos, k=8). Aplica Counting Sort estable dígito a dígito del menos al más significativo (LSD — Least Significant Digit). La estabilidad garantiza que el orden de pasadas anteriores se preserve.

**Subrutina Counting Sort:** para cada dígito, cuenta las ocurrencias, acumula los conteos para determinar posiciones finales, y construye la salida de derecha a izquierda (para mantener estabilidad).

**Criterio secundario:** después de ordenar por fecha, aplica Insertion Sort dentro de cada grupo de misma fecha para ordenar por cierre.

**En nuestros datos:** 109.888 ms. Eficiente porque k=8 es constante y pequeño.

**Funciones:** `radix_sort()`, `_counting_sort_por_digito()`

---

## Tabla 1 — Resultados Reales del Benchmark

Ejecutado sobre **5,000 registros** del dataset unificado (misma muestra para todos los algoritmos, garantizando comparación justa).

| # | Método de Ordenamiento | Complejidad | Tamaño | Tiempo (ms) |
|---|---|---|---|---|
| 1 | Gnome Sort | O(n²) | 5,000 | 10.336 |
| 2 | Pigeonhole Sort | O(n + k) | 5,000 | 37.369 |
| 3 | Bucket Sort | O(n + k) | 5,000 | 55.524 |
| 4 | TimSort | O(n log n) | 5,000 | 67.589 |
| 5 | RadixSort | O(nk) | 5,000 | 109.888 |
| 6 | Binary Insertion Sort | O(n²) | 5,000 | 131.496 |
| 7 | QuickSort | O(n log n) | 5,000 | 208.022 |
| 8 | Comb Sort | O(n log n) | 5,000 | 294.347 |
| 9 | HeapSort | O(n log n) | 5,000 | 333.874 |
| 10 | Bitonic Sort | O(n log² n) | 5,000 | 730.210 |
| 11 | Selection Sort | O(n²) | 5,000 | 28,960.340 |
| 12 | Tree Sort | O(n log n) | 5,000 | 41,604.703 |

**Análisis de resultados:**

- **Gnome Sort (10 ms)** fue el más rápido en esta muestra porque los datos ya estaban parcialmente ordenados (vienen de la BD ordenados por fecha). Gnome Sort es muy eficiente en datos casi ordenados.
- **TimSort (67 ms)** confirma su eficiencia O(n log n) en datos reales. Es el algoritmo interno de Python, aquí implementado explícitamente.
- **Selection Sort (28,960 ms)** y **Tree Sort (41,604 ms)** son los más lentos. Selection Sort siempre hace n(n-1)/2 comparaciones sin importar el estado inicial. Tree Sort degeneró porque los datos ordenados producen un árbol BST degenerado (lista enlazada), llevándolo a O(n²).
- **Pigeonhole Sort (37 ms)** y **Bucket Sort (55 ms)** son eficientes porque explotan la distribución uniforme de las fechas bursátiles.

**Criterio de ordenamiento:** fecha ASC (primario), cierre ASC (secundario).  
**Implementación:** función `_clave(registro)` en `algoritmos/ordenamiento.py`.

---

## Estructura del Proyecto (Nombres en Español)

```
proyectoFinalAlgoritmos/
├── algoritmos/          ← Núcleo algorítmico
│   ├── ordenamiento.py  ← 12 algoritmos de ordenamiento
│   ├── similitud.py     ← 4 algoritmos de similitud
│   ├── patrones.py      ← Ventana deslizante + Golden/Death Cross
│   └── volatilidad.py   ← VaR, Sharpe, Drawdown, volatilidad
├── etl/                 ← Pipeline de datos
│   ├── descargador.py   ← Descarga HTTP desde Yahoo Finance
│   ├── limpieza.py      ← Interpolación lineal + Z-Score
│   └── database.py      ← CRUD PostgreSQL
├── api/
│   └── server.py        ← Servidor HTTP (18 endpoints)
├── interfaz/
│   └── index.html       ← Dashboard SPA
├── reportes/
│   └── generador.py     ← Reporte JSON y texto plano
├── basedatos/
│   └── init.sql         ← Schema PostgreSQL
├── config.py            ← Configuración global
├── main.py              ← Orquestador de pipelines
└── requirements.txt     ← psycopg2-binary==2.9.9
```

---

## Cómo Ejecutar

```bash
# 1. Levantar contenedores (BD + API)
docker compose -f docker-compose.local.yml up --build -d

# 2. Correr el ETL (descarga 5 años × 20 activos, ~10 min)
docker compose -f docker-compose.local.yml exec bvc_api python main.py etl

# 3. Correr el benchmark de ordenamiento (~10 min)
docker compose -f docker-compose.local.yml exec bvc_api python main.py ordenamiento

# Dashboard: http://localhost:8001
```

---

## Soportes del Seguimiento 1 — Cómo Obtenerlos

Esta sección explica exactamente cómo sacar cada soporte que pide la entrega.

### Soporte 1 — Tabla 1 con los 12 algoritmos (tamaño y tiempo)

Los datos ya están en la BD después de correr `python main.py ordenamiento`.

**Opción A — Dashboard visual:**
1. Abre `http://localhost:8001`
2. En el sidebar izquierdo → "Req 1 — Ordenamiento" → "Tabla 1 + Barras"
3. Aparece la tabla completa con algoritmo, complejidad, tamaño y tiempo en ms
4. Captura de pantalla o `Ctrl+P` → Guardar como PDF

**Opción B — Endpoint directo:**
```
http://localhost:8001/ordenamiento/benchmark
```

**Datos de referencia (ejecutados en este equipo):**

| # | Método | Complejidad | Tamaño | Tiempo (ms) |
|---|---|---|---|---|
| 1 | Gnome Sort | O(n²) | 5,000 | 10.336 |
| 2 | Pigeonhole Sort | O(n + k) | 5,000 | 37.369 |
| 3 | Bucket Sort | O(n + k) | 5,000 | 55.524 |
| 4 | TimSort | O(n log n) | 5,000 | 67.589 |
| 5 | RadixSort | O(nk) | 5,000 | 109.888 |
| 6 | Binary Insertion Sort | O(n²) | 5,000 | 131.496 |
| 7 | QuickSort | O(n log n) | 5,000 | 208.022 |
| 8 | Comb Sort | O(n log n) | 5,000 | 294.347 |
| 9 | HeapSort | O(n log n) | 5,000 | 333.874 |
| 10 | Bitonic Sort | O(n log² n) | 5,000 | 730.210 |
| 11 | Selection Sort | O(n²) | 5,000 | 28,960.340 |
| 12 | Tree Sort | O(n log n) | 5,000 | 41,604.703 |

### Soporte 2 — Diagrama de barras ASC de los 12 tiempos

1. Mismo dashboard → "Req 1 — Tabla 1 + Barras"
2. El diagrama SVG aparece debajo de la tabla, ordenado de menor a mayor tiempo
3. Para exportar: clic derecho sobre el gráfico → "Guardar imagen como" o `Ctrl+P`

### Soporte 3 — Top-15 días con mayor volumen (ASC)

1. Dashboard → "Req 1 — Top-15 Volumen"
2. Tabla con ticker, fecha, volumen y cierre ordenados ascendentemente
3. Endpoint directo: `http://localhost:8001/ordenamiento/top-volumen`

### Soporte 4 — Evidencia del ETL (datos en BD)

```
http://localhost:8001/etl/status
```
Muestra: `{"activos": 20, "registros_precios": 25579, "etl_ejecutado": true}`

### Soporte 5 — Código fuente para mostrar en sustentación

Archivos clave del Seguimiento 1:
- `etl/descargador.py` — descarga HTTP sin yfinance
- `etl/limpieza.py` — interpolación lineal y Z-Score
- `algoritmos/ordenamiento.py` — los 12 algoritmos
- `config.py` — los 20 activos y parámetros

---

## Declaración de Uso de IA

Este proyecto utilizó herramientas de inteligencia artificial generativa (Kiro/Claude) como apoyo en el desarrollo. El diseño algorítmico, la formulación matemática, la implementación explícita de cada algoritmo y el análisis de complejidad fueron realizados y verificados por los estudiantes. Las herramientas de IA se usaron como soporte de codificación y revisión, no como sustituto del análisis formal requerido por el curso.

---

*Universidad del Quindío — Análisis de Algoritmos — 2025*

---

## Guía de Capturas para el Documento

Esta sección indica exactamente qué capturar, de dónde y en qué orden colocarlo en el documento de sustentación.

---

### BLOQUE 1 — Requerimiento 1: ETL

#### Captura 1.1 — Construcción de la URL de descarga
- **Archivo:** `etl/descargador.py`
- **Qué mostrar:** función `descargar_ticker()` — las líneas donde se construye la URL con `urllib.parse.urlencode()` y se hace `urlopen()`
- **Dónde en el doc:** después de explicar que la descarga es HTTP directa sin yfinance

#### Captura 1.2 — Parseo manual del JSON
- **Archivo:** `etl/descargador.py`
- **Qué mostrar:** el bloque `try` donde se extrae `result["timestamp"]`, `indicadores["close"]` y se construye el dict con fecha, apertura, maximo, minimo, cierre, volumen
- **Dónde en el doc:** después de explicar la estructura del JSON de Yahoo Finance

#### Captura 1.3 — Interpolación lineal
- **Archivo:** `etl/limpieza.py`
- **Qué mostrar:** función `interpolar_linealmente()` — el CASO 3 (líneas con `v_izq`, `v_der`, `fraccion`, `resultado[k]`)
- **Dónde en el doc:** al explicar el algoritmo de limpieza de valores faltantes

#### Captura 1.4 — Z-Score
- **Archivo:** `etl/limpieza.py`
- **Qué mostrar:** función `detectar_outliers_zscore()` — el cálculo de `media`, `suma_cuadrados`, `std` y el filtro `abs((v - media) / std) > umbral`
- **Dónde en el doc:** al explicar la detección de anomalías

#### Captura 1.5 — Evidencia de datos en BD (UI)
- **Dónde:** abrir `http://localhost:8001/etl/status` en el navegador
- **Qué mostrar:** el JSON con `"activos": 20, "registros_precios": 25579, "etl_ejecutado": true`
- **Dónde en el doc:** como evidencia de que el ETL corrió exitosamente

---

### BLOQUE 2 — Requerimiento 2: Ordenamiento

#### Captura 2.1 — Criterio de ordenamiento compuesto
- **Archivo:** `algoritmos/ordenamiento.py`
- **Qué mostrar:** función `_clave(registro)` — las 3 líneas que retornan `(str(fecha), float(cierre))`
- **Dónde en el doc:** al explicar el criterio fecha ASC + cierre ASC

#### Captura 2.2 — TimSort
- **Archivo:** `algoritmos/ordenamiento.py`
- **Qué mostrar:** función `timsort()` completa (Paso 1 y Paso 2) + `_merge_tim()`
- **Dónde en el doc:** al describir el algoritmo más rápido del benchmark

#### Captura 2.3 — QuickSort con mediana de tres
- **Archivo:** `algoritmos/ordenamiento.py`
- **Qué mostrar:** función `_mediana_tres()` + `_particionar()` + `quicksort()`
- **Dónde en el doc:** al explicar la optimización del pivote

#### Captura 2.4 — HeapSort
- **Archivo:** `algoritmos/ordenamiento.py`
- **Qué mostrar:** función `_heapify()` + `heapsort()` (Fase 1 y Fase 2)
- **Dónde en el doc:** al explicar la estructura heap

#### Captura 2.5 — Tree Sort (BST)
- **Archivo:** `algoritmos/ordenamiento.py`
- **Qué mostrar:** clase `_NodoBST` + `_bst_insertar()` + `_bst_inorden()`
- **Dónde en el doc:** al explicar por qué degeneró a O(n²)

#### Captura 2.6 — RadixSort
- **Archivo:** `algoritmos/ordenamiento.py`
- **Qué mostrar:** función `_counting_sort_por_digito()` + inicio de `radix_sort()` (el bucle de los 8 dígitos)
- **Dónde en el doc:** al explicar el ordenamiento por dígitos LSD

#### Captura 2.7 — Selection Sort
- **Archivo:** `algoritmos/ordenamiento.py`
- **Qué mostrar:** función `selection_sort()` completa (es corta, cabe en una captura)
- **Dónde en el doc:** al explicar el algoritmo con más comparaciones

#### Captura 2.8 — Gnome Sort
- **Archivo:** `algoritmos/ordenamiento.py`
- **Qué mostrar:** función `gnome_sort()` completa (la más corta de todas)
- **Dónde en el doc:** al explicar por qué fue el más rápido con datos casi ordenados

#### Captura 2.9 — Tabla 1 con tiempos reales (UI)
- **Dónde:** `http://localhost:8001` → sidebar "Req 1 — Ordenamiento" → "Tabla 1 + Barras"
- **Qué mostrar:** la tabla completa con los 12 algoritmos, complejidad, tamaño y tiempo en ms
- **Dónde en el doc:** como la Tabla 1 oficial del requerimiento

#### Captura 2.10 — Diagrama de barras (UI)
- **Dónde:** misma sección del dashboard, debajo de la tabla
- **Qué mostrar:** el diagrama SVG horizontal con las barras ordenadas ASC por tiempo
- **Dónde en el doc:** inmediatamente después de la Tabla 1

#### Captura 2.11 — Top-15 mayor volumen (UI)
- **Dónde:** `http://localhost:8001` → sidebar "Req 1 — Top-15 Volumen"
- **Qué mostrar:** la tabla con ticker, fecha, volumen y cierre ordenados ASC
- **Dónde en el doc:** al final del Requerimiento 2

---

### BLOQUE 3 — Similitud (entrega posterior)

#### Captura 3.1 — Correlación de Pearson
- **Archivo:** `algoritmos/similitud.py`
- **Qué mostrar:** función `correlacion_pearson()` — el cálculo de `numerador`, `var_a`, `var_b`, `denominador`

#### Captura 3.2 — Distancia Euclidiana
- **Archivo:** `algoritmos/similitud.py`
- **Qué mostrar:** función `distancia_euclidiana()` + `normalizar_minmax()`

#### Captura 3.3 — DTW
- **Archivo:** `algoritmos/similitud.py`
- **Qué mostrar:** función `dtw()` — el bucle de la matriz con la recurrencia `min(arriba, izquierda, diagonal)`

#### Captura 3.4 — Comparación de activos (UI)
- **Dónde:** `http://localhost:8001` → "Req 2 — Comparar Activos" → seleccionar dos activos → Comparar
- **Qué mostrar:** los 4 valores de similitud (Euclidiana, Pearson, Coseno, DTW) y el gráfico de % cambio acumulado

#### Captura 3.5 — Mapa de calor (UI)
- **Dónde:** `http://localhost:8001` → "Req 2 — Mapa de Calor"
- **Qué mostrar:** la matriz 20×20 con los colores verde/rojo/gris

---

### Cómo hacer las capturas de código

**Opción A — VS Code con CodeSnap:**
1. Instala la extensión CodeSnap (`Ctrl+Shift+X` → buscar "CodeSnap")
2. Selecciona las líneas de código
3. Clic derecho → "CodeSnap"
4. Ajusta el tema y guarda como imagen

**Opción B — Captura de pantalla simple:**
1. Abre el archivo en VS Code
2. Navega a la función (usa `Ctrl+G` + número de línea)
3. `Win + Shift + S` para captura de área

**Opción C — GitHub:**
1. Ve a `https://github.com/andresD1az/proyectoFinalAlgoritmos`
2. Navega al archivo
3. Haz clic en el número de línea para resaltar
4. Captura de pantalla

---

*Universidad del Quindío — Análisis de Algoritmos — 2025*
