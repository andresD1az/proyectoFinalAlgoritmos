# Seguimiento 1  Análisis de Algoritmos

**Universidad del Quindío**
**Programa de Ingeniería de Sistemas y Computación**
**Análisis de Algoritmos  Proyecto Final**

---

## 1. Introducción

El análisis financiero moderno depende en gran medida de la capacidad computacional para procesar grandes volúmenes de datos históricos y detectar patrones relevantes en el comportamiento de los activos financieros. En los mercados actuales, donde la información se genera de manera continua y a gran escala, resulta indispensable el uso de algoritmos eficientes que permitan comparar, agrupar y analizar series de tiempo financieras de forma rigurosa.

Este proyecto aplica métodos cuantitativos, algoritmos clásicos y técnicas de análisis de series temporales sobre datos reales provenientes de la Bolsa de Valores de Colombia (BVC) y de activos globales relevantes para el inversor local, como índices bursátiles y ETFs internacionales (S&P 500). El enfoque principal se centra en el análisis algorítmico del comportamiento histórico de precios, retornos y volatilidad, con el fin de establecer relaciones de similitud, detectar patrones recurrentes y construir agrupamientos basados exclusivamente en criterios matemáticos y computacionales.

---

## 2. Fuentes de Información

La información financiera se obtiene de Yahoo Finance mediante peticiones HTTP directas con `urllib.request` (stdlib de Python). No se usa `yfinance`, `pandas_datareader` ni ninguna librería de alto nivel.

| Campo  | Descripción                      |
|--------|----------------------------------|
| Fecha  | Fecha de cotización (YYYY-MM-DD) |
| Open   | Precio de apertura               |
| Close  | Precio de cierre                 |
| High   | Precio máximo del día            |
| Low    | Precio mínimo del día            |
| Volume | Volumen de negociación           |

Horizonte histórico: **5 años** | Portafolio: **20 activos**

---

## 3. Portafolio de Activos

| Ticker | Nombre                   | Tipo   | Mercado |
|--------|--------------------------|--------|---------|
| EC     | Ecopetrol S.A.           | Acción | NYSE    |
| CIB    | Bancolombia S.A.         | Acción | NYSE    |
| GXG    | iShares MSCI Colombia    | ETF    | NYSE    |
| ILF    | iShares Latin America 40 | ETF    | NYSE    |
| EWZ    | iShares MSCI Brazil      | ETF    | NYSE    |
| EWW    | iShares MSCI Mexico      | ETF    | NYSE    |
| SPY    | S&P 500 ETF              | ETF    | NYSE    |
| QQQ    | Nasdaq 100 ETF           | ETF    | NASDAQ  |
| DIA    | Dow Jones ETF            | ETF    | NYSE    |
| EEM    | Emerging Markets ETF     | ETF    | NYSE    |
| VT     | Vanguard Total World     | ETF    | NYSE    |
| IEMG   | Core Emerging Markets    | ETF    | NYSE    |
| GLD    | SPDR Gold Shares         | ETF    | NYSE    |
| SLV    | iShares Silver Trust     | ETF    | NYSE    |
| USO    | US Oil Fund              | ETF    | NYSE    |
| TLT    | iShares 20Y Treasury     | ETF    | NASDAQ  |
| XLE    | Energy Select Sector     | ETF    | NYSE    |
| XLF    | Financial Select Sector  | ETF    | NYSE    |
| XLK    | Technology Select Sector | ETF    | NYSE    |
| VNQ    | Vanguard Real Estate     | ETF    | NYSE    |

---

## 4. Arquitectura General del Sistema

