"""
algorithms/patterns.py — Detección de Patrones con Ventana Deslizante
Universidad del Quindío — Análisis de Algoritmos — Requerimiento 3

PROPÓSITO:
    Implementa los algoritmos de detección de patrones en series de precios
    financieros usando la técnica de ventana deslizante (sliding window).

ALGORITMOS IMPLEMENTADOS:
    1. Ventana deslizante — O(n·k) — detecta patrones en segmentos de k días
    2. Detección de picos y valles — O(n) — máximos y mínimos locales
    3. Media Móvil Simple (SMA) — O(n·k) — suaviza la serie de precios
    4. Golden Cross / Death Cross — O(n) — señales de cruce de medias móviles

PATRONES DEFINIDOS (requeridos por el enunciado):
    Patrón 1 — Días consecutivos al alza:
        Si >= 75% de los días en la ventana tienen cierre > cierre anterior
        → patrón "N_dias_alza"

    Patrón 2 — Rebote (V-shape):
        Si la primera mitad de la ventana es bajista y la segunda es alcista
        → patrón "rebote"
        Este es el patrón adicional definido por el equipo.

RESTRICCIONES DEL ENUNCIADO CUMPLIDAS:
    - NO usa pandas (rolling, shift), numpy ni scipy.
    - Todos los algoritmos implementados con bucles y operaciones básicas.
"""

import math
from config import VENTANA_DESLIZANTE_DIAS


# ------------------------------------------------------------------
# ALGORITMO 1: VENTANA DESLIZANTE (SLIDING WINDOW)
# ------------------------------------------------------------------

def detectar_patrones(
    fechas: list[str],
    precios: list[float],
    ventana: int = VENTANA_DESLIZANTE_DIAS
) -> list[dict]:
    """
    Recorre la serie de precios con una ventana deslizante y clasifica
    cada segmento en un patrón predefinido.

    ALGORITMO — Complejidad: O(n · k)
    ────────────────────────────────────
        n = longitud de la serie de precios
        k = tamaño de la ventana (default: 20 días)

        Para cada posición i desde 0 hasta n-k:
            segmento = precios[i : i + k]
            patrón   = clasificar(segmento)

        Total de ventanas evaluadas: n - k + 1

    CLASIFICACIÓN DE PATRONES:
        Para cada segmento se cuentan los días de alza y baja:
            días_alza = #{j : precios[j] > precios[j-1]}
            días_baja = #{j : precios[j] < precios[j-1]}

        Reglas de clasificación (umbral = 75%):
            Si días_alza / (k-1) >= 0.75 → "N_dias_alza"
            Si días_baja / (k-1) >= 0.75 → "N_dias_baja"
            Si primera mitad baja Y segunda mitad sube → "rebote"
            En otro caso → "neutro" (no se guarda)

        Variación porcentual del segmento:
            Δ% = (precio_final - precio_inicial) / precio_inicial × 100

    FILTRO DE RELEVANCIA:
        Solo se guardan patrones donde:
            - El patrón NO es "neutro", O
            - La variación porcentual es >= 1% (movimiento significativo)

    Args:
        fechas:   Lista de fechas 'YYYY-MM-DD' (misma longitud que precios)
        precios:  Lista de precios de cierre ordenados ASC por fecha
        ventana:  Tamaño de la ventana en días (default: 20 de config.py)

    Returns:
        Lista de dicts con los patrones detectados:
        [{
            "fecha_inicio":  "2023-01-02",
            "fecha_fin":     "2023-01-27",
            "patron":        "19_dias_alza",
            "valor_inicio":  150.25,
            "valor_fin":     165.80,
            "variacion_pct": 10.35
        }, ...]
    """
    n = len(precios)
    if n < ventana:
        return []   # Serie demasiado corta para la ventana solicitada

    resultados = []

    for i in range(n - ventana + 1):
        # Extraer el segmento actual
        segmento   = precios[i : i + ventana]
        fechas_seg = fechas[i : i + ventana]

        precio_inicial = segmento[0]
        precio_final   = segmento[-1]

        if precio_inicial == 0:
            continue   # Evitar división por cero

        # Calcular variación porcentual total del segmento
        variacion_pct = (precio_final - precio_inicial) / precio_inicial * 100

        # Clasificar el patrón del segmento
        patron = _clasificar_segmento(segmento)

        # Guardar solo patrones relevantes
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


