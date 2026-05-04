"""
reportes/generador.py — Generador de Reporte Tecnico con Graficos SVG
Universidad del Quindio — Analisis de Algoritmos 2026-1
Sin dependencias externas — solo stdlib. Graficos generados como SVG inline.
"""

import math
from datetime import datetime
from config import TICKERS, VENTANA_DESLIZANTE_DIAS, DIAS_VOLATILIDAD
from etl.database import get_connection, obtener_precios


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _consultar(sql: str, params: tuple = ()) -> list[tuple]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def _categoria(vol: float) -> str:
    if vol < 0.15:
        return "Conservador"
    if vol < 0.30:
        return "Moderado"
    return "Agresivo"


def _cat_color(cat: str) -> str:
    return {"Conservador": "#059669", "Moderado": "#d97706", "Agresivo": "#dc2626"}.get(cat, "#64748b")


def _cat_badge(cat: str) -> str:
    cls = {"Conservador": "badge-c", "Moderado": "badge-m", "Agresivo": "badge-a"}.get(cat, "")
    return f"<span class='badge {cls}'>{cat}</span>"


# ─── SECCIONES DE DATOS ───────────────────────────────────────────────────────

def _seccion_datos() -> dict:
    filas = _consultar("""
        SELECT a.ticker, COUNT(p.id), MIN(p.fecha), MAX(p.fecha)
        FROM activos a
        LEFT JOIN precios p ON p.activo_id = a.id
        GROUP BY a.ticker ORDER BY a.ticker;
    """)
    registros = [{"ticker": f[0], "total_dias": f[1],
                  "fecha_inicio": str(f[2]) if f[2] else None,
                  "fecha_fin": str(f[3]) if f[3] else None} for f in filas]
    return {"activos_totales": len(registros),
            "filas_totales": sum(r["total_dias"] for r in registros),
            "cobertura": registros}


def _seccion_similitud() -> dict:
    algoritmos = {
        "pearson":    {"orden": "DESC", "etiqueta": "Correlacion de Pearson"},
        "coseno":     {"orden": "DESC", "etiqueta": "Similitud por Coseno"},
        "euclidiana": {"orden": "ASC",  "etiqueta": "Distancia Euclidiana"},
        "dtw":        {"orden": "ASC",  "etiqueta": "Dynamic Time Warping"},
    }
    resultado = {}
    for algo, cfg in algoritmos.items():
        filas = _consultar(
            f"SELECT a1.ticker, a2.ticker, r.valor "
            f"FROM resultados_similitud r "
            f"JOIN activos a1 ON a1.id = r.activo1_id "
            f"JOIN activos a2 ON a2.id = r.activo2_id "
            f"WHERE r.algoritmo = %s ORDER BY r.valor {cfg['orden']} LIMIT 5;",
            (algo,))
        resultado[algo] = {"etiqueta": cfg["etiqueta"],
                           "top_5": [{"ticker1": f[0], "ticker2": f[1], "valor": float(f[2])} for f in filas]}
    # Matriz completa Pearson para heatmap
    tickers_bd = [r[0] for r in _consultar("SELECT ticker FROM activos ORDER BY ticker;")]
    n = len(tickers_bd)
    idx = {t: i for i, t in enumerate(tickers_bd)}
    mat = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    pares = _consultar(
        "SELECT a1.ticker, a2.ticker, r.valor "
        "FROM resultados_similitud r "
        "JOIN activos a1 ON a1.id = r.activo1_id "
        "JOIN activos a2 ON a2.id = r.activo2_id "
        "WHERE r.algoritmo = 'pearson';")
    for t1, t2, v in pares:
        if t1 in idx and t2 in idx:
            mat[idx[t1]][idx[t2]] = float(v)
            mat[idx[t2]][idx[t1]] = float(v)
    resultado["_matriz"] = {"tickers": tickers_bd, "valores": mat}
    return resultado


def _seccion_volatilidad() -> dict:
    filas = _consultar("""
        SELECT DISTINCT ON (a.ticker) a.ticker, rv.volatilidad, rv.retorno_medio, rv.fecha
        FROM resultados_volatilidad rv
        JOIN activos a ON a.id = rv.activo_id
        ORDER BY a.ticker, rv.fecha DESC;
    """)
    if not filas:
        return {"ranking": []}
    ranking = sorted(
        [{"ticker": f[0], "volatilidad_anual": float(f[1]),
          "retorno_medio": float(f[2]), "fecha": str(f[3])} for f in filas],
        key=lambda x: x["volatilidad_anual"], reverse=True)
    return {"ranking": ranking}


def _seccion_riesgo() -> dict:
    from algoritmos.volatilidad import resumen_riesgo
    resultados = {}
    for ticker in TICKERS:
        filas = obtener_precios(ticker, "cierre")
        if not filas:
            continue
        resultados[ticker] = resumen_riesgo(ticker, [float(f["cierre"]) for f in filas])
    return resultados


