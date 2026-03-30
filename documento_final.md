# Documento Final — BVC Analytics
## Análisis de Algoritmos sobre Datos Financieros de la BVC

**Universidad del Quindío**  
**Programa de Ingeniería de Sistemas y Computación**  
**Análisis de Algoritmos — Proyecto Final**

---

## 1. Introducción

El presente proyecto implementa una plataforma de análisis financiero cuantitativo sobre datos históricos de 20 activos de la Bolsa de Valores de Colombia (BVC) y ETFs globales. El sistema aplica métodos cuantitativos, algoritmos clásicos y técnicas de análisis de series temporales para establecer relaciones de similitud, detectar patrones recurrentes y clasificar instrumentos financieros por nivel de riesgo.

**Principio fundamental:** toda la lógica algorítmica está implementada desde cero con estructuras básicas de Python 3.11. La única dependencia externa es `psycopg2-binary` como driver de conexión a PostgreSQL.

---

## 2. Fuentes de Información

**Fuente:** Yahoo Finance API v8 (pública, sin autenticación)  
**URL:** `https://query1.finance.yahoo.com/v8/finance/chart/{ticker}`  
**Método:** Peticiones HTTP directas con `urllib.request` (stdlib de Python)

**Campos obtenidos por activo:**

| Campo | Descripción | Tipo |
|---|---|---|
| fecha | Fecha de cotización (YYYY-MM-DD) | DATE |
| apertura | Precio de apertura (Open) | NUMERIC(12,4) |
| maximo | Precio máximo del día (High) | NUMERIC(12,4) |
| minimo | Precio mínimo del día (Low) | NUMERIC(12,4) |
| cierre | Precio de cierre ajustado (Close) | NUMERIC(12,4) |
| volumen | Volumen de negociación | BIGINT |

**Portafolio de 20 activos:**

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

**Horizonte histórico:** 5 años (≈ 1,260 días bursátiles por activo)  
**Total de registros en BD:** 25,579 filas OHLCV

---

## 3. Requerimiento 1 — ETL Automatizado

### 3.1 Descarga (`etl/descargador.py`)

Se construye la URL manualmente con `urllib.parse.urlencode()`:

```
https://query1.finance.yahoo.com/v8/finance/chart/{ticker}
  ?period1={unix_inicio}&period2={unix_fin}&interval=1d&events=history
```

Los parámetros `period1` y `period2` son Unix timestamps calculados con `datetime.timestamp()`. La respuesta JSON se parsea con `json.loads()` de stdlib. Los timestamps Unix se convierten a fechas con `datetime.utcfromtimestamp()`. Se implementan 3 reintentos con pausa de 1 segundo entre peticiones (scraping ético).

### 3.2 Limpieza (`etl/limpieza.py`)

**Algoritmo 1 — Interpolación Lineal — O(n)**

Rellena valores `None` entre dos puntos conocidos:

```
V[k] = V[izq] + (V[der] - V[izq]) × (k - izq) / (der - izq)
```

Casos especiales:
- Nones al inicio → backward fill (primer valor conocido)
- Nones al final → forward fill (último valor conocido)

**Justificación:** apropiada para series de tiempo financieras porque asume variación lineal entre dos puntos conocidos. Maneja diferencias de calendarios bursátiles entre NYSE y NASDAQ.

**Algoritmo 2 — Detección de Outliers Z-Score — O(n)**

```
z = (x - μ) / σ    →    outlier si |z| > 3.5
```

**Justificación del umbral 3.5:** los retornos financieros tienen "colas pesadas" (fat tails). El umbral estándar de 3.0 eliminaría movimientos legítimos como crashes o rallies. Con 3.5 se preservan eventos extremos reales.

**Decisiones de limpieza:**
- Se interpola OHLC pero NO el volumen (el volumen es discreto, no tiene sentido interpolarlo)
- Se eliminan cierres ≤ 0 antes de interpolar (precio negativo es físicamente imposible)

### 3.3 Unificación del Dataset

