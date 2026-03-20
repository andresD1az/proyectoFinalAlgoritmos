"""
algorithms/patterns.py — Reconocimiento de Patrones con Ventana Deslizante
Implementado DESDE CERO — SIN numpy, SIN pandas

Detecta secuencias significativas en series de precios:
  - Días consecutivos al alza / a la baja
  - Rebotes (baja seguida de alza)
  - Tendencias neutrales
"""

import math
from config import VENTANA_DESLIZANTE_DIAS


# ======================================================= #
# ⚠️ ALGORITMO: Ventana Deslizante (Sliding Window)       #
# ✏️ ZONA DE LÓGICA MODIFICABLE                           #
# Complejidad Esperada: O(n · k)                           #
# donde n = longitud de la serie, k = tamaño de ventana   #
# ======================================================= #
def detectar_patrones(
    fechas: list[str],
    precios: list[float],
    ventana: int = VENTANA_DESLIZANTE_DIAS
) -> list[dict]:
    """
    Recorre la serie con una ventana deslizante de tamaño `ventana` y
    clasifica cada segmento en un patrón.

    Para cada posición i (de 0 a n-ventana):
        segmento = precios[i : i + ventana]

    Clasificación del segmento:
        - 'alza_N':  todos los días positivos (cierre[j] > cierre[j-1])
        - 'baja_N':  todos los días negativos
        - 'rebote':  baja en la primera mitad, alza en la segunda
        - 'neutro':  sin tendencia clara

    Variación porcentual del segmento:
        Δ% = (precio_final - precio_inicial) / precio_inicial × 100

    Args:
        fechas:   Lista de fechas en formato 'YYYY-MM-DD'
        precios:  Lista de precios de cierre
        ventana:  Tamaño de la ventana (días). Default: config.py

    Returns:
        Lista de dicts con el patrón de cada ventana que sea significativo
    """
    n = len(precios)
    if n < ventana:
        return []

    resultados = []

    for i in range(n - ventana + 1):
        segmento       = precios[i: i + ventana]
        fechas_seg     = fechas[i: i + ventana]
        precio_inicial = segmento[0]
        precio_final   = segmento[-1]

        if precio_inicial == 0:
            continue

        # Variación porcentual total del segmento
        variacion_pct = (precio_final - precio_inicial) / precio_inicial * 100

        # Clasificar el patrón interno del segmento
        patron = _clasificar_segmento(segmento)

        # Solo guardar patrones no neutros o variaciones significativas (> 1%)
        if patron != "neutro" or abs(variacion_pct) >= 1.0:
            resultados.append({
                "fecha_inicio":  fechas_seg[0],
                "fecha_fin":     fechas_seg[-1],
                "patron":        patron,
                "valor_inicio":  round(precio_inicial, 4),
                "valor_fin":     round(precio_final, 4),
                "variacion_pct": round(variacion_pct, 4),
            })

    return resultados
# ======================================================= #


def _clasificar_segmento(segmento: list[float]) -> str:
    """
    Clasifica un segmento de precios en un patrón.

    Lógica:
        Contar días positivos (cierre[j] > cierre[j-1]) y negativos.
        Si positivos >= 80% del total → 'alza_{n}'
        Si negativos >= 80% del total → 'baja_{n}'
        Si baja en mitad 1 y alza en mitad 2 → 'rebote'
        Caso contrario → 'neutro'
    """
    k = len(segmento)
    if k < 2:
        return "neutro"

    dias_alza  = sum(1 for j in range(1, k) if segmento[j] > segmento[j - 1])
    dias_baja  = sum(1 for j in range(1, k) if segmento[j] < segmento[j - 1])
    total_dias = k - 1

    umbral = 0.75    # 75% de los días deben cumplir la condición para clasificar

    if dias_alza / total_dias >= umbral:
        return f"{total_dias}_dias_alza"
    if dias_baja / total_dias >= umbral:
        return f"{total_dias}_dias_baja"

    # Detectar rebote: primera mitad hacia abajo, segunda hacia arriba
    mitad = k // 2
    primera_baja = all(segmento[j] <= segmento[j - 1] for j in range(1, mitad))
    segunda_alza = all(segmento[j] >= segmento[j - 1] for j in range(mitad, k))
    if primera_baja and segunda_alza:
        return "rebote"

    return "neutro"


