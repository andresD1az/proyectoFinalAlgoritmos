# Requerimiento 3 — Patrones y Medición de Volatilidad

## Enunciado

> Se deberá implementar un algoritmo basado en ventanas deslizantes (sliding window) que recorra el historial de precios y detecte la frecuencia de patrones previamente definidos. Adicionalmente, se deberán calcular métricas de dispersión, como la desviación estándar y la volatilidad histórica, para clasificar cada instrumento financiero en categorías de riesgo.

---

## Archivos Involucrados

| Archivo | Función |
|---|---|
| `algoritmos/patrones.py` | Ventana deslizante, picos/valles, SMA, Golden/Death Cross |
| `algoritmos/volatilidad.py` | Retornos log, volatilidad, VaR, Sharpe, Drawdown |
| `main.py → pipeline_volatilidad()` | Orquestador |
| `api/server.py → _patrones(), _clasificacion_riesgo()` | Endpoints API |

---

## Parte 1: Detección de Patrones

### Algoritmo Principal: Ventana Deslizante — O(n·k)

**Función:** `detectar_patrones()` en `algoritmos/patrones.py`

**Parámetros:**
- `n` = longitud de la serie (~1255 días)
- `k` = tamaño de la ventana (20 días, configurable en `config.py`)
- Ventanas evaluadas: `n - k + 1` = ~1235 por activo

**Pseudocódigo:**
```
Para i desde 0 hasta n - k:
    segmento   = precios[i : i + k]
    fechas_seg = fechas[i : i + k]
    variacion  = (segmento[-1] - segmento[0]) / segmento[0] × 100
    patron     = clasificar_segmento(segmento)
    Si patron != "neutro" O |variacion| >= 1%:
        guardar resultado
```

**Complejidad:** O(n·k) — n posiciones de ventana, k comparaciones por ventana

---

### Patrón 1: Días Consecutivos al Alza

**Formalización matemática:**

Sea `P = [P₀, P₁, ..., Pₖ₋₁]` el segmento de precios de la ventana.

```
días_alza  = |{ j ∈ {1,...,k−1} : Pⱼ > Pⱼ₋₁ }|
total_días = k − 1

Condición: días_alza / total_días ≥ 0.75
```

**Nombre del patrón:** `"N_dias_alza"` donde N = total_días (ej: `"19_dias_alza"`)

**Interpretación:** Al menos el 75% de los días dentro de la ventana cerraron por encima del día anterior. Indica una tendencia alcista sostenida.

**Implementación:**
```python
dias_alza = sum(1 for j in range(1, k) if segmento[j] > segmento[j - 1])
total_dias = k - 1
if dias_alza / total_dias >= 0.75:
    return f"{total_dias}_dias_alza"
```

---

### Patrón 2: Rebote en V (V-shape) — Patrón Adicional

**Formalización matemática:**

Sea `P = [P₀, P₁, ..., Pₖ₋₁]` el segmento y `m = ⌊k/2⌋` el índice de la mitad.

```
primera_mitad_bajista = ∀ j ∈ {1,...,m−1} : Pⱼ ≤ Pⱼ₋₁
segunda_mitad_alcista = ∀ j ∈ {m,...,k−1} : Pⱼ ≥ Pⱼ₋₁

Condición: primera_mitad_bajista = True  AND  segunda_mitad_alcista = True
```

**Nombre del patrón:** `"rebote"`

**Interpretación:** El precio cae de forma sostenida durante la primera mitad de la ventana y luego se recupera de forma sostenida durante la segunda mitad, formando una "V". Indica que el mercado encontró un soporte y revirtió la tendencia.

**Ejemplo con ventana de 6 días:**
```
Precios: [100, 98, 95, 93, 96, 100]
         ←  bajista  →  ← alcista →
→ Patrón: "rebote"
```

**Implementación:**
```python
mitad = k // 2
primera_baja = all(segmento[j] <= segmento[j - 1] for j in range(1, mitad))
segunda_alza = all(segmento[j] >= segmento[j - 1] for j in range(mitad, k))
if primera_baja and segunda_alza:
    return "rebote"
```

---

### Algoritmo 2: Detección de Picos y Valles — O(n)

**Función:** `detectar_picos_valles()` en `algoritmos/patrones.py`

**Algoritmo:**
```
Para cada punto i (excluyendo los bordes con vecindad=3):
    ventana = precios[i - 3 : i + 4]
    Es PICO  si precios[i] >= todos los valores de la ventana
    Es VALLE si precios[i] <= todos los valores de la ventana
```

**Aplicación financiera:** Los picos y valles son niveles de soporte y resistencia. Identificarlos algorítmicamente permite detectar puntos donde el mercado históricamente ha revertido su tendencia.

---

### Algoritmo 3: Media Móvil Simple (SMA) — O(n·k)

**Función:** `media_movil_simple()` en `algoritmos/patrones.py`

**Fórmula:**
```
SMA[i] = (P[i] + P[i-1] + ... + P[i-k+1]) / k
Para i < k-1: SMA[i] = None (ventana incompleta)
```

**Nota sobre optimización:** La implementación es O(n·k) directa. Se podría optimizar a O(n) con suma rodante (restar el elemento que sale, sumar el que entra), pero se implementa la forma directa para mayor transparencia algorítmica.

---

### Algoritmo 4: Golden Cross / Death Cross — O(n·k)

