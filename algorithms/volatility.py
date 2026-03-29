"""
algorithms/volatility.py — Métricas de Riesgo y Volatilidad Financiera
Universidad del Quindío — Análisis de Algoritmos — Requerimiento 3

PROPÓSITO:
    Implementa los algoritmos de medición de riesgo financiero para clasificar
    cada activo del portafolio en categorías: Conservador, Moderado o Agresivo.

MÉTRICAS IMPLEMENTADAS:
    1. Retornos Logarítmicos     — O(n)       — base para todas las métricas
    2. Volatilidad Histórica     — O(n)       — desviación estándar anualizada
    3. Máximo Drawdown           — O(n)       — mayor caída pico a valle
    4. VaR Histórico (95%)       — O(n log n) — pérdida máxima esperada
    5. Sharpe Ratio              — O(n)       — retorno ajustado por riesgo

CLASIFICACIÓN DE RIESGO:
    Basada en la volatilidad anualizada (σ):
        Conservador: σ < 15%   (ej: bonos del Tesoro TLT)
        Moderado:    15% ≤ σ < 30%  (ej: S&P 500 SPY)
        Agresivo:    σ ≥ 30%   (ej: petróleo USO, activos emergentes)

RESTRICCIONES DEL ENUNCIADO CUMPLIDAS:
    - NO usa numpy (std, mean), scipy (stats) ni pandas.
    - Todos los cálculos estadísticos implementados manualmente.
    - Fórmulas matemáticas documentadas en cada función.
"""

import math
from config import DIAS_VOLATILIDAD


# ------------------------------------------------------------------
# ALGORITMO 1: RETORNOS LOGARÍTMICOS
# ------------------------------------------------------------------

def calcular_retornos_log(precios: list[float]) -> list[float]:
    """
    Calcula los retornos logarítmicos diarios de una serie de precios.

    FÓRMULA — Complejidad: O(n)
    ────────────────────────────
        rᵢ = ln(Pᵢ / Pᵢ₋₁)   para i = 1, 2, ..., n-1

    VENTAJAS SOBRE RETORNOS SIMPLES ((Pᵢ - Pᵢ₋₁) / Pᵢ₋₁):
        1. ADITIVIDAD: los retornos log son aditivos en el tiempo.
           r_total = r₁ + r₂ + ... + rₙ (no es así con retornos simples)
        2. SIMETRÍA: una subida del 10% y una bajada del 10% tienen
           el mismo valor absoluto en retornos log.
        3. DISTRIBUCIÓN: los retornos log se aproximan mejor a una
           distribución normal, lo que facilita el análisis estadístico.

    NOTA: La serie de retornos tiene n-1 elementos (se pierde el primero
    porque no hay precio anterior para el día 0).

    Args:
        precios: Lista de precios de cierre ordenados ASC por fecha

    Returns:
        Lista de n-1 retornos logarítmicos diarios
    """
    retornos = []
    for i in range(1, len(precios)):
        if precios[i - 1] <= 0 or precios[i] <= 0:
            # Precio inválido (no debería ocurrir después de la limpieza ETL)
            retornos.append(0.0)
        else:
            retornos.append(math.log(precios[i] / precios[i - 1]))
    return retornos


# ------------------------------------------------------------------
# ALGORITMO 2: VOLATILIDAD HISTÓRICA RODANTE
# ------------------------------------------------------------------

