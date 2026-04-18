# =============================================================
# etl/database.py — Capa de Acceso a Datos (psycopg2 puro, sin ORM)
# =============================================================

import psycopg2
import psycopg2.extras
from config import DB_CONFIG, ACTIVOS


def get_connection():
    """Retorna una conexión activa a PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG)


# ------------------------------------------------------------------
# ACTIVOS
# ------------------------------------------------------------------

def insertar_activos():
    """
    Puebla la tabla `activos` con los 20 instrumentos definidos en config.py.
    Usa ON CONFLICT DO NOTHING para ser idempotente (se puede ejecutar varias veces).
    """
    sql = """
        INSERT INTO activos (ticker, nombre, tipo, mercado)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (ticker) DO NOTHING;
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for activo in ACTIVOS:
                cur.execute(sql, (
                    activo["ticker"],
                    activo["nombre"],
                    activo["tipo"],
                    activo["mercado"]
                ))
        conn.commit()
        print(f"[DB] {len(ACTIVOS)} activos registrados correctamente.")
    finally:
        conn.close()


def obtener_id_activo(ticker: str) -> int | None:
    """Retorna el ID de un activo dado su ticker, o None si no existe."""
    sql = "SELECT id FROM activos WHERE ticker = %s;"
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (ticker,))
            fila = cur.fetchone()
            return fila[0] if fila else None
    finally:
        conn.close()


# ------------------------------------------------------------------
# PRECIOS
# ------------------------------------------------------------------

def insertar_precios_lote(activo_id: int, filas: list[dict]):
    """
    Inserta múltiples filas de precios OHLCV en lote.
    `filas` es una lista de dicts con keys: fecha, apertura, maximo, minimo, cierre, volumen
    Usa ON CONFLICT DO NOTHING para no duplicar días ya guardados.
    """
    sql = """
        INSERT INTO precios (activo_id, fecha, apertura, maximo, minimo, cierre, volumen)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (activo_id, fecha) DO NOTHING;
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            datos = [
                (activo_id,
                 f["fecha"],
                 f.get("apertura"),
                 f.get("maximo"),
                 f.get("minimo"),
                 f["cierre"],
                 f.get("volumen"))
                for f in filas
            ]
            cur.executemany(sql, datos)
        conn.commit()
        print(f"[DB] {len(filas)} filas insertadas para activo_id={activo_id}.")
    finally:
        conn.close()


def obtener_precios(ticker: str, columna: str = "cierre") -> list[dict]:
    """
    Retorna los precios históricos de un activo ordenados por fecha ASC.
    columna: 'cierre' | 'apertura' | 'maximo' | 'minimo'
    """
    columnas_validas = {"cierre", "apertura", "maximo", "minimo", "volumen"}
    if columna not in columnas_validas:
        raise ValueError(f"Columna '{columna}' no válida. Usa: {columnas_validas}")

    sql = f"""
        SELECT p.fecha, p.{columna}
        FROM precios p
        JOIN activos a ON a.id = p.activo_id
        WHERE a.ticker = %s
        ORDER BY p.fecha ASC;
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, (ticker,))
            return [dict(fila) for fila in cur.fetchall()]
    finally:
        conn.close()


# ------------------------------------------------------------------
# SIMILITUD
# ------------------------------------------------------------------

def guardar_similitud(activo1_id: int, activo2_id: int, algoritmo: str, valor: float):
    sql = """
        INSERT INTO resultados_similitud (activo1_id, activo2_id, algoritmo, valor)
        VALUES (%s, %s, %s, %s);
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (activo1_id, activo2_id, algoritmo, valor))
        conn.commit()
    finally:
        conn.close()


def obtener_similitudes(algoritmo: str) -> list[dict]:
    sql = """
        SELECT a1.ticker AS ticker1, a2.ticker AS ticker2,
               r.algoritmo, r.valor, r.calculado_en
        FROM resultados_similitud r
        JOIN activos a1 ON a1.id = r.activo1_id
        JOIN activos a2 ON a2.id = r.activo2_id
        WHERE r.algoritmo = %s
        ORDER BY r.valor DESC;
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, (algoritmo,))
            return [dict(fila) for fila in cur.fetchall()]
    finally:
        conn.close()


# ------------------------------------------------------------------
# VOLATILIDAD
# ------------------------------------------------------------------

def guardar_volatilidad(activo_id: int, fecha: str, ventana: int,
                         volatilidad: float, retorno_medio: float):
    sql = """
        INSERT INTO resultados_volatilidad
            (activo_id, fecha, ventana_dias, volatilidad, retorno_medio)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (activo_id, fecha, ventana_dias) DO UPDATE
            SET volatilidad = EXCLUDED.volatilidad,
                retorno_medio = EXCLUDED.retorno_medio;
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (activo_id, fecha, ventana, volatilidad, retorno_medio))
        conn.commit()
    finally:
        conn.close()


def obtener_ohlcv_completo(ticker: str) -> list[dict]:
    """
    Retorna todos los campos OHLCV para un ticker (para gráfico de velas).
    """
    sql = """
        SELECT p.fecha, p.apertura, p.maximo, p.minimo, p.cierre, p.volumen
        FROM precios p
        JOIN activos a ON a.id = p.activo_id
        WHERE a.ticker = %s
        ORDER BY p.fecha ASC;
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, (ticker,))
            return [dict(f) for f in cur.fetchall()]
    finally:
        conn.close()


