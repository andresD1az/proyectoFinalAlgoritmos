"""
algorithms/similarity.py — Algoritmos de Similitud entre Series Temporales
Universidad del Quindío — Análisis de Algoritmos — Requerimiento 2

PROPÓSITO:
    Implementa los 4 algoritmos de similitud exigidos por el enunciado para
    comparar pares de series de tiempo financieras (precios de cierre).

ALGORITMOS IMPLEMENTADOS:
    1. Distancia Euclidiana    — O(n)   — mide distancia geométrica
    2. Correlación de Pearson  — O(n)   — mide relación lineal
    3. Similitud por Coseno    — O(n)   — mide ángulo entre vectores
    4. DTW (Dynamic Time Warping) — O(n²) — alinea series desfasadas

RESTRICCIONES DEL ENUNCIADO CUMPLIDAS:
    - NO usa numpy (linalg.norm, corrcoef), scipy (distance, stats) ni sklearn.
    - Cada algoritmo está implementado explícitamente con bucles y operaciones básicas.
    - Cada función incluye su formulación matemática completa.

CUÁNDO USAR CADA ALGORITMO:
    - Euclidiana: cuando las series tienen la misma escala o se normalizan previamente.
    - Pearson: cuando interesa la dirección del movimiento, no la magnitud.
    - Coseno: cuando los precios absolutos no importan, solo la tendencia relativa.
    - DTW: cuando las series pueden estar desfasadas en el tiempo (ej: mercados
      que reaccionan con retraso a los mismos eventos macroeconómicos).
"""

import math

# UTILIDADES COMPARTIDAS

def _validar_series(a: list[float], b: list[float], nombre: str):
    """
    Valida que ambas series sean listas no vacías antes de calcular similitud.

    Args:
        a, b:   Series a validar
        nombre: Nombre del algoritmo (para el mensaje de error)

    Raises:
        ValueError: Si alguna serie está vacía
    """
    if not a or not b:
        raise ValueError(f"[{nombre}] Las series no pueden estar vacías.")

def normalizar_minmax(serie: list[float]) -> list[float]:
    """
    Normaliza una serie al rango [0, 1] usando Min-Max Scaling.

    FÓRMULA — Complejidad: O(n)
    ────────────────────────────
        x_norm = (x - min(serie)) / (max(serie) - min(serie))

    CUÁNDO ES NECESARIA:
        Antes de calcular la Distancia Euclidiana cuando se comparan activos
        con rangos de precios muy distintos. Por ejemplo:
        - EC (Ecopetrol) cotiza entre $5 y $15 USD
        - SPY (S&P 500 ETF) cotiza entre $300 y $500 USD
        Sin normalización, la distancia estaría dominada por la diferencia
        de escala, no por la similitud de comportamiento.

    Args:
        serie: Lista de floats a normalizar

    Returns:
        Lista de floats en el rango [0, 1]
        Si todos los valores son iguales (rango = 0), retorna lista de ceros.
    """
    minimo = min(serie)
    maximo = max(serie)
    rango  = maximo - minimo
    if rango == 0:
        return [0.0] * len(serie)   # Serie constante → todos los valores son 0
    return [(v - minimo) / rango for v in serie]

def _media(serie: list[float]) -> float:
    """
    Calcula la media aritmética de una serie.

    Fórmula: μ = Σ(vᵢ) / n   — Complejidad: O(n)
    """
    return sum(serie) / len(serie)

# ALGORITMO 1: DISTANCIA EUCLIDIANA

