# BVC Analytics — Documentación para Exposición

**Universidad del Quindío — Ingeniería de Sistemas y Computación — Análisis de Algoritmos 2026-1**

---

## ESTADO DEL PROYECTO: COMPLETO ✅

Todos los requerimientos están implementados y funcionando. El sistema está corriendo en **http://localhost:8001**

---

## CÓMO LEVANTAR EL PROYECTO (desde cero)

```bash
# 1. Levantar los contenedores
docker compose -f docker-compose.local.yml up -d

# 2. Esperar ~5 segundos y ejecutar los pipelines
docker exec bvc_api python main.py etl           # ~10 min — descarga 5 años de datos
docker exec bvc_api python main.py similitud     # ~5 min — 190 pares × 4 algoritmos
docker exec bvc_api python main.py volatilidad   # ~1 min — métricas de riesgo
docker exec bvc_api python main.py ordenamiento  # ~3 min — benchmark 12 algoritmos

# 3. Abrir el dashboard
# http://localhost:8001
```

---

## REQUERIMIENTO 1 — ETL: Extracción, Limpieza y Unificación de Datos

### Qué hace
Descarga automáticamente 5 años de datos OHLCV (Open, High, Low, Close, Volume) para 20 activos financieros desde Yahoo Finance, los limpia y los carga en PostgreSQL.

### Dónde está el código
| Archivo | Qué hace |
|---|---|
| `config.py` | Define los 20 activos y el horizonte de 5 años |
| `etl/descargador.py` | Descarga HTTP directa sin yfinance |
| `etl/limpieza.py` | Interpolación lineal + Z-Score |
| `etl/database.py` | Carga en PostgreSQL + alineación de calendarios |
| `main.py → pipeline_etl()` | Orquesta todo el proceso |

### Los 20 activos del portafolio
| Grupo | Tickers |
|---|---|
| Colombia ADRs (NYSE) | EC (Ecopetrol), CIB (Bancolombia), GXG (iShares Colombia) |
| ETFs Latinoamérica | ILF, EWZ (Brasil), EWW (México) |
| ETFs Globales | SPY (S&P 500), QQQ (Nasdaq), DIA (Dow Jones), EEM, VT, IEMG |
| Sectores y Commodities | GLD (Oro), SLV (Plata), USO (Petróleo), TLT (Bonos), XLE, XLF, XLK, VNQ |

### Cómo funciona la descarga (sin yfinance)
```python
# etl/descargador.py — construye la URL manualmente
params = urllib.parse.urlencode({
    "period1": timestamp_inicio,   # Unix timestamp 5 años atrás
    "period2": timestamp_fin,      # Unix timestamp hoy
    "interval": "1d",              # datos diarios
    "events": "history"
})
url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?{params}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0..."})
with urllib.request.urlopen(req, timeout=30) as resp:
    raw = json.loads(resp.read().decode("utf-8"))  # parseo manual
```

### Algoritmos de limpieza

**Interpolación Lineal — O(n)**
```
Para cada bloque de Nones entre posiciones izq y der:
    V[k] = V[izq] + (V[der] - V[izq]) × (k - izq) / (der - izq)
```
- Rellena días festivos y diferencias de calendarios entre mercados
- Preserva la tendencia local sin introducir sesgo

**Detección de Outliers Z-Score — O(n)**
```
z_i = (v_i - media) / std
Outlier si |z_i| > 3.5
```
- Umbral 3.5 (no 3.0) porque en finanzas los movimientos extremos son legítimos

**Alineación de calendarios bursátiles**
```python
# etl/database.py → obtener_series_alineadas()
# Calcula la intersección de fechas entre todos los activos
fechas_comunes = set(ticker1_fechas) & set(ticker2_fechas) & ... & set(ticker20_fechas)
# Resultado: todas las series tienen exactamente la misma longitud
# y cada posición i corresponde al mismo día calendario
```

### Resultados
- **20/20 activos** descargados exitosamente
- **~1,255 días** por activo (5 años de historia diaria)
- **~25,100 registros** OHLCV en PostgreSQL
- **~1,272 días comunes** después de alinear calendarios

### Dónde verlo en el dashboard
- **Overview** → card "Registros en BD" muestra el total
- **Reporte/PDF** → Sección 01 muestra la cobertura por activo

---