Todos los activos se almacenan en una sola tabla `precios` con `activo_id` como clave foránea. La restricción `UNIQUE(activo_id, fecha)` garantiza integridad. El proceso es idempotente (`ON CONFLICT DO NOTHING`).

---

## 4. Requerimiento 2 — Algoritmos de Ordenamiento

### 4.1 Tabla 1 — Resultados del Benchmark

Ejecutado sobre **n = 5,000 registros** del dataset unificado (misma muestra para todos los algoritmos, garantizando comparación justa).

**Criterio de ordenamiento:** fecha ASC (primario), precio de cierre ASC (secundario).  
**Implementación:** función `_clave(registro)` en `algoritmos/ordenamiento.py`.

| # | Método de Ordenamiento | Complejidad | Tamaño (n) | Tiempo (ms) |
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

### 4.2 Análisis de Resultados

**Gnome Sort (10 ms) fue el más rápido** porque los datos venían de la BD ya ordenados por fecha. Gnome Sort es muy eficiente en datos casi ordenados — avanza sin retroceder cuando el orden ya está establecido.

**Tree Sort (41,604 ms) fue el más lento** porque los datos ordenados producen un BST degenerado (cada nodo solo tiene hijo derecho, se convierte en lista enlazada). Esto lo lleva a O(n²) en inserción, más el overhead de recursión en el recorrido in-orden.

**Selection Sort (28,960 ms)** siempre hace exactamente n(n-1)/2 = 12,497,500 comparaciones sin importar el estado inicial del arreglo.

**Pigeonhole Sort (37 ms) y Bucket Sort (55 ms)** son eficientes porque explotan la distribución uniforme de las fechas bursátiles (k ≈ 1,826 días en 5 años).

### 4.3 Diagrama de Barras

El diagrama de barras horizontal está disponible en el dashboard en la sección "Req 1 — Tabla 1 + Barras". Los algoritmos se presentan en orden ascendente por tiempo de ejecución. Los colores indican velocidad relativa: verde (< 33% del máximo), amarillo (33-66%), rojo (> 66%).

### 4.4 Top-15 Días con Mayor Volumen (ASC)

Calculado con HeapSort manual sobre el dataset completo de 25,579 registros — O(n log n).

| # | Ticker | Fecha | Volumen | Cierre |
|---|---|---|---|---|
| 1-15 | Ver dashboard | `/ordenamiento/top-volumen` | — | — |

*Los datos exactos están disponibles en el endpoint `GET /ordenamiento/top-volumen` y en la sección "Top-15 Volumen" del dashboard.*

---

## 5. Requerimiento 3 — Similitud entre Series de Tiempo

### 5.1 Los 4 Algoritmos

**Distancia Euclidiana — O(n)**

```
d(A, B) = √( Σᵢ (Aᵢ - Bᵢ)² )
```
Requiere normalización Min-Max previa: `x_norm = (x - min) / (max - min)`

**Correlación de Pearson — O(n)**

```
r = Σ((Aᵢ - Ā)(Bᵢ - B̄)) / √(Σ(Aᵢ - Ā)² · Σ(Bᵢ - B̄)²)
```
Rango [-1, 1]. No requiere normalización.

**Similitud por Coseno — O(n)**

```
cos(θ) = (A · B) / (‖A‖ · ‖B‖) = Σ(Aᵢ·Bᵢ) / (√Σ(Aᵢ²) · √Σ(Bᵢ²))
```
Invariante a la magnitud.

**DTW — Dynamic Time Warping — O(n²)**

```
matriz[i][j] = |A[i] - B[j]| + min(arriba, izquierda, diagonal)
```
Optimizado con ventana Sakoe-Chiba (10%) → O(n·k).

**Total de pares calculados:** C(20,2) = 190 pares × 4 algoritmos = 760 cálculos.

### 5.2 Visualización

El mapa de calor de correlaciones (Pearson, 20×20) está disponible en la sección "Mapa de Calor" del dashboard. Cada celda es un `<rect>` SVG con color calculado algorítmicamente.

---

## 6. Requerimiento 4 — Patrones y Volatilidad

### 6.1 Patrones con Ventana Deslizante — O(n·k)

