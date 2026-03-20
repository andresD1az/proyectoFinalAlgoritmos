"""
algorithms/similarity.py — Algoritmos de Similitud entre Series Temporales
Implementados DESDE CERO — SIN numpy, SIN scipy, SIN sklearn

Algoritmos disponibles:
  1. Distancia Euclidiana          O(n)
  2. Correlación de Pearson        O(n)
  3. Similitud por Coseno          O(n)
  4. DTW (Dynamic Time Warping)    O(n²)
"""

import math


# ------------------------------------------------------------------
# UTILIDADES COMPARTIDAS
# ------------------------------------------------------------------

def _validar_series(a: list[float], b: list[float], nombre: str):
    """Valida que ambas series sean listas no vacías."""
    if not a or not b:
        raise ValueError(f"[{nombre}] Las series no pueden estar vacías.")


def normalizar_minmax(serie: list[float]) -> list[float]:
    """
    Normaliza una serie al rango [0, 1] usando Min-Max Scaling.

    Fórmula:
        x_norm = (x - min) / (max - min)

    Necesario antes de Distancia Euclidiana cuando se comparan
    activos con rangos de precios muy distintos (ej. COP vs USD).

    Complejidad: O(n)
    """
    minimo = min(serie)
    maximo = max(serie)
    rango = maximo - minimo
    if rango == 0:
        return [0.0] * len(serie)
    return [(v - minimo) / rango for v in serie]


def _media(serie: list[float]) -> float:
    """Media aritmética manual: Σ(v) / n   — O(n)"""
    return sum(serie) / len(serie)


# ======================================================= #
# ⚠️ ALGORITMO: Distancia Euclidiana                      #
# ✏️ ZONA DE LÓGICA MODIFICABLE                           #
# Complejidad Esperada: O(n)                               #
# ======================================================= #
def distancia_euclidiana(a: list[float], b: list[float],
                          normalizar: bool = True) -> float:
    """
    Calcula la distancia euclidiana entre dos series de igual longitud.

    Fórmula:
        d(A, B) = √( Σᵢ (Aᵢ - Bᵢ)² )

    Args:
        a, b:        Series de precios (ej. cierres históricos)
        normalizar:  Si True, aplica Min-Max antes de calcular
                     (recomendado cuando las escalas difieren)

    Returns:
        float ≥ 0  (0 = series idénticas, mayor = más diferentes)
    """
    _validar_series(a, b, "Euclidiana")

    # Igualar longitud tomando el mínimo (alinear por el final)
    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]

    if normalizar:
        a = normalizar_minmax(a)
        b = normalizar_minmax(b)

    suma_cuadrados = sum((ai - bi) ** 2 for ai, bi in zip(a, b))
    return math.sqrt(suma_cuadrados)
# ======================================================= #


# ======================================================= #
# ⚠️ ALGORITMO: Correlación de Pearson                    #
# ✏️ ZONA DE LÓGICA MODIFICABLE                           #
# Complejidad Esperada: O(n)                               #
# ======================================================= #
def correlacion_pearson(a: list[float], b: list[float]) -> float:
    """
    Mide la relación lineal entre dos series temporales.

    Fórmula:
        r = Σ((Aᵢ - Ā)(Bᵢ - B̄))
            ─────────────────────────────
            √(Σ(Aᵢ - Ā)² · Σ(Bᵢ - B̄)²)

    Donde Ā y B̄ son las medias de cada serie.

    Returns:
        float en [-1, 1]
         1  → correlación positiva perfecta
        -1  → correlación inversa perfecta
         0  → sin correlación lineal

    Nota: No usa escalas, por eso NO requiere normalización previa.
    """
    _validar_series(a, b, "Pearson")

    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]

    media_a = _media(a)
    media_b = _media(b)

    numerador     = sum((ai - media_a) * (bi - media_b) for ai, bi in zip(a, b))
    var_a         = sum((ai - media_a) ** 2 for ai in a)
    var_b         = sum((bi - media_b) ** 2 for bi in b)
    denominador   = math.sqrt(var_a * var_b)

    if denominador == 0:
        return 0.0   # Serie constante → correlación indefinida, retorna 0

    return numerador / denominador
# ======================================================= #


# ======================================================= #
# ⚠️ ALGORITMO: Similitud por Coseno                      #
# ✏️ ZONA DE LÓGICA MODIFICABLE                           #
# Complejidad Esperada: O(n)                               #
# ======================================================= #
def similitud_coseno(a: list[float], b: list[float]) -> float:
    """
    Trata cada serie como un vector en ℝⁿ y mide el ángulo entre ellos.
    Invariante a la magnitud (escala de precios).

    Fórmula:
        cos(θ) = (A · B) / (‖A‖ · ‖B‖)
               = Σ(Aᵢ·Bᵢ) / (√Σ(Aᵢ²) · √Σ(Bᵢ²))

    Returns:
        float en [-1, 1]
         1  → misma dirección (comportamiento idéntico de precios)
         0  → vectores perpendiculares (sin relación)
        -1  → direcciones opuestas
    """
    _validar_series(a, b, "Coseno")

    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]

    producto_punto = sum(ai * bi for ai, bi in zip(a, b))
    norma_a = math.sqrt(sum(ai ** 2 for ai in a))
    norma_b = math.sqrt(sum(bi ** 2 for bi in b))

    if norma_a == 0 or norma_b == 0:
        return 0.0

    return producto_punto / (norma_a * norma_b)
