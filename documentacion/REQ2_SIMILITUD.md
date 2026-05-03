# Requerimiento 2 — Algoritmos de Similitud de Series de Tiempo

## Enunciado

> Se deben implementar al menos cuatro algoritmos de similitud entre series de tiempo. La aplicación deberá permitir al usuario seleccionar dos activos, visualizar sus series temporales y mostrar los valores de similitud calculados por cada algoritmo. Para cada método, se deberá presentar una explicación matemática, una descripción algorítmica detallada y el análisis de su complejidad computacional.

---

## Archivos Involucrados

| Archivo | Función |
|---|---|
| `algoritmos/similitud.py` | Implementación de los 4 algoritmos |
| `etl/database.py → obtener_series_alineadas()` | Alineación de series por fecha |
| `main.py → pipeline_similitud()` | Orquestador del cálculo |
| `api/server.py → _similitud(), _correlacion_matriz()` | Endpoints API |

---

## Preprocesamiento: Alineación de Series

Antes de calcular similitud, las series se alinean por fecha exacta (intersección de calendarios bursátiles). Esto garantiza que la posición `i` de cada serie corresponde al mismo día calendario.

**Sin alineación:** Se compararían días distintos entre mercados con calendarios diferentes, introduciendo ruido en todos los algoritmos.

---

## Algoritmo 1: Distancia Euclidiana — O(n)

### Concepto

Trata cada serie de precios como un vector en ℝⁿ y mide la distancia geométrica entre los dos puntos en ese espacio n-dimensional.

### Fórmula

```
d(A, B) = √( Σᵢ (Aᵢ - Bᵢ)² )
```

### Normalización Min-Max

Antes de calcular, se aplica normalización Min-Max al rango [0, 1]:

```
x_norm = (x - min(serie)) / (max(serie) - min(serie))
```

**Necesidad:** Sin normalización, la distancia estaría dominada por la diferencia de escala. EC cotiza entre $5-$15 USD y SPY entre $300-$500 USD. La distancia reflejaría la diferencia de precio, no la similitud de comportamiento.

### Implementación

```python
def distancia_euclidiana(a, b, normalizar=True):
    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]
    if normalizar:
        a = normalizar_minmax(a)
        b = normalizar_minmax(b)
    suma_cuadrados = sum((ai - bi) ** 2 for ai, bi in zip(a, b))
    return math.sqrt(suma_cuadrados)
```

### Interpretación

| Valor | Significado |
|---|---|
| d = 0 | Series idénticas (después de normalizar) |
| d pequeña | Comportamiento similar |
| d grande | Comportamiento muy diferente |

**Ordenamiento de resultados:** Ascendente (menor distancia = más similar).

### Complejidad

- Tiempo: O(n) — una pasada sobre los n elementos
- Espacio: O(n) — copia de las series normalizadas

---

## Algoritmo 2: Correlación de Pearson — O(n)

### Concepto

Mide la relación lineal entre dos series. No mide si los precios son similares en magnitud, sino si se mueven en la misma dirección y proporción.

### Fórmula

```
r = Σ((Aᵢ - Ā)(Bᵢ - B̄)) / √(Σ(Aᵢ - Ā)² · Σ(Bᵢ - B̄)²)

Donde:
    Ā = media(A) = Σ(Aᵢ) / n
    B̄ = media(B) = Σ(Bᵢ) / n
```

Equivalentemente: `r = Cov(A, B) / (σ_A · σ_B)`

### Implementación

```python
def correlacion_pearson(a, b):
    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]
    media_a = sum(a) / n
    media_b = sum(b) / n
    numerador = sum((ai - media_a) * (bi - media_b) for ai, bi in zip(a, b))
    var_a = sum((ai - media_a) ** 2 for ai in a)
    var_b = sum((bi - media_b) ** 2 for bi in b)
    denominador = math.sqrt(var_a * var_b)
    if denominador == 0:
        return 0.0
    return numerador / denominador
```

### Interpretación

| Valor | Significado |
|---|---|
| r = +1 | Correlación positiva perfecta (suben y bajan juntos) |
| r = -1 | Correlación negativa perfecta (movimientos opuestos) |
| r = 0 | Sin correlación lineal |
| \|r\| > 0.7 | Correlación fuerte |
| \|r\| < 0.3 | Correlación débil |

**Ventaja sobre Euclidiana:** No requiere normalización. Al trabajar con desviaciones respecto a la media, cancela automáticamente las diferencias de escala.

**Ordenamiento de resultados:** Descendente (mayor correlación = más similar).

### Complejidad

- Tiempo: O(n) — tres pasadas sobre los n elementos (media, varianzas, covarianza)
- Espacio: O(1) — cálculo en línea sin estructuras adicionales

---

## Algoritmo 3: Similitud por Coseno — O(n)

### Concepto

Mide el ángulo entre dos series tratadas como vectores en ℝⁿ. En lugar de medir la distancia entre los extremos de los vectores (Euclidiana), mide el ángulo entre ellos.

### Fórmula

```
cos(θ) = (A · B) / (‖A‖ · ‖B‖)
       = Σ(Aᵢ · Bᵢ) / (√Σ(Aᵢ²) · √Σ(Bᵢ²))

Donde:
    A · B  = producto punto
    ‖A‖    = norma euclidiana = √Σ(Aᵢ²)
```

