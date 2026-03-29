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
# Con Docker (recomendado)
docker compose -f docker-compose.local.yml up --build

# Pipelines (dentro del contenedor)
docker compose -f docker-compose.local.yml exec bvc_api python main.py etl
docker compose -f docker-compose.local.yml exec bvc_api python main.py similitud
docker compose -f docker-compose.local.yml exec bvc_api python main.py volatilidad
docker compose -f docker-compose.local.yml exec bvc_api python main.py ordenamiento

# Dashboard: http://localhost:8001
```

---

## Declaración de Uso de IA

Este proyecto utilizó herramientas de inteligencia artificial generativa (Kiro/Claude) como apoyo en el desarrollo. El diseño algorítmico, la formulación matemática, la implementación explícita de cada algoritmo y el análisis de complejidad fueron realizados y verificados por los estudiantes. Las herramientas de IA se usaron como soporte de codificación y revisión, no como sustituto del análisis formal requerido por el curso.

---

*Universidad del Quindío — Análisis de Algoritmos — 2025*