def calcular_volatilidad(
    precios: list[float],
    ventana: int = DIAS_VOLATILIDAD
) -> list[dict]:
    """
    Calcula la volatilidad histórica rodante usando ventanas de `ventana` días.

    CONCEPTO:
        La volatilidad mide la dispersión de los retornos alrededor de su media.
        Una volatilidad alta indica que el precio fluctúa mucho (activo riesgoso).
        Una volatilidad baja indica que el precio es estable (activo conservador).

    ALGORITMO — Complejidad: O(n)
    ─────────────────────────────
        Para cada ventana de k retornos [rᵢ₋ₖ₊₁, ..., rᵢ]:

        1. Media de retornos:
               r̄ = Σ(rⱼ) / k

        2. Varianza muestral (corrección de Bessel, denominador k-1):
               s² = Σ(rⱼ - r̄)² / (k - 1)

           NOTA: Se usa k-1 (no k) para obtener un estimador insesgado
           de la varianza poblacional. Esto es la "corrección de Bessel".

        3. Volatilidad diaria:
               σ_diaria = √s²

        4. Volatilidad anualizada (factor √252):
               σ_anual = σ_diaria × √252

           NOTA: 252 es el número de días de negociación en un año bursátil
           (no 365, porque los mercados no operan fines de semana ni festivos).

    VENTANA RODANTE:
        Se calcula para cada posición i desde ventana-1 hasta n-1.
        Esto produce una serie de volatilidades que muestra cómo cambia
        el riesgo del activo a lo largo del tiempo.

    Args:
        precios: Lista de precios de cierre ordenados ASC
        ventana: Número de días para cada cálculo (default: 30 de config.py)

    Returns:
        Lista de dicts con la volatilidad de cada período:
        [{
            "indice":                 31,
            "ventana_dias":           30,
            "retorno_medio":          0.000823,
            "volatilidad_diaria":     0.012456,
            "volatilidad_anualizada": 0.197834
        }, ...]
    """
    retornos = calcular_retornos_log(precios)
    n = len(retornos)
    resultados = []

    for i in range(ventana - 1, n):
        # Extraer la ventana de retornos
        ventana_ret = retornos[i - ventana + 1 : i + 1]
        k = len(ventana_ret)

        # Calcular media de retornos
        media_r = sum(ventana_ret) / k

        # Calcular varianza muestral (corrección de Bessel: denominador k-1)
        if k > 1:
            varianza = sum((r - media_r) ** 2 for r in ventana_ret) / (k - 1)
        else:
            varianza = 0.0

        # Volatilidad diaria = desviación estándar de los retornos
        volatilidad_diaria = math.sqrt(varianza)

        # Volatilidad anualizada = volatilidad diaria × √252
        volatilidad_anualizada = volatilidad_diaria * math.sqrt(252)

        resultados.append({
            "indice":                 i + 1,   # +1 porque los retornos empiezan en el día 1
            "ventana_dias":           ventana,
            "retorno_medio":          round(media_r, 6),
            "volatilidad_diaria":     round(volatilidad_diaria, 6),
            "volatilidad_anualizada": round(volatilidad_anualizada, 6),
        })

    return resultados


# ------------------------------------------------------------------
# ALGORITMO 3: MÁXIMO DRAWDOWN
# ------------------------------------------------------------------

def calcular_max_drawdown(precios: list[float]) -> dict:
    """
    Calcula el Máximo Drawdown (MDD): la mayor caída desde un pico hasta un valle.

    CONCEPTO:
        El MDD mide la peor pérdida que habría sufrido un inversor que compró
        en el peor momento (el pico más alto) y vendió en el peor momento
        (el valle más bajo posterior a ese pico).

    FÓRMULA — Complejidad: O(n)
    ────────────────────────────
        MDD = (precio_valle - precio_pico) / precio_pico × 100

        El resultado es negativo (representa una pérdida).

    ALGORITMO (una sola pasada):
        1. Mantener el pico máximo visto hasta la posición actual
        2. Para cada precio, calcular el drawdown desde ese pico
        3. El MDD es el mínimo de todos los drawdowns

        pico_actual = precios[0]
        Para cada precio P:
            Si P > pico_actual: actualizar pico_actual = P
            drawdown = (P - pico_actual) / pico_actual
            Si drawdown < MDD: actualizar MDD = drawdown

    INTERPRETACIÓN:
        MDD = -20%: en algún momento el activo cayó un 20% desde su máximo
        MDD = -50%: el activo llegó a valer la mitad de su precio máximo
        MDD cercano a 0: el activo nunca cayó significativamente

    Args:
        precios: Lista de precios de cierre ordenados ASC

    Returns:
        {
            "mdd_pct":      -15.34,   ← porcentaje de caída (negativo)
            "precio_pico":  450.25,   ← precio en el punto más alto
            "precio_valle": 381.20    ← precio en el punto más bajo posterior
        }
    """
    if not precios:
        return {"mdd_pct": 0.0, "precio_pico": 0.0, "precio_valle": 0.0}

    pico_maximo  = precios[0]
    mdd          = 0.0
    precio_pico  = precios[0]
    precio_valle = precios[0]

    for precio in precios:
        # Actualizar el pico máximo si encontramos un nuevo máximo
        if precio > pico_maximo:
            pico_maximo = precio

        # Calcular el drawdown desde el pico actual
        drawdown = (precio - pico_maximo) / pico_maximo

        # Actualizar el MDD si este drawdown es peor (más negativo)
        if drawdown < mdd:
            mdd          = drawdown
            precio_pico  = pico_maximo
            precio_valle = precio

    return {
        "mdd_pct":      round(mdd * 100, 4),
        "precio_pico":  round(precio_pico, 4),
        "precio_valle": round(precio_valle, 4),
    }