def _clasificar_segmento(segmento: list[float]) -> str:
    """
    Clasifica un segmento de precios en uno de los patrones definidos.

    LÓGICA DE CLASIFICACIÓN:
        1. Contar días de alza y baja en el segmento
        2. Aplicar reglas con umbral del 75%
        3. Verificar patrón de rebote (V-shape)
        4. Si ninguna regla aplica → "neutro"

    Args:
        segmento: Lista de precios de cierre del segmento

    Returns:
        String con el nombre del patrón detectado
    """
    k = len(segmento)
    if k < 2:
        return "neutro"

    # Contar días de alza y baja
    dias_alza = sum(1 for j in range(1, k) if segmento[j] > segmento[j - 1])
    dias_baja = sum(1 for j in range(1, k) if segmento[j] < segmento[j - 1])
    total_dias = k - 1   # días con cambio (k-1 porque comparamos pares)

    umbral = 0.75   # 75% de los días deben cumplir la condición

    # PATRÓN 1: Días consecutivos al alza
    if dias_alza / total_dias >= umbral:
        return f"{total_dias}_dias_alza"

    # PATRÓN 1b: Días consecutivos a la baja
    if dias_baja / total_dias >= umbral:
        return f"{total_dias}_dias_baja"

    # PATRÓN 2: Rebote (V-shape)
    # Primera mitad bajista Y segunda mitad alcista
    mitad = k // 2
    primera_baja = all(segmento[j] <= segmento[j - 1] for j in range(1, mitad))
    segunda_alza = all(segmento[j] >= segmento[j - 1] for j in range(mitad, k))
    if primera_baja and segunda_alza:
        return "rebote"

    return "neutro"


# ------------------------------------------------------------------
# ALGORITMO 2: DETECCIÓN DE PICOS Y VALLES
# ------------------------------------------------------------------

def detectar_picos_valles(
    fechas: list[str],
    precios: list[float],
    vecindad: int = 3
) -> dict:
    """
    Identifica máximos locales (picos) y mínimos locales (valles) en la serie.

    ALGORITMO — Complejidad: O(n)
    ─────────────────────────────
        Para cada punto i (excluyendo los bordes):
            ventana = precios[i - vecindad : i + vecindad + 1]

            Es PICO  si precios[i] >= todos los valores de la ventana
            Es VALLE si precios[i] <= todos los valores de la ventana

    PARÁMETRO vecindad:
        Define el "radio" de comparación. Con vecindad=3, un pico debe
        ser mayor que los 3 días anteriores Y los 3 días posteriores.
        Mayor vecindad → menos picos/valles detectados (más significativos).

    APLICACIÓN FINANCIERA:
        Los picos y valles son puntos de soporte y resistencia en análisis
        técnico. Identificarlos algorítmicamente permite detectar niveles
        de precio donde el mercado históricamente ha revertido su tendencia.

    Args:
        fechas:   Lista de fechas
        precios:  Lista de precios de cierre
        vecindad: Radio de comparación (default: 3 días)

    Returns:
        {
            "picos":  [{"fecha": "2023-05-15", "precio": 450.25}, ...],
            "valles": [{"fecha": "2023-03-10", "precio": 380.50}, ...]
        }
    """
    n = len(precios)
    picos  = []
    valles = []

    # Iterar desde vecindad hasta n-vecindad para tener vecinos en ambos lados
    for i in range(vecindad, n - vecindad):
        ventana = precios[i - vecindad : i + vecindad + 1]
        centro  = precios[i]

        # Es pico si es mayor o igual a todos los valores de la ventana
        es_pico  = all(centro >= v for v in ventana)
        # Es valle si es menor o igual a todos los valores de la ventana
        es_valle = all(centro <= v for v in ventana)

        if es_pico:
            picos.append({"fecha": fechas[i], "precio": round(centro, 4)})
        elif es_valle:
            valles.append({"fecha": fechas[i], "precio": round(centro, 4)})

    return {"picos": picos, "valles": valles}


# ------------------------------------------------------------------
# ALGORITMO 3: MEDIA MÓVIL SIMPLE (SMA)
# ------------------------------------------------------------------

def media_movil_simple(precios: list[float], ventana: int) -> list[float | None]:
    """
    Calcula la Media Móvil Simple (SMA) para cada posición de la serie.

    CONCEPTO:
        La SMA suaviza la serie de precios promediando los últimos k días.
        Elimina el "ruido" de las fluctuaciones diarias y revela la tendencia.

    FÓRMULA — Complejidad: O(n · k)
    ────────────────────────────────
        SMA[i] = (P[i] + P[i-1] + ... + P[i-k+1]) / k

        Para i < k-1: SMA[i] = None (ventana incompleta)

    NOTA SOBRE OPTIMIZACIÓN:
        Esta implementación es O(n·k). Se podría optimizar a O(n) usando
        una "suma rodante" (sliding sum): restar el elemento que sale de la
        ventana y sumar el que entra. Se implementa la forma directa para
        mayor claridad académica, como indica el enunciado.

    APLICACIÓN:
        Se usa como base para detectar Golden Cross y Death Cross.
        También se dibuja sobre el gráfico de velas OHLC en el dashboard.

    Args:
        precios: Lista de precios de cierre
        ventana: Número de días para el promedio (ej: 10, 30, 50, 200)

    Returns:
        Lista de floats (o None para las primeras k-1 posiciones)
    """
    n = len(precios)
    resultado = [None] * n

    for i in range(ventana - 1, n):
        # Extraer el segmento de los últimos `ventana` días
        segmento = precios[i - ventana + 1 : i + 1]
        resultado[i] = sum(segmento) / ventana

    return resultado


