"""
reports/generator.py — Generador de Reporte Técnico Completo
Produce un resumen analítico de todos los algoritmos ejecutados.
Sin dependencias externas — solo stdlib.
"""

import json
from datetime import datetime
from config import ACTIVOS, TICKERS, VENTANA_DESLIZANTE_DIAS, DIAS_VOLATILIDAD
from etl.database import get_connection, obtener_precios, obtener_id_activo


# ------------------------------------------------------------------
# HELPERS DE CONSULTA
# ------------------------------------------------------------------

def _consultar(sql: str, params: tuple = ()) -> list[tuple]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


# ------------------------------------------------------------------
# SECCIÓN 1: Resumen de la base de datos
# ------------------------------------------------------------------

def _seccion_datos() -> dict:
    """Cuántos registros hay en la BD por activo."""
    filas = _consultar("""
        SELECT a.ticker, COUNT(p.id) AS total_dias,
               MIN(p.fecha) AS fecha_inicio, MAX(p.fecha) AS fecha_fin
        FROM activos a
        LEFT JOIN precios p ON p.activo_id = a.id
        GROUP BY a.ticker
        ORDER BY a.ticker;
    """)
    registros = [
        {
            "ticker":       f[0],
            "total_dias":   f[1],
            "fecha_inicio": str(f[2]) if f[2] else None,
            "fecha_fin":    str(f[3]) if f[3] else None,
        }
        for f in filas
    ]
    total_filas = sum(r["total_dias"] for r in registros)
    return {
        "activos_totales":  len(registros),
        "filas_totales":    total_filas,
        "cobertura":        registros,
    }


# ------------------------------------------------------------------
# SECCIÓN 2: Top similitudes por algoritmo
# ------------------------------------------------------------------

def _seccion_similitud() -> dict:
    """Top 5 pares más similares para cada algoritmo."""
    algoritmos = {
        "pearson":   {"orden": "DESC", "etiqueta": "Mayor correlación"},
        "coseno":    {"orden": "DESC", "etiqueta": "Mayor similitud vectorial"},
        "euclidiana":{"orden": "ASC",  "etiqueta": "Menor distancia"},
        "dtw":       {"orden": "ASC",  "etiqueta": "Menor distancia temporal"},
    }
    resultado = {}
    for algo, cfg in algoritmos.items():
        filas = _consultar(f"""
            SELECT a1.ticker, a2.ticker, r.valor
            FROM resultados_similitud r
            JOIN activos a1 ON a1.id = r.activo1_id
            JOIN activos a2 ON a2.id = r.activo2_id
            WHERE r.algoritmo = %s
            ORDER BY r.valor {cfg["orden"]}
            LIMIT 5;
        """, (algo,))
        resultado[algo] = {
            "etiqueta": cfg["etiqueta"],
            "top_5": [
                {"ticker1": f[0], "ticker2": f[1], "valor": float(f[2])}
                for f in filas
            ]
        }
    return resultado


# ------------------------------------------------------------------
# SECCIÓN 3: Activos más volátiles
# ------------------------------------------------------------------

def _seccion_volatilidad() -> dict:
    """Ranking de activos por volatilidad anualizada reciente."""
    filas = _consultar("""
        SELECT DISTINCT ON (a.ticker)
               a.ticker, rv.volatilidad, rv.retorno_medio, rv.fecha
        FROM resultados_volatilidad rv
        JOIN activos a ON a.id = rv.activo_id
        ORDER BY a.ticker, rv.fecha DESC;
    """)
    if not filas:
        return {"ranking": [], "nota": "Ejecutar pipeline de volatilidad primero."}

    ranking = sorted(
        [{"ticker": f[0], "volatilidad_anual": float(f[1]),
          "retorno_medio": float(f[2]), "fecha": str(f[3])} for f in filas],
        key=lambda x: x["volatilidad_anual"],
        reverse=True
    )
    return {
        "mas_volátil":   ranking[0]["ticker"] if ranking else None,
        "menos_volátil": ranking[-1]["ticker"] if ranking else None,
        "ranking":       ranking,
    }


# ------------------------------------------------------------------
# SECCIÓN 4: Resumen de riesgo individual
# ------------------------------------------------------------------

def _seccion_riesgo(max_activos: int = 5) -> dict:
    """VaR y Sharpe Ratio para los primeros N activos con datos."""
    from algorithms.volatility import resumen_riesgo

    resultados = {}
    conteo = 0
    for ticker in TICKERS:
        if conteo >= max_activos:
            break
        filas = obtener_precios(ticker, "cierre")
        if not filas:
            continue
        precios = [float(f["cierre"]) for f in filas]
        resultados[ticker] = resumen_riesgo(ticker, precios)
        conteo += 1

    return resultados