def _seccion_patrones() -> dict:
    from algoritmos.patrones import detectar_patrones, detectar_picos_valles
    resultados = {}
    for ticker in TICKERS:
        filas = obtener_precios(ticker, "cierre")
        if not filas:
            continue
        fechas  = [str(f["fecha"]) for f in filas]
        precios = [float(f["cierre"]) for f in filas]
        patrones = detectar_patrones(fechas, precios, VENTANA_DESLIZANTE_DIAS)
        pv = detectar_picos_valles(fechas, precios)
        conteo: dict[str, int] = {}
        for p in patrones:
            conteo[p["patron"]] = conteo.get(p["patron"], 0) + 1
        resultados[ticker] = {"patrones_detectados": len(patrones),
                              "distribucion": conteo,
                              "picos": len(pv["picos"]),
                              "valles": len(pv["valles"])}
    return resultados


def _seccion_sorting() -> list:
    filas = _consultar("SELECT algoritmo, complejidad, tamanio, tiempo_ms FROM resultados_sorting ORDER BY tiempo_ms ASC;")
    return [{"algoritmo": f[0], "complejidad": f[1], "tamanio": f[2], "tiempo_ms": float(f[3])} for f in filas]


# ─── GENERADORES DE GRAFICOS SVG ──────────────────────────────────────────────

def _svg_barras_volatilidad(ranking: list) -> str:
    """Barras horizontales de volatilidad anualizada para todos los activos."""
    if not ranking:
        return "<p style='color:#94a3b8;font-size:11px'>Sin datos de volatilidad.</p>"
    W, PL, PR, PT, PB = 680, 72, 80, 16, 28
    bar_h, gap = 14, 3
    H = PT + len(ranking) * (bar_h + gap) + PB
    max_v = max(r["volatilidad_anual"] for r in ranking)
    xs = W - PL - PR
    bars = []
    for i, r in enumerate(ranking):
        y = PT + i * (bar_h + gap)
        bw = max((r["volatilidad_anual"] / max_v) * xs, 3)
        cat = _categoria(r["volatilidad_anual"])
        col = _cat_color(cat)
        pct = r["volatilidad_anual"] * 100
        ret = r["retorno_medio"] * 252 * 100
        ret_col = "#059669" if ret >= 0 else "#dc2626"
        bars.append(
            f'<text x="{PL-5}" y="{y+bar_h/2+4:.1f}" text-anchor="end" '
            f'font-size="10" fill="#1e293b" font-family="Inter,sans-serif" font-weight="600">{r["ticker"]}</text>'
            f'<rect x="{PL}" y="{y}" width="{bw:.1f}" height="{bar_h}" fill="{col}" rx="3" opacity="0.85"/>'
            f'<text x="{PL+bw+5:.1f}" y="{y+bar_h/2+4:.1f}" font-size="9.5" fill="#475569" '
            f'font-family="monospace">{pct:.1f}%</text>'
            f'<text x="{W-PR+4}" y="{y+bar_h/2+4:.1f}" font-size="9" fill="{ret_col}" '
            f'font-family="monospace">{"+" if ret>=0 else ""}{ret:.1f}%</text>'
        )
    # Líneas de referencia 15% y 30%
    refs = []
    for threshold, label in [(0.15, "15%"), (0.30, "30%")]:
        xr = PL + (threshold / max_v) * xs
        refs.append(
            f'<line x1="{xr:.1f}" y1="{PT}" x2="{xr:.1f}" y2="{H-PB}" '
            f'stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4,3"/>'
            f'<text x="{xr:.1f}" y="{PT-2}" text-anchor="middle" font-size="8" fill="#94a3b8" '
            f'font-family="Inter,sans-serif">{label}</text>'
        )
    legend = (
        f'<circle cx="{PL}" cy="{H-2}" r="4" fill="#059669"/>'
        f'<text x="{PL+8}" y="{H+2}" font-size="9" fill="#475569" font-family="Inter,sans-serif">Conservador</text>'
        f'<circle cx="{PL+90}" cy="{H-2}" r="4" fill="#d97706"/>'
        f'<text x="{PL+98}" y="{H+2}" font-size="9" fill="#475569" font-family="Inter,sans-serif">Moderado</text>'
        f'<circle cx="{PL+170}" cy="{H-2}" r="4" fill="#dc2626"/>'
        f'<text x="{PL+178}" y="{H+2}" font-size="9" fill="#475569" font-family="Inter,sans-serif">Agresivo</text>'
        f'<text x="{W-PR+4}" y="{H+2}" font-size="9" fill="#94a3b8" font-family="Inter,sans-serif">Retorno est.</text>'
    )
    return (f'<svg viewBox="0 0 {W} {H+14}" style="width:100%;height:{H+14}px;display:block">'
            + "".join(refs) + "".join(bars) + legend + "</svg>")


