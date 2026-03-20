"""
algorithms/volatility.py — Cálculo de Riesgo y Volatilidad Financiera
Implementado DESDE CERO — SIN numpy, SIN scipy

Métricas implementadas:
  1. Retornos Logarítmicos            O(n)
  2. Volatilidad Histórica (std dev)  O(n)
  3. Volatilidad Anualizada           O(1)
  4. Sharpe Ratio simplificado        O(n)
  5. Máximo Drawdown                  O(n)
  6. Value at Risk (VaR) Histórico    O(n log n)
"""

import math
from config import DIAS_VOLATILIDAD


# ======================================================= #
# ⚠️ ALGORITMO: Retornos Logarítmicos                     #
# ✏️ ZONA DE LÓGICA MODIFICABLE                           #
# Complejidad Esperada: O(n)                               #
# ======================================================= #
def calcular_retornos_log(precios: list[float]) -> list[float]:
    """
    Calcula los retornos logarítmicos diarios.

    Fórmula:
        r_i = ln(P_i / P_{i-1})

    Ventaja sobre retornos simples: los retornos log son aditivos
    en el tiempo y tienen una distribución más cercana a la normal.

    Returns:
        Lista de n-1 retornos (el primero se pierde al dividir)
    """
    retornos = []
    for i in range(1, len(precios)):
        if precios[i - 1] <= 0 or precios[i] <= 0:
            retornos.append(0.0)
        else:
            retornos.append(math.log(precios[i] / precios[i - 1]))
    return retornos
# ======================================================= #


# ======================================================= #
# ⚠️ ALGORITMO: Volatilidad Histórica                     #
# ✏️ ZONA DE LÓGICA MODIFICABLE                           #
# Complejidad Esperada: O(n)                               #
# ======================================================= #
def calcular_volatilidad(
    precios: list[float],
    ventana: int = DIAS_VOLATILIDAD
) -> list[dict]:
    """
    Calcula la volatilidad histórica rodante en ventanas de `ventana` días.

    Pasos:
      1. Calcular retornos logarítmicos: r_i = ln(P_i / P_{i-1})
      2. Para cada ventana de k retornos:
         a. Media de retornos: r̄ = Σr / k
         b. Varianza muestral: s² = Σ(r_i - r̄)² / (k-1)
         c. Desviación estándar (volatilidad diaria): σ = √s²
         d. Volatilidad anualizada: σ_anual = σ × √252

    Args:
        precios: Lista de precios de cierre ordenados ASC
        ventana: Número de días para cada cálculo

    Returns:
        Lista de dicts con volatilidad por período
    """
    retornos = calcular_retornos_log(precios)
    n = len(retornos)
    resultados = []

    for i in range(ventana - 1, n):
        ventana_ret = retornos[i - ventana + 1: i + 1]
        k = len(ventana_ret)

        # Media de retornos
        media_r = sum(ventana_ret) / k

        # Varianza muestral (denominador k-1 para corrección de Bessel)
        if k > 1:
            varianza = sum((r - media_r) ** 2 for r in ventana_ret) / (k - 1)
        else:
            varianza = 0.0

        volatilidad_diaria   = math.sqrt(varianza)
        volatilidad_anualizada = volatilidad_diaria * math.sqrt(252)

        resultados.append({
            "indice":                i + 1,         # +1 por el retorno que se perdió
            "ventana_dias":          ventana,
            "retorno_medio":         round(media_r, 6),
            "volatilidad_diaria":    round(volatilidad_diaria, 6),
            "volatilidad_anualizada": round(volatilidad_anualizada, 6),
        })

    return resultados
# ======================================================= #


# ======================================================= #
# ⚠️ ALGORITMO: Máximo Drawdown                           #
# ✏️ ZONA DE LÓGICA MODIFICABLE                           #
# Complejidad Esperada: O(n)                               #
# ======================================================= #
def calcular_max_drawdown(precios: list[float]) -> dict:
    """
    Calcula el Máximo Drawdown (MDD): la mayor caída desde un pico
    hasta un valle posterior, expresada como porcentaje.

    Fórmula:
        MDD = (valle_mínimo - pico_máximo) / pico_máximo × 100

    Algoritmo:
        1. Iterar la serie manteniendo el pico máximo visto hasta i
        2. Para cada posición, calcular drawdown_i = (precio_i - pico) / pico
        3. MDD = min(todos los drawdowns)

    Complejidad: O(n)

    Returns:
        {"mdd_pct": -15.3, "precio_pico": 450.0, "precio_valle": 380.0}
    """
    if not precios:
        return {"mdd_pct": 0.0, "precio_pico": 0.0, "precio_valle": 0.0}

    pico_maximo  = precios[0]
    mdd          = 0.0
    precio_pico  = precios[0]
    precio_valle = precios[0]

    for precio in precios:
        if precio > pico_maximo:
            pico_maximo = precio

        drawdown = (precio - pico_maximo) / pico_maximo

        if drawdown < mdd:
            mdd          = drawdown
            precio_pico  = pico_maximo
            precio_valle = precio

    return {
        "mdd_pct":      round(mdd * 100, 4),
        "precio_pico":  round(precio_pico, 4),
        "precio_valle": round(precio_valle, 4),
    }