def distancia_euclidiana(a: list[float], b: list[float],
                          normalizar: bool = True) -> float:
    """
    Calcula la distancia euclidiana entre dos series de precios.

    CONCEPTO:
        Trata cada serie como un vector en ℝⁿ y mide la distancia
        geométrica entre los dos puntos en ese espacio n-dimensional.

    FÓRMULA — Complejidad: O(n)
    ────────────────────────────
        d(A, B) = √( Σᵢ (Aᵢ - Bᵢ)² )

    INTERPRETACIÓN:
        - d = 0: series idénticas (después de normalizar)
        - d pequeña: series con comportamiento similar
        - d grande: series con comportamiento muy diferente
        - No tiene límite superior (depende de la escala)

    NORMALIZACIÓN:
        Se aplica Min-Max antes de calcular para que la distancia
        refleje similitud de comportamiento, no diferencia de escala.

    ALINEACIÓN:
        Si las series tienen diferente longitud, se alinean tomando
        los últimos min(len(a), len(b)) elementos de cada una.

    Args:
        a, b:       Series de precios de cierre
        normalizar: Si True (default), aplica Min-Max antes de calcular

    Returns:
        float >= 0. Menor valor = series más similares.
    """
    _validar_series(a, b, "Euclidiana")

    # Alinear longitudes tomando los últimos N elementos de cada serie
    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]

    # Normalizar si se requiere (recomendado para activos con escalas distintas)
    if normalizar:
        a = normalizar_minmax(a)
        b = normalizar_minmax(b)

    # Calcular suma de cuadrados de diferencias
    suma_cuadrados = sum((ai - bi) ** 2 for ai, bi in zip(a, b))
    return math.sqrt(suma_cuadrados)

# ALGORITMO 2: CORRELACIÓN DE PEARSON

def correlacion_pearson(a: list[float], b: list[float]) -> float:
    """
    Mide la relación lineal entre dos series temporales.

    CONCEPTO:
        Calcula qué tan bien se puede predecir una serie a partir de la otra
        mediante una función lineal. No mide si los precios son similares en
        magnitud, sino si se mueven en la misma dirección y proporción.

    FÓRMULA — Complejidad: O(n)
    ────────────────────────────
        r = Σ((Aᵢ - Ā)(Bᵢ - B̄)) / √(Σ(Aᵢ - Ā)² · Σ(Bᵢ - B̄)²)

        Donde Ā = media(A) y B̄ = media(B)

        Equivalentemente:
        r = Cov(A, B) / (σ_A · σ_B)

    INTERPRETACIÓN:
        r = +1: correlación positiva perfecta (suben y bajan juntos)
        r = -1: correlación negativa perfecta (cuando uno sube, el otro baja)
        r =  0: sin correlación lineal (movimientos independientes)
        |r| > 0.7: correlación fuerte
        |r| < 0.3: correlación débil

    VENTAJA SOBRE EUCLIDIANA:
        No requiere normalización porque trabaja con desviaciones respecto
        a la media, lo que cancela las diferencias de escala.

    Args:
        a, b: Series de precios de cierre

    Returns:
        float en [-1, 1]
    """
    _validar_series(a, b, "Pearson")

    # Alinear longitudes
    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]

    # Calcular medias
    media_a = _media(a)
    media_b = _media(b)

    # Calcular numerador: covarianza (sin dividir por n)
    numerador = sum((ai - media_a) * (bi - media_b) for ai, bi in zip(a, b))

    # Calcular denominador: producto de desviaciones estándar (sin dividir por n)
    var_a       = sum((ai - media_a) ** 2 for ai in a)
    var_b       = sum((bi - media_b) ** 2 for bi in b)
    denominador = math.sqrt(var_a * var_b)

    if denominador == 0:
        # Una o ambas series son constantes → correlación indefinida
        return 0.0

    return numerador / denominador

# ALGORITMO 3: SIMILITUD POR COSENO