def _svg_scatter_sharpe_vol(sec4: dict) -> str:
    """Scatter plot Sharpe Ratio vs Volatilidad anualizada."""
    puntos = []
    for ticker, riesgo in sec4.items():
        if "error" in riesgo:
            continue
        vol    = riesgo.get("volatilidad_reciente", {}).get("volatilidad_anualizada")
        sharpe = riesgo.get("sharpe_ratio", {}).get("sharpe")
        if vol is None or sharpe is None:
            continue
        puntos.append({"ticker": ticker, "vol": vol, "sharpe": sharpe,
                       "cat": _categoria(vol)})
    if not puntos:
        return "<p style='color:#94a3b8;font-size:11px'>Sin datos de riesgo.</p>"

    W, PL, PR, PT, PB = 680, 52, 20, 20, 36
    xs, ys = W - PL - PR, 200 - PT - PB

    vols    = [p["vol"] for p in puntos]
    sharpes = [p["sharpe"] for p in puntos]
    min_v, max_v = min(vols), max(vols)
    min_s, max_s = min(sharpes) - 0.1, max(sharpes) + 0.1
    rng_v = max_v - min_v or 0.01
    rng_s = max_s - min_s or 0.01

    def px(v): return PL + (v - min_v) / rng_v * xs
    def py(s): return PT + (1 - (s - min_s) / rng_s) * ys

    # Grid
    grid = []
    for i in range(5):
        yg = PT + i / 4 * ys
        sv = min_s + (1 - i / 4) * rng_s
        grid.append(
            f'<line x1="{PL}" y1="{yg:.1f}" x2="{W-PR}" y2="{yg:.1f}" stroke="#f1f5f9" stroke-width="1"/>'
            f'<text x="{PL-4}" y="{yg+3:.1f}" text-anchor="end" font-size="8" fill="#94a3b8" '
            f'font-family="monospace">{sv:.2f}</text>'
        )
    for i in range(5):
        xg = PL + i / 4 * xs
        vv = min_v + i / 4 * rng_v
        grid.append(
            f'<line x1="{xg:.1f}" y1="{PT}" x2="{xg:.1f}" y2="{PT+ys}" stroke="#f1f5f9" stroke-width="1"/>'
            f'<text x="{xg:.1f}" y="{PT+ys+12}" text-anchor="middle" font-size="8" fill="#94a3b8" '
            f'font-family="monospace">{vv*100:.0f}%</text>'
        )
    # Línea Sharpe=0
    y0 = py(0)
    if PT <= y0 <= PT + ys:
        grid.append(
            f'<line x1="{PL}" y1="{y0:.1f}" x2="{W-PR}" y2="{y0:.1f}" '
            f'stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4,3"/>'
            f'<text x="{PL-4}" y="{y0+3:.1f}" text-anchor="end" font-size="8" fill="#94a3b8" '
            f'font-family="Inter,sans-serif">0</text>'
        )

    dots = []
    for p in puntos:
        cx, cy = px(p["vol"]), py(p["sharpe"])
        col = _cat_color(p["cat"])
        dots.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="{col}" opacity="0.85" stroke="#fff" stroke-width="1.5"/>'
            f'<text x="{cx+7:.1f}" y="{cy+3:.1f}" font-size="8.5" fill="#334155" '
            f'font-family="Inter,sans-serif" font-weight="600">{p["ticker"]}</text>'
        )

    axes = (
        f'<text x="{PL + xs/2:.1f}" y="{PT+ys+28}" text-anchor="middle" font-size="9" fill="#64748b" '
        f'font-family="Inter,sans-serif">Volatilidad anualizada (%)</text>'
        f'<text x="10" y="{PT + ys/2:.1f}" text-anchor="middle" font-size="9" fill="#64748b" '
        f'font-family="Inter,sans-serif" transform="rotate(-90,10,{PT+ys/2:.1f})">Sharpe Ratio</text>'
    )
    return (f'<svg viewBox="0 0 {W} {PT+ys+40}" style="width:100%;height:{PT+ys+40}px;display:block">'
            + "".join(grid) + "".join(dots) + axes + "</svg>")


def _svg_barras_patrones(sec5: dict) -> str:
    """Barras apiladas: patrones significativos vs neutros por activo."""
    items = [(t, d) for t, d in sec5.items() if d.get("patrones_detectados", 0) > 0]
    if not items:
        return "<p style='color:#94a3b8;font-size:11px'>Sin datos de patrones.</p>"
    W, PL, PR, PT, PB = 680, 72, 20, 10, 36
    bar_h, gap = 12, 3
    H = PT + len(items) * (bar_h + gap) + PB
    max_total = max(d["patrones_detectados"] for _, d in items) or 1
    xs = W - PL - PR
    bars = []
    for i, (ticker, d) in enumerate(items):
        y = PT + i * (bar_h + gap)
        total = d["patrones_detectados"]
        sig   = sum(v for k, v in d.get("distribucion", {}).items() if k != "neutro")
        neutro = total - sig
        w_sig   = (sig / max_total) * xs
        w_neu   = (neutro / max_total) * xs
        bars.append(
            f'<text x="{PL-5}" y="{y+bar_h/2+4:.1f}" text-anchor="end" font-size="10" '
            f'fill="#1e293b" font-family="Inter,sans-serif" font-weight="600">{ticker}</text>'
            f'<rect x="{PL}" y="{y}" width="{w_sig:.1f}" height="{bar_h}" fill="#0284c7" rx="2" opacity="0.85"/>'
            f'<rect x="{PL+w_sig:.1f}" y="{y}" width="{w_neu:.1f}" height="{bar_h}" fill="#e2e8f0" rx="2"/>'
            f'<text x="{PL+w_sig+w_neu+5:.1f}" y="{y+bar_h/2+4:.1f}" font-size="9" fill="#64748b" '
            f'font-family="monospace">{sig} / {total}</text>'
        )
    legend = (
        f'<rect x="{PL}" y="{H-10}" width="12" height="8" fill="#0284c7" rx="2"/>'
        f'<text x="{PL+16}" y="{H-2}" font-size="9" fill="#475569" font-family="Inter,sans-serif">Significativos</text>'
        f'<rect x="{PL+110}" y="{H-10}" width="12" height="8" fill="#e2e8f0" rx="2"/>'
        f'<text x="{PL+126}" y="{H-2}" font-size="9" fill="#475569" font-family="Inter,sans-serif">Neutros</text>'
        f'<text x="{W-PR}" y="{H-2}" text-anchor="end" font-size="9" fill="#94a3b8" '
        f'font-family="Inter,sans-serif">Significativos / Total</text>'
    )
    return (f'<svg viewBox="0 0 {W} {H+4}" style="width:100%;height:{H+4}px;display:block">'
            + "".join(bars) + legend + "</svg>")


