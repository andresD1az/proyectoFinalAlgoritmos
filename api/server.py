"""
api/server.py — Servidor HTTP puro (http.server stdlib)
Endpoints estrictamente limitados a los 5 requerimientos del enunciado:
  Req 1: ETL  |  Req 2: Similitud  |  Req 3: Patrones + Volatilidad
  Req 4: Dashboard (heatmap, velas, reporte)  |  Req 5: Despliegue
Extra: Conversor USD/COP
"""

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from config import API_HOST, API_PORT

def _respuesta_json(handler, codigo: int, datos):
    cuerpo = json.dumps(datos, ensure_ascii=False, default=str).encode("utf-8")
    handler.send_response(codigo)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(cuerpo)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(cuerpo)

def _parsear_query(path: str) -> dict:
    partes = urllib.parse.urlparse(path)
    return dict(urllib.parse.parse_qsl(partes.query))

class BVCHandler(BaseHTTPRequestHandler):

    def log_message(self, formato, *args):
        print(f"[API] {self.address_string()} — {formato % args}")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        import json as _json
        ruta   = urllib.parse.urlparse(self.path).path
        params = _parsear_query(self.path)
        length = int(self.headers.get('Content-Length', 0))
        body   = _json.loads(self.rfile.read(length)) if length else {}

        rutas_post = {
            '/etl/iniciar': self._etl_iniciar,
        }
        handler = rutas_post.get(ruta)
        if handler:
            handler(params, body)
        else:
            _respuesta_json(self, 404, {'error': f"POST {ruta} no encontrado"})

    def do_GET(self):
        ruta   = urllib.parse.urlparse(self.path).path
        params = _parsear_query(self.path)

        rutas = {
            "/":                     self._app,
            "/app":                  self._app,
            # Sistema
            "/health":               self._health,
            "/etl/status":           self._etl_status,
            # Req 1 — Datos
            "/activos":              self._activos,
            "/precios":              self._precios,
            "/precios/ohlcv":        self._ohlcv,
            # Req 2 — Similitud
            "/similitud":            self._similitud,
            "/correlacion/matriz":   self._correlacion_matriz,
            # Req 3 — Patrones y Volatilidad
            "/patrones":             self._patrones,
            "/patrones/cruces":      self._cruces_medias,
            "/riesgo/clasificacion": self._clasificacion_riesgo,
            # Req 4 — Dashboard
            "/reporte":              self._reporte,
            "/reporte/txt":          self._reporte_txt,
            # Ordenamiento
            "/ordenamiento/benchmark":   self._sorting_benchmark,
            "/ordenamiento/top-volumen": self._sorting_top_volumen,
            # Extra — Conversor
            "/monedas/tasa":         self._monedas_tasa,
        }

        handler = rutas.get(ruta)
        if handler:
            handler(params)
        else:
            _respuesta_json(self, 404, {"error": f"Ruta '{ruta}' no encontrada."})

    # ── FRONTEND ──────────────────────────────────────────────────

    def _app(self, params):
        import os
        ruta = os.path.join(os.path.dirname(__file__), '..', 'interfaz', 'index.html')
        try:
            with open(ruta, 'rb') as f:
                contenido = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(contenido)))
            self.end_headers()
            self.wfile.write(contenido)
        except FileNotFoundError:
            _respuesta_json(self, 404, {'error': 'frontend/index.html no encontrado'})

    # ── SISTEMA ───────────────────────────────────────────────────

    def _health(self, params):
        _respuesta_json(self, 200, {"estado": "ok", "servicio": "Algorit Finance API"})

    def _etl_status(self, params):
        """GET /etl/status — Cuántos registros hay en la BD."""
        try:
            from etl.database import get_connection
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM precios;")
                total_precios = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM activos;")
                total_activos = cur.fetchone()[0]
            conn.close()
            _respuesta_json(self, 200, {
                "activos": total_activos,
                "registros_precios": total_precios,
                "etl_ejecutado": total_precios > 0,
            })
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})

    def _etl_iniciar(self, params, body):
        """POST /etl/iniciar — Dispara el ETL en segundo plano."""
        import threading
        def _run():
            try:
                from main import pipeline_etl
                pipeline_etl()
            except Exception as ex:
                print(f"[ETL-API] Error: {ex}")
        threading.Thread(target=_run, daemon=True).start()
        _respuesta_json(self, 202, {
            "estado": "iniciado",
            "mensaje": "ETL corriendo en segundo plano. Consulta /etl/status para ver el progreso.",
        })

    # ── REQ 1 — DATOS ─────────────────────────────────────────────

    def _activos(self, params):
        """GET /activos — Lista de activos con cantidad de días en BD."""
        try:
            from etl.database import get_connection
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.ticker, a.nombre, a.mercado, COUNT(p.id) AS dias
                    FROM activos a
                    LEFT JOIN precios p ON p.activo_id = a.id
                    GROUP BY a.id, a.ticker, a.nombre, a.mercado
                    ORDER BY a.ticker;
                """)
                filas = cur.fetchall()
            conn.close()
            activos = [{'ticker': f[0], 'nombre': f[1], 'mercado': f[2], 'dias': f[3]} for f in filas]
            _respuesta_json(self, 200, {'activos': activos, 'total': len(activos)})
        except Exception as e:
            from config import ACTIVOS
            _respuesta_json(self, 200, {'activos': ACTIVOS, 'total': len(ACTIVOS)})

    def _precios(self, params):
        """GET /precios?ticker=SPY&columna=cierre"""
        ticker = params.get("ticker")
        if not ticker:
            _respuesta_json(self, 400, {"error": "Parámetro 'ticker' requerido."})
            return
        try:
            from etl.database import obtener_precios
            columna = params.get("columna", "cierre")
            datos = obtener_precios(ticker.upper(), columna)
            _respuesta_json(self, 200, {"ticker": ticker.upper(), "columna": columna, "datos": datos})
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})

    def _ohlcv(self, params):
        """GET /precios/ohlcv?ticker=SPY&n=120"""
        ticker = params.get('ticker')
        if not ticker:
            _respuesta_json(self, 400, {'error': 'ticker requerido'})
            return
        try:
            from etl.database import obtener_ohlcv_completo
            n = int(params.get('n', 120))
            datos = obtener_ohlcv_completo(ticker.upper())[-n:]
            _respuesta_json(self, 200, {
                'ticker': ticker.upper(),
                'datos': [{'fecha': str(d['fecha']), 'apertura': float(d['apertura'] or 0),
                           'maximo': float(d['maximo'] or 0), 'minimo': float(d['minimo'] or 0),
                           'cierre': float(d['cierre'] or 0), 'volumen': int(d['volumen'] or 0)}
                          for d in datos]
            })
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})

    # ── REQ 2 — SIMILITUD ─────────────────────────────────────────

    def _similitud(self, params):
        """GET /similitud?algoritmo=pearson — euclidiana|pearson|coseno|dtw"""
        algoritmo = params.get("algoritmo", "pearson")
        if algoritmo not in {"euclidiana", "pearson", "coseno", "dtw"}:
            _respuesta_json(self, 400, {"error": "algoritmo debe ser: euclidiana|pearson|coseno|dtw"})
            return
        try:
            from etl.database import obtener_similitudes
            datos = obtener_similitudes(algoritmo)
            _respuesta_json(self, 200, {"algoritmo": algoritmo, "resultados": datos})
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})

    def _correlacion_matriz(self, params):
        """GET /correlacion/matriz — Matriz 20x20 de Pearson para el heatmap."""
        try:
            from config import TICKERS
            from etl.database import get_connection
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a1.ticker, a2.ticker, r.valor
                    FROM resultados_similitud r
                    JOIN activos a1 ON a1.id = r.activo1_id
                    JOIN activos a2 ON a2.id = r.activo2_id
                    WHERE r.algoritmo = 'pearson';
                """)
                filas = cur.fetchall()
            conn.close()
            n   = len(TICKERS)
            idx = {t: i for i, t in enumerate(TICKERS)}
            mat = [[0.0] * n for _ in range(n)]
            for i in range(n):
                mat[i][i] = 1.0
            for t1, t2, val in filas:
                if t1 in idx and t2 in idx:
                    mat[idx[t1]][idx[t2]] = round(float(val), 4)
                    mat[idx[t2]][idx[t1]] = round(float(val), 4)
            _respuesta_json(self, 200, {'tickers': TICKERS, 'matriz': mat})
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})

    # ── REQ 3 — PATRONES Y VOLATILIDAD ────────────────────────────

    def _patrones(self, params):
        """GET /patrones?ticker=SPY — Ventana deslizante + picos/valles."""
        ticker = params.get("ticker")
        if not ticker:
            _respuesta_json(self, 400, {"error": "ticker requerido"})
            return
        try:
            from etl.database import obtener_precios
            from algoritmos.patrones import detectar_patrones, detectar_picos_valles
            from config import VENTANA_DESLIZANTE_DIAS
            filas   = obtener_precios(ticker.upper(), "cierre")
            fechas  = [str(f["fecha"])    for f in filas]
            precios = [float(f["cierre"]) for f in filas]
            patrones     = detectar_patrones(fechas, precios, VENTANA_DESLIZANTE_DIAS)
            picos_valles = detectar_picos_valles(fechas, precios)
            _respuesta_json(self, 200, {
                "ticker": ticker.upper(),
                "total_patrones": len(patrones),
                "patrones": patrones[-50:],
                "picos_recientes":  picos_valles["picos"][-10:],
                "valles_recientes": picos_valles["valles"][-10:],
            })
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})

    def _cruces_medias(self, params):
        """GET /patrones/cruces?ticker=SPY&corta=10&larga=30 — Golden/Death Cross."""
        ticker = params.get("ticker")
        if not ticker:
            _respuesta_json(self, 400, {"error": "ticker requerido"})
            return
        try:
            from etl.database import obtener_precios
            from algoritmos.patrones import detectar_cruces_medias
            filas   = obtener_precios(ticker.upper(), "cierre")
            fechas  = [str(f["fecha"])    for f in filas]
            precios = [float(f["cierre"]) for f in filas]
            corta   = int(params.get("corta", 10))
            larga   = int(params.get("larga", 30))
            cruces  = detectar_cruces_medias(fechas, precios, corta, larga)
            _respuesta_json(self, 200, {
                "ticker": ticker.upper(), "sma_corta": corta, "sma_larga": larga,
                "golden_cross": [c for c in cruces if c["tipo"] == "golden_cross"],
                "death_cross":  [c for c in cruces if c["tipo"] == "death_cross"],
            })
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})

    def _clasificacion_riesgo(self, params):
        """GET /riesgo/clasificacion — Clasifica los 20 activos por volatilidad."""
        try:
            from etl.database import obtener_todos_cierres
            from algoritmos.volatilidad import calcular_volatilidad, calcular_sharpe, calcular_var_historico
            from config import DIAS_VOLATILIDAD
            series = obtener_todos_cierres()
            resultado = []
            for ticker, precios in series.items():
                if len(precios) < DIAS_VOLATILIDAD:
                    continue
                vols = calcular_volatilidad(precios, DIAS_VOLATILIDAD)
                if not vols:
                    continue
                vol_anual = vols[-1]['volatilidad_anualizada']
                sharpe    = calcular_sharpe(precios)['sharpe']
                var95     = calcular_var_historico(precios, 0.95)['var_pct']
                categoria = 'Conservador' if vol_anual < 0.15 else ('Moderado' if vol_anual < 0.30 else 'Agresivo')
                resultado.append({
                    'ticker': ticker, 'vol_pct': round(vol_anual * 100, 2),
                    'categoria': categoria, 'sharpe': round(sharpe, 3), 'var95_pct': round(var95, 4),
                })
            resultado.sort(key=lambda x: x['vol_pct'], reverse=True)
            conteo = {'Conservador': 0, 'Moderado': 0, 'Agresivo': 0}
            for a in resultado:
                conteo[a['categoria']] += 1
            _respuesta_json(self, 200, {'activos': resultado, 'conteo': conteo, 'total': len(resultado)})
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})

    # ── REQ 4 — REPORTE ───────────────────────────────────────────

    def _reporte(self, params):
        """GET /reporte — Reporte técnico completo en JSON."""
        try:
            from reportes.generador import generar_reporte_json
            _respuesta_json(self, 200, generar_reporte_json())
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})

    def _reporte_txt(self, params):
        """GET /reporte/txt — Reporte técnico en texto plano (para PDF)."""
        try:
            from reportes.generador import generar_reporte_html
            contenido = generar_reporte_html().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(contenido)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(contenido)
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})

    # ── ORDENAMIENTO ──────────────────────────────────────────────

    def _sorting_benchmark(self, params):
        """GET /ordenamiento/benchmark — Tabla 1: 12 algoritmos, tamaño y tiempo (ASC por tiempo)."""
        try:
            from etl.database import get_connection
            import psycopg2.extras
            conn = get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT algoritmo, complejidad, tamanio, tiempo_ms
                    FROM resultados_sorting ORDER BY tiempo_ms ASC;
                """)
                filas = [dict(f) for f in cur.fetchall()]
            conn.close()
            if not filas:
                _respuesta_json(self, 404, {'error': 'Sin resultados. Ejecuta: python main.py ordenamiento'})
                return
            _respuesta_json(self, 200, {'tabla1': filas, 'total': len(filas)})
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})

    def _sorting_top_volumen(self, params):
        """GET /ordenamiento/top-volumen — Top-15 días con mayor volumen (ASC)."""
        try:
            from etl.database import get_connection
            import psycopg2.extras
            conn = get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT ticker, fecha, volumen, cierre FROM top_volumen ORDER BY volumen ASC;")
                filas = [dict(f) for f in cur.fetchall()]
            conn.close()
            if not filas:
                _respuesta_json(self, 404, {'error': 'Sin resultados. Ejecuta: python main.py ordenamiento'})
                return
            _respuesta_json(self, 200, {'top15': filas})
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})

    # ── EXTRA — CONVERSOR USD/COP ──────────────────────────────────

    def _monedas_tasa(self, params):
        """GET /monedas/tasa — Tasa USD/COP en tiempo real desde Yahoo Finance."""
        try:
            import urllib.request
            url = "https://query1.finance.yahoo.com/v8/finance/chart/COP=X?interval=1d&range=1d"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            precio = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            _respuesta_json(self, 200, {
                "usd_cop": round(precio, 2),
                "cop_usd": round(1 / precio, 8),
                "fuente":  "Yahoo Finance (COP=X)",
            })
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})

# ── INICIO ────────────────────────────────────────────────────────

def iniciar_servidor():
    servidor = ThreadingHTTPServer((API_HOST, API_PORT), BVCHandler)
    print(f"[API] Algorit Finance corriendo en http://{API_HOST}:{API_PORT}")
    print("[API] Req1: /activos /precios /etl/status")
    print("[API] Req2: /similitud /correlacion/matriz")
    print("[API] Req3: /patrones /patrones/cruces /riesgo/clasificacion")
    print("[API] Req4: /reporte /reporte/txt /precios/ohlcv")
    print("[API] Extra: /monedas/tasa")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[API] Servidor detenido.")
        servidor.server_close()