### Implementación

```python
def similitud_coseno(a, b):
    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]
    producto_punto = sum(ai * bi for ai, bi in zip(a, b))
    norma_a = math.sqrt(sum(ai ** 2 for ai in a))
    norma_b = math.sqrt(sum(bi ** 2 for bi in b))
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return producto_punto / (norma_a * norma_b)
```

### Diferencia con Pearson

Pearson centra los datos (resta la media) antes de calcular. Coseno no centra, por lo que es sensible al nivel absoluto de precios. Para series financieras, Pearson suele ser más informativo porque elimina el efecto del nivel de precios.

### Interpretación

| Valor | Significado |
|---|---|
| cos(θ) = +1 | Vectores en la misma dirección |
| cos(θ) = 0 | Vectores perpendiculares (sin relación) |
| cos(θ) = -1 | Vectores en direcciones opuestas |

**Ordenamiento de resultados:** Descendente (mayor similitud = más similar).

### Complejidad

- Tiempo: O(n) — tres pasadas sobre los n elementos
- Espacio: O(1)

---

## Algoritmo 4: Dynamic Time Warping (DTW) — O(n²)

### Concepto

A diferencia de la Distancia Euclidiana (que compara punto a punto), DTW permite "estirar" o "comprimir" el eje temporal para encontrar la alineación óptima entre las dos series. Útil cuando dos activos reaccionan al mismo evento macroeconómico con diferente retraso temporal.

### Algoritmo (Programación Dinámica)

```
Construir matriz (n+1) × (m+1):
    matriz[0][0] = 0
    matriz[i][j] = |A[i-1] - B[j-1]| + min(
        matriz[i-1][j],      ← avanzar solo en A
        matriz[i][j-1],      ← avanzar solo en B
        matriz[i-1][j-1]     ← avanzar en ambas
    )

Distancia DTW = matriz[n][m]
```

### Optimización: Ventana Sakoe-Chiba

Para reducir la complejidad de O(n²) a O(n·w), se restringe la búsqueda a una banda diagonal de ancho `w = n × 0.10` (10% del tamaño de la serie).

```python
window = max(int(n * 0.10), abs(n - m))
for i in range(1, n + 1):
    inicio_j = max(1, i - window)
    fin_j    = min(m, i + window)
    for j in range(inicio_j, fin_j + 1):
        ...
```

**Justificación:** Evita alineaciones "irrazonables" (comparar el primer día de una serie con el último de la otra). Con 10%, la complejidad real es O(0.1n²).

### Implementación

```python
def dtw(a, b, normalizar=True, window_pct=0.1):
    if normalizar:
        a = normalizar_minmax(a)
        b = normalizar_minmax(b)
    n, m = len(a), len(b)
    window = max(int(n * window_pct), abs(n - m))
    INF = float("inf")
    matriz = [[INF] * (m + 1) for _ in range(n + 1)]
    matriz[0][0] = 0.0
    for i in range(1, n + 1):
        for j in range(max(1, i - window), min(m, i + window) + 1):
            costo = abs(a[i-1] - b[j-1])
            matriz[i][j] = costo + min(
                matriz[i-1][j],
                matriz[i][j-1],
                matriz[i-1][j-1]
            )
    return matriz[n][m]
```

### Interpretación

| Valor | Significado |
|---|---|
| DTW = 0 | Series idénticas (después de normalizar) |
| DTW pequeño | Series similares aunque desfasadas |
| DTW grande | Series muy diferentes |

**Ordenamiento de resultados:** Ascendente (menor distancia = más similar).

### Complejidad

- Tiempo: O(n·w) con ventana Sakoe-Chiba, O(n²) sin ventana
- Espacio: O(n·m) — matriz completa

---

## Comparación de Algoritmos

| Algoritmo | Complejidad | Normalización | Rango | Ordenamiento |
|---|---|---|---|---|
| Euclidiana | O(n) | Requerida (Min-Max) | [0, ∞) | ASC |
| Pearson | O(n) | No requerida | [-1, +1] | DESC |
| Coseno | O(n) | No requerida | [-1, +1] | DESC |
| DTW | O(n²) | Recomendada | [0, ∞) | ASC |

### Cuándo Usar Cada Uno

| Situación | Algoritmo Recomendado |
|---|---|
| Activos con escalas de precio muy distintas | Euclidiana (con normalización) |
| Medir si los activos se mueven juntos | Pearson |
| Comparar tendencias sin importar nivel | Coseno |
| Activos que reaccionan con retraso al mismo evento | DTW |

---

## Matriz de Similitud

Se calculan todos los pares posibles: C(20, 2) = 190 pares.

**Complejidad total:** O(n² · m) donde n = 20 activos, m = 1272 días comunes

**Resultados guardados:** 190 pares × 4 algoritmos = 760 registros en `resultados_similitud`

---

## Endpoints API

```
GET /similitud?algoritmo=pearson     → 190 pares ordenados
GET /similitud?algoritmo=euclidiana  → 190 pares ordenados
GET /similitud?algoritmo=coseno      → 190 pares ordenados
GET /similitud?algoritmo=dtw         → 190 pares ordenados
GET /correlacion/matriz              → Matriz 20×20 para heatmap
```