def similitud_coseno(a: list[float], b: list[float]) -> float:
    """
    Mide el ángulo entre dos series tratadas como vectores en ℝⁿ.

    CONCEPTO:
        En lugar de medir la distancia entre los extremos de los vectores
        (como Euclidiana), mide el ángulo entre ellos. Dos vectores con
        el mismo ángulo tienen similitud coseno = 1, independientemente
        de su magnitud.

    FÓRMULA — Complejidad: O(n)
    ────────────────────────────
        cos(θ) = (A · B) / (‖A‖ · ‖B‖)
               = Σ(Aᵢ · Bᵢ) / (√Σ(Aᵢ²) · √Σ(Bᵢ²))

        Donde:
            A · B  = producto punto (dot product)
            ‖A‖    = norma euclidiana del vector A

    INTERPRETACIÓN:
        cos(θ) = +1: vectores en la misma dirección (comportamiento idéntico)
        cos(θ) =  0: vectores perpendiculares (sin relación)
        cos(θ) = -1: vectores en direcciones opuestas

    DIFERENCIA CON PEARSON:
        Pearson centra los datos (resta la media) antes de calcular.
        Coseno no centra, por lo que es sensible al nivel absoluto de precios.
        Para series financieras, Pearson suele ser más informativo.

    Args:
        a, b: Series de precios de cierre

    Returns:
        float en [-1, 1]
    """
    _validar_series(a, b, "Coseno")

    # Alinear longitudes
    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]

    # Producto punto: Σ(Aᵢ · Bᵢ)
    producto_punto = sum(ai * bi for ai, bi in zip(a, b))

    # Normas euclidianas: ‖A‖ = √Σ(Aᵢ²)
    norma_a = math.sqrt(sum(ai ** 2 for ai in a))
    norma_b = math.sqrt(sum(bi ** 2 for bi in b))

    if norma_a == 0 or norma_b == 0:
        return 0.0   # Vector nulo → similitud indefinida

    return producto_punto / (norma_a * norma_b)

# ALGORITMO 4: DTW — DYNAMIC TIME WARPING

def dtw(a: list[float], b: list[float],
        normalizar: bool = True, window_pct: float = 0.1) -> float:
    """
    Calcula la distancia DTW entre dos series temporales.

    CONCEPTO:
        A diferencia de la Distancia Euclidiana (que compara punto a punto),
        DTW permite "estirar" o "comprimir" el eje temporal para encontrar
        la alineación óptima entre las dos series.

        Esto es útil cuando dos activos reaccionan al mismo evento
        macroeconómico pero con diferente retraso temporal.

    ALGORITMO — Programación Dinámica — Complejidad: O(n²)
    ────────────────────────────────────────────────────────
        Se construye una matriz (n+1) × (m+1) donde:
            matriz[i][j] = costo mínimo de alinear A[0..i-1] con B[0..j-1]

        Recurrencia:
            costo_local = |A[i-1] - B[j-1]|
            matriz[i][j] = costo_local + min(
                matriz[i-1][j],      ← inserción (avanzar en A)
                matriz[i][j-1],      ← eliminación (avanzar en B)
                matriz[i-1][j-1]     ← coincidencia (avanzar en ambas)
            )

        La distancia DTW es matriz[n][m].

    OPTIMIZACIÓN — Ventana de Sakoe-Chiba:
        Para reducir la complejidad de O(n²) a O(n·w), se restringe
        la búsqueda a una banda diagonal de ancho w = n × window_pct.
        Esto evita alineaciones "irrazonables" (ej: comparar el primer
        día de una serie con el último de la otra).

        Con window_pct = 0.1 (10%), w = 0.1 × n días.

    INTERPRETACIÓN:
        DTW = 0: series idénticas (después de normalizar)
        DTW pequeño: series similares aunque desfasadas
        DTW grande: series muy diferentes

    Args:
        a, b:        Series de precios de cierre
        normalizar:  Si True, aplica Min-Max antes de calcular
        window_pct:  Tamaño de la ventana Sakoe-Chiba como fracción de n

    Returns:
        float >= 0. Menor valor = series más similares.
    """
    _validar_series(a, b, "DTW")

    # Normalizar para comparar comportamiento, no magnitud
    if normalizar:
        a = normalizar_minmax(a)
        b = normalizar_minmax(b)

    n = len(a)
    m = len(b)

    # Radio de la ventana Sakoe-Chiba
    # max(..., abs(n-m)) garantiza que siempre sea posible alinear series de diferente longitud
    window = max(int(n * window_pct), abs(n - m))

    # Inicializar matriz con infinito (posiciones fuera de la ventana permanecen en inf)
    INF = float("inf")
    matriz = [[INF] * (m + 1) for _ in range(n + 1)]
    matriz[0][0] = 0.0   # caso base: alinear series vacías tiene costo 0

    # Llenar la matriz dentro de la ventana Sakoe-Chiba
    for i in range(1, n + 1):
        # Limitar j al rango [max(1, i-window), min(m, i+window)]
        inicio_j = max(1, i - window)
        fin_j    = min(m, i + window)

        for j in range(inicio_j, fin_j + 1):
            # Costo local: diferencia absoluta entre los dos puntos
            costo = abs(a[i - 1] - b[j - 1])

            # Costo acumulado mínimo de las tres posibles transiciones
            matriz[i][j] = costo + min(
                matriz[i - 1][j],      # vengo de arriba (avanzar solo en A)
                matriz[i][j - 1],      # vengo de la izquierda (avanzar solo en B)
                matriz[i - 1][j - 1],  # vengo de la diagonal (avanzar en ambas)
            )

    return matriz[n][m]