# ======================================================= #
# ⚠️ ALGORITMO: Detección de Máximos y Mínimos Locales    #
# ✏️ ZONA DE LÓGICA MODIFICABLE                           #
# Complejidad Esperada: O(n)                               #
# ======================================================= #
def detectar_picos_valles(
    fechas: list[str],
    precios: list[float],
    vecindad: int = 3
) -> dict:
    """
    Identifica picos (máximos locales) y valles (mínimos locales)
    en la serie de precios.

    Un punto i es PICO si:
        precios[i] > precios[j]  para todo j en [i-vecindad, i+vecindad], j ≠ i

    Un punto i es VALLE si:
        precios[i] < precios[j]  para todo j en [i-vecindad, i+vecindad], j ≠ i

    Args:
        vecindad: Radio de vecindad para comparar (default=3 días)

    Returns:
        {"picos": [...], "valles": [...]}
    """
    n = len(precios)
    picos  = []
    valles = []

    for i in range(vecindad, n - vecindad):
        ventana = precios[i - vecindad: i + vecindad + 1]
        centro  = precios[i]

        es_pico  = all(centro >= v for v in ventana)
        es_valle = all(centro <= v for v in ventana)

        if es_pico:
            picos.append({"fecha": fechas[i], "precio": round(centro, 4)})
        elif es_valle:
            valles.append({"fecha": fechas[i], "precio": round(centro, 4)})

    return {"picos": picos, "valles": valles}
# ======================================================= #


# ======================================================= #
# ⚠️ ALGORITMO: Media Móvil Simple (SMA)                  #
# ✏️ ZONA DE LÓGICA MODIFICABLE                           #
# Complejidad Esperada: O(n · k)                           #
# ======================================================= #
def media_movil_simple(precios: list[float], ventana: int) -> list[float | None]:
    """
    Calcula la Media Móvil Simple (SMA) para cada posición.

    Fórmula:
        SMA[i] = (P[i] + P[i-1] + ... + P[i-k+1]) / k

    Para posiciones i < k-1, retorna None (ventana incompleta).

    Complejidad: O(n · k)  — se puede optimizar a O(n) con suma rodante,
    pero se implementa la forma directa para mayor claridad académica.
    """
    n = len(precios)
    resultado = [None] * n

    for i in range(ventana - 1, n):
        segmento = precios[i - ventana + 1: i + 1]
        resultado[i] = sum(segmento) / ventana

    return resultado
# ======================================================= #


# ======================================================= #
# ⚠️ ALGORITMO: Cruce de Medias Móviles (Golden/Death Cross) #
# ✏️ ZONA DE LÓGICA MODIFICABLE                              #
# Complejidad Esperada: O(n)                                 #
# ======================================================= #
def detectar_cruces_medias(
    fechas: list[str],
    precios: list[float],
    ventana_corta: int = 10,
    ventana_larga: int = 30
) -> list[dict]:
    """
    Detecta Golden Cross y Death Cross entre dos medias móviles.

    GOLDEN CROSS: SMA_corta cruza SMA_larga hacia ARRIBA
        → Señal alcista (potencial compra)

    DEATH CROSS:  SMA_corta cruza SMA_larga hacia ABAJO
        → Señal bajista (potencial venta)

    Complejidad: O(n · max(ventana_corta, ventana_larga))
    """
    sma_corta = media_movil_simple(precios, ventana_corta)
    sma_larga = media_movil_simple(precios, ventana_larga)

    cruces = []
    n = len(precios)

    for i in range(1, n):
        c_prev = sma_corta[i - 1]
        c_curr = sma_corta[i]
        l_prev = sma_larga[i - 1]
        l_curr = sma_larga[i]

        if None in (c_prev, c_curr, l_prev, l_curr):
            continue

        # Cruce alcista: la corta pasa de DEBAJO a ARRIBA de la larga
        if c_prev <= l_prev and c_curr > l_curr:
            cruces.append({
                "fecha":  fechas[i],
                "tipo":   "golden_cross",
                "precio": round(precios[i], 4),
                "sma_corta": round(c_curr, 4),
                "sma_larga": round(l_curr, 4),
            })

        # Cruce bajista: la corta pasa de ARRIBA a DEBAJO de la larga
        elif c_prev >= l_prev and c_curr < l_curr:
            cruces.append({
                "fecha":  fechas[i],
                "tipo":   "death_cross",
                "precio": round(precios[i], 4),
                "sma_corta": round(c_curr, 4),
                "sma_larga": round(l_curr, 4),
            })

    return cruces
# ======================================================= #
