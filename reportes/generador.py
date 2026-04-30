"""
reports/generator.py — Generador de Reporte Técnico Completo
Produce un resumen analítico de todos los algoritmos ejecutados.
Sin dependencias externas — solo stdlib.
"""

import json
from datetime import datetime
from config import ACTIVOS, TICKERS, VENTANA_DESLIZANTE_DIAS, DIAS_VOLATILIDAD
from etl.database import get_connection, obtener_precios, obtener_id_activo

# HELPERS DE CONSULTA

def _consultar(sql: str, params: tuple = ()) -> list[tuple]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()

# SECCIÓN 1: Resumen de la base de datos

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

# SECCIÓN 2: Top similitudes por algoritmo

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

# SECCIÓN 3: Activos más volátiles

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

# SECCIÓN 4: Resumen de riesgo individual

def _seccion_riesgo(max_activos: int = 5) -> dict:
    """VaR y Sharpe Ratio para los primeros N activos con datos."""
    from algoritmos.volatilidad import resumen_riesgo

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

# SECCIÓN 5: Patrones detectados por activo

def _seccion_patrones(max_activos: int = 5) -> dict:
    """Resumen de patrones detectados por ventana deslizante."""
    from algoritmos.patrones import detectar_patrones, detectar_picos_valles

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

# FUNCIÓN PRINCIPAL

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