```
bvc-analytics/
 etl/
    downloader.py     # Descarga HTTP pura (urllib)
    cleaner.py        # Interpolación lineal + Z-Score
    database.py       # Acceso a PostgreSQL (psycopg2)
 algorithms/
    sorting.py        # 12 algoritmos de ordenamiento (Req. 2)
    similarity.py     # 4 algoritmos de similitud (Req. 2 enunciado completo)
    patterns.py       # Ventana deslizante, SMA, Golden Cross (Req. 3)
    volatility.py     # VaR, Sharpe, Drawdown, Volatilidad (Req. 3)
 api/server.py         # Servidor HTTP stdlib  sin Flask/Django
 auth/auth.py          # Autenticación SHA-256 + sesiones
 cms/content.py        # Lecciones financieras + paper trading
 reports/generator.py  # Reportes JSON y TXT (Req. 4)
 frontend/index.html   # Dashboard SPA  SVG + Canvas (Req. 4)
 database/init.sql     # Esquema PostgreSQL completo
 main.py               # Orquestador de pipelines
 config.py             # Configuración global
 docker-compose.yml    # PostgreSQL 15 + API (Req. 5)
```

**Stack tecnológico:**

| Capa          | Tecnología                              |
|---------------|-----------------------------------------|
| Backend       | Python 3.11 (solo stdlib para lógica)   |
| Base de datos | PostgreSQL 15                           |
| Servidor HTTP | http.server (stdlib)  sin frameworks   |
| Frontend      | HTML5 + CSS3 + JavaScript vanilla       |
| Visualización | SVG + Canvas API  sin matplotlib       |
| Contenedores  | Docker + Docker Compose                 |
| Dependencia   | psycopg2-binary (solo driver de BD)     |

---

## 5. Requerimiento 1 — ETL Automatizado

### 5.1 Descripcion

Se implemento un proceso completamente automatizado de Extraccion, Transformacion y Carga (ETL)
que descarga, limpia y almacena 5 anos de datos OHLCV para los 20 activos.
Archivos: etl/downloader.py, etl/cleaner.py, etl/database.py
Ejecucion: python main.py etl

### 5.2 Flujo del ETL

```
Yahoo Finance (API v8 JSON)
        |
urllib.request — peticion HTTP directa (stdlib)
        |
Parsing manual del JSON (timestamps Unix -> fechas ISO)
        |
Deteccion de outliers con Z-Score — O(n)
        |
Interpolacion lineal para valores faltantes — O(n)
        |
PostgreSQL — tabla unificada `precios`
```

### 5.3 Descarga — etl/downloader.py

URL: https://query1.finance.yahoo.com/v8/finance/chart/{ticker}
     ?period1={unix_inicio}&period2={unix_fin}&interval=1d

- Libreria: urllib.request (stdlib — permitida)
- Sin yfinance, pandas_datareader ni requests
- Timestamps Unix a fechas: implementado manualmente
- Manejo de errores: 3 reintentos con pausa entre intentos
- Pausa entre tickers: 1 segundo (scraping etico)

### 5.4 Limpieza — etl/cleaner.py

**Algoritmo 1: Z-Score para Outliers — O(n)**

```
z = (x - mu) / sigma
Si |z| > 3.5 el registro se descarta
```

Implementado con sumas manuales, sin statistics.stdev ni numpy.

**Algoritmo 2: Interpolacion Lineal — O(n)**

```
V[i] = V[izq] + (V[der] - V[izq]) * (i - izq) / (der - izq)
Nones al inicio: backward fill con el primer valor conocido
Nones al final:  forward fill con el ultimo valor conocido
```

Justificacion: preserva la tendencia sin distorsionar los datos; adecuado para dias festivos.

### 5.5 Almacenamiento — etl/database.py

Tabla `precios` en PostgreSQL: id, activo_id, fecha, apertura, maximo, minimo, cierre, volumen.
UNIQUE (activo_id, fecha) — idempotente.
Manejo de calendarios distintos: interpolacion lineal resuelve desalineaciones entre NYSE y NASDAQ.

---

## 6. Requerimiento 2 — Algoritmos de Ordenamiento

### 6.1 Descripcion

12 algoritmos implementados desde cero en algorithms/sorting.py, sin sorted() ni .sort().
Criterio compuesto: fecha ASC (primario), cierre ASC (secundario).
Ejecucion: python main.py ordenamiento

### 6.2 Clave de Comparacion

```python
def _clave(registro: dict) -> tuple:
    return (str(registro["fecha"]), float(registro["cierre"]))
```