# ======================================================= #


# ======================================================= #
# ⚠️ ALGORITMO: Value at Risk (VaR) Histórico             #
# ✏️ ZONA DE LÓGICA MODIFICABLE                           #
# Complejidad Esperada: O(n log n) por el ordenamiento     #
# ======================================================= #
def calcular_var_historico(
    precios: list[float],
    nivel_confianza: float = 0.95
) -> dict:
    """
    Calcula el Value at Risk (VaR) histórico.

    Definición: La pérdida máxima esperada con un nivel de confianza
    del X% en un horizonte de 1 día.

    Método histórico:
      1. Calcular todos los retornos logarítmicos diarios
      2. Ordenar los retornos ascendentemente (peores primero)
      3. VaR = retorno en el percentil (1 - nivel_confianza)

    Ejemplo con 95% confianza:
        VaR_0.95 = percentil 5 de los retornos
        → "Solo en el 5% de los días la pérdida supera este valor"

    Complejidad: O(n log n) dominado por el ordenamiento

    Args:
        nivel_confianza: 0.95 para VaR al 95%

    Returns:
        {"var_diario": -0.0234, "nivel_confianza": 0.95,
         "interpretacion": "Pérdida máxima esperada con 95% confianza: -2.34%"}
    """
    retornos = calcular_retornos_log(precios)
    if not retornos:
        return {"var_diario": 0.0, "nivel_confianza": nivel_confianza}

    # Ordenar ascendente (los peores retornos primero)
    retornos_ordenados = sorted(retornos)

    # Índice del percentil (1 - confianza)
    indice_var = int((1 - nivel_confianza) * len(retornos_ordenados))
    var = retornos_ordenados[indice_var]

    return {
        "var_diario":       round(var, 6),
        "var_pct":          round(var * 100, 4),
        "nivel_confianza":  nivel_confianza,
        "interpretacion":   (
            f"Con {nivel_confianza*100:.0f}% de confianza, "
            f"la pérdida diaria no superará el {abs(var*100):.2f}%"
        )
    }
# ======================================================= #


# ======================================================= #
# ⚠️ ALGORITMO: Sharpe Ratio Simplificado                 #
# ✏️ ZONA DE LÓGICA MODIFICABLE                           #
# Complejidad Esperada: O(n)                               #
# ======================================================= #
def calcular_sharpe(
    precios: list[float],
    tasa_libre_riesgo_anual: float = 0.05
) -> dict:
    """
    Calcula el Sharpe Ratio: relación entre retorno excedente y riesgo.

    Fórmula:
        Sharpe = (R_portfolio - R_libre_riesgo) / σ_portfolio

    Donde:
        R_portfolio     = media de retornos logarítmicos diarios × 252
        R_libre_riesgo  = tasa anual convertida a diaria (÷ 252)
        σ_portfolio     = volatilidad anualizada

    Interpretación:
        Sharpe > 1  → buena relación riesgo/retorno
        Sharpe > 2  → muy buena
        Sharpe < 0  → el activo rinde menos que la tasa libre de riesgo

    Complejidad: O(n)
    """
    retornos = calcular_retornos_log(precios)
    n = len(retornos)
    if n < 2:
        return {"sharpe": 0.0}

    # Retorno medio diario y anualizado
    media_diaria    = sum(retornos) / n
    retorno_anual   = media_diaria * 252

    # Desviación estándar muestral de retornos
    varianza = sum((r - media_diaria) ** 2 for r in retornos) / (n - 1)
    std_diaria = math.sqrt(varianza)
    std_anual  = std_diaria * math.sqrt(252)

    # Tasa libre de riesgo diaria
    rf_diaria = tasa_libre_riesgo_anual / 252

    if std_anual == 0:
        return {"sharpe": 0.0}

    sharpe = (retorno_anual - tasa_libre_riesgo_anual) / std_anual

    return {
        "sharpe":               round(sharpe, 4),
        "retorno_anual_pct":    round(retorno_anual * 100, 4),
        "volatilidad_anual_pct": round(std_anual * 100, 4),
        "tasa_libre_riesgo_pct": round(tasa_libre_riesgo_anual * 100, 2),
    }
# ======================================================= #


# ------------------------------------------------------------------
# FUNCIÓN PRINCIPAL: Resumen de riesgo para un activo
# ------------------------------------------------------------------

def resumen_riesgo(ticker: str, precios: list[float]) -> dict:
    """
    Genera el resumen completo de riesgo para un activo.
    Ejecuta todos los algoritmos de volatilidad y riesgo.
    """
    if len(precios) < 30:
        return {"error": f"Datos insuficientes para {ticker} (mínimo 30 días)"}

    ultima_vol = calcular_volatilidad(precios, DIAS_VOLATILIDAD)
    vol_reciente = ultima_vol[-1] if ultima_vol else {}

    return {
        "ticker":                ticker,
        "dias_analizados":       len(precios),
        "volatilidad_reciente":  vol_reciente,
        "max_drawdown":          calcular_max_drawdown(precios),
        "var_95":                calcular_var_historico(precios, 0.95),
        "var_99":                calcular_var_historico(precios, 0.99),
        "sharpe_ratio":          calcular_sharpe(precios),
    }