## REQUERIMIENTO 2 — Algoritmos de Similitud de Series de Tiempo

### Qué hace
Compara pares de series de tiempo financieras usando 4 algoritmos distintos. Calcula los 190 pares posibles (C(20,2)) para cada algoritmo.

### Dónde está el código
| Archivo | Qué hace |
|---|---|
| `algoritmos/similitud.py` | Los 4 algoritmos implementados desde cero |
| `main.py → pipeline_similitud()` | Calcula los 190 pares × 4 algoritmos |
| `api/server.py → _similitud()` | Endpoint GET /similitud |
| `api/server.py → _correlacion_matriz()` | Endpoint GET /correlacion/matriz |

### Los 4 algoritmos

#### 1. Distancia Euclidiana — O(n)
```
d(A, B) = √( Σᵢ (Aᵢ - Bᵢ)² )
```
- Se aplica normalización Min-Max antes: `x_norm = (x - min) / (max - min)`
- **Menor valor = más similar** (d=0 significa series idénticas)
- Mide distancia geométrica en espacio n-dimensional

#### 2. Correlación de Pearson — O(n)
```
r = Σ((Aᵢ - Ā)(Bᵢ - B̄)) / √(Σ(Aᵢ - Ā)² · Σ(Bᵢ - B̄)²)
```
- Rango: [-1, +1]
- **r = +1**: suben y bajan juntos | **r = -1**: movimientos opuestos | **r = 0**: independientes
- No requiere normalización (cancela diferencias de escala)

#### 3. Similitud por Coseno — O(n)
```
cos(θ) = (A · B) / (‖A‖ · ‖B‖)
```
- Rango: [-1, +1]
- Mide el ángulo entre los vectores, no la distancia
- Diferencia con Pearson: no centra los datos (sensible al nivel absoluto)

#### 4. Dynamic Time Warping (DTW) — O(n²)
```
D[i][j] = |A[i] - B[j]| + min(D[i-1][j], D[i][j-1], D[i-1][j-1])
```
- Permite "estirar" el eje temporal para alinear series desfasadas
- Optimización: ventana Sakoe-Chiba al 10% → O(n·0.1n) en la práctica
- Útil cuando dos activos reaccionan al mismo evento con diferente retraso

### Comparación de algoritmos
| Algoritmo | Complejidad | Normalización | Rango | Cuándo usar |
|---|---|---|---|---|
| Euclidiana | O(n) | Requerida | [0, ∞) | Escalas distintas |
| Pearson | O(n) | No necesaria | [-1, +1] | Dirección del movimiento |
| Coseno | O(n) | No necesaria | [-1, +1] | Tendencia relativa |
| DTW | O(n²) | Recomendada | [0, ∞) | Series desfasadas |

### Dónde verlo en el dashboard
- **Comparar Activos** → selecciona 2 activos, ve el gráfico y los 4 valores
- **Mapa de Calor** → matriz 20×20 de correlaciones Pearson
- **Overview** → Top 5 pares más correlacionados

---

## REQUERIMIENTO 3 — Patrones y Medición de Volatilidad

### Qué hace
Detecta patrones en series de precios usando ventana deslizante, y calcula métricas de riesgo para clasificar cada activo.

### Dónde está el código
| Archivo | Qué hace |
|---|---|
| `algoritmos/patrones.py` | Ventana deslizante + 2 patrones + SMA + Golden/Death Cross |
| `algoritmos/volatilidad.py` | Desviación estándar + VaR + Sharpe + Drawdown |
| `api/server.py → _patrones()` | Endpoint GET /patrones |
| `api/server.py → _clasificacion_riesgo()` | Endpoint GET /riesgo/clasificacion |

### Ventana Deslizante — O(n·k)

```
Para i desde 0 hasta n - k:
    segmento = precios[i : i + k]    # k = 20 días
    patron = clasificar(segmento)
```
- **n** = ~1255 días por activo
- **k** = 20 días (configurable en config.py)
- **Ventanas evaluadas** = n - k + 1 = ~1235 por activo

### Patrón 1: Días Consecutivos al Alza (del enunciado)

**Formalización matemática:**
```
dias_alza = |{ j ∈ {1,...,k-1} : P[j] > P[j-1] }|
Condición: dias_alza / (k-1) ≥ 0.75
Nombre: "19_dias_alza"
```
- Al menos el 75% de los días cerraron por encima del día anterior
- Indica tendencia alcista sostenida