### 6.3 Tabla 1 — Analisis de Algoritmos de Ordenamiento

Dataset: ~25.000 registros (20 activos x ~1.260 dias habiles). Tiempos con time.perf_counter().

| #  | Metodo de Ordenamiento | Complejidad  | Tamano  | Tiempo (ms)   |
|----|------------------------|--------------|---------|---------------|
|  1 | TimSort                | O(n log n)   | ~25.000 | ver benchmark |
|  2 | Comb Sort              | O(n log n)   | ~25.000 | ver benchmark |
|  3 | Selection Sort         | O(n^2)       | ~25.000 | ver benchmark |
|  4 | Tree Sort              | O(n log n)   | ~25.000 | ver benchmark |
|  5 | Pigeonhole Sort        | O(n + k)     | ~25.000 | ver benchmark |
|  6 | Bucket Sort            | O(n + k)     | ~25.000 | ver benchmark |
|  7 | QuickSort              | O(n log n)   | ~25.000 | ver benchmark |
|  8 | HeapSort               | O(n log n)   | ~25.000 | ver benchmark |
|  9 | Bitonic Sort           | O(n log^2 n) | ~25.000 | ver benchmark |
| 10 | Gnome Sort             | O(n^2)       | ~25.000 | ver benchmark |
| 11 | Binary Insertion Sort  | O(n^2)       | ~25.000 | ver benchmark |
| 12 | RadixSort              | O(nk)        | ~25.000 | ver benchmark |

Valores exactos: python main.py ordenamiento o GET /ordenamiento/benchmark

### 6.4 Descripcion Tecnica de Cada Algoritmo

1. TimSort O(n log n): Runs de 32 con Insertion Sort, fusionados con Merge Sort progresivo.
2. Comb Sort O(n log n): Bubble Sort con brecha decreciente factor 1.3 para eliminar tortugas.
3. Selection Sort O(n^2): Minimo en arr[i..n-1] intercambiado con arr[i]. Siempre n(n-1)/2 comparaciones.
4. Tree Sort O(n log n): Insercion en BST, extraccion en recorrido in-orden (izq -> raiz -> der).
5. Pigeonhole Sort O(n+k): Cubeta por cada valor entero de fecha YYYYMMDD en [min, max].
6. Bucket Sort O(n+k): Normaliza fechas a [0,n-1], n cubetas con Insertion Sort interno.
7. QuickSort O(n log n) promedio: Particion Lomuto con pivote mediana-de-tres.
8. HeapSort O(n log n): Build Max-Heap O(n) + extraccion sucesiva O(n log n).
9. Bitonic Sort O(n log^2 n): Potencia de 2 con centinela. Secuencias bitonicas recursivas.
10. Gnome Sort O(n^2): Avanza si arr[i]>=arr[i-1], retrocede e intercambia si no.
11. Binary Insertion Sort O(n^2): Busqueda binaria para posicion O(log n), desplazamiento O(n).
12. RadixSort O(nk): Counting Sort estable LSD sobre 8 digitos de fecha YYYYMMDD.

### 6.5 Diagrama de Barras de Tiempos

GET /ordenamiento/benchmark retorna los 12 resultados ASC por tiempo.
El frontend los visualiza con SVG/Canvas API sin librerias externas.
Los algoritmos O(n^2) aparecen con barras notablemente mas largas que los O(n log n).

### 6.6 Top-15 Dias con Mayor Volumen

top15_mayor_volumen() usa HeapSort manual sobre campo volumen:
1. Build Max-Heap sobre dataset completo — O(n)
2. Extraer los 15 maximos del heap — O(15 log n)
3. Reordenar los 15 ASC por volumen — O(1)
Resultado: GET /ordenamiento/top-volumen

---

## 7. Requerimiento 3 — Similitud de Series de Tiempo

### 7.1 Descripcion

Se implementaron 4 algoritmos de similitud en algorithms/similarity.py desde cero, sin numpy,
scipy ni sklearn. Permiten comparar cualquier par de los 20 activos.
Ejecucion: python main.py similitud

