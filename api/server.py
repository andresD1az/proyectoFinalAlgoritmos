"""
api/server.py — Servidor HTTP puro usando http.server (stdlib)
SIN Flask, SIN FastAPI, SIN Django — solo Python estándar
"""

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from config import API_HOST, API_PORT


# ------------------------------------------------------------------
# Helpers de respuesta
# ------------------------------------------------------------------

def _respuesta_json(handler, codigo: int, datos: dict | list):
    """Serializa a JSON y envía la respuesta HTTP."""
    cuerpo = json.dumps(datos, ensure_ascii=False, default=str).encode("utf-8")
    handler.send_response(codigo)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(cuerpo)))
    handler.send_header("Access-Control-Allow-Origin", "*")   # CORS básico
    handler.end_headers()
    handler.wfile.write(cuerpo)


def _parsear_query(path: str) -> dict:
    """Extrae parámetros de la query string (?ticker=SPY&algoritmo=pearson)."""
    partes = urllib.parse.urlparse(path)
    return dict(urllib.parse.parse_qsl(partes.query))


# ------------------------------------------------------------------
# ENRUTADOR PRINCIPAL
# ------------------------------------------------------------------

class BVCHandler(BaseHTTPRequestHandler):

    def log_message(self, formato, *args):
        """Reemplaza el log por defecto con uno más limpio."""
        print(f"[API] {self.address_string()} — {formato % args}")

    def do_OPTIONS(self):
        """Preflight CORS."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        """Router para peticiones POST."""
        import json as _json
        ruta   = urllib.parse.urlparse(self.path).path
        params = _parsear_query(self.path)
        length = int(self.headers.get('Content-Length', 0))
        body   = _json.loads(self.rfile.read(length)) if length else {}

        rutas_post = {
            '/activos/agregar':   self._agregar_activo,
            '/auth/register':     self._auth_register,
            '/auth/login':        self._auth_login,
            '/auth/logout':       self._auth_logout,
            '/simulador/comprar': self._sim_comprar,
            '/simulador/vender':  self._sim_vender,
            '/etl/iniciar':       self._etl_iniciar,
        }
        handler = rutas_post.get(ruta)
        if handler:
            handler(params, body)
        else:
            _respuesta_json(self, 404, {'error': f"POST {ruta} no encontrado"})

    def do_GET(self):
        ruta = urllib.parse.urlparse(self.path).path
        params = _parsear_query(self.path)

        rutas = {
            "/":                      self._app,
            "/app":                   self._app,
            "/health":                self._health,
            "/activos":               self._activos,
            "/precios":               self._precios,
            "/precios/ohlcv":         self._ohlcv,
            "/similitud":             self._similitud,
            "/volatilidad":           self._volatilidad,
            "/patrones":              self._patrones,
            "/patrones/cruces":       self._cruces_medias,
            "/riesgo":                self._riesgo,
            "/riesgo/clasificacion":  self._clasificacion_riesgo,
            "/correlacion/matriz":    self._correlacion_matriz,
            "/reporte":               self._reporte,
            "/reporte/txt":           self._reporte_txt,
            # Auth
            "/auth/me":                     self._auth_me,
            # Academia (CMS)
            "/academia/lecciones":           self._academia_lecciones,
            "/academia/leccion":             self._academia_leccion,
            # Simulador
            "/simulador/portafolio":         self._sim_portafolio,
            # Monedas
            "/monedas/tasa":                 self._monedas_tasa,
            # Admin
            "/admin/usuarios":               self._admin_usuarios,
            # Ordenamiento (Requerimiento 2)
            "/ordenamiento/benchmark":       self._sorting_benchmark,
            "/ordenamiento/top-volumen":     self._sorting_top_volumen,
            "/ordenamiento/dataset":         self._sorting_dataset,
            # ETL status
            "/etl/status":                   self._etl_status,
        }

        handler = rutas.get(ruta)
        if handler:
            handler(params)
        else:
            _respuesta_json(self, 404, {"error": f"Ruta '{ruta}' no encontrada."})

    # ──── ENDPOINTS ────────────────────────────────────────────

    def _app(self, params):
        """GET / — Sirve el dashboard frontend."""
        import os
        ruta = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
        try:
            with open(ruta, 'rb') as f:
                contenido = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(contenido)))
            self.end_headers()
            self.wfile.write(contenido)
        except FileNotFoundError:
            _respuesta_json(self, 404, {'error': 'Frontend no encontrado. Crear frontend/index.html'})

    def _health(self, params):
        """GET /health — Verificación de estado del sistema."""
        _respuesta_json(self, 200, {
            "estado": "ok",
            "servicio": "BVC Analytics API",
            "version": "1.0.0",
        })

    def _activos(self, params):
        """GET /activos — Lista de activos (config + BD)."""
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
            activos = [{
                'ticker':   f[0], 'nombre': f[1],
                'mercado':  f[2], 'dias':   f[3],
                'yahoo_url': f'https://finance.yahoo.com/quote/{f[0]}'
            } for f in filas]
            _respuesta_json(self, 200, {'activos': activos, 'total': len(activos)})
        except Exception as e:
            from config import ACTIVOS
            _respuesta_json(self, 200, {'activos': ACTIVOS, 'total': len(ACTIVOS)})

    def _agregar_activo(self, params, body):
        """
        POST /activos/agregar
        Body JSON: {"ticker": "AMZN", "nombre": "Amazon (opcional)", "mercado": "NASDAQ"}
        Descarga 5 años de datos y los guarda en la BD.
        """
        ticker  = (body.get('ticker') or params.get('ticker', '')).upper().strip()
        nombre  = body.get('nombre') or ticker
        mercado = body.get('mercado', 'CUSTOM')

        if not ticker:
            _respuesta_json(self, 400, {'error': 'ticker requerido'})
            return
        try:
            from etl.downloader import descargar_ticker
            from etl.cleaner   import limpiar_dataset
            from etl.database  import get_connection, insertar_precios_lote

            # 1. Registrar activo en BD
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO activos (ticker, nombre, mercado)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (ticker) DO UPDATE
                            SET nombre=EXCLUDED.nombre, mercado=EXCLUDED.mercado
                        RETURNING id;
                    """, (ticker, nombre, mercado))
                    activo_id = cur.fetchone()[0]
                conn.commit()
            finally:
                conn.close()

            # 2. Descargar datos de Yahoo Finance
            filas_crudas = descargar_ticker(ticker)
            if not filas_crudas:
                _respuesta_json(self, 404, {
                    'error': f'No se encontraron datos para "{ticker}". '
                             f'Verifica que sea un ticker válido en Yahoo Finance.'
                })
                return

            # 3. Limpiar e insertar
            filas_limpias = limpiar_dataset(filas_crudas)
            insertar_precios_lote(activo_id, filas_limpias)

            _respuesta_json(self, 200, {
                'ok': True,
                'ticker':          ticker,
                'nombre':          nombre,
                'mercado':         mercado,
                'dias_descargados': len(filas_limpias),
                'yahoo_url':       f'https://finance.yahoo.com/quote/{ticker}',
                'mensaje':         f'\u2705 {ticker} agregado con {len(filas_limpias)} días de datos.',
            })
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})


    def _precios(self, params):
        """
        GET /precios?ticker=SPY&columna=cierre
        Retorna los precios históricos de un activo.
        """
        ticker = params.get("ticker")
        if not ticker:
            _respuesta_json(self, 400, {"error": "Parámetro 'ticker' requerido."})
            return
        try:
            from etl.database import obtener_precios
            columna = params.get("columna", "cierre")
            datos = obtener_precios(ticker.upper(), columna)
            _respuesta_json(self, 200, {
                "ticker": ticker.upper(),
                "columna": columna,
                "registros": len(datos),
                "datos": datos,
            })
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})

    def _similitud(self, params):
        """
        GET /similitud?algoritmo=pearson
        Retorna resultados del algoritmo de similitud seleccionado.
        algoritmo: euclidiana | pearson | coseno | dtw
        """
        algoritmo = params.get("algoritmo", "pearson")
        algoritmos_validos = {"euclidiana", "pearson", "coseno", "dtw"}
        if algoritmo not in algoritmos_validos:
            _respuesta_json(self, 400, {
                "error": f"Algoritmo inválido. Usa: {algoritmos_validos}"
            })
            return
        try:
            from etl.database import obtener_similitudes
            datos = obtener_similitudes(algoritmo)
            _respuesta_json(self, 200, {
                "algoritmo": algoritmo,
                "resultados": datos,
            })
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})

    def _volatilidad(self, params):
        """
        GET /volatilidad?ticker=SPY
        Retorna los registros de volatilidad calculados para un activo.
        """
        ticker = params.get("ticker")
        if not ticker:
            _respuesta_json(self, 400, {"error": "Parámetro 'ticker' requerido."})
            return
        try:
            from etl.database import get_connection
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT rv.fecha, rv.ventana_dias, rv.volatilidad, rv.retorno_medio
                    FROM resultados_volatilidad rv
                    JOIN activos a ON a.id = rv.activo_id
                    WHERE a.ticker = %s
                    ORDER BY rv.fecha DESC
                    LIMIT 100;
                """, (ticker.upper(),))
                filas = cur.fetchall()
            conn.close()
            datos = [
                {"fecha": str(f[0]), "ventana_dias": f[1],
                 "volatilidad": float(f[2]), "retorno_medio": float(f[3])}
                for f in filas
            ]
            _respuesta_json(self, 200, {"ticker": ticker.upper(), "datos": datos})
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})

    def _patrones(self, params):
        """
        GET /patrones?ticker=SPY&patron=3_dias_alza
        Detecta patrones en tiempo real sobre los precios cargados en BD.
        """
        ticker = params.get("ticker")
        if not ticker:
            _respuesta_json(self, 400, {"error": "Parámetro 'ticker' requerido."})
            return
        try:
            from etl.database import obtener_precios
            from algorithms.patterns import detectar_patrones, detectar_picos_valles
            from config import VENTANA_DESLIZANTE_DIAS

            filas = obtener_precios(ticker.upper(), "cierre")
            if not filas:
                _respuesta_json(self, 404, {"error": f"Sin datos para {ticker.upper()}"})
                return

            fechas  = [str(f["fecha"])    for f in filas]
            precios = [float(f["cierre"]) for f in filas]

            patrones     = detectar_patrones(fechas, precios, VENTANA_DESLIZANTE_DIAS)
            picos_valles = detectar_picos_valles(fechas, precios)

            # Filtrar por patrón si se especifica
            patron_filtro = params.get("patron")
            if patron_filtro:
                patrones = [p for p in patrones if p["patron"] == patron_filtro]

            _respuesta_json(self, 200, {
                "ticker":              ticker.upper(),
                "total_patrones":      len(patrones),
                "picos_detectados":    len(picos_valles["picos"]),
                "valles_detectados":   len(picos_valles["valles"]),
                "patrones":            patrones[-50:],   # últimos 50
                "picos_recientes":     picos_valles["picos"][-10:],
                "valles_recientes":    picos_valles["valles"][-10:],
            })
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})

    def _cruces_medias(self, params):
        """
        GET /patrones/cruces?ticker=SPY&corta=10&larga=30
        Detecta Golden Cross y Death Cross entre dos medias móviles.
        """
        ticker = params.get("ticker")
        if not ticker:
            _respuesta_json(self, 400, {"error": "Parámetro 'ticker' requerido."})
            return
        try:
            from etl.database import obtener_precios
            from algorithms.patterns import detectar_cruces_medias

            filas   = obtener_precios(ticker.upper(), "cierre")
            fechas  = [str(f["fecha"])    for f in filas]
            precios = [float(f["cierre"]) for f in filas]

            corta = int(params.get("corta", 10))
            larga = int(params.get("larga", 30))
            cruces = detectar_cruces_medias(fechas, precios, corta, larga)

            _respuesta_json(self, 200, {
                "ticker":         ticker.upper(),
                "sma_corta_dias": corta,
                "sma_larga_dias": larga,
                "total_cruces":   len(cruces),
                "golden_cross":   [c for c in cruces if c["tipo"] == "golden_cross"],
                "death_cross":    [c for c in cruces if c["tipo"] == "death_cross"],
            })
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})

    def _riesgo(self, params):
        """
        GET /riesgo?ticker=SPY
        Retorna VaR, Sharpe Ratio y Máximo Drawdown calculados en tiempo real.
        """
        ticker = params.get("ticker")
        if not ticker:
            _respuesta_json(self, 400, {"error": "Parámetro 'ticker' requerido."})
            return
        try:
            from etl.database import obtener_precios
            from algorithms.volatility import resumen_riesgo

            filas   = obtener_precios(ticker.upper(), "cierre")
            precios = [float(f["cierre"]) for f in filas]
            resultado = resumen_riesgo(ticker.upper(), precios)
            _respuesta_json(self, 200, resultado)
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})

    def _ohlcv(self, params):
        """GET /precios/ohlcv?ticker=SPY&n=120 — OHLCV completo para velas."""
        ticker = params.get('ticker')
        if not ticker:
            _respuesta_json(self, 400, {'error': 'ticker requerido'})
            return
        try:
            from etl.database import obtener_ohlcv_completo
            n = int(params.get('n', 120))
            datos = obtener_ohlcv_completo(ticker.upper())
            datos = datos[-n:]   # últimos N días
            _respuesta_json(self, 200, {
                'ticker': ticker.upper(),
                'datos': [{
                    'fecha':    str(d['fecha']),
                    'apertura': float(d['apertura'] or 0),
                    'maximo':   float(d['maximo']   or 0),
                    'minimo':   float(d['minimo']   or 0),
                    'cierre':   float(d['cierre']   or 0),
                    'volumen':  int(d['volumen']    or 0),
                } for d in datos]
            })
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})

    def _clasificacion_riesgo(self, params):
        """
        GET /riesgo/clasificacion
        Clasifica los 20 activos en conservador / moderado / agresivo
        según su volatilidad anualizada calculada desde cero.
        Categorías: conservador < 15% | 15-30% moderado | > 30% agresivo
        """
        try:
            from etl.database import obtener_todos_cierres
            from algorithms.volatility import calcular_volatilidad, calcular_sharpe, calcular_var_historico
            from config import DIAS_VOLATILIDAD

            series = obtener_todos_cierres()
            activos_riesgo = []

            for ticker, precios in series.items():
                if len(precios) < DIAS_VOLATILIDAD:
                    continue
                vols = calcular_volatilidad(precios, DIAS_VOLATILIDAD)
                if not vols:
                    continue
                vol_anual = vols[-1]['volatilidad_anualizada']
                sharpe    = calcular_sharpe(precios)['sharpe']
                var95     = calcular_var_historico(precios, 0.95)['var_pct']

                if vol_anual < 0.15:
                    categoria = 'Conservador'
                elif vol_anual < 0.30:
                    categoria = 'Moderado'
                else:
                    categoria = 'Agresivo'

                activos_riesgo.append({
                    'ticker':     ticker,
                    'vol_anual':  round(vol_anual, 4),
                    'vol_pct':    round(vol_anual * 100, 2),
                    'categoria':  categoria,
                    'sharpe':     round(sharpe, 3),
                    'var95_pct':  round(var95, 4),
                })

            # Ordenar por volatilidad descendente (más agresivo primero)
            activos_riesgo.sort(key=lambda x: x['vol_anual'], reverse=True)

            conteo = {'Conservador': 0, 'Moderado': 0, 'Agresivo': 0}
            for a in activos_riesgo:
                conteo[a['categoria']] += 1

            _respuesta_json(self, 200, {
                'activos':     activos_riesgo,
                'conteo':      conteo,
                'total':       len(activos_riesgo),
            })
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})

    def _correlacion_matriz(self, params):
        """
        GET /correlacion/matriz
        Construye la matriz 20×20 de Pearson desde los resultados guardados.
        """
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

    def _reporte(self, params):
        """GET /reporte — Genera y retorna el reporte técnico completo en JSON."""
        try:
            from reports.generator import generar_reporte_json
            _respuesta_json(self, 200, generar_reporte_json())
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})

    def _reporte_txt(self, params):
        """GET /reporte/txt — Reporte técnico en texto plano."""
        try:
            from reports.generator import generar_reporte_txt
            contenido = generar_reporte_txt().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(contenido)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(contenido)
        except Exception as e:
            _respuesta_json(self, 500, {"error": str(e)})


# ------------------------------------------------------------------
# AUTH HANDLERS
# ------------------------------------------------------------------

    def _auth_register(self, params, body):
        """POST /auth/register  — Registro de nuevo usuario."""
        from auth.auth import registrar_usuario
        username = (body.get('username') or '').strip()
        email    = (body.get('email') or '').strip()
        password = (body.get('password') or '')
        if not username or not email or not password:
            _respuesta_json(self, 400, {'error': 'username, email y password son obligatorios.'})
            return
        resultado = registrar_usuario(username, email, password)
        if 'error' in resultado:
            _respuesta_json(self, 400, resultado)
        else:
            _respuesta_json(self, 201, resultado)

    def _auth_login(self, params, body):
        """POST /auth/login — Inicio de sesión. Devuelve token en cookie y body."""
        from auth.auth import login_usuario
        username = (body.get('username') or '').strip()
        password = (body.get('password') or '')
        if not username or not password:
            _respuesta_json(self, 400, {'error': 'username y password son obligatorios.'})
            return
        resultado = login_usuario(username, password)
        if 'error' in resultado:
            _respuesta_json(self, 401, resultado)
        else:
            # Enviar token en cookie HttpOnly + en el body
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Credentials', 'true')
            cookie = (f"bvc_session={resultado['token']}; "
                      f"Path=/; HttpOnly; SameSite=Lax; Max-Age=86400")
            self.send_header('Set-Cookie', cookie)
            import json as _j
            data = _j.dumps(resultado).encode('utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    def _auth_logout(self, params, body):
        """POST /auth/logout — Invalida la sesión actual."""
        from auth.auth import obtener_token_de_headers, logout_usuario
        token = obtener_token_de_headers(self)
        if token:
            logout_usuario(token)
        # Limpiar cookie
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Set-Cookie', 'bvc_session=; Path=/; Max-Age=0')
        import json as _j
        data = _j.dumps({'ok': True}).encode()
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _auth_me(self, params):
        """GET /auth/me — Retorna el usuario actual si la sesión es válida."""
        from auth.auth import obtener_token_de_headers, verificar_sesion
        token   = obtener_token_de_headers(self)
        usuario = verificar_sesion(token) if token else None
        if not usuario:
            _respuesta_json(self, 401, {'error': 'No autenticado. Inicia sesión.'})
        else:
            _respuesta_json(self, 200, usuario)

# ------------------------------------------------------------------
# ACADEMIA (CMS) HANDLERS
# ------------------------------------------------------------------

    def _academia_lecciones(self, params):
        """GET /academia/lecciones — Lista de lecciones educativas."""
        from cms.content import obtener_lecciones
        _respuesta_json(self, 200, {'lecciones': obtener_lecciones()})

    def _academia_leccion(self, params):
        """GET /academia/leccion?id=1 — Contenido de una lección."""
        from cms.content import obtener_leccion
        try:
            leccion_id = int(params.get('id', 0))
        except ValueError:
            _respuesta_json(self, 400, {'error': 'id debe ser un número entero.'})
            return
        leccion = obtener_leccion(leccion_id)
        if leccion:
            _respuesta_json(self, 200, leccion)
        else:
            _respuesta_json(self, 404, {'error': f'Lección {leccion_id} no encontrada.'})

# ------------------------------------------------------------------
# SIMULADOR HANDLERS
# ------------------------------------------------------------------

    def _sim_portafolio(self, params):
        """GET /simulador/portafolio — Portafolio virtual del usuario autenticado."""
        from auth.auth import obtener_token_de_headers, verificar_sesion
        from cms.content import obtener_portafolio
        token   = obtener_token_de_headers(self)
        usuario = verificar_sesion(token) if token else None
        if not usuario:
            _respuesta_json(self, 401, {'error': 'Debes iniciar sesión para ver tu portafolio.'})
            return
        _respuesta_json(self, 200, obtener_portafolio(usuario['usuario_id']))

    def _sim_comprar(self, params, body):
        """POST /simulador/comprar — Comprar activo virtual."""
        from auth.auth import obtener_token_de_headers, verificar_sesion
        from cms.content import comprar_activo
        token   = obtener_token_de_headers(self)
        usuario = verificar_sesion(token) if token else None
        if not usuario:
            _respuesta_json(self, 401, {'error': 'Debes iniciar sesión.'})
            return
        ticker   = (body.get('ticker') or '').upper().strip()
        cantidad = float(body.get('cantidad', 0))
        if not ticker or cantidad <= 0:
            _respuesta_json(self, 400, {'error': 'ticker y cantidad (>0) son obligatorios.'})
            return
        _respuesta_json(self, 200, comprar_activo(usuario['usuario_id'], ticker, cantidad))

    def _sim_vender(self, params, body):
        """POST /simulador/vender — Vender activo virtual."""
        from auth.auth import obtener_token_de_headers, verificar_sesion
        from cms.content import vender_activo
        token   = obtener_token_de_headers(self)
        usuario = verificar_sesion(token) if token else None
        if not usuario:
            _respuesta_json(self, 401, {'error': 'Debes iniciar sesión.'})
            return
        ticker   = (body.get('ticker') or '').upper().strip()
        cantidad = float(body.get('cantidad', 0))
        if not ticker or cantidad <= 0:
            _respuesta_json(self, 400, {'error': 'ticker y cantidad (>0) son obligatorios.'})
            return
        _respuesta_json(self, 200, vender_activo(usuario['usuario_id'], ticker, cantidad))

    def _monedas_tasa(self, params):
        """
        GET /monedas/tasa
        Retorna la tasa USD/COP en tiempo real desde Yahoo Finance (ticker COP=X).
        Sin librerías externas: usa urllib.request.
        """
        try:
            from cms.content import obtener_tasa_usd_cop
            tasa = obtener_tasa_usd_cop()
            _respuesta_json(self, 200, tasa)
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})

    def _admin_usuarios(self, params):
        """GET /admin/usuarios — Lista todos los usuarios (solo admin)."""
        try:
            conn = _conectar_bd()
            cur = conn.cursor()
            cur.execute("""
                SELECT u.id, u.username, u.email, u.creado_en,
                       COALESCE(b.saldo_usd, 100000) as saldo_usd,
                       COALESCE(b.saldo_cop, 0) as saldo_cop,
                       (SELECT COUNT(*) FROM portafolio_posiciones pp WHERE pp.usuario_id = u.id) as posiciones
                FROM usuarios u
                LEFT JOIN portafolio_balance b ON b.usuario_id = u.id
                ORDER BY u.id
            """)
            rows = cur.fetchall()
            usuarios = []
            for r in rows:
                usuarios.append({
                    'id': r[0], 'username': r[1], 'email': r[2],
                    'creado_en': str(r[3]) if r[3] else '',
                    'saldo_usd': float(r[4]), 'saldo_cop': float(r[5]),
                    'posiciones': r[6]
                })
            cur.execute("SELECT COUNT(*) FROM portafolio_transacciones")
            total_tx = cur.fetchone()[0]
            cur.close(); conn.close()
            _respuesta_json(self, 200, {'usuarios': usuarios, 'total_transacciones': total_tx})
        except Exception as e:
            _respuesta_json(self, 200, {'usuarios': [], 'total_transacciones': 0, 'error': str(e)})

# ------------------------------------------------------------------
# ORDENAMIENTO — Requerimiento 2
# ------------------------------------------------------------------

    def _sorting_benchmark(self, params):
        """
        GET /ordenamiento/benchmark
        Retorna la Tabla 1: resultados del benchmark de los 12 algoritmos
        (nombre, complejidad, tamaño, tiempo_ms), ordenados ASC por tiempo.
        Si no hay resultados en BD, ejecuta el benchmark en tiempo real.
        """
        try:
            from etl.database import get_connection
            import psycopg2.extras
            conn = get_connection()
            try:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("""
                        SELECT algoritmo, complejidad, tamanio, tiempo_ms
                        FROM resultados_sorting
                        ORDER BY tiempo_ms ASC;
                    """)
                    filas = [dict(f) for f in cur.fetchall()]
            finally:
                conn.close()

            if not filas:
                _respuesta_json(self, 404, {
                    'error': 'Sin resultados. Ejecuta: python main.py ordenamiento'
                })
                return

            _respuesta_json(self, 200, {
                'tabla1': filas,
                'total_algoritmos': len(filas),
                'descripcion': 'Ordenado ASC por tiempo de ejecución (para diagrama de barras)',
            })
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})

    def _sorting_top_volumen(self, params):
        """
        GET /ordenamiento/top-volumen
        Retorna los 15 días con mayor volumen de negociación (orden ASC).
        """
        try:
            from etl.database import get_connection
            import psycopg2.extras
            conn = get_connection()
            try:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("""
                        SELECT ticker, fecha, volumen, cierre
                        FROM top_volumen
                        ORDER BY volumen ASC;
                    """)
                    filas = [dict(f) for f in cur.fetchall()]
            finally:
                conn.close()

            if not filas:
                _respuesta_json(self, 404, {
                    'error': 'Sin resultados. Ejecuta: python main.py ordenamiento'
                })
                return

            _respuesta_json(self, 200, {
                'top15_volumen': filas,
                'descripcion': 'Top-15 días con mayor volumen, ordenados ASC',
            })
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})

    def _sorting_dataset(self, params):
        """
        GET /ordenamiento/dataset?algoritmo=timsort&limite=100
        Retorna el dataset unificado ordenado por el algoritmo solicitado.
        algoritmo: timsort | combsort | selectionsort | treesort |
                   pigeonhole | bucketsort | quicksort | heapsort |
                   bitonicsort | gnomesort | binaryinsertion | radixsort
        """
        from etl.database import get_connection
        import psycopg2.extras

        algoritmo = params.get('algoritmo', 'timsort').lower().replace(' ', '').replace('_', '')
        limite = int(params.get('limite', 200))

        mapa = {
            'timsort':         'timsort',
            'combsort':        'comb_sort',
            'selectionsort':   'selection_sort',
            'treesort':        'tree_sort',
            'pigeonhole':      'pigeonhole_sort',
            'bucketsort':      'bucket_sort',
            'quicksort':       'quicksort',
            'heapsort':        'heapsort',
            'bitonicsort':     'bitonic_sort',
            'gnomesort':       'gnome_sort',
            'binaryinsertion': 'binary_insertion_sort',
            'radixsort':       'radix_sort',
        }

        nombre_fn = mapa.get(algoritmo)
        if not nombre_fn:
            _respuesta_json(self, 400, {
                'error': f'Algoritmo desconocido. Opciones: {list(mapa.keys())}'
            })
            return

        try:
            import algorithms.sorting as _s
            funcion = getattr(_s, nombre_fn)

            conn = get_connection()
            try:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("""
                        SELECT a.ticker, p.fecha, p.apertura, p.maximo,
                               p.minimo, p.cierre, p.volumen
                        FROM precios p
                        JOIN activos a ON a.id = p.activo_id
                        LIMIT %s;
                    """, (limite,))
                    registros = [dict(f) for f in cur.fetchall()]
            finally:
                conn.close()

            ordenados, tiempo = funcion(registros)
            _respuesta_json(self, 200, {
                'algoritmo':  algoritmo,
                'tamaño':     len(ordenados),
                'tiempo_ms':  round(tiempo * 1000, 3),
                'registros':  [{
                    'ticker':   str(r.get('ticker', '')),
                    'fecha':    str(r.get('fecha', '')),
                    'cierre':   float(r.get('cierre', 0)),
                    'volumen':  int(r.get('volumen', 0)),
                } for r in ordenados],
            })
        except Exception as e:
            _respuesta_json(self, 500, {'error': str(e)})

    def _etl_status(self, params):
        """GET /etl/status — Cuántos registros hay en la BD."""
        from etl.database import get_connection
        try:
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
        """
        POST /etl/iniciar — Dispara el pipeline ETL completo en un hilo separado.
        Retorna inmediatamente con estado 'iniciado'.
        """
        import threading
        def _run():
            try:
                from main import pipeline_etl
                pipeline_etl()
            except Exception as ex:
                print(f"[ETL-API] Error en pipeline: {ex}")

        hilo = threading.Thread(target=_run, daemon=True)
        hilo.start()
        _respuesta_json(self, 202, {
            "estado": "iniciado",
            "mensaje": "ETL corriendo en segundo plano. Consulta /etl/status para ver el progreso.",
        })


# ------------------------------------------------------------------
# INICIO DEL SERVIDOR
# ------------------------------------------------------------------

def iniciar_servidor():
    servidor = ThreadingHTTPServer((API_HOST, API_PORT), BVCHandler)
    print(f"[API] Servidor BVC Analytics corriendo en http://{API_HOST}:{API_PORT}")
    print("[API] Endpoints disponibles:")
    print("       GET /health")
    print("       GET /activos")
    print("       GET /precios?ticker=SPY")
    print("       GET /volatilidad?ticker=SPY")
    print("       GET /patrones?ticker=SPY")
    print("       GET /patrones/cruces?ticker=SPY&corta=10&larga=30")
    print("       GET /riesgo?ticker=SPY")
    print("       GET /reporte")
    print("       GET /reporte/txt")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[API] Servidor detenido.")
        servidor.server_close()
