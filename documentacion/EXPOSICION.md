# Guía de Exposición — BVC Analytics
Universidad del Quindío — Análisis de Algoritmos

---

## Flujo de ejecución (para arrancar antes de exponer)

```bash
# 1. Levantar contenedores
cp .env.example .env
docker compose -f docker-compose.local.yml up --build -d

# 2. ETL — descarga 5 años de datos (~10 min)
docker exec bvc_api python main.py etl

# 3. Similitud — 190 pares × 4 algoritmos (DTW tarda varios minutos)
docker exec bvc_api python main.py similitud

# 4. Volatilidad
docker exec bvc_api python main.py volatilidad

# 5. Ordenamiento — benchmark 12 algoritmos
docker exec bvc_api python main.py ordenamiento

# Ver logs en tiempo real
docker logs -f bvc_api
```

Dashboard en: http://localhost:8001

---

## Orden de exposición archivo por archivo

---

### 1. `config.py` — 30 seg

Qué hace:
- Define los 20 activos del portafolio con ticker, nombre, tipo y mercado
- Calcula FECHA_INICIO y FECHA_FIN automáticamente (5 años hacia atrás desde hoy)
- Centraliza todos los parámetros: ventana deslizante 20 días, umbral similitud 0.75, ventana volatilidad 30 días
- Lee las variables de entorno para la conexión a PostgreSQL (DB_HOST, DB_USER, etc.)
- Si existe DATABASE_URL (formato Render/Heroku), la parsea con regex manualmente

Qué decir:
"Aquí están los 20 activos que analizamos y todos los parámetros del sistema.
Cualquier cambio de parámetro se hace en un solo lugar."

Portafolio:
- 2 ADRs colombianos en NYSE: EC (Ecopetrol), CIB (Bancolombia)
- 1 ETF Colombia: GXG
- 3 ETFs Latinoamérica: ILF, EWZ, EWW
- 6 ETFs globales: SPY, QQQ, DIA, EEM, VT, IEMG
- 8 ETFs sectoriales/commodities: GLD, SLV, USO, TLT, XLE, XLF, XLK, VNQ

---

### 2. `etl/descargador.py` — 1 min

Qué hace:
- Construye la URL de Yahoo Finance manualmente con urllib.parse.urlencode
  URL: https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?period1=...&period2=...&interval=1d&events=history
- Hace la petición HTTP con urllib.request (stdlib pura, sin requests ni yfinance)
- Parsea el JSON con json.loads()
- Convierte cada Unix timestamp a fecha con datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
- 3 reintentos con pausa de 1 segundo entre peticiones
- Retorna lista de dicts: {fecha, apertura, maximo, minimo, cierre, volumen}
- descargar_todos() itera los 20 activos con pausa de 1s entre cada uno (scraping ético)

Qué decir:
"Construimos la URL manualmente, parseamos el JSON a mano y convertimos
los timestamps Unix a fechas. Sin yfinance, sin requests."

---

### 3. `etl/limpieza.py` — 1 min

Qué hace:
- limpiar_dataset(): 4 pasos en orden:
  1. Ordena por fecha ASC
  2. Elimina filas con cierre <= 0 (precio negativo es físicamente imposible)
  3. Interpola linealmente columnas OHLC individualmente
  4. Rellena volumen nulo con 0 (el volumen no se interpola)

- interpolar_linealmente(): implementa la fórmula:
  V[k] = V[izq] + (V[der] - V[izq]) × (k - izq) / (der - izq)
  Casos especiales: Nones al inicio → backward fill, al final → forward fill

- detectar_outliers_zscore(): calcula media y std manualmente, umbral 3.5
  z = (x - media) / std → outlier si |z| > 3.5
  Umbral 3.5 en lugar del estándar 3.0 porque en finanzas los movimientos
  extremos son legítimos (crashes, rallies)

Qué decir:
"Aquí está la interpolación lineal implementada desde cero.
El umbral Z-Score es 3.5 y no 3.0 porque en finanzas los movimientos
extremos son reales, no errores."

---

### 4. `etl/database.py` — 30 seg (opcional, mostrar rápido)

Qué hace:
- Capa de acceso a datos con psycopg2 puro, sin ORM
- init_schema(): crea las 6 tablas si no existen (activos, precios, resultados_similitud,
  resultados_volatilidad, resultados_sorting, top_volumen)
- insertar_precios_lote(): usa executemany + ON CONFLICT DO NOTHING (idempotente)
- obtener_precios(): query con JOIN activos, ordenado ASC por fecha
- guardar_similitud(), guardar_volatilidad(): insertan resultados de los algoritmos

---

### 5. `algoritmos/ordenamiento.py` — 2 min

Qué hace:
- 12 algoritmos implementados desde cero, sin sorted() ni .sort()
- Todos ordenan por: fecha ASC (primario), cierre ASC (secundario)
- Clave de comparación: _clave(registro) → (str(fecha), float(cierre))