### 7.2 Algoritmos Implementados

#### Algoritmo 1: Distancia Euclidiana — O(n)

Mide la distancia geometrica entre dos series normalizadas.

```
Normalizacion Min-Max:
  x_norm = (x - min) / (max - min)

Distancia:
  d(A, B) = sqrt( sum_i (A_i - B_i)^2 )
```

- Resultado: 0 = series identicas, mayor valor = mas diferentes
- Normalizacion necesaria cuando las escalas difieren (COP vs USD)
- Complejidad: O(n) — un barrido de la serie

#### Algoritmo 2: Correlacion de Pearson — O(n)

Mide la relacion lineal entre dos series de retornos.

```
r = cov(A, B) / (sigma_A * sigma_B)

cov(A, B) = sum_i (A_i - A_mean)(B_i - B_mean) / (n-1)
sigma_A   = sqrt( sum_i (A_i - A_mean)^2 / (n-1) )
```

- Resultado: [-1, 1]. 1 = perfectamente correlacionados, -1 = inversamente correlacionados
- Complejidad: O(n) — calcula medias y covarianza en un barrido

#### Algoritmo 3: Similitud por Coseno — O(n)

Mide el angulo entre dos vectores de rendimientos diarios.

```
cos(theta) = (A . B) / (|A| * |B|)

A . B = sum_i (A_i * B_i)
|A|   = sqrt( sum_i A_i^2 )
```

- Invariante a la escala (no requiere normalizacion previa)
- Resultado: [0, 1] para retornos positivos
- Complejidad: O(n)

#### Algoritmo 4: DTW (Dynamic Time Warping) — O(n^2)

Compara secuencias que pueden diferir en velocidad o fase.

```
DTW(i, j) = dist(A_i, B_j) + min(
    DTW(i-1, j),    # insercion
    DTW(i, j-1),    # eliminacion
    DTW(i-1, j-1)   # coincidencia
)
```

- Banda Sakoe-Chiba (10% de n) para reducir complejidad de O(n^2) a O(n * 0.1n)
- Util para comparar activos con desfases temporales (ej. mercados en distintas zonas horarias)
- Complejidad: O(n^2) sin banda, O(n * w) con banda w

### 7.3 Comparacion de Algoritmos

| Algoritmo          | Complejidad | Escala-invariante | Desfase temporal | Uso recomendado |
|--------------------|-------------|-------------------|------------------|-----------------|
| Euclidiana         | O(n)        | No (requiere norm)| No               | Precios normalizados |
| Pearson            | O(n)        | Si                | No               | Retornos lineales |
| Coseno             | O(n)        | Si                | No               | Vectores de rendimiento |
| DTW                | O(n^2)      | No                | Si               | Series con desfase |

### 7.4 Resultados

- 190 pares de activos (C(20,2) = 190)
- 4 algoritmos x 190 pares = 760 valores de similitud calculados
- Almacenados en tabla resultados_similitud en PostgreSQL
- Disponibles en: GET /similitud?algoritmo=pearson|coseno|euclidiana|dtw

---

## 8. Requerimiento 4 — Patrones y Volatilidad

### 8.1 Ventana Deslizante — algorithms/patterns.py

#### Algoritmo: Sliding Window — O(n * k)

Recorre el historial de precios con una ventana de k dias y clasifica cada segmento.

```
Para cada posicion i (de 0 a n-k):
    segmento = precios[i : i + k]
    variacion_pct = (precio_final - precio_inicial) / precio_inicial * 100
    patron = clasificar_segmento(segmento)
```

**Patron 1 — Alza consecutiva:** todos los dias del segmento tienen cierre > cierre anterior.
**Patron 2 — Baja consecutiva:** todos los dias del segmento tienen cierre < cierre anterior.
**Patron 3 — Rebote:** primera mitad a la baja, segunda mitad al alza.
**Patron 4 — Neutro:** sin tendencia clara.

Ventana configurable en config.py (default: 20 dias).
Ejecucion: GET /patrones?ticker=SPY