Ventana de 20 días. Para cada segmento:

**Patrón 1 — Días consecutivos al alza/baja:**
```
Si días_alza / (k-1) >= 0.75 → "N_dias_alza"
Si días_baja / (k-1) >= 0.75 → "N_dias_baja"
```

**Patrón 2 — Rebote (V-shape):**
```
Si primera_mitad_bajista AND segunda_mitad_alcista → "rebote"
```

**Golden/Death Cross — O(n):**
- Golden Cross: SMA(10) cruza SMA(30) hacia arriba → señal alcista
- Death Cross: SMA(10) cruza SMA(30) hacia abajo → señal bajista

### 6.2 Métricas de Volatilidad y Riesgo

**Retornos logarítmicos — O(n):**
```
rᵢ = ln(Pᵢ / Pᵢ₋₁)
```

**Volatilidad histórica anualizada — O(n):**
```
σ_anual = √(Σ(rᵢ - r̄)² / (k-1)) × √252
```
Corrección de Bessel (k-1) para estimador insesgado. Factor √252 = días bursátiles/año.

**Máximo Drawdown — O(n):**
```
MDD = (precio_valle - precio_pico) / precio_pico × 100
```

**VaR Histórico (95%) — O(n log n):**
```
VaR₀.₉₅ = percentil 5% de los retornos ordenados
```

**Sharpe Ratio — O(n):**
```
Sharpe = (R_activo - R_libre) / σ_activo
```
Tasa libre de riesgo: 5% anual.

**Clasificación de riesgo:**
- Conservador: σ_anual < 15%
- Moderado: 15% ≤ σ_anual < 30%
- Agresivo: σ_anual ≥ 30%

---

## 7. Requerimiento 5 — Dashboard y Despliegue

### 7.1 Dashboard Visual (`interfaz/index.html`)

SPA completa sin frameworks. Visualizaciones:
- Mapa de calor de correlaciones (SVG, 20×20)
- Gráfico de velas OHLC con SMA (Canvas API)
- Diagrama de barras del benchmark (SVG horizontal)
- Tabla 1 con los 12 algoritmos
- Top-15 días con mayor volumen
- Clasificación de riesgo de los 20 activos
- Comparación de activos (% cambio acumulado)
- Patrones detectados y Golden/Death Cross

### 7.2 Reporte Técnico

Disponible en:
- `GET /reporte` → JSON completo
- `GET /reporte/txt` → texto plano
- Botón "Exportar PDF" → `window.print()` del navegador

### 7.3 Despliegue

**Producción:** https://bvc-analytics-api.onrender.com  
**Configuración:** `render.yaml` — Python 3.11 nativo, sin Docker  
**BD:** PostgreSQL en Render (plan gratuito)

**Reproducibilidad — comandos para reconstruir desde cero:**
```bash
docker compose -f docker-compose.local.yml up --build
docker compose -f docker-compose.local.yml exec bvc_api python main.py etl
docker compose -f docker-compose.local.yml exec bvc_api python main.py similitud
docker compose -f docker-compose.local.yml exec bvc_api python main.py volatilidad
docker compose -f docker-compose.local.yml exec bvc_api python main.py ordenamiento
```

---

## 8. Arquitectura del Sistema

```
interfaz/index.html          ← Capa de presentación (SPA)
        │ HTTP fetch()
api/server.py                ← Capa de API (http.server stdlib)
        │
algoritmos/                  ← Capa algorítmica (28 algoritmos)
  ordenamiento.py            ← 12 algoritmos de ordenamiento
  similitud.py               ← 4 algoritmos de similitud
  patrones.py                ← Ventana deslizante + Golden/Death Cross
  volatilidad.py             ← VaR, Sharpe, Drawdown, volatilidad
        │
etl/                         ← Capa de datos
  descargador.py             ← urllib → Yahoo Finance
  limpieza.py                ← Interpolación lineal + Z-Score
  database.py                ← psycopg2 → PostgreSQL
        │
PostgreSQL 15                ← Persistencia
  activos, precios, resultados_similitud,
  resultados_volatilidad, resultados_sorting, top_volumen
```