def _svg_barras_sorting(sorting: list) -> str:
    """Barras horizontales del benchmark de ordenamiento."""
    if not sorting:
        return "<p style='color:#94a3b8;font-size:11px'>Sin datos. Ejecutar: python main.py ordenamiento</p>"
    W, PL, PR, PT, PB = 680, 160, 80, 10, 10
    bar_h, gap = 16, 4
    H = PT + len(sorting) * (bar_h + gap) + PB
    max_t = max(r["tiempo_ms"] for r in sorting) or 1
    xs = W - PL - PR
    PALETTE = ["#0284c7", "#0891b2", "#059669", "#65a30d", "#d97706",
               "#ea580c", "#dc2626", "#9333ea", "#7c3aed", "#2563eb",
               "#0f766e", "#b45309"]
    bars = []
    for i, r in enumerate(sorting):
        y = PT + i * (bar_h + gap)
        bw = max((r["tiempo_ms"] / max_t) * xs, 2)
        col = PALETTE[i % len(PALETTE)]
        bars.append(
            f'<text x="{PL-5}" y="{y+bar_h/2+4:.1f}" text-anchor="end" font-size="10" '
            f'fill="#1e293b" font-family="Inter,sans-serif">{r["algoritmo"]}</text>'
            f'<rect x="{PL}" y="{y}" width="{bw:.1f}" height="{bar_h}" fill="{col}" rx="3" opacity="0.85"/>'
            f'<text x="{PL+bw+5:.1f}" y="{y+bar_h/2+4:.1f}" font-size="9.5" fill="#475569" '
            f'font-family="monospace">{r["tiempo_ms"]:.2f} ms</text>'
            f'<text x="{W-PR+4}" y="{y+bar_h/2+4:.1f}" font-size="9" fill="#94a3b8" '
            f'font-family="monospace">{r["complejidad"]}</text>'
        )
    return (f'<svg viewBox="0 0 {W} {H}" style="width:100%;height:{H}px;display:block">'
            + "".join(bars) + "</svg>")


def _svg_heatmap_pearson(matriz_data: dict) -> str:
    """Heatmap de correlacion Pearson 20x20."""
    tickers = matriz_data.get("tickers", [])
    mat     = matriz_data.get("valores", [])
    if not tickers or not mat:
        return "<p style='color:#94a3b8;font-size:11px'>Sin datos de correlacion.</p>"
    n = len(tickers)
    cell, lbl = 14, 24
    W = lbl + n * cell
    H = lbl + n * cell

    def cor_color(v: float) -> str:
        if v >= 0:
            r = int(16 + (240 - 16) * (1 - v))
            g = 185
            b = int(129 * v)
        else:
            t = -v
            r = 244
            g = int(63 + 90 * (1 - t))
            b = int(94 * (1 - t))
        return f"rgb({r},{g},{b})"

    xl, yl, rects = [], [], []
    for i, t in enumerate(tickers):
        x = lbl + i * cell + cell / 2
        xl.append(
            f'<text x="{x:.1f}" y="{lbl-3}" text-anchor="middle" font-size="6" fill="#475569" '
            f'font-family="sans-serif" transform="rotate(-45,{x:.1f},{lbl-3})">{t}</text>'
        )
        yl.append(
            f'<text x="{lbl-3}" y="{lbl+i*cell+cell/2+3:.1f}" text-anchor="end" font-size="6" '
            f'fill="#475569" font-family="sans-serif">{t}</text>'
        )
        for j in range(n):
            v = mat[i][j] if mat[i] else 0.0
            rects.append(
                f'<rect x="{lbl+j*cell}" y="{lbl+i*cell}" width="{cell-1}" height="{cell-1}" '
                f'fill="{cor_color(v)}" rx="2"/>'
            )
            if i == j:
                rects.append(
                    f'<text x="{lbl+j*cell+cell/2:.1f}" y="{lbl+i*cell+cell/2+3:.1f}" '
                    f'text-anchor="middle" font-size="6" fill="#fff" font-family="Inter,sans-serif">1.0</text>'
                )

    # Leyenda gradiente
    grad_y = H + 8
    legend = (
        f'<defs><linearGradient id="hm-grad" x1="0" x2="1" y1="0" y2="0">'
        f'<stop offset="0%" stop-color="rgb(244,63,94)"/>'
        f'<stop offset="50%" stop-color="rgb(51,65,85)"/>'
        f'<stop offset="100%" stop-color="rgb(16,185,129)"/>'
        f'</linearGradient></defs>'
        f'<rect x="{lbl}" y="{grad_y}" width="120" height="7" fill="url(#hm-grad)" rx="3"/>'
        f'<text x="{lbl}" y="{grad_y+18}" font-size="8" fill="#64748b" font-family="Inter,sans-serif">-1 inversa</text>'
        f'<text x="{lbl+60}" y="{grad_y+18}" text-anchor="middle" font-size="8" fill="#64748b" font-family="Inter,sans-serif">0</text>'
        f'<text x="{lbl+120}" y="{grad_y+18}" text-anchor="end" font-size="8" fill="#64748b" font-family="Inter,sans-serif">+1 perfecta</text>'
    )
    return (f'<svg viewBox="0 0 {W} {H+28}" style="width:100%;max-width:{W}px;height:{H+28}px;display:block;overflow:hidden">'
            + legend + "".join(xl) + "".join(yl) + "".join(rects) + "</svg>")


