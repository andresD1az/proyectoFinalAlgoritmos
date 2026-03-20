# 🧮 Módulo 2 & 3: Algoritmos de Análisis Financiero

## Responsabilidad

Implementar **desde cero** (sin librerías matemáticas externas) los algoritmos de:
- **Similitud** entre series temporales de precios
- **Reconocimiento de patrones** mediante ventana deslizante
- **Cálculo de riesgo y volatilidad** histórica

**Restricción académica:** Prohibido usar `.corr()`, `.std()`, `scipy`, `sklearn` o cualquier función que encapsule la matemática compleja.

---

## 📁 Archivos del Módulo

| Archivo | Algoritmos |
|---------|-----------|
| `similarity.py` | Euclidiana, Pearson, Coseno, DTW |
| `patterns.py` | Ventana Deslizante, Detección de Secuencias |
| `volatility.py` | Volatilidad Histórica, Retornos Logarítmicos |

---

## ⚠️ Protocolo de Aprobación

Antes de implementar cualquier algoritmo en este módulo, el plan matemático debe ser:
1. Propuesto con la **fórmula matemática** explícita
2. **Aprobado** por el desarrollador principal
3. Documentado aquí con la fórmula, complejidad y ejemplo numérico

---

## 🧮 Algoritmo 3: Distancia Euclidiana

**Archivo:** `similarity.py` → función `distancia_euclidiana()`  
**Estado:** ⏳ Pendiente de aprobación

### Plan matemático propuesto

Dadas dos series de precios A y B de igual longitud n, la distancia euclidiana mide la "distancia geométrica" entre ellas en un espacio n-dimensional.

$$d(A, B) = \sqrt{\sum_{i=1}^{n}(A_i - B_i)^2}$$

- **Valor = 0:** series idénticas
- **Valor alto:** series muy diferentes
- **Limitación:** sensible a diferencias de escala (un activo en USD vs COP)
- **Solución:** normalizar previamente cada serie al rango [0, 1]

**Complejidad:** O(n)

---

## 🧮 Algoritmo 4: Correlación de Pearson

**Archivo:** `similarity.py` → función `correlacion_pearson()`  
**Estado:** ⏳ Pendiente de aprobación

### Plan matemático propuesto

Mide la **relación lineal** entre dos series. Rango: [-1, 1].

$$r = \frac{\sum_{i=1}^{n}(A_i - \bar{A})(B_i - \bar{B})}{\sqrt{\sum_{i=1}^{n}(A_i - \bar{A})^2 \cdot \sum_{i=1}^{n}(B_i - \bar{B})^2}}$$

Donde $\bar{A}$ y $\bar{B}$ son las medias aritméticas de cada serie.

- **r = 1:** correlación perfecta positiva
- **r = -1:** correlación perfecta inversa
- **r = 0:** sin correlación lineal

**Complejidad:** O(n)

---

## 🧮 Algoritmo 5: Similitud por Coseno

**Archivo:** `similarity.py` → función `similitud_coseno()`  
**Estado:** ⏳ Pendiente de aprobación

### Plan matemático propuesto

Trata cada serie como un vector en ℝⁿ y mide el ángulo entre ellos. Invariante a la magnitud (escala).

$$\cos(\theta) = \frac{A \cdot B}{\|A\| \cdot \|B\|} = \frac{\sum_{i=1}^{n} A_i \cdot B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \cdot \sqrt{\sum_{i=1}^{n} B_i^2}}$$

- **Valor = 1:** misma dirección (comportamiento idéntico)
- **Valor = 0:** perpendiculares (sin relación)

**Complejidad:** O(n)

---

## 🧮 Algoritmo 6: DTW (Dynamic Time Warping)

**Archivo:** `similarity.py` → función `dtw()`  
**Estado:** ⏳ Pendiente de aprobación

### Plan matemático propuesto

Permite comparar series que están **desfasadas en el tiempo** (ej. el mismo patrón ocurre 3 días después en otro activo). Usa programación dinámica.

Sea la **matriz de costos acumulados** DTW[i][j]:

$$DTW[i][j] = |A_i - B_j| + \min \begin{cases} DTW[i-1][j] \\ DTW[i][j-1] \\ DTW[i-1][j-1] \end{cases}$$

La distancia final es `DTW[n][m]`.

- **Ventaja vs Euclidiana:** tolera desplazamientos temporales
- **Desventaja:** O(n·m) en tiempo y espacio

**Complejidad:** O(n²) tiempo, O(n²) espacio

---

## 🧮 Algoritmo 7: Ventana Deslizante (Sliding Window)

**Archivo:** `patterns.py` → función `detectar_patrones()`  
**Estado:** ⏳ Pendiente de aprobación

### Plan matemático propuesto

Recorre la serie con una ventana de tamaño k, evaluando en cada posición si se cumple una condición de patrón.

Para cada posición `i` de 0 a n-k:
- `ventana = precios[i : i+k]`
- Evaluar si todos los días de la ventana son alcistas: `∀j: ventana[j] > ventana[j-1]`

**Variación porcentual de la ventana:**
$$\Delta\% = \frac{V_{i+k-1} - V_i}{V_i} \times 100$$

**Complejidad:** O(n·k) donde k es el tamaño de ventana (configurable en `config.py`)

---

## 🧮 Algoritmo 8: Volatilidad Histórica

**Archivo:** `volatility.py` → función `calcular_volatilidad()`  
**Estado:** ⏳ Pendiente de aprobación

### Plan matemático propuesto

**Paso 1:** Calcular retornos logarítmicos diarios (más estables que retornos simples):
$$r_i = \ln\left(\frac{P_i}{P_{i-1}}\right)$$

**Paso 2:** Calcular media de retornos en ventana de k días:
$$\bar{r} = \frac{\sum_{i=1}^{k} r_i}{k}$$

**Paso 3:** Calcular desviación estándar muestral (volatilidad):
$$\sigma = \sqrt{\frac{\sum_{i=1}^{k}(r_i - \bar{r})^2}{k-1}}$$

**Paso 4:** Anualizar (252 días hábiles en un año):
$$\sigma_{anual} = \sigma \times \sqrt{252}$$

**Complejidad:** O(n) por activo

---

## 🗝️ Convención de Comentarios en Código

Todos los algoritmos de este módulo usan el siguiente formato para delimitarlos:

```python
# ======================================================= #
# ⚠️ ALGORITMO: [Nombre del Algoritmo]
# ✏️ ZONA DE LÓGICA MODIFICABLE
# Complejidad Esperada: O(...)
# ======================================================= #
```

Esto permite localizar y modificar la lógica matemática sin tocar el resto del código.
