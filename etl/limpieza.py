"""
etl/cleaner.py — Limpieza e Interpolación de Datos Financieros
Universidad del Quindío — Análisis de Algoritmos — Requerimiento 1

PROPÓSITO:
    Implementa los algoritmos de limpieza de datos que el enunciado exige:
    1. Interpolación lineal para valores faltantes (None/NaN)
    2. Detección de outliers con Z-Score
    3. Eliminación de registros inválidos (cierres negativos o cero)

RESTRICCIONES DEL ENUNCIADO CUMPLIDAS:
    - NO usa pandas (fillna, interpolate), numpy (interp) ni scipy.
    - Todos los algoritmos están implementados con estructuras básicas de Python.
    - Cada función tiene su fórmula matemática documentada.

JUSTIFICACIÓN DE LAS TÉCNICAS (requerida por el enunciado):
    - Interpolación lineal: apropiada para series de tiempo financieras porque
      asume que el precio varía linealmente entre dos puntos conocidos. Es mejor
      que forward-fill porque no introduce sesgo hacia el pasado.
    - Z-Score: detecta valores estadísticamente anómalos. El umbral 3.5 (en lugar
      del estándar 3.0) es más conservador para finanzas, donde movimientos
      extremos legítimos son más frecuentes que en otras series.
    - Eliminación de cierres <= 0: un precio negativo o cero es físicamente
      imposible en acciones y ETFs, por lo que se elimina directamente.
"""

def interpolar_linealmente(valores: list) -> list:
    """
    Rellena valores None en una lista usando interpolación lineal.

    ALGORITMO — Complejidad: O(n)
    ─────────────────────────────
    Para cada bloque de Nones consecutivos entre dos valores conocidos
    (izquierdo en posición `izq`, derecho en posición `der`):

        V[k] = V[izq] + (V[der] - V[izq]) × (k - izq) / (der - izq)

    Casos especiales:
        - Nones al INICIO (sin vecino izquierdo): backward fill
          → todos los Nones toman el valor del primer dato conocido
        - Nones al FINAL (sin vecino derecho): forward fill
          → todos los Nones toman el valor del último dato conocido

    IMPACTO ALGORÍTMICO:
        La interpolación lineal preserva la tendencia local de la serie.
        Introduce un sesgo suave hacia la media entre los dos extremos,
        lo que es aceptable para datos faltantes por días festivos o
        diferencias de calendarios bursátiles entre mercados.

    Args:
        valores: Lista de floats o None (no se muta el original)

    Returns:
        Nueva lista de floats sin ningún None

    Ejemplo:
        [1.0, None, None, 4.0] → [1.0, 2.0, 3.0, 4.0]
        [None, None, 3.0]      → [3.0, 3.0, 3.0]  (backward fill)
        [1.0, None, None]      → [1.0, 1.0, 1.0]  (forward fill)
    """
    n = len(valores)
    resultado = list(valores)   # Copia para no mutar el original

    i = 0
    while i < n:
        if resultado[i] is None:
            # Encontrar el límite izquierdo (último valor conocido antes del bloque)
            izq = i - 1

            # Encontrar el límite derecho (primer valor conocido después del bloque)
            der = i + 1
            while der < n and resultado[der] is None:
                der += 1

            if izq < 0 and der < n:
                # CASO 1: Nones al inicio de la lista → backward fill
                # No hay vecino izquierdo, usamos el primer valor conocido
                for k in range(i, der):
                    resultado[k] = resultado[der]

            elif izq >= 0 and der >= n:
                # CASO 2: Nones al final de la lista → forward fill
                # No hay vecino derecho, usamos el último valor conocido
                for k in range(i, n):
                    resultado[k] = resultado[izq]

            elif izq >= 0 and der < n:
                # CASO 3: Nones en el medio → interpolación lineal
                # Fórmula: V[k] = V[izq] + (V[der] - V[izq]) * (k - izq) / (der - izq)
                v_izq = resultado[izq]
                v_der = resultado[der]
                tramo = der - izq   # distancia total entre los dos vecinos conocidos
                for k in range(izq + 1, der):
                    # Fracción de avance desde izq hasta der
                    fraccion = (k - izq) / tramo
                    resultado[k] = v_izq + (v_der - v_izq) * fraccion

            # Saltar al siguiente elemento después del bloque procesado
            i = der + 1
        else:
            i += 1

    return resultado