# ─── JSON ─────────────────────────────────────────────────────────────────────

def generar_reporte_json() -> dict:
    return {
        "meta": {
            "titulo":       "BVC Analytics — Reporte Tecnico de Analisis",
            "generado_en":  datetime.utcnow().isoformat() + "Z",
            "ventana_dias": VENTANA_DESLIZANTE_DIAS,
            "ventana_vol":  DIAS_VOLATILIDAD,
            "algoritmos_usados": [
                "Interpolacion Lineal — O(n)",
                "Deteccion Outliers Z-Score — O(n)",
                "Distancia Euclidiana — O(n)",
                "Correlacion de Pearson — O(n)",
                "Similitud por Coseno — O(n)",
                "Dynamic Time Warping — O(n^2)",
                "Ventana Deslizante — O(n*k)",
                "Deteccion Picos y Valles — O(n)",
                "Media Movil Simple — O(n*k)",
                "Golden / Death Cross — O(n*k)",
                "Volatilidad Historica Anualizada — O(n)",
                "Maximo Drawdown — O(n)",
                "VaR Historico 95% — O(n log n)",
                "Sharpe Ratio — O(n)",
            ],
        },
        "seccion_1_datos":       _seccion_datos(),
        "seccion_2_similitud":   _seccion_similitud(),
        "seccion_3_volatilidad": _seccion_volatilidad(),
        "seccion_4_riesgo":      _seccion_riesgo(),
        "seccion_5_patrones":    _seccion_patrones(),
    }


# ─── HTML ─────────────────────────────────────────────────────────────────────