# FUNCIÓN DE CONVENIENCIA: Calcular los 4 algoritmos para un par

def calcular_todas(ticker_a: str, serie_a: list[float],
                   ticker_b: str, serie_b: list[float]) -> dict:
    """
    Ejecuta los 4 algoritmos de similitud para un par de activos.

    Args:
        ticker_a, ticker_b: Símbolos de los activos (ej: "SPY", "QQQ")
        serie_a, serie_b:   Series de precios de cierre

    Returns:
        Dict con los resultados de los 4 algoritmos:
        {
            "par":        "SPY vs QQQ",
            "euclidiana": 0.123,   ← menor = más similar
            "pearson":    0.856,   ← mayor = más similar
            "coseno":     0.921,   ← mayor = más similar
            "dtw":        0.045,   ← menor = más similar
        }
    """
    return {
        "par":        f"{ticker_a} vs {ticker_b}",
        "euclidiana": distancia_euclidiana(serie_a, serie_b, normalizar=True),
        "pearson":    correlacion_pearson(serie_a, serie_b),
        "coseno":     similitud_coseno(serie_a, serie_b),
        "dtw":        dtw(serie_a, serie_b, normalizar=True),
    }

# FUNCIÓN PRINCIPAL: Matriz de similitud para todos los pares

def matriz_similitud(series: dict[str, list[float]],
                     algoritmo: str = "pearson") -> list[dict]:
    """
    Genera la matriz de similitud completa para todos los pares de activos.

    COMPLEJIDAD TOTAL: O(n² · m)
        n = número de activos (20)
        m = longitud de cada serie (~1260 días para 5 años)
        Pares calculados: C(20,2) = 190 pares

    ORDENAMIENTO DE RESULTADOS:
        - Euclidiana y DTW: orden ASCENDENTE (menor distancia = más similar)
        - Pearson y Coseno: orden DESCENDENTE (mayor correlación = más similar)

    Args:
        series:    {ticker: [precios_cierre]}
        algoritmo: 'euclidiana' | 'pearson' | 'coseno' | 'dtw'

    Returns:
        Lista de 190 dicts ordenada por similitud (más similares primero):
        [{"ticker1": "SPY", "ticker2": "QQQ", "algoritmo": "pearson", "valor": 0.97}, ...]
    """
    algoritmos_disponibles = {
        "euclidiana": lambda a, b: distancia_euclidiana(a, b),
        "pearson":    correlacion_pearson,
        "coseno":     similitud_coseno,
        "dtw":        lambda a, b: dtw(a, b),
    }

    if algoritmo not in algoritmos_disponibles:
        raise ValueError(
            f"Algoritmo '{algoritmo}' no disponible. "
            f"Opciones: {list(algoritmos_disponibles.keys())}"
        )

    fn      = algoritmos_disponibles[algoritmo]
    tickers = list(series.keys())
    resultados = []

    # Iterar solo el triángulo superior de la matriz (evitar duplicados)
    # Par (A, B) es equivalente a (B, A) para todos los algoritmos
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
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
                print(f"[SIMILITUD] Error calculando {t1}-{t2} con {algoritmo}: {e}")

    # Ordenar: distancias ASC (menor = más similar), correlaciones DESC (mayor = más similar)
    invertir = algoritmo in {"pearson", "coseno"}
    resultados.sort(key=lambda r: r["valor"], reverse=invertir)

    return resultados