**Función:** `detectar_cruces_medias()` en `algoritmos/patrones.py`

**Parámetros:** SMA corta = 10 días, SMA larga = 30 días

**Definiciones:**

```
Golden Cross: SMA_corta[i-1] ≤ SMA_larga[i-1]  AND  SMA_corta[i] > SMA_larga[i]
              → Señal alcista (posible compra)

Death Cross:  SMA_corta[i-1] ≥ SMA_larga[i-1]  AND  SMA_corta[i] < SMA_larga[i]
              → Señal bajista (posible venta)
```

**Limitación:** Es un indicador rezagado (lagging). Confirma una tendencia que ya comenzó, no la predice.

---

## Parte 2: Medición de Volatilidad y Riesgo

### Paso Previo: Retornos Logarítmicos — O(n)

**Función:** `calcular_retornos_log()` en `algoritmos/volatilidad.py`

**Fórmula:**
```
rᵢ = ln(Pᵢ / Pᵢ₋₁)   para i = 1, 2, ..., n-1
```

**Ventajas sobre retornos simples:**
1. **Aditividad:** `r_total = r₁ + r₂ + ... + rₙ`
2. **Simetría:** subida del 10% y bajada del 10% tienen igual valor absoluto
3. **Distribución:** se aproximan mejor a una distribución normal

---

### Algoritmo 5: Desviación Estándar y Volatilidad Histórica — O(n)

**Función:** `calcular_volatilidad()` en `algoritmos/volatilidad.py`

**Fórmula completa:**
```
1. Media de retornos:
   r̄ = Σ(rⱼ) / k

2. Varianza muestral (corrección de Bessel, denominador k−1):
   s² = Σ(rⱼ − r̄)² / (k − 1)

3. Desviación estándar diaria:
   σ_diaria = √s²

4. Volatilidad anualizada:
   σ_anual = σ_diaria × √252
```

**Corrección de Bessel (k−1):** Se usa el estimador insesgado de la varianza poblacional. Con k (varianza poblacional) se subestimaría la dispersión real.

**Factor √252:** 252 es el número de días de negociación en un año bursátil (no 365, porque los mercados no operan fines de semana ni festivos).

**Implementación:**
```python
media_r = sum(ventana_ret) / k
varianza = sum((r - media_r) ** 2 for r in ventana_ret) / (k - 1)
volatilidad_diaria = math.sqrt(varianza)
volatilidad_anualizada = volatilidad_diaria * math.sqrt(252)
```

---

### Algoritmo 6: Máximo Drawdown — O(n)

**Función:** `calcular_max_drawdown()` en `algoritmos/volatilidad.py`

**Fórmula:**
```
MDD = (precio_valle - precio_pico) / precio_pico × 100
```

**Algoritmo (una sola pasada):**
```
pico_actual = precios[0]
Para cada precio P:
    Si P > pico_actual: pico_actual = P
    drawdown = (P - pico_actual) / pico_actual
    Si drawdown < MDD: MDD = drawdown
```

**Interpretación:** MDD = -20% significa que en algún momento el activo cayó un 20% desde su máximo histórico.

---

### Algoritmo 7: Value at Risk (VaR) Histórico — O(n log n)

**Función:** `calcular_var_historico()` en `algoritmos/volatilidad.py`

**Método:** Simulación histórica (no paramétrico, no asume distribución normal)

**Algoritmo:**
```
1. Calcular retornos logarítmicos diarios
2. Ordenar retornos de menor a mayor (O(n log n))
3. VaR = retorno en el percentil (1 - nivel_confianza)

Para nivel_confianza = 0.95:
    índice_VaR = int(0.05 × n)
    VaR = retornos_ordenados[índice_VaR]
```

**Interpretación:** "Con 95% de confianza, la pérdida diaria no superará el X%"

**Ventaja del método histórico:** Captura los eventos extremos reales del activo (fat tails) sin asumir distribución normal.

---

### Algoritmo 8: Sharpe Ratio — O(n)

**Función:** `calcular_sharpe()` en `algoritmos/volatilidad.py`

**Fórmula:**
```
Sharpe = (R_activo - R_libre) / σ_activo

Donde:
    R_activo = media(retornos_diarios) × 252
    R_libre  = 5% anual (bonos del Tesoro EE.UU. a 10 años)
    σ_activo = std(retornos_diarios) × √252
```

**Interpretación:**

| Valor | Significado |
|---|---|
| Sharpe > 2.0 | Excelente |
| Sharpe > 1.0 | Bueno |
| Sharpe > 0.5 | Aceptable |
| Sharpe < 0.0 | Rinde menos que la tasa libre de riesgo |

---

## Clasificación de Riesgo

Basada en la volatilidad anualizada (σ):

| Categoría | Condición | Ejemplos |
|---|---|---|
| Conservador | σ < 15% | TLT (bonos del Tesoro) |
| Moderado | 15% ≤ σ < 30% | SPY (S&P 500), QQQ |
| Agresivo | σ ≥ 30% | USO (petróleo), GXG (Colombia), SLV |

El sistema genera un listado de activos ordenados por nivel de riesgo calculado algorítmicamente.

---

## Endpoints API

```
GET /patrones?ticker=SPY                          → Ventana deslizante + picos/valles
GET /patrones/cruces?ticker=SPY&corta=10&larga=30 → Golden/Death Cross
GET /riesgo/clasificacion                         → Ranking de 25 activos por volatilidad
```