def generar_reporte_html() -> str:
    data  = generar_reporte_json()
    meta  = data["meta"]
    sec1  = data["seccion_1_datos"]
    sec2  = data["seccion_2_similitud"]
    sec3  = data["seccion_3_volatilidad"]
    sec4  = data["seccion_4_riesgo"]
    sec5  = data["seccion_5_patrones"]
    sorting = _seccion_sorting()

    fecha_gen = meta["generado_en"][:10]
    ranking   = sec3.get("ranking", [])
    n_cons = sum(1 for r in ranking if r["volatilidad_anual"] < 0.15)
    n_mod  = sum(1 for r in ranking if 0.15 <= r["volatilidad_anual"] < 0.30)
    n_agr  = sum(1 for r in ranking if r["volatilidad_anual"] >= 0.30)
    total_activos   = sec1.get("activos_totales", 0)
    total_registros = sec1.get("filas_totales", 0)

    # ── Tabla cobertura ───────────────────────────────────────
    filas_cob = "".join(
        f"<tr><td>{r['ticker']}</td><td class='n'>{r['total_dias']}</td>"
        f"<td>{r['fecha_inicio'] or '—'}</td><td>{r['fecha_fin'] or '—'}</td></tr>"
        for r in sec1.get("cobertura", [])
    )

    # ── Tablas similitud ──────────────────────────────────────
    bloques_sim = ""
    for algo, info in sec2.items():
        if algo.startswith("_"):
            continue
        filas = "".join(
            f"<tr><td>{p['ticker1']} / {p['ticker2']}</td>"
            f"<td class='n'>{p['valor']:.6f}</td></tr>"
            for p in info.get("top_5", [])
        )
        bloques_sim += (
            f"<div class='sub-section'>"
            f"<div class='sub-title'>{info['etiqueta']}</div>"
            f"<table><thead><tr><th>Par de activos</th><th>Valor</th></tr></thead>"
            f"<tbody>{filas}</tbody></table></div>"
        )

    # ── Tabla volatilidad ─────────────────────────────────────
    filas_vol = ""
    for i, r in enumerate(ranking):
        cat = _categoria(r["volatilidad_anual"])
        ret = r["retorno_medio"] * 252 * 100
        ret_col = "#059669" if ret >= 0 else "#dc2626"
        filas_vol += (
            f"<tr><td class='n'>{i+1}</td><td><b>{r['ticker']}</b></td>"
            f"<td class='n'>{r['volatilidad_anual']*100:.2f}%</td>"
            f"<td class='n' style='color:{ret_col}'>{'+'if ret>=0 else ''}{ret:.2f}%</td>"
            f"<td>{_cat_badge(cat)}</td></tr>"
        )

    # ── Tabla riesgo ──────────────────────────────────────────
    filas_riesgo = ""
    for ticker, riesgo in sec4.items():
        if "error" in riesgo:
            continue
        vol    = riesgo.get("volatilidad_reciente", {}).get("volatilidad_anualizada")
        sharpe = riesgo.get("sharpe_ratio", {}).get("sharpe")
        var95  = riesgo.get("var_95", {}).get("var_pct")
        mdd    = riesgo.get("max_drawdown", {}).get("mdd_pct")
        cat    = _categoria(vol) if vol is not None else "—"
        sc = "#059669" if (sharpe or 0) > 1 else ("#d97706" if (sharpe or 0) > 0 else "#dc2626")
        filas_riesgo += (
            f"<tr><td><b>{ticker}</b></td>"
            + (f"<td class='n'>{vol*100:.2f}%</td>" if vol is not None else "<td>—</td>")
            + (f"<td class='n' style='color:{sc}'>{sharpe:.3f}</td>" if sharpe is not None else "<td>—</td>")
            + (f"<td class='n'>{var95:.3f}%</td>" if var95 is not None else "<td>—</td>")
            + (f"<td class='n'>{mdd:.2f}%</td>" if mdd is not None else "<td>—</td>")
            + f"<td>{_cat_badge(cat)}</td></tr>"
        )

    # ── Tabla patrones ────────────────────────────────────────
    filas_pat = ""
    for ticker, info in sec5.items():
        dist_items = sorted(info.get("distribucion", {}).items(), key=lambda x: x[1], reverse=True)
        top_patron = dist_items[0][0] if dist_items else "—"
        sig = sum(v for k, v in dist_items if k != "neutro")
        filas_pat += (
            f"<tr><td><b>{ticker}</b></td>"
            f"<td class='n'>{info['patrones_detectados']}</td>"
            f"<td class='n'>{sig}</td>"
            f"<td class='n'>{info['picos']}</td>"
            f"<td class='n'>{info['valles']}</td>"
            f"<td>{top_patron}</td></tr>"
        )

    # ── Tabla algoritmos ──────────────────────────────────────
    algos_html = "".join(
        f"<tr><td>{a.split(' — ')[0]}</td>"
        f"<td class='n'>{a.split(' — ')[1] if ' — ' in a else ''}</td></tr>"
        for a in meta.get("algoritmos_usados", [])
    )

    # ── Tabla sorting ─────────────────────────────────────────
    filas_sort = "".join(
        f"<tr><td>{r['algoritmo']}</td><td class='n'>{r['complejidad']}</td>"
        f"<td class='n'>{r['tamanio']:,}</td><td class='n'>{r['tiempo_ms']:.3f} ms</td></tr>"
        for r in sorting
    ) if sorting else "<tr><td colspan='4' style='color:#94a3b8'>Sin datos. Ejecutar: python main.py ordenamiento</td></tr>"

    # ── Graficos SVG ──────────────────────────────────────────
    svg_vol     = _svg_barras_volatilidad(ranking)
    svg_scatter = _svg_scatter_sharpe_vol(sec4)
    svg_pat     = _svg_barras_patrones(sec5)
    svg_sort    = _svg_barras_sorting(sorting)
    svg_hm      = _svg_heatmap_pearson(sec2.get("_matriz", {}))

    CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Arial,sans-serif;font-size:9.5px;color:#0f172a;background:#fff;line-height:1.35}