---

## 9. Verificación de Restricciones

| Restricción | Verificación |
|---|---|
| Sin yfinance/pandas_datareader | `requirements.txt` solo tiene `psycopg2-binary==2.9.9` |
| Sin pandas/numpy/scipy/sklearn | Ningún import de estas librerías en todo el proyecto |
| Sin datasets estáticos | Los datos se descargan en tiempo de ejecución |
| Algoritmos implementados explícitamente | Cada función tiene su lógica completa, sin llamadas de alto nivel |
| Reproducibilidad | `python main.py todo` reconstruye el dataset desde cero |
| Scraping ético | Pausa de 1 segundo entre peticiones, 3 reintentos máximo |
| Declaración de IA | Incluida en este documento (sección 10) |

---

## 10. Declaración de Uso de Inteligencia Artificial

En el desarrollo del presente proyecto se utilizaron herramientas de inteligencia artificial generativa como apoyo puntual en las siguientes situaciones:

**1. Revisión de sintaxis — Servidor HTTP**  
Durante la implementación del servidor HTTP con `http.server`, se consultó a una herramienta de IA para verificar la sintaxis del método `do_GET` y la estructura del enrutador. El diseño de los endpoints y la lógica de negocio fueron definidos por el equipo.

**2. Optimización del algoritmo DTW**  
Al implementar Dynamic Time Warping, se consultó a una herramienta de IA sobre técnicas de optimización, que sugirió la ventana de Sakoe-Chiba. El equipo evaluó la propuesta, comprendió su fundamento matemático y realizó la implementación manualmente.

**3. Corrección de bug — Tree Sort**  
Se detectó que `_bst_inorden` no terminaba correctamente en casos de árbol degenerado. Se consultó a una herramienta de IA para identificar la condición de parada faltante. La corrección fue revisada y aplicada por el equipo.

**4. Formato del documento de arquitectura**  
Se utilizó una herramienta de IA para dar formato y estructura al documento de arquitectura. El contenido técnico y las decisiones de diseño fueron redactados por el equipo.

En todos los casos, el diseño algorítmico, las fórmulas matemáticas, el análisis de complejidad y la implementación final fueron realizados por los integrantes del equipo.

---

## 11. Cómo Obtener los Soportes para la Sustentación

### Soporte 1 — Tabla 1 con datos reales
Abre en el navegador: `http://localhost:8001` → sección "Req 1 — Tabla 1 + Barras"  
O directamente: `http://localhost:8001/ordenamiento/benchmark`

### Soporte 2 — Diagrama de barras
Mismo dashboard, sección "Tabla 1 + Barras" — el diagrama SVG aparece debajo de la tabla.  
Para exportar: clic derecho sobre el SVG → "Guardar imagen como"

### Soporte 3 — Top-15 mayor volumen
Dashboard → sección "Top-15 Volumen"  
O: `http://localhost:8001/ordenamiento/top-volumen`

### Soporte 4 — Mapa de calor de correlaciones
Dashboard → sección "Req 2 — Mapa de Calor"  
Para exportar: `Ctrl+P` → "Guardar como PDF" (solo esa sección)

### Soporte 5 — Reporte técnico completo (PDF)
Dashboard → sección "Req 4 — Reporte / PDF" → botón "Exportar PDF"  
O: `http://localhost:8001/reporte/txt` → copiar y pegar en Word/Google Docs

### Soporte 6 — Capturas del código fuente
Los archivos clave para mostrar en sustentación:
- `algoritmos/ordenamiento.py` — líneas 1-50 (criterio de ordenamiento)
- `algoritmos/similitud.py` — función `correlacion_pearson()` y `dtw()`
- `etl/limpieza.py` — función `interpolar_linealmente()`
- `algoritmos/volatilidad.py` — función `calcular_var_historico()`

### Soporte 7 — Repositorio GitHub
URL: `https://github.com/andresD1az/proyectoFinalAlgoritmos`  
Muestra el historial de commits como evidencia del proceso de desarrollo.

---

*Universidad del Quindío — Análisis de Algoritmos — 2025*