### Patrón 2: Rebote en V — V-shape (patrón adicional formalizado)

**Formalización matemática:**
```
m = ⌊k/2⌋  (mitad de la ventana)
primera_mitad_bajista = ∀ j ∈ {1,...,m-1} : P[j] ≤ P[j-1]
segunda_mitad_alcista = ∀ j ∈ {m,...,k-1} : P[j] ≥ P[j-1]
Condición: primera_mitad_bajista AND segunda_mitad_alcista
Nombre: "rebote"
```
- El precio cae sostenidamente y luego se recupera sostenidamente
- Indica reversión de tendencia (el mercado encontró soporte)

**Ejemplo:**
```
Precios: [100, 98, 95, 93, 96, 100]
          ← bajista →  ← alcista →
→ Patrón: "rebote"
```

### Desviación Estándar y Volatilidad — O(n)

```python
# algoritmos/volatilidad.py → calcular_volatilidad()

# Paso 1: Retornos logarítmicos
r_i = ln(P_i / P_{i-1})

# Paso 2: Media de retornos
r_media = Σ(r_j) / k

# Paso 3: Varianza muestral (corrección de Bessel, denominador k-1)
s² = Σ(r_j - r_media)² / (k - 1)

# Paso 4: Desviación estándar diaria
σ_diaria = √s²

# Paso 5: Volatilidad anualizada
σ_anual = σ_diaria × √252
```

**Por qué k-1 (corrección de Bessel):** estimador insesgado de la varianza poblacional.
**Por qué √252:** 252 días de negociación en un año bursátil (no 365).

### Clasificación de Riesgo

| Categoría | Condición | Ejemplos en el portafolio |
|---|---|---|
| Conservador | σ_anual < 15% | TLT (bonos del Tesoro) |
| Moderado | 15% ≤ σ_anual < 30% | SPY (S&P 500), QQQ, DIA |
| Agresivo | σ_anual ≥ 30% | USO (petróleo), GXG (Colombia), SLV |

### Otras métricas implementadas
- **VaR Histórico 95% — O(n log n):** pérdida máxima esperada en un día normal
- **Sharpe Ratio — O(n):** retorno ajustado por riesgo (tasa libre = 5% anual)
- **Máximo Drawdown — O(n):** mayor caída desde un pico hasta un valle

### Dónde verlo en el dashboard
- **Patrones** → selecciona un ticker, ve los patrones detectados y Golden/Death Cross
- **Clasificación Riesgo** → ranking de 20 activos ordenado por volatilidad
- **Overview** → distribución de riesgo (dona) y barras de volatilidad

---

## REQUERIMIENTO 4 — Dashboard Visual y Reporte

### Qué hace
Interfaz web interactiva con visualizaciones de todos los análisis y exportación de reporte técnico en PDF.

### Dónde está el código
| Archivo | Qué hace |
|---|---|
| `interfaz/index.html` | Dashboard SPA completo (HTML5 + CSS3 + JS vanilla) |
| `reportes/generador.py` | Genera reporte técnico con gráficos SVG |
| `api/server.py → _reporte_txt()` | Endpoint GET /reporte/txt |

### Visualizaciones implementadas

#### Mapa de Calor de Correlación (Req 4 explícito)
- Matriz 20×20 de correlaciones Pearson
- Escala de color: rojo (-1) → gris (0) → verde (+1)
- Tooltip interactivo al pasar el mouse
- Generado con SVG puro en JavaScript

#### Gráfico de Velas OHLC con Medias Móviles (Req 4 explícito)
- Canvas HTML5 API (sin librerías de gráficos)
- Velas verdes (alcistas) y rojas (bajistas)
- SMA rápida (default 10 días) en azul
- SMA lenta (default 30 días) en naranja
- Controles: ticker, períodos SMA, rango de días

#### Reporte Técnico PDF (Req 4 explícito)
- Portada profesional con KPIs
- 7 secciones: ETL, Similitud, Volatilidad, Riesgo, Patrones, Ordenamiento, Algoritmos
- 5 gráficos SVG generados en Python puro
- Exportación via `window.print()` del iframe