Los 12 algoritmos:
1.  TimSort              O(n log n)  — runs de 32 + merge progresivo
2.  Comb Sort            O(n log n)  — Bubble Sort con gap que reduce por factor 1.3
3.  Selection Sort       O(n²)       — busca el mínimo en cada iteración
4.  Tree Sort            O(n log n)  — inserta en BST, extrae en recorrido in-orden
5.  Pigeonhole Sort      O(n + k)    — palomares indexados por fecha como entero YYYYMMDD
6.  Bucket Sort          O(n + k)    — cubetas por fecha normalizada [0,1]
7.  QuickSort            O(n log n)  — pivote mediana-de-tres, partición Lomuto
8.  HeapSort             O(n log n)  — max-heap, build O(n) + n extracciones O(log n)
9.  Bitonic Sort         O(n log²n)  — requiere potencia de 2, rellena con centinela
10. Gnome Sort           O(n²)       — avanza si ok, retrocede e intercambia si no
11. Binary Insertion Sort O(n²)      — búsqueda binaria O(log n) para posición, desplazamiento O(n)
12. RadixSort            O(nk)       — 8 pasadas (dígitos de YYYYMMDD) con Counting Sort estable

Benchmark: ejecutar_benchmark() corre los 12 sobre 5.000 registros y mide con time.perf_counter()
top15_mayor_volumen(): HeapSort por volumen DESC, extrae los 15 mayores, reordena ASC

Qué decir:
"Mostramos TimSort (el más rápido) y Selection Sort (el más lento).
Tree Sort puede degenerar a O(n²) si el árbol queda desbalanceado
porque los datos ya vienen ordenados por fecha."

---

### 6. `algoritmos/similitud.py` — 2 min

Qué hace:
- 4 algoritmos que comparan pares de series de precios de cierre
- Calcula los 190 pares: C(20,2) = 20×19/2 = 190 (triángulo superior de la matriz)

Algoritmo 1 — Distancia Euclidiana O(n):
  d(A,B) = √(Σ(Aᵢ - Bᵢ)²)
  Aplica normalización Min-Max antes: x_norm = (x - min) / (max - min)
  Sin normalización, la diferencia de escala dominaría (EC cotiza $5-15, SPY $300-500)

Algoritmo 2 — Correlación de Pearson O(n):
  r = Σ((Aᵢ-Ā)(Bᵢ-B̄)) / √(Σ(Aᵢ-Ā)² · Σ(Bᵢ-B̄)²)
  Rango [-1, 1]. No requiere normalización porque trabaja con desviaciones respecto a la media.
  r=+1: se mueven igual, r=-1: se mueven opuesto, r=0: independientes

Algoritmo 3 — Similitud Coseno O(n):
  cos(θ) = (A·B) / (‖A‖·‖B‖) = Σ(Aᵢ·Bᵢ) / (√Σ(Aᵢ²) · √Σ(Bᵢ²))
  Diferencia con Pearson: coseno no centra los datos (no resta la media)

Algoritmo 4 — DTW O(n²):
  Programación dinámica. Matriz (n+1)×(m+1).
  matriz[i][j] = |A[i-1]-B[j-1]| + min(matriz[i-1][j], matriz[i][j-1], matriz[i-1][j-1])
  Ventana Sakoe-Chiba: restringe la búsqueda a una banda diagonal de ancho w = n × 10%
  Reduce de O(n²) a O(n·w). Evita alineaciones irrazonables.

Qué decir:
"DTW permite comparar series desfasadas en el tiempo. La ventana Sakoe-Chiba
al 10% evita que compare el primer día de una serie con el último de la otra."

---

### 7. `algoritmos/patrones.py` — 1 min

Qué hace:
- detectar_patrones(): ventana deslizante de 20 días sobre la serie de precios
  Para cada posición i: segmento = precios[i : i+20]
  Clasifica con _clasificar_segmento():
    - Si ≥75% de días son alza → "N_dias_alza"
    - Si ≥75% de días son baja → "N_dias_baja"
    - Si primera mitad baja Y segunda mitad sube → "rebote" (V-shape)
    - Otro caso → "neutro" (no se guarda)
  Total de ventanas: n - 20 + 1

- detectar_picos_valles(): para cada punto i, compara con vecindad de 3 días
  Es pico si precios[i] >= todos en ventana[i-3 : i+4]
  Es valle si precios[i] <= todos en ventana[i-3 : i+4]

- media_movil_simple(): SMA[i] = (P[i] + P[i-1] + ... + P[i-k+1]) / k

- detectar_cruces_medias(): Golden Cross cuando SMA10 cruza SMA30 hacia arriba,
  Death Cross cuando SMA10 cruza SMA30 hacia abajo