#### Algoritmo adicional: Golden Cross / Death Cross — O(n)

Detecta cruces entre dos medias moviles simples (SMA).

```
SMA_corta[i] = promedio(precios[i-c+1 : i+1])
SMA_larga[i] = promedio(precios[i-l+1 : i+1])

Golden Cross: SMA_corta cruza SMA_larga hacia arriba (senal alcista)
Death Cross:  SMA_corta cruza SMA_larga hacia abajo (senal bajista)
```

Ejecucion: GET /patrones/cruces?ticker=SPY&corta=10&larga=30

### 8.2 Volatilidad y Clasificacion de Riesgo — algorithms/volatility.py

#### Algoritmo 1: Retornos Logaritmicos — O(n)

```
r_i = ln(P_i / P_{i-1})
```

Ventaja sobre retornos simples: aditivos en el tiempo, distribucion mas cercana a la normal.

#### Algoritmo 2: Volatilidad Historica — O(n)

```
Paso 1: Calcular retornos logaritmicos
Paso 2: Para cada ventana de k retornos:
    media_r = sum(r) / k
    varianza = sum((r_i - media_r)^2) / (k-1)   [correccion de Bessel]
    sigma_diaria = sqrt(varianza)
    sigma_anual  = sigma_diaria * sqrt(252)
```

#### Algoritmo 3: Maximo Drawdown — O(n)

```
MDD = (valle_minimo - pico_maximo) / pico_maximo * 100
```

Mantiene el pico maximo visto hasta i y calcula la caida en cada punto.

#### Algoritmo 4: VaR Historico — O(n log n)

```
1. Calcular todos los retornos logaritmicos
2. Ordenar ascendentemente (peores primero)
3. VaR_95 = retorno en el percentil 5%
```

Interpretacion: con 95% de confianza, la perdida diaria no superara este valor.

#### Algoritmo 5: Sharpe Ratio — O(n)

```
Sharpe = (R_portfolio - R_libre_riesgo) / sigma_portfolio

R_portfolio    = media_retornos_diarios * 252
sigma_portfolio = sigma_diaria * sqrt(252)
```

#### Clasificacion de Riesgo

| Categoria    | Volatilidad Anualizada |
|--------------|------------------------|
| Conservador  | < 15%                  |
| Moderado     | 15% — 30%              |
| Agresivo     | > 30%                  |

El sistema genera un listado de los 20 activos ordenados por nivel de riesgo.
Ejecucion: GET /riesgo/clasificacion

---

## 9. Requerimiento 5 — Dashboard Visual y Despliegue

### 9.1 Dashboard — frontend/index.html

SPA completa en HTML5 + CSS3 + JavaScript vanilla, sin React, Vue ni Angular.
Visualizaciones implementadas con SVG y Canvas API (sin matplotlib, plotly ni Chart.js).

**Secciones del dashboard:**

| Seccion              | Descripcion                                              |
|----------------------|----------------------------------------------------------|
| Overview             | Estadisticas generales, top pares similares, distribucion de riesgo |
| Comparar Activos     | Seleccion de 2 activos, grafico de lineas SVG, 4 metricas de similitud |
| Mapa de Calor        | Matriz de correlacion 20x20 con gradiente de color SVG   |
| Velas OHLC           | Grafico candlestick con Canvas API + SMA superpuesta     |
| Clasificacion Riesgo | Ranking de 20 activos por volatilidad anualizada         |
| Ordenamiento         | Diagrama de barras de tiempos de los 12 algoritmos       |
| Top Volumen          | Top-15 dias con mayor volumen de negociacion             |
| Academia             | 8 lecciones de educacion financiera                      |
| Simulador            | Paper trading con USD 100.000 virtuales                  |
| Tasa USD/COP         | Tasa de cambio en tiempo real (Yahoo Finance COP=X)      |

### 9.2 Matriz de Correlacion (Mapa de Calor)

Construida desde los resultados de Pearson almacenados en BD.
Matriz 20x20 con gradiente de color: rojo (correlacion negativa) -> blanco (0) -> azul (correlacion positiva).
Endpoint: GET /correlacion/matriz