def generar_reporte_html() -> str:
    """
    Genera el reporte técnico completo en HTML con formato para impresión/PDF.
    Incluye estilos inline para que funcione correctamente con window.print().
    """
    data = generar_reporte_json()
    meta = data["meta"]
    sec1 = data["seccion_1_datos"]
    sec2 = data["seccion_2_similitud"]
    sec3 = data["seccion_3_volatilidad"]
    sec4 = data["seccion_4_riesgo"]
    sec5 = data["seccion_5_patrones"]

    # ── Sección 1: cobertura ──────────────────────────────────
    filas_cob = "".join(
        f"<tr><td>{r['ticker']}</td><td>{r['total_dias']}</td>"
        f"<td>{r['fecha_inicio'] or '-'}</td><td>{r['fecha_fin'] or '-'}</td></tr>"
        for r in sec1.get("cobertura", [])
    )

    # ── Sección 2: similitud ──────────────────────────────────
    bloques_sim = ""
    for algo, info in sec2.items():
        filas = "".join(
            f"<tr><td>{p['ticker1']} ↔ {p['ticker2']}</td><td>{p['valor']:.6f}</td></tr>"
            for p in info.get("top_5", [])
        )
        bloques_sim += f"""
        <h3 style="margin:16px 0 8px;color:#0284c7;font-size:13px;text-transform:uppercase;letter-spacing:.5px">
            {algo.upper()} — {info['etiqueta']}
        </h3>
        <table><thead><tr><th>Par</th><th>Valor</th></tr></thead><tbody>{filas}</tbody></table>
        """

    # ── Sección 3: volatilidad ────────────────────────────────
    ranking = sec3.get("ranking", [])
    filas_vol = "".join(
        f"<tr><td>{i+1}</td><td>{r['ticker']}</td>"
        f"<td>{r['volatilidad_anual']*100:.2f}%</td>"
        f"<td>{'Conservador' if r['volatilidad_anual']<0.15 else 'Moderado' if r['volatilidad_anual']<0.30 else 'Agresivo'}</td></tr>"
        for i, r in enumerate(ranking)
    )

    # ── Sección 4: riesgo ─────────────────────────────────────
    filas_riesgo = ""
    for ticker, riesgo in sec4.items():
        var   = riesgo.get("var_95", {}).get("var_pct", "N/A")
        sharpe = riesgo.get("sharpe_ratio", {}).get("sharpe", "N/A")
        vol   = riesgo.get("volatilidad_reciente", {}).get("volatilidad_anualizada", "N/A")
        mdd   = riesgo.get("max_drawdown", {}).get("mdd_pct", "N/A")
        filas_riesgo += (
            f"<tr><td>{ticker}</td>"
            f"<td>{float(vol)*100:.2f}% anual" if isinstance(vol, (int, float)) else f"<td>{vol}"
            f"</td><td>{sharpe}</td><td>{var}%</td><td>{mdd}%</td></tr>"
        )

    # ── Sección 5: patrones ───────────────────────────────────
    filas_pat = ""
    for ticker, info in sec5.items():
        dist = ", ".join(f"{k}: {v}" for k, v in info.get("distribucion", {}).items()) or "—"
        filas_pat += (
            f"<tr><td>{ticker}</td><td>{info['patrones_detectados']}</td>"
            f"<td>{info['picos']}</td><td>{info['valles']}</td><td style='font-size:10px'>{dist}</td></tr>"
        )

    algos_html = "".join(f"<li>{a}</li>" for a in meta.get("algoritmos_usados", []))

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>BVC Analytics — Reporte Técnico</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Inter',sans-serif;font-size:12px;color:#0f172a;background:#fff;padding:32px 40px}}
  h1{{font-size:22px;font-weight:700;color:#0f172a;margin-bottom:4px}}
  h2{{font-size:15px;font-weight:700;color:#0284c7;margin:28px 0 10px;padding-bottom:6px;border-bottom:2px solid #e2e8f0}}
  h3{{font-size:12px;font-weight:600;color:#334155;margin:14px 0 6px}}
  .meta{{font-size:11px;color:#64748b;margin-bottom:24px}}
  .meta span{{margin-right:20px}}
  table{{width:100%;border-collapse:collapse;margin-bottom:12px;font-size:11px}}
  th{{background:#f1f5f9;text-align:left;padding:7px 10px;font-size:10px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:.5px;border-bottom:2px solid #e2e8f0}}
  td{{padding:7px 10px;border-bottom:1px solid #f1f5f9;color:#1e293b}}
  tr:last-child td{{border-bottom:none}}
  .badge{{display:inline-block;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:700}}
  .badge-g{{background:#d1fae5;color:#065f46}}
  .badge-y{{background:#fef3c7;color:#92400e}}
  .badge-r{{background:#fee2e2;color:#991b1b}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
  .stat-box{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px;margin-bottom:12px}}
  .stat-box .lbl{{font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.5px;font-weight:600}}
  .stat-box .val{{font-size:24px;font-weight:700;font-family:'JetBrains Mono',monospace;color:#0f172a;margin:4px 0 2px}}
  .stat-box .sub{{font-size:11px;color:#94a3b8}}
  .algo-list{{columns:2;gap:20px;list-style:none;padding:0}}
  .algo-list li{{padding:3px 0;font-size:11px;color:#334155}}
  .algo-list li::before{{content:"▸ ";color:#0284c7;font-weight:700}}
  .footer{{margin-top:32px;padding-top:16px;border-top:1px solid #e2e8f0;font-size:10px;color:#94a3b8;text-align:center}}
  @media print{{
    body{{padding:16px 20px}}
    h2{{page-break-before:auto}}
    table{{page-break-inside:avoid}}
  }}
</style>
</head>
<body>

<h1>📈 BVC Analytics — Reporte Técnico</h1>
<div class="meta">
  <span>🏛 Universidad del Quindío — Análisis de Algoritmos</span>
  <span>📅 Generado: {meta['generado_en'][:10]}</span>
  <span>⏱ Ventana deslizante: {meta['ventana_dias']} días</span>
  <span>📊 Ventana volatilidad: {meta['ventana_vol']} días</span>
</div>

<!-- SECCIÓN 1 -->
<h2>Sección 1 — Cobertura de Datos (ETL)</h2>
<div style="display:flex;gap:16px;margin-bottom:16px">
  <div class="stat-box" style="flex:1">
    <div class="lbl">Activos analizados</div>
    <div class="val">{sec1['activos_totales']}</div>
    <div class="sub">20 instrumentos financieros</div>
  </div>
  <div class="stat-box" style="flex:1">
    <div class="lbl">Total registros OHLCV</div>
    <div class="val">{sec1['filas_totales']:,}</div>
    <div class="sub">5 años de historia diaria</div>
  </div>
</div>
<table>
  <thead><tr><th>Ticker</th><th>Días en BD</th><th>Fecha inicio</th><th>Fecha fin</th></tr></thead>
  <tbody>{filas_cob}</tbody>
</table>

<!-- SECCIÓN 2 -->
<h2>Sección 2 — Similitud de Series de Tiempo</h2>
<p style="font-size:11px;color:#64748b;margin-bottom:12px">
  190 pares calculados — C(20,2). Series alineadas por fecha exacta (intersección de calendarios bursátiles).
</p>
{bloques_sim}

<!-- SECCIÓN 3 -->
<h2>Sección 3 — Ranking de Volatilidad Anualizada</h2>
<p style="font-size:11px;color:#64748b;margin-bottom:12px">
  Clasificación: Conservador σ &lt; 15% | Moderado 15% ≤ σ &lt; 30% | Agresivo σ ≥ 30%
</p>
<table>
  <thead><tr><th>#</th><th>Ticker</th><th>Volatilidad Anual (σ)</th><th>Categoría</th></tr></thead>
  <tbody>{filas_vol}</tbody>
</table>

<!-- SECCIÓN 4 -->
<h2>Sección 4 — Métricas de Riesgo Individual</h2>
<table>
  <thead><tr><th>Ticker</th><th>Volatilidad</th><th>Sharpe Ratio</th><th>VaR 95%</th><th>Max Drawdown</th></tr></thead>
  <tbody>{filas_riesgo}</tbody>
</table>

<!-- SECCIÓN 5 -->
<h2>Sección 5 — Patrones Detectados (Ventana Deslizante)</h2>
<table>
  <thead><tr><th>Ticker</th><th>Patrones</th><th>Picos</th><th>Valles</th><th>Distribución</th></tr></thead>
  <tbody>{filas_pat}</tbody>
</table>

<!-- ALGORITMOS -->
<h2>Algoritmos Implementados</h2>
<ul class="algo-list">{algos_html}</ul>

<div class="footer">
  BVC Analytics — Universidad del Quindío — Análisis de Algoritmos 2025 |
  Implementado en Python 3.11 stdlib pura — sin pandas, numpy, scipy, sklearn
</div>

</body>
</html>"""