# ======================================================= #


# ======================================================= #
# ⚠️ ALGORITMO: DTW — Dynamic Time Warping                #
# ✏️ ZONA DE LÓGICA MODIFICABLE                           #
# Complejidad Esperada: O(n²) tiempo y espacio             #
# ======================================================= #
def dtw(a: list[float], b: list[float],
        normalizar: bool = True, window_pct: float = 0.1) -> float:
    """
    Calcula la distancia DTW entre dos series temporales.
    Optimizado con ventana de Sakoe-Chiba para mejorar el rendimiento.

    Args:
        a, b:        Series de precios
        normalizar:  Aplica Min-Max scaling
        window_pct:  Porcentaje de la longitud de la serie para la ventana de búsqueda (0.1 = 10%).
                     Esto reduce la complejidad de O(n²) a O(n * k).
    """
    _validar_series(a, b, "DTW")

    if normalizar:
        a = normalizar_minmax(a)
        b = normalizar_minmax(b)

    n = len(a)
    m = len(b)

    # Calculamos el radio de la ventana (Sakoe-Chiba)
    # n * window_pct asegura que las comparaciones se mantengan cerca de la diagonal
    window = max(int(n * window_pct), abs(n - m))

    # Inicializar matriz con infinito
    INF = float("inf")
    matriz = [[INF] * (m + 1) for _ in range(n + 1)]
    matriz[0][0] = 0.0

    # Llenar la matriz considerando la ventana
    for i in range(1, n + 1):
        # Rango dinámico para la ventana de Sakoe-Chiba
        start = max(1, i - window)
        end = min(m, i + window)
        
        for j in range(start, end + 1):
            costo = abs(a[i - 1] - b[j - 1])
            matriz[i][j] = costo + min(
                matriz[i - 1][j],      # vengo de arriba
                matriz[i][j - 1],      # vengo de la izquierda
                matriz[i - 1][j - 1],  # vengo de la diagonal
            )

    return matriz[n][m]
# ======================================================= #


# ------------------------------------------------------------------
# FUNCIÓN PRINCIPAL: Calcular todas las similitudes para un par
# ------------------------------------------------------------------

def calcular_todas(ticker_a: str, serie_a: list[float],
                   ticker_b: str, serie_b: list[float]) -> dict:
    """
    Ejecuta los 4 algoritmos entre un par de series y retorna
    un dict con todos los resultados.

    Args:
        ticker_a, ticker_b: Identificadores del activo
        serie_a, serie_b:   Series de precios de cierre

    Returns:
        {
            "par": "EC vs SPY",
            "euclidiana": 0.123,
            "pearson":    0.856,
            "coseno":     0.921,
            "dtw":        0.045,
        }
    """
    return {
        "par":        f"{ticker_a} vs {ticker_b}",
        "euclidiana": distancia_euclidiana(serie_a, serie_b, normalizar=True),
        "pearson":    correlacion_pearson(serie_a, serie_b),
        "coseno":     similitud_coseno(serie_a, serie_b),
        "dtw":        dtw(serie_a, serie_b, normalizar=True),
    }


# ------------------------------------------------------------------
# MATRIZ DE SIMILITUD: Todos los pares posibles entre N activos
# ------------------------------------------------------------------

def matriz_similitud(series: dict[str, list[float]],
                     algoritmo: str = "pearson") -> list[dict]:
    """
    Genera la matriz de similitud completa para todos los pares de activos.

    Args:
        series:    {ticker: [precios_cierre]}
        algoritmo: 'euclidiana' | 'pearson' | 'coseno' | 'dtw'

    Returns:
        Lista de dicts ordenada por valor descendente (mayor similitud primero)
        [{"ticker1": "SPY", "ticker2": "QQQ", "algoritmo": "pearson", "valor": 0.97}, ...]

    Complejidad: O(n² · m) donde n = número de activos, m = longitud de la serie
    """
    algoritmos_disponibles = {
        "euclidiana": lambda a, b: distancia_euclidiana(a, b),
        "pearson":    correlacion_pearson,
        "coseno":     similitud_coseno,
        "dtw":        lambda a, b: dtw(a, b),
    }

    if algoritmo not in algoritmos_disponibles:
        raise ValueError(
            f"Algoritmo '{algoritmo}' no existe. "
            f"Usa: {list(algoritmos_disponibles.keys())}"
        )

    fn = algoritmos_disponibles[algoritmo]
    tickers = list(series.keys())
    resultados = []

    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):          # Solo triángulo superior
            t1, t2 = tickers[i], tickers[j]
            try:
                valor = fn(series[t1], series[t2])
                resultados.append({
                    "ticker1":   t1,
                    "ticker2":   t2,
                    "algoritmo": algoritmo,
                    "valor":     round(valor, 6),
                })
            except Exception as e:
                print(f"[SIMILITUD] Error {t1}-{t2}: {e}")

    # Ordenar: para distancias (euclidiana, dtw) → ascendente (menor = más similar)
    # Para métricas de correlación (pearson, coseno) → descendente (mayor = más similar)
    invertir = algoritmo in {"pearson", "coseno"}
    resultados.sort(key=lambda r: r["valor"], reverse=invertir)

    return resultados