#### Otras visualizaciones del dashboard
- **Portafolio:** 20 gráficos de precio histórico con sparklines
- **Comparar Activos:** gráfico de líneas % cambio acumulado
- **Benchmark Ordenamiento:** barras horizontales con tiempos
- **Top-15 Volumen:** tabla con barras de volumen

### Dónde verlo
- **http://localhost:8001** → todas las secciones del sidebar

---

## REQUERIMIENTO 5 — Despliegue

### Qué hace
La aplicación está desplegada como servidor web funcional, reproducible y documentada.

### Dónde está el código
| Archivo | Qué hace |
|---|---|
| `api/server.py` | Servidor HTTP puro (http.server stdlib, sin Flask) |
| `docker-compose.local.yml` | Entorno local con PostgreSQL + Python |
| `render.yaml` | Configuración de despliegue en Render |
| `requirements.txt` | Solo psycopg2-binary==2.9.9 |

### Endpoints de la API (18 en total)
```
GET  /                          → Dashboard HTML
GET  /health                    → Estado del servicio
GET  /activos                   → 20 activos con días en BD
GET  /precios?ticker=SPY        → Serie de precios
GET  /precios/ohlcv?ticker=SPY  → Datos OHLCV para velas
GET  /similitud?algoritmo=pearson → 190 pares ordenados
GET  /correlacion/matriz        → Matriz 20×20 para heatmap
GET  /patrones?ticker=SPY       → Patrones detectados
GET  /patrones/cruces?ticker=SPY → Golden/Death Cross
GET  /riesgo/clasificacion      → Ranking de riesgo
GET  /ordenamiento/benchmark    → 12 algoritmos con tiempos
GET  /ordenamiento/top-volumen  → Top-15 días mayor volumen
GET  /reporte                   → Reporte JSON completo
GET  /reporte/txt               → Reporte HTML para PDF
GET  /monedas/tasa              → Tasa USD/COP en tiempo real
GET  /etl/status                → Registros en BD
POST /etl/iniciar               → Dispara ETL en segundo plano
```

---

## RESUMEN DE ALGORITMOS IMPLEMENTADOS (28 en total)

### ETL (2)
| Algoritmo | Complejidad | Archivo |
|---|---|---|
| Interpolación Lineal | O(n) | etl/limpieza.py |
| Detección Outliers Z-Score | O(n) | etl/limpieza.py |

### Similitud (4)
| Algoritmo | Complejidad | Archivo |
|---|---|---|
| Distancia Euclidiana | O(n) | algoritmos/similitud.py |
| Correlación de Pearson | O(n) | algoritmos/similitud.py |
| Similitud por Coseno | O(n) | algoritmos/similitud.py |
| Dynamic Time Warping | O(n²) | algoritmos/similitud.py |

### Patrones (4)
| Algoritmo | Complejidad | Archivo |
|---|---|---|
| Ventana Deslizante | O(n·k) | algoritmos/patrones.py |
| Detección Picos y Valles | O(n) | algoritmos/patrones.py |
| Media Móvil Simple (SMA) | O(n·k) | algoritmos/patrones.py |
| Golden / Death Cross | O(n·k) | algoritmos/patrones.py |

### Volatilidad y Riesgo (5)
| Algoritmo | Complejidad | Archivo |
|---|---|---|
| Retornos Logarítmicos | O(n) | algoritmos/volatilidad.py |
| Volatilidad Histórica Anualizada | O(n) | algoritmos/volatilidad.py |
| Máximo Drawdown | O(n) | algoritmos/volatilidad.py |
| VaR Histórico 95% | O(n log n) | algoritmos/volatilidad.py |
| Sharpe Ratio | O(n) | algoritmos/volatilidad.py |

### Ordenamiento (12)
| Algoritmo | Complejidad | Archivo |
|---|---|---|
| TimSort | O(n log n) | algoritmos/ordenamiento.py |
| Comb Sort | O(n log n) | algoritmos/ordenamiento.py |
| Selection Sort | O(n²) | algoritmos/ordenamiento.py |
| Tree Sort | O(n log n) | algoritmos/ordenamiento.py |
| Pigeonhole Sort | O(n + k) | algoritmos/ordenamiento.py |
| Bucket Sort | O(n + k) | algoritmos/ordenamiento.py |
| QuickSort | O(n log n) | algoritmos/ordenamiento.py |
| HeapSort | O(n log n) | algoritmos/ordenamiento.py |
| Bitonic Sort | O(n log²n) | algoritmos/ordenamiento.py |
| Gnome Sort | O(n²) | algoritmos/ordenamiento.py |
| Binary Insertion Sort | O(n²) | algoritmos/ordenamiento.py |
| RadixSort | O(nk) | algoritmos/ordenamiento.py |