### 9.3 Graficos de Velas (Candlestick)

Implementados con Canvas API:
- Cuerpo de la vela: rectangulo verde (cierre > apertura) o rojo (cierre < apertura)
- Mechas: lineas verticales desde minimo hasta maximo
- SMA superpuesta: calculada algoritmicamente (sin librerias)
Endpoint: GET /precios/ohlcv?ticker=SPY&n=120

### 9.4 Reporte Tecnico

El sistema genera reportes en dos formatos:
- JSON: GET /reporte — consolidado de todos los modulos
- TXT:  GET /reporte/txt — version legible para exportar

El reporte incluye: cobertura de datos, top similitudes, ranking de volatilidad, VaR, Sharpe y patrones detectados.

### 9.5 Despliegue — Docker

```
docker-compose up --build
```

Servicios:
- PostgreSQL 15 con volumen persistente y health check
- API Python 3.11-slim en puerto 8000
- Frontend servido desde GET /

Reproducibilidad total: un evaluador puede ejecutar el proyecto desde cero con un solo comando.

---

## 10. Restricciones Academicas — Verificacion de Cumplimiento

| Restriccion                                    | Estado | Evidencia |
|------------------------------------------------|--------|-----------|
| Sin yfinance / pandas_datareader               | CUMPLE | etl/downloader.py usa urllib.request directo |
| Sin pandas / numpy / scipy / sklearn           | CUMPLE | requirements.txt solo contiene psycopg2-binary |
| Sin Flask / FastAPI / Django                   | CUMPLE | Servidor con http.server (stdlib) |
| Sin matplotlib / plotly / Chart.js             | CUMPLE | Visualizacion con SVG + Canvas API |
| Algoritmos implementados explicitamente        | CUMPLE | Codigo transparente, sin funciones de alto nivel |
| Sin sorted() ni .sort() en algoritmos          | CUMPLE | Cada algoritmo implementa su propia logica |
| Sin datasets estaticos                         | CUMPLE | Descarga dinamica en cada ejecucion del ETL |
| Minimo 20 activos                              | CUMPLE | 20 activos en config.py |
| Horizonte >= 5 anos                            | CUMPLE | FECHA_INICIO = datetime.today() - timedelta(days=5*365) |
| Reproducibilidad                               | CUMPLE | docker-compose up --build && python main.py todo |
| Scraping etico                                 | CUMPLE | Pausa de 1s entre tickers, respeta limites de Yahoo Finance |
| Uso de IA declarado                            | CUMPLE | Ver seccion 11 |

---

## 11. Declaracion de Uso de Inteligencia Artificial

En el desarrollo de este proyecto se utilizo **Kiro (IA generativa)** como herramienta de soporte para:

- Revision de sintaxis y estructura del codigo Python.
- Sugerencias de organizacion modular del proyecto.
- Verificacion de la correcta implementacion de formulas matematicas.
- Generacion de documentacion tecnica (docstrings y README).

**El uso de IA NO reemplazo:**
- El diseno algoritmico de los 12 algoritmos de ordenamiento.
- El analisis formal de complejidad (notacion O).
- La implementacion explicita de cada algoritmo desde cero.
- Las decisiones de arquitectura del sistema.

Conforme a las directrices del curso, toda implementacion algoritmica fue revisada, comprendida y validada por el equipo antes de su inclusion en el proyecto.

---

## 12. Como Ejecutar el Proyecto

### Con Docker (recomendado)

```bash
docker-compose up --build
```

### Sin Docker

```bash
pip install -r requirements.txt
cp .env.example .env
psql -U postgres -f database/init.sql
python main.py etl            # Requerimiento 1: ETL
python main.py similitud      # Requerimiento 3: similitud
python main.py volatilidad    # Requerimiento 4: volatilidad
python main.py ordenamiento   # Requerimiento 2: benchmark
python main.py api            # Servidor HTTP
```

### Pipeline completo

```bash
python main.py todo
```

---

*Seguimiento 1 — Universidad del Quindio — Analisis de Algoritmos*