# ------------------------------------------------------------------
# SECCIÓN 5: Patrones detectados por activo
# ------------------------------------------------------------------

def _seccion_patrones(max_activos: int = 5) -> dict:
    """Resumen de patrones detectados por ventana deslizante."""
    from algorithms.patterns import detectar_patrones, detectar_picos_valles

    resultados = {}
    conteo = 0
    for ticker in TICKERS:
        if conteo >= max_activos:
            break
        filas = obtener_precios(ticker, "cierre")
        if not filas:
            continue
        fechas  = [str(f["fecha"])    for f in filas]
        precios = [float(f["cierre"]) for f in filas]

        patrones = detectar_patrones(fechas, precios, VENTANA_DESLIZANTE_DIAS)
        picos_valles = detectar_picos_valles(fechas, precios)

        conteo_patrones: dict[str, int] = {}
        for p in patrones:
            conteo_patrones[p["patron"]] = conteo_patrones.get(p["patron"], 0) + 1

        resultados[ticker] = {
            "patrones_detectados":  len(patrones),
            "distribucion":         conteo_patrones,
            "picos":                len(picos_valles["picos"]),
            "valles":               len(picos_valles["valles"]),
            "muestra_reciente":     patrones[-3:] if patrones else [],
        }
        conteo += 1

    return resultados


# ------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ------------------------------------------------------------------

def generar_reporte_json() -> dict:
    """
    Genera el reporte técnico completo en formato JSON.
    Agrega resultados de todos los módulos del sistema.
    """
    generado_en = datetime.utcnow().isoformat() + "Z"

    reporte = {
        "meta": {
            "titulo":          "BVC Analytics — Reporte Técnico de Análisis",
            "generado_en":     generado_en,
            "ventana_dias":    VENTANA_DESLIZANTE_DIAS,
            "ventana_vol":     DIAS_VOLATILIDAD,
            "algoritmos_usados": [
                "Interpolación Lineal O(n)",
                "Z-Score Outliers O(n)",
                "Distancia Euclidiana O(n)",
                "Correlación de Pearson O(n)",
                "Similitud Coseno O(n)",
                "DTW Programación Dinámica O(n²)",
                "Ventana Deslizante O(n·k)",
                "Detección Picos/Valles O(n)",
                "Media Móvil Simple O(n·k)",
                "Golden/Death Cross O(n)",
                "Volatilidad Histórica O(n)",
                "Máximo Drawdown O(n)",
                "VaR Histórico O(n log n)",
                "Sharpe Ratio O(n)",
            ],
        },
        "seccion_1_datos":       _seccion_datos(),
        "seccion_2_similitud":   _seccion_similitud(),
        "seccion_3_volatilidad": _seccion_volatilidad(),
        "seccion_4_riesgo":      _seccion_riesgo(max_activos=5),
        "seccion_5_patrones":    _seccion_patrones(max_activos=5),
    }

    return reporte


def generar_reporte_txt() -> str:
    """Versión legible del reporte para exportar como .txt."""
    data = generar_reporte_json()
    lineas = [
        "=" * 70,
        "  BVC ANALYTICS — REPORTE TÉCNICO",
        f"  Generado: {data['meta']['generado_en']}",
        "=" * 70,
        "",
        "▶ SECCIÓN 1 — COBERTURA DE DATOS",
        f"  Activos analizados: {data['seccion_1_datos']['activos_totales']}",
        f"  Total de filas en BD: {data['seccion_1_datos']['filas_totales']:,}",
        "",
        "▶ SECCIÓN 2 — TOP 5 PARES MÁS SIMILARES (Pearson)",
    ]
    for par in data["seccion_2_similitud"].get("pearson", {}).get("top_5", []):
        lineas.append(f"  {par['ticker1']} ↔ {par['ticker2']}: r = {par['valor']:.4f}")

    lineas += [
        "",
        "▶ SECCIÓN 3 — RANKING DE VOLATILIDAD ANUALIZADA",
    ]
    for r in data["seccion_3_volatilidad"].get("ranking", [])[:5]:
        lineas.append(f"  {r['ticker']}: σ = {r['volatilidad_anual']*100:.2f}%")

    lineas += [
        "",
        "▶ SECCIÓN 4 — RIESGO (VaR 95%)",
    ]
    for ticker, riesgo in data["seccion_4_riesgo"].items():
        var = riesgo.get("var_95", {}).get("var_pct", "N/A")
        sharpe = riesgo.get("sharpe_ratio", {}).get("sharpe", "N/A")
        lineas.append(f"  {ticker}: VaR(95%) = {var}%  |  Sharpe = {sharpe}")

    lineas += ["", "=" * 70, "  FIN DEL REPORTE", "=" * 70]
    return "\n".join(lineas)