---

## RESTRICCIONES DEL ENUNCIADO — TODAS CUMPLIDAS

| Restricción | Estado | Evidencia |
|---|---|---|
| Sin yfinance ni pandas_datareader | ✅ | urllib.request + json.loads() manual |
| Sin pandas, numpy, scipy, sklearn | ✅ | requirements.txt solo tiene psycopg2 |
| Sin funciones de alto nivel para algoritmos | ✅ | Todo implementado con bucles Python |
| Datos obtenidos automáticamente | ✅ | pipeline_etl() descarga desde cero |
| Reproducibilidad garantizada | ✅ | docker compose + python main.py todo |
| Fórmulas matemáticas documentadas | ✅ | Docstrings en cada función |
| Complejidades explícitas | ✅ | O(n), O(n²), O(n log n) en cada función |
| Patrones adicionales formalizados | ✅ | Rebote V-shape con fórmula matemática |
| Despliegue web funcional | ✅ | http://localhost:8001 |

---

## PREGUNTAS FRECUENTES EN EXPOSICIÓN

**¿Por qué no usaron yfinance?**
El enunciado lo prohíbe explícitamente. Implementamos la descarga con `urllib.request` construyendo la URL manualmente y parseando el JSON de Yahoo Finance API v8 directamente.

**¿Por qué el umbral del Z-Score es 3.5 y no 3.0?**
En finanzas, los retornos tienen "colas pesadas" (fat tails). Un crash del mercado o un rally extremo son eventos legítimos que no deben eliminarse. El umbral 3.5 es más conservador y evita descartar movimientos reales.

**¿Por qué se usa √252 para anualizar la volatilidad?**
252 es el número de días de negociación en un año bursátil (no 365, porque los mercados no operan fines de semana ni festivos). La volatilidad diaria se escala a anual multiplicando por √252 porque la varianza es aditiva en el tiempo.

**¿Por qué DTW es mejor que Euclidiana para series desfasadas?**
La Euclidiana compara posición a posición (día 1 con día 1, día 2 con día 2). Si dos activos reaccionan al mismo evento con 3 días de diferencia, la Euclidiana los verá como muy distintos. DTW permite "estirar" el eje temporal para encontrar la alineación óptima.

**¿Qué es la corrección de Bessel en la varianza?**
Al calcular la varianza de una muestra (no de toda la población), dividir por k-1 en lugar de k produce un estimador insesgado. Con k se subestimaría la varianza real de la distribución.

**¿Qué es el Sharpe Ratio?**
Mide el retorno extra que ofrece un activo por cada unidad de riesgo asumida, comparado con una inversión sin riesgo (bonos del Tesoro al 5% anual). Sharpe > 1 es bueno, Sharpe < 0 significa que el activo rinde menos que los bonos.

**¿Qué es el VaR histórico?**
"Con 95% de confianza, la pérdida diaria no superará X%". Se calcula ordenando todos los retornos históricos y tomando el percentil 5%. No asume distribución normal — usa los datos reales.

---

## FLUJO COMPLETO DEL SISTEMA

```
Yahoo Finance API v8
        ↓ urllib.request (HTTP directo)
etl/descargador.py
        ↓ 20 activos × ~1255 días = ~25,100 registros crudos
etl/limpieza.py
        ↓ Interpolación lineal + Z-Score + validación
etl/database.py → PostgreSQL
        ↓
        ├── algoritmos/similitud.py → 190 pares × 4 algoritmos → BD
        ├── algoritmos/volatilidad.py → métricas de riesgo → BD
        ├── algoritmos/patrones.py → patrones detectados
        └── algoritmos/ordenamiento.py → benchmark 12 algoritmos → BD
                ↓
        api/server.py (http.server stdlib)
                ↓ 18 endpoints HTTP/JSON
        interfaz/index.html (HTML5 + JS vanilla)
                ↓
        reportes/generador.py → PDF con gráficos SVG
```

---

*Universidad del Quindío — Análisis de Algoritmos — 2026-1*
*Proyecto completamente funcional en http://localhost:8001*