Qué decir:
"La ventana deslizante evalúa cada segmento de 20 días y lo clasifica.
El patrón rebote es el V-shape: primera mitad bajista, segunda alcista."

---

### 8. `algoritmos/volatilidad.py` — 1 min

Qué hace:
- calcular_retornos_log(): rᵢ = ln(Pᵢ / Pᵢ₋₁)
  Ventaja sobre retornos simples: son aditivos en el tiempo y más simétricos

- calcular_volatilidad(): ventana rodante de 30 días
  1. Media de retornos: r̄ = Σ(rⱼ) / k
  2. Varianza muestral con corrección de Bessel: s² = Σ(rⱼ - r̄)² / (k-1)
     Se usa k-1 (no k) para estimador insesgado de la varianza poblacional
  3. Volatilidad diaria: σ = √s²
  4. Volatilidad anualizada: σ_anual = σ × √252
     252 = días de negociación en un año bursátil (no 365)
  Clasificación: Conservador σ<15%, Moderado 15-30%, Agresivo σ>30%

- calcular_var_historico(): método histórico O(n log n)
  Ordena retornos ASC, toma el percentil 5% (para VaR 95%)
  No asume distribución normal, usa los retornos reales observados

- calcular_sharpe(): Sharpe = (R_anual - 5%) / σ_anual
  Tasa libre de riesgo: 5% anual (bonos del Tesoro EE.UU. a 10 años)

- calcular_max_drawdown(): una sola pasada O(n)
  Mantiene el pico máximo visto, calcula drawdown = (precio - pico) / pico
  MDD = el mínimo de todos los drawdowns

Qué decir:
"La corrección de Bessel usa k-1 en el denominador para un estimador insesgado.
El factor √252 anualiza la volatilidad porque hay 252 días de negociación al año."

---

### 9. `api/server.py` — 30 seg

Qué hace:
- ThreadingHTTPServer de stdlib (sin Flask, sin FastAPI)
- BVCHandler extiende BaseHTTPRequestHandler
- do_GET() y do_POST() mapean rutas a métodos privados
- _respuesta_json(): serializa con json.dumps y agrega header CORS
- POST /etl/iniciar: lanza pipeline_etl() en threading.Thread daemon
- Sirve el frontend HTML en GET /

18 endpoints en total.

---

### 10. `main.py` — 15 seg

Qué hace:
- Lee sys.argv[1] para decidir qué pipeline correr
- Modos: etl, similitud, volatilidad, ordenamiento, api, todo
- "todo" los corre en secuencia con pausas entre pipelines
- Es el punto de entrada para docker exec bvc_api python main.py etl

---

### 11. Dashboard en el navegador — 2 min

Abrir http://localhost:8001 y mostrar:

- Overview: 20 activos, registros en BD, 190 pares de similitud, 28 algoritmos
- Comparar Activos: tabla de pares Pearson ordenada por correlación DESC
- Mapa de Calor: matriz 20×20 de correlaciones Pearson
- Patrones: ventana deslizante por ticker, Golden/Death Cross
- Clasificación Riesgo: ranking de los 20 activos por volatilidad anualizada
- Tabla 1 + Barras: benchmark de los 12 algoritmos con tiempos reales
- Top-15 Volumen: los 15 días con mayor volumen de negociación
- Velas OHLC: gráfico de velas con SMA10 y SMA30 superpuestas
- Reporte/PDF: reporte técnico completo en texto plano
- Tasa USD/COP: consulta en tiempo real a Yahoo Finance (COP=X)

---

## Restricción clave para mencionar

requirements.txt tiene UNA sola dependencia:
  psycopg2-binary==2.9.9  ← solo para conectar a PostgreSQL

Todo lo demás es Python stdlib:
  urllib     → descarga HTTP
  json       → parseo de respuestas
  math       → cálculos matemáticos
  http.server → servidor HTTP
  threading  → ETL en background
  time       → benchmark de algoritmos
  datetime   → conversión de timestamps

Sin pandas, numpy, scipy, sklearn, yfinance, requests, Flask, FastAPI.

---

## Complejidades para mencionar si preguntan

| Algoritmo | Complejidad | Nota |
|---|---|---|
| Interpolación lineal | O(n) | Una pasada sobre la serie |
| Z-Score outliers | O(n) | Media + std + comparación |
| TimSort | O(n log n) | El más rápido en benchmark |
| Selection Sort | O(n²) | El más lento en benchmark |
| Pearson | O(n) | Sin normalización previa |
| Euclidiana | O(n) | Con normalización Min-Max |
| DTW | O(n²) → O(n·w) | Sakoe-Chiba reduce a O(n·w) |
| Ventana deslizante | O(n·k) | n posiciones × k días |
| Volatilidad rodante | O(n) | Una pasada por ventana |
| VaR histórico | O(n log n) | Dominado por el sort |
| Max Drawdown | O(n) | Una sola pasada |

---

*No subir este archivo — solo para la exposición*