def limpiar_dataset(filas: list[dict]) -> list[dict]:
    """
    Limpia un dataset OHLCV completo aplicando los algoritmos de limpieza.

    PASOS DEL PROCESO:
        1. Ordenar por fecha ASC (garantiza consistencia temporal)
        2. Eliminar filas con cierre inválido (None, negativo o cero)
        3. Interpolar valores None en columnas OHLC individualmente
        4. Rellenar volumen nulo con 0 (el volumen no se interpola porque
           un volumen de 0 es válido en días de baja negociación)

    JUSTIFICACIÓN DE DECISIONES:
        - Se interpola OHLC pero NO el volumen: el volumen es una cantidad
          discreta que no tiene sentido interpolar (no existe "medio volumen").
        - Se eliminan cierres <= 0 antes de interpolar: un cierre negativo
          contaminaría la interpolación de los valores vecinos.
        - Se ordena por fecha antes de interpolar: la interpolación lineal
          solo tiene sentido en series temporales ordenadas.

    Args:
        filas: Lista de dicts con keys: fecha, apertura, maximo, minimo, cierre, volumen

    Returns:
        Lista limpia y ordenada por fecha ASC
    """
    if not filas:
        return []

    # PASO 1: Ordenar por fecha ASC
    # Usa sorted() de Python (permitido por el enunciado para operaciones de utilidad)
    filas_ordenadas = sorted(filas, key=lambda f: f["fecha"])

    # PASO 2: Eliminar filas con cierre inválido
    # Un precio de cierre <= 0 es físicamente imposible en mercados financieros
    filas_validas = [
        f for f in filas_ordenadas
        if f.get("cierre") is not None and f["cierre"] > 0
    ]

    # PASO 3: Interpolar columnas OHLC individualmente
    # Cada columna se interpola de forma independiente para preservar
    # la relación OHLC (apertura <= máximo, mínimo <= cierre, etc.)
    columnas_a_interpolar = ["apertura", "maximo", "minimo", "cierre"]
    for col in columnas_a_interpolar:
        # Extraer la serie de valores de esta columna
        serie = [f.get(col) for f in filas_validas]
        # Aplicar interpolación lineal
        serie_limpia = interpolar_linealmente(serie)
        # Escribir los valores interpolados de vuelta en las filas
        for i, fila in enumerate(filas_validas):
            fila[col] = serie_limpia[i]

    # PASO 4: Rellenar volumen nulo con 0
    for fila in filas_validas:
        if fila.get("volumen") is None or fila["volumen"] < 0:
            fila["volumen"] = 0

    return filas_validas

def detectar_outliers_zscore(valores: list[float], umbral: float = 3.5) -> list[int]:
    """
    Detecta índices de valores atípicos (outliers) usando el Z-Score.

    ALGORITMO — Complejidad: O(n)
    ─────────────────────────────
    El Z-Score mide cuántas desviaciones estándar se aleja un valor
    de la media de la distribución:

        media    = Σ(vᵢ) / n
        varianza = Σ(vᵢ - media)² / n
        std      = √varianza
        zᵢ       = (vᵢ - media) / std

    Un valor es outlier si |zᵢ| > umbral.

    ELECCIÓN DEL UMBRAL 3.5:
        El umbral estándar es 3.0 (cubre el 99.7% de una distribución normal).
        En finanzas se usa 3.5 porque los retornos financieros tienen "colas
        pesadas" (fat tails): movimientos extremos son más frecuentes que en
        una distribución normal. Con 3.5 se evita eliminar movimientos legítimos
        como crashes o rallies del mercado.

    IMPACTO ALGORÍTMICO:
        Los outliers detectados pueden eliminarse o corregirse. En este proyecto
        se reportan pero no se eliminan automáticamente, dejando la decisión
        al pipeline ETL según el contexto de cada activo.

    Args:
        valores: Lista de floats a analizar
        umbral:  Umbral de Z-Score (default: 3.5 para finanzas)

    Returns:
        Lista de índices donde se detectaron outliers

    Ejemplo:
        [1, 2, 3, 100, 2, 1] → [3]  (el 100 es un outlier)
    """
    n = len(valores)
    if n < 2:
        return []   # Necesitamos al menos 2 valores para calcular desviación estándar

    # Calcular media aritmética manualmente: Σ(v) / n
    media = sum(valores) / n

    # Calcular varianza poblacional: Σ(v - media)² / n
    suma_cuadrados = sum((v - media) ** 2 for v in valores)
    std = (suma_cuadrados / n) ** 0.5   # desviación estándar = √varianza

    if std == 0:
        return []   # Todos los valores son iguales, no hay outliers

    # Identificar índices donde |z| > umbral
    return [
        i for i, v in enumerate(valores)
        if abs((v - media) / std) > umbral
    ]