/* PORTADA */
.cover{width:100%;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;padding:60px 72px;page-break-after:always;break-after:page;border-left:6px solid #0284c7}
.cover-uni{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#64748b;margin-bottom:32px}
.cover h1{font-size:32px;font-weight:700;color:#0f172a;line-height:1.2;margin-bottom:16px;max-width:520px}
.cover-sub{font-size:13px;color:#475569;margin-bottom:48px;max-width:480px}
.cover-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;width:100%;max-width:600px;margin-bottom:48px}
.cover-kpi{border-top:3px solid #e2e8f0;padding-top:12px}
.cover-kpi.bl{border-top-color:#0284c7}
.cover-kpi.gr{border-top-color:#059669}
.cover-kpi.am{border-top-color:#d97706}
.cover-kpi.rd{border-top-color:#dc2626}
.cover-kpi .lbl{font-size:8px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#94a3b8;margin-bottom:4px}
.cover-kpi .val{font-size:26px;font-weight:700;font-family:monospace;color:#0f172a;line-height:1}
.cover-kpi .sub{font-size:9px;color:#94a3b8;margin-top:3px}
.cover-meta{font-size:9px;color:#94a3b8;border-top:1px solid #e2e8f0;padding-top:16px;width:100%;max-width:600px}
.cover-meta b{color:#475569}
/* CONTENIDO */
.content{padding:20px 28px}
.section{margin-bottom:16px}
.section-header{display:flex;align-items:baseline;gap:10px;margin-bottom:8px;padding-bottom:5px;border-bottom:1.5px solid #e2e8f0}
.section-number{font-size:8.5px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#94a3b8;min-width:18px}
.section-title{font-size:11px;font-weight:700;color:#0f172a}
.sub-section{margin-bottom:10px}
.sub-title{font-size:8.5px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:#475569;margin-bottom:4px;padding:3px 0;border-bottom:1px solid #f1f5f9}
table{width:100%;border-collapse:collapse;margin-bottom:8px;font-size:8.5px}
thead tr{background:#f8fafc}
th{text-align:left;padding:4px 8px;font-size:7.5px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.5px;border-bottom:2px solid #e2e8f0;white-space:nowrap}
td{padding:4px 8px;border-bottom:1px solid #f1f5f9;color:#1e293b;vertical-align:middle}
tr:last-child td{border-bottom:none}
tbody tr:nth-child(even) td{background:#fafafa}
td.n{font-family:monospace;font-size:8px}
.badge{display:inline-block;padding:1px 6px;border-radius:3px;font-size:8px;font-weight:700}
.badge-c{background:#dcfce7;color:#166534}
.badge-m{background:#fef9c3;color:#854d0e}
.badge-a{background:#fee2e2;color:#991b1b}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.note{font-size:8.5px;color:#64748b;margin-bottom:8px;padding:5px 9px;background:#f8fafc;border-left:3px solid #e2e8f0;border-radius:0 3px 3px 0}
.chart-box{background:#fafafa;border:1px solid #e2e8f0;border-radius:5px;padding:10px;margin-bottom:10px}
.chart-title{font-size:8.5px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:#475569;margin-bottom:8px}
.report-footer{margin-top:16px;padding-top:10px;border-top:1px solid #e2e8f0;display:flex;justify-content:space-between;font-size:8px;color:#94a3b8}
.report-footer .left{font-weight:600;color:#64748b}
@media print{
  *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .cover{height:100vh;page-break-after:always;break-after:page}
  svg{max-width:100%;display:block}
}
"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>BVC Analytics — Reporte Tecnico</title>
<style>{CSS}</style>
</head>
<body>

<!-- PORTADA -->
<div class="cover">
  <div class="cover-uni">Universidad del Quindio &mdash; Ingenieria de Sistemas y Computacion &mdash; Analisis de Algoritmos 2026-1</div>
  <h1>Reporte Tecnico de Analisis Financiero Cuantitativo</h1>
  <div class="cover-sub">Analisis algoritmico de {total_activos} activos financieros con cinco anos de historia diaria. Implementado en Python 3.11 stdlib sin pandas, numpy ni scipy.</div>
  <div class="cover-kpis">
    <div class="cover-kpi bl"><div class="lbl">Activos</div><div class="val">{total_activos}</div><div class="sub">Acciones y ETFs</div></div>
    <div class="cover-kpi gr"><div class="lbl">Registros OHLCV</div><div class="val">{total_registros:,}</div><div class="sub">5 anos historico</div></div>
    <div class="cover-kpi am"><div class="lbl">Pares similitud</div><div class="val">190</div><div class="sub">C(20,2) x 4 algoritmos</div></div>
    <div class="cover-kpi rd"><div class="lbl">Algoritmos</div><div class="val">28</div><div class="sub">Desde cero, sin libs</div></div>
  </div>
  <div class="cover-meta">
    <b>Fecha de generacion:</b> {fecha_gen} &nbsp;&nbsp;
    <b>Ventana deslizante:</b> {meta['ventana_dias']} dias &nbsp;&nbsp;
    <b>Ventana volatilidad:</b> {meta['ventana_vol']} dias &nbsp;&nbsp;
    <b>Distribucion de riesgo:</b> {n_cons} conservadores / {n_mod} moderados / {n_agr} agresivos
  </div>
</div>

<!-- CONTENIDO -->
<div class="content">
<!-- 01 ETL -->
<div class="section" style="page-break-before:avoid;break-before:avoid">
  <div class="section-header">
    <span class="section-number">01</span>
    <span class="section-title">Cobertura de Datos &mdash; Proceso ETL</span>
  </div>
  <div class="note">Descarga via HTTP directo a Yahoo Finance API v8 (urllib stdlib). Limpieza: interpolacion lineal O(n) y deteccion de outliers Z-Score O(n) con umbral 3.5.</div>
  <table>
    <thead><tr><th>Ticker</th><th>Dias en BD</th><th>Fecha inicio</th><th>Fecha fin</th></tr></thead>
    <tbody>{filas_cob}</tbody>
  </table>
</div>

<!-- 02 SIMILITUD -->
<div class="section">
  <div class="section-header">
    <span class="section-number">02</span>
    <span class="section-title">Similitud de Series de Tiempo &mdash; 4 Algoritmos</span>
  </div>
  <div class="note">190 pares &mdash; C(20,2). Series alineadas por interseccion de calendarios bursatiles. Complejidades: Euclidiana O(n), Pearson O(n), Coseno O(n), DTW O(n&sup2;) con ventana Sakoe-Chiba 10%.</div>
  <div class="chart-box" style="height:auto">
    <div class="chart-title">Mapa de Calor &mdash; Correlacion de Pearson (20 x 20)</div>
    {svg_hm}
  </div>
  <div class="grid2">{bloques_sim}</div>
</div>

<!-- 03 VOLATILIDAD -->
<div class="section">
  <div class="section-header">
    <span class="section-number">03</span>
    <span class="section-title">Clasificacion de Riesgo &mdash; Volatilidad Historica Anualizada</span>
  </div>
  <div class="note">Desviacion estandar muestral de retornos logaritmicos diarios, anualizada por &radic;252. Distribucion: {n_cons} conservadores, {n_mod} moderados, {n_agr} agresivos.</div>
  <div class="chart-box">
    <div class="chart-title">Volatilidad anualizada por activo &mdash; ordenado de mayor a menor riesgo</div>
    {svg_vol}
  </div>
  <table>
    <thead><tr><th>#</th><th>Ticker</th><th>Volatilidad anual</th><th>Retorno anual est.</th><th>Categoria</th></tr></thead>
    <tbody>{filas_vol}</tbody>
  </table>
</div>

<!-- 04 RIESGO -->
<div class="section">
  <div class="section-header">
    <span class="section-number">04</span>
    <span class="section-title">Metricas de Riesgo Individual</span>
  </div>
  <div class="note">VaR historico al 95% (simulacion historica, sin supuesto de normalidad). Sharpe Ratio con tasa libre de riesgo 5% anual. Max Drawdown: mayor caida pico a valle.</div>
  <div class="chart-box">
    <div class="chart-title">Sharpe Ratio vs Volatilidad anualizada &mdash; cada punto es un activo</div>
    {svg_scatter}
  </div>
  <table>
    <thead><tr><th>Ticker</th><th>Volatilidad anual</th><th>Sharpe Ratio</th><th>VaR 95% diario</th><th>Max Drawdown</th><th>Categoria</th></tr></thead>
    <tbody>{filas_riesgo}</tbody>
  </table>
</div>

<!-- 05 PATRONES -->
<div class="section">
  <div class="section-header">
    <span class="section-number">05</span>
    <span class="section-title">Deteccion de Patrones &mdash; Ventana Deslizante</span>
  </div>
  <div class="note">Ventana deslizante O(n&middot;k) con k={meta['ventana_dias']} dias. Patron 1: dias consecutivos al alza (umbral 75%). Patron 2: rebote en V (primera mitad bajista, segunda alcista).</div>
  <div class="chart-box">
    <div class="chart-title">Patrones significativos vs neutros por activo</div>
    {svg_pat}
  </div>
  <table>
    <thead><tr><th>Ticker</th><th>Total ventanas</th><th>Significativos</th><th>Picos locales</th><th>Valles locales</th><th>Patron dominante</th></tr></thead>
    <tbody>{filas_pat}</tbody>
  </table>
</div>

<!-- 06 ORDENAMIENTO -->
<div class="section">
  <div class="section-header">
    <span class="section-number">06</span>
    <span class="section-title">Benchmark de Ordenamiento &mdash; 12 Algoritmos</span>
  </div>
  <div class="note">Muestra de n=5,000 registros OHLCV. Criterio: fecha ASC (primario), cierre ASC (secundario). Tiempos medidos con time.perf_counter(). Sin sorted() ni .sort().</div>
  <div class="chart-box">
    <div class="chart-title">Tiempo de ejecucion por algoritmo &mdash; ordenado de menor a mayor</div>
    {svg_sort}
  </div>
  <table>
    <thead><tr><th>Algoritmo</th><th>Complejidad</th><th>Tamano (n)</th><th>Tiempo</th></tr></thead>
    <tbody>{filas_sort}</tbody>
  </table>
</div>

<!-- 07 ALGORITMOS -->
<div class="section">
  <div class="section-header">
    <span class="section-number">07</span>
    <span class="section-title">Inventario de Algoritmos Implementados</span>
  </div>
  <table>
    <thead><tr><th>Algoritmo</th><th>Complejidad</th></tr></thead>
    <tbody>{algos_html}</tbody>
  </table>
</div>

<div class="report-footer">
  <span class="left">BVC Analytics &mdash; Universidad del Quindio &mdash; Analisis de Algoritmos 2026-1</span>
  <span>Generado el {fecha_gen} &mdash; Python 3.11 stdlib</span>
</div>

</div><!-- /content -->
</body>
</html>"""