# ------------------------------------------------------------------
# ALGORITMO 4: VALUE AT RISK (VaR) HISTÓRICO
# ------------------------------------------------------------------

def calcular_var_historico(
    precios: list[float],
    nivel_confianza: float = 0.95
) -> dict:
    """
    Calcula el Value at Risk (VaR) histórico con el método de simulación histórica.

    CONCEPTO:
        El VaR responde a la pregunta: "¿Cuál es la pérdida máxima que puedo
        esperar en un día normal, con un nivel de confianza del X%?"

        Con VaR al 95%: "Solo en el 5% de los días la pérdida superará este valor."

    MÉTODO HISTÓRICO — Complejidad: O(n log n)
    ────────────────────────────────────────────
        1. Calcular todos los retornos logarítmicos diarios
        2. Ordenar los retornos de menor a mayor (peores primero)
        3. VaR = retorno en el percentil (1 - nivel_confianza)

        Para nivel_confianza = 0.95:
            índice_VaR = int(0.05 × n)
            VaR = retornos_ordenados[índice_VaR]

    VENTAJA DEL MÉTODO HISTÓRICO:
        No asume ninguna distribución estadística (no asume normalidad).
        Usa directamente los retornos observados, capturando los eventos
        extremos reales del activo.

    COMPLEJIDAD:
        O(n log n) dominado por el ordenamiento de los retornos.
        El resto del algoritmo es O(n).

    Args:
        precios:          Lista de precios de cierre
        nivel_confianza:  0.95 para VaR al 95% (default)

    Returns:
        {
            "var_diario":      -0.0234,
            "var_pct":         -2.34,
            "nivel_confianza": 0.95,
            "interpretacion":  "Con 95% de confianza, la pérdida diaria no superará el 2.34%"
        }
    """
    retornos = calcular_retornos_log(precios)
    if not retornos:
        return {"var_diario": 0.0, "nivel_confianza": nivel_confianza}

    # Ordenar retornos ascendentemente (los peores retornos primero)
    # Nota: sorted() está permitido por el enunciado para operaciones de utilidad
    retornos_ordenados = sorted(retornos)

    # Calcular el índice del percentil (1 - nivel_confianza)
    # Para 95% de confianza: índice = int(0.05 × n) → percentil 5%
    indice_var = int((1 - nivel_confianza) * len(retornos_ordenados))
    var = retornos_ordenados[indice_var]

    return {
        "var_diario":      round(var, 6),
        "var_pct":         round(var * 100, 4),
        "nivel_confianza": nivel_confianza,
        "interpretacion":  (
            f"Con {nivel_confianza*100:.0f}% de confianza, "
            f"la pérdida diaria no superará el {abs(var*100):.2f}%"
        )
    }


# ------------------------------------------------------------------
# ALGORITMO 5: SHARPE RATIO
# ------------------------------------------------------------------