def obtener_todos_cierres() -> dict[str, list]:
    """
    Retorna {ticker: [precios_cierre]} para todos los activos.
    Usado para calcular la matriz de correlación completa.
    """
    from config import TICKERS
    resultado = {}
    for ticker in TICKERS:
        filas = obtener_precios(ticker, "cierre")
        if filas:
            resultado[ticker] = [float(f["cierre"]) for f in filas]
    return resultado


def obtener_series_alineadas(tickers: list[str]) -> dict[str, list[float]]:
    """
    Retorna series de cierre alineadas por fecha exacta para una lista de tickers.

    PROBLEMA QUE RESUELVE:
        Dos activos pueden tener diferente número de días de negociación
        (ej: un ETF colombiano puede tener festivos distintos a un ETF de NYSE).
        Comparar posición a posición sin alinear introduce ruido en los algoritmos
        de similitud porque se estarían comparando días distintos.

    ALGORITMO — Complejidad: O(n * k)
        n = número de tickers
        k = número de fechas en la intersección

        1. Obtener todas las fechas de cada ticker como conjuntos
        2. Calcular la intersección de todas las fechas (fechas comunes)
        3. Para cada ticker, filtrar solo los precios de esas fechas
        4. Ordenar por fecha ASC para garantizar alineación temporal

    RESULTADO:
        Todos los tickers retornados tienen exactamente la misma longitud
        y cada posición i corresponde al mismo día calendario.

    Args:
        tickers: Lista de tickers a alinear

    Returns:
        {ticker: [precios_cierre]} donde todas las listas tienen igual longitud
        y están alineadas por fecha exacta. Tickers sin datos se omiten.
    """
    # Paso 1: obtener {ticker: {fecha: cierre}} para todos
    datos_por_ticker = {}
    for ticker in tickers:
        filas = obtener_precios(ticker, "cierre")
        if filas:
            datos_por_ticker[ticker] = {
                str(f["fecha"]): float(f["cierre"]) for f in filas
            }

    if not datos_por_ticker:
        return {}

    # Paso 2: intersección de fechas — solo días en que TODOS los activos tienen dato
    conjuntos = [set(d.keys()) for d in datos_por_ticker.values()]
    fechas_comunes = conjuntos[0]
    for s in conjuntos[1:]:
        fechas_comunes = fechas_comunes & s  # intersección

    if not fechas_comunes:
        return {}

    # Paso 3: ordenar fechas ASC (strings ISO son comparables lexicográficamente)
    fechas_ordenadas = sorted(fechas_comunes)

    # Paso 4: construir series alineadas
    resultado = {}
    for ticker, mapa in datos_por_ticker.items():
        resultado[ticker] = [mapa[fecha] for fecha in fechas_ordenadas]

    return resultado


# ------------------------------------------------------------------
# INICIALIZACIÓN DEL SCHEMA (usado en el build de Render)
# ------------------------------------------------------------------

def init_schema():
    """
    Crea todas las tablas necesarias si no existen.
    Equivalente a ejecutar database/init.sql pero desde Python.
    Se llama durante el buildCommand en Render.
    """
    sql = """
        CREATE TABLE IF NOT EXISTS activos (
            id      SERIAL PRIMARY KEY,
            ticker  VARCHAR(10) UNIQUE NOT NULL,
            nombre  VARCHAR(100),
            tipo    VARCHAR(20),
            mercado VARCHAR(20)
        );

        CREATE TABLE IF NOT EXISTS precios (
            id        SERIAL PRIMARY KEY,
            activo_id INTEGER REFERENCES activos(id),
            fecha     DATE NOT NULL,
            apertura  NUMERIC(12,4),
            maximo    NUMERIC(12,4),
            minimo    NUMERIC(12,4),
            cierre    NUMERIC(12,4) NOT NULL,
            volumen   BIGINT,
            UNIQUE (activo_id, fecha)
        );

        CREATE TABLE IF NOT EXISTS resultados_similitud (
            id         SERIAL PRIMARY KEY,
            activo1_id INTEGER REFERENCES activos(id),
            activo2_id INTEGER REFERENCES activos(id),
            algoritmo  VARCHAR(30),
            valor      NUMERIC(10,6),
            calculado_en TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS resultados_volatilidad (
            id           SERIAL PRIMARY KEY,
            activo_id    INTEGER REFERENCES activos(id),
            fecha        DATE,
            ventana_dias INTEGER,
            volatilidad  NUMERIC(12,6),
            retorno_medio NUMERIC(12,6),
            calculado_en TIMESTAMP DEFAULT NOW(),
            UNIQUE (activo_id, fecha, ventana_dias)
        );

        CREATE TABLE IF NOT EXISTS resultados_sorting (
            id           SERIAL PRIMARY KEY,
            algoritmo    VARCHAR(50),
            complejidad  VARCHAR(20),
            tamanio      INTEGER,
            tiempo_ms    NUMERIC(12,6),
            calculado_en TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS top_volumen (
            id           SERIAL PRIMARY KEY,
            ticker       VARCHAR(10),
            fecha        DATE,
            volumen      BIGINT,
            cierre       NUMERIC(12,4),
            calculado_en TIMESTAMP DEFAULT NOW()
        );
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("[DB] Schema inicializado correctamente.")
    except Exception as e:
        print(f"[DB] Error al inicializar schema: {e}")
        conn.rollback()
    finally:
        conn.close()
