"""
etl/cleaner.py — Limpieza e Interpolación Manual de Datos
SIN pandas, SIN numpy — estructuras de datos básicas de Python
"""


# ======================================================= #
# ⚠️ ALGORITMO: Interpolación Lineal Manual               #
# ✏️ ZONA DE LÓGICA MODIFICABLE                           #
# Complejidad Esperada: O(n)                               #
# ======================================================= #
def interpolar_linealmente(valores: list) -> list:
    """
    Rellena valores None/NaN en una lista usando interpolación lineal.

    Fórmula para el punto i entre dos vecinos conocidos (a, b):
        V[i] = V[izq] + (V[der] - V[izq]) * (i - izq) / (der - izq)

    Si hay Nones al inicio o al final de la lista (sin vecinos),
    se rellena con el primer o último valor conocido (fill forward/backward).

    Args:
        valores: Lista de floats o None

    Returns:
        Lista de floats sin None
    """
    n = len(valores)
    resultado = list(valores)   # Copia para no mutar el original

    i = 0
    while i < n:
        if resultado[i] is None:
            # Buscar el índice izquierdo conocido
            izq = i - 1
            # Buscar el índice derecho conocido
            der = i + 1
            while der < n and resultado[der] is None:
                der += 1

            if izq < 0 and der < n:
                # Nones al inicio → backward fill con el primer valor conocido
                for k in range(i, der):
                    resultado[k] = resultado[der]

            elif izq >= 0 and der >= n:
                # Nones al final → forward fill con el último valor conocido
                for k in range(i, n):
                    resultado[k] = resultado[izq]

            elif izq >= 0 and der < n:
                # Interpolación lineal entre dos vecinos conocidos
                v_izq = resultado[izq]
                v_der = resultado[der]
                tramo = der - izq      # Número de pasos entre los dos vecinos
                for k in range(izq + 1, der):
                    resultado[k] = v_izq + (v_der - v_izq) * (k - izq) / tramo

            i = der + 1
        else:
            i += 1

    return resultado
# ======================================================= #


def limpiar_dataset(filas: list[dict]) -> list[dict]:
    """
    Limpia un dataset OHLCV completo:
    1. Ordena por fecha (ascendente)
    2. Detecta y rellena valores None en cierre, apertura, máximo, mínimo
    3. Elimina filas con volumen negativo o cierres <= 0

    Args:
        filas: Lista de dicts con keys fecha, apertura, maximo, minimo, cierre, volumen

    Returns:
        Lista limpia ordenada
    """
    if not filas:
        return []

    # 1. Ordenar por fecha
    filas_ordenadas = sorted(filas, key=lambda f: f["fecha"])

    # 2. Eliminar filas con cierre inválido (negativo o cero)
    filas_validas = [
        f for f in filas_ordenadas
        if f.get("cierre") is not None and f["cierre"] > 0
    ]

    # 3. Interpolar columnas OHLC individualmente
    columnas = ["apertura", "maximo", "minimo", "cierre"]
    for col in columnas:
        serie = [f.get(col) for f in filas_validas]
        serie_limpia = interpolar_linealmente(serie)
        for i, fila in enumerate(filas_validas):
            fila[col] = serie_limpia[i]

    # 4. Rellenar volumen nulo con 0 (no se interpola volumen)
    for fila in filas_validas:
        if fila.get("volumen") is None or fila["volumen"] < 0:
            fila["volumen"] = 0

    return filas_validas


def detectar_outliers_zscore(valores: list[float], umbral: float = 3.5) -> list[int]:
    """
    Detecta índices de posibles outliers usando Z-score implementado manualmente.
    Un valor es outlier si |z| > umbral.

    Fórmula:
        media = Σ(v) / n
        varianza = Σ((v - media)²) / n
        std = √varianza
        z_i = (v_i - media) / std

    Args:
        valores:  Lista de floats
        umbral:   Umbral de Z-score (por defecto 3.5 para finanzas)

    Returns:
        Lista de índices donde hay outliers
    """
    n = len(valores)
    if n < 2:
        return []

    # Media manual
    media = sum(valores) / n

    # Varianza manual
    suma_cuadrados = sum((v - media) ** 2 for v in valores)
    std = (suma_cuadrados / n) ** 0.5

    if std == 0:
        return []

    return [
        i for i, v in enumerate(valores)
        if abs((v - media) / std) > umbral
    ]