# ------------------------------------------------------------------
# ALGORITMO 4: GOLDEN CROSS / DEATH CROSS
# ------------------------------------------------------------------

def detectar_cruces_medias(
    fechas: list[str],
    precios: list[float],
    ventana_corta: int = 10,
    ventana_larga: int = 30
) -> list[dict]:
    """
    Detecta señales de cruce entre dos medias móviles simples.

    CONCEPTO:
        Se calculan dos SMAs con diferentes períodos:
        - SMA corta (ej: 10 días): más reactiva, sigue el precio de cerca
        - SMA larga (ej: 30 días): más suave, representa la tendencia

        Cuando la SMA corta cruza la SMA larga, se genera una señal:

    GOLDEN CROSS (señal alcista):
        La SMA corta pasa de DEBAJO a ARRIBA de la SMA larga.
        Indica que el momentum de corto plazo supera al de largo plazo.
        → Señal de posible compra

    DEATH CROSS (señal bajista):
        La SMA corta pasa de ARRIBA a ABAJO de la SMA larga.
        Indica que el momentum de corto plazo cae por debajo del largo plazo.
        → Señal de posible venta

    ALGORITMO — Complejidad: O(n · max(ventana_corta, ventana_larga))
    ──────────────────────────────────────────────────────────────────
        1. Calcular SMA corta y SMA larga para toda la serie
        2. Para cada día i (desde 1 hasta n):
            Si SMA_corta[i-1] <= SMA_larga[i-1] Y SMA_corta[i] > SMA_larga[i]:
                → Golden Cross en el día i
            Si SMA_corta[i-1] >= SMA_larga[i-1] Y SMA_corta[i] < SMA_larga[i]:
                → Death Cross en el día i

    LIMITACIÓN:
        Las señales de cruce son indicadores rezagados (lagging indicators):
        confirman una tendencia que ya comenzó, no la predicen.

    Args:
        fechas:        Lista de fechas
        precios:       Lista de precios de cierre
        ventana_corta: Período de la SMA rápida (default: 10 días)
        ventana_larga: Período de la SMA lenta (default: 30 días)

    Returns:
        Lista de dicts con cada cruce detectado:
        [{
            "fecha":     "2023-06-15",
            "tipo":      "golden_cross",
            "precio":    450.25,
            "sma_corta": 448.10,
            "sma_larga": 445.30
        }, ...]
    """
    # Calcular ambas medias móviles
    sma_corta = media_movil_simple(precios, ventana_corta)
    sma_larga = media_movil_simple(precios, ventana_larga)

    cruces = []
    n = len(precios)

    for i in range(1, n):
        # Valores del día anterior y del día actual para ambas SMAs
        c_prev = sma_corta[i - 1]
        c_curr = sma_corta[i]
        l_prev = sma_larga[i - 1]
        l_curr = sma_larga[i]

        # Saltar si alguna SMA no tiene valor (ventana incompleta)
        if None in (c_prev, c_curr, l_prev, l_curr):
            continue

        # GOLDEN CROSS: SMA corta cruza SMA larga hacia arriba
        # Condición: ayer estaba debajo (o igual) y hoy está arriba
        if c_prev <= l_prev and c_curr > l_curr:
            cruces.append({
                "fecha":     fechas[i],
                "tipo":      "golden_cross",
                "precio":    round(precios[i], 4),
                "sma_corta": round(c_curr, 4),
                "sma_larga": round(l_curr, 4),
            })

        # DEATH CROSS: SMA corta cruza SMA larga hacia abajo
        # Condición: ayer estaba arriba (o igual) y hoy está abajo
        elif c_prev >= l_prev and c_curr < l_curr:
            cruces.append({
                "fecha":     fechas[i],
                "tipo":      "death_cross",
                "precio":    round(precios[i], 4),
                "sma_corta": round(c_curr, 4),
                "sma_larga": round(l_curr, 4),
            })

    return cruces