def calcular_sharpe(
    precios: list[float],
    tasa_libre_riesgo_anual: float = 0.05
) -> dict:
    """
    Calcula el Sharpe Ratio: medida de retorno ajustado por riesgo.

    CONCEPTO:
        El Sharpe Ratio responde a: "¿Cuánto retorno extra obtengo por cada
        unidad de riesgo que asumo, comparado con una inversión sin riesgo?"

        Un Sharpe alto indica que el activo ofrece buen retorno para su nivel
        de riesgo. Un Sharpe negativo indica que el activo rinde menos que
        la tasa libre de riesgo (ej: bonos del gobierno).

    FÓRMULA — Complejidad: O(n)
    ────────────────────────────
        Sharpe = (R_activo - R_libre) / σ_activo

        Donde:
            R_activo = retorno anualizado del activo
                     = media(retornos_diarios) × 252
            R_libre  = tasa libre de riesgo anual (default: 5%)
                     = tasa de los bonos del Tesoro de EE.UU. a 10 años
            σ_activo = volatilidad anualizada del activo
                     = std(retornos_diarios) × √252

    INTERPRETACIÓN:
        Sharpe > 2.0: excelente (raro en la práctica)
        Sharpe > 1.0: bueno
        Sharpe > 0.5: aceptable
        Sharpe < 0.0: el activo rinde menos que la tasa libre de riesgo

    TASA LIBRE DE RIESGO:
        Se usa 5% anual como aproximación de la tasa de los bonos del
        Tesoro de EE.UU. a 10 años. Esta es la tasa de referencia estándar
        en finanzas para el "activo sin riesgo".

    Args:
        precios:                  Lista de precios de cierre
        tasa_libre_riesgo_anual:  Tasa anual libre de riesgo (default: 5%)

    Returns:
        {
            "sharpe":                0.8234,
            "retorno_anual_pct":     12.45,
            "volatilidad_anual_pct": 18.23,
            "tasa_libre_riesgo_pct": 5.0
        }
    """
    retornos = calcular_retornos_log(precios)
    n = len(retornos)
    if n < 2:
        return {"sharpe": 0.0}

    # Retorno medio diario
    media_diaria = sum(retornos) / n

    # Retorno anualizado: media diaria × 252 días de negociación
    retorno_anual = media_diaria * 252

    # Desviación estándar muestral de los retornos diarios (corrección de Bessel)
    varianza   = sum((r - media_diaria) ** 2 for r in retornos) / (n - 1)
    std_diaria = math.sqrt(varianza)

    # Volatilidad anualizada: std diaria × √252
    std_anual = std_diaria * math.sqrt(252)

    if std_anual == 0:
        return {"sharpe": 0.0}   # Activo sin volatilidad (imposible en la práctica)

    # Sharpe Ratio: retorno excedente / volatilidad
    sharpe = (retorno_anual - tasa_libre_riesgo_anual) / std_anual

    return {
        "sharpe":                round(sharpe, 4),
        "retorno_anual_pct":     round(retorno_anual * 100, 4),
        "volatilidad_anual_pct": round(std_anual * 100, 4),
        "tasa_libre_riesgo_pct": round(tasa_libre_riesgo_anual * 100, 2),
    }


# ------------------------------------------------------------------
# FUNCIÓN PRINCIPAL: Resumen completo de riesgo para un activo
# ------------------------------------------------------------------

def resumen_riesgo(ticker: str, precios: list[float]) -> dict:
    """
    Genera el resumen completo de riesgo ejecutando todos los algoritmos.

    Args:
        ticker:  Símbolo del activo (ej: "SPY")
        precios: Lista de precios de cierre

    Returns:
        Dict con todas las métricas de riesgo calculadas
    """
    if len(precios) < 30:
        return {"error": f"Datos insuficientes para {ticker} (mínimo 30 días)"}

    ultima_vol   = calcular_volatilidad(precios, DIAS_VOLATILIDAD)
    vol_reciente = ultima_vol[-1] if ultima_vol else {}

    return {
        "ticker":               ticker,
        "dias_analizados":      len(precios),
        "volatilidad_reciente": vol_reciente,
        "max_drawdown":         calcular_max_drawdown(precios),
        "var_95":               calcular_var_historico(precios, 0.95),
        "var_99":               calcular_var_historico(precios, 0.99),
        "sharpe_ratio":         calcular_sharpe(precios),
    }
