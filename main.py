"""
main.py — Punto de entrada principal del proyecto BVC Analytics
Orquesta los módulos ETL, Algoritmos y API
"""

import time
from config import ACTIVOS, TICKERS
from etl.downloader import descargar_todos
from etl.cleaner    import limpiar_dataset
from etl.database   import (
    insertar_activos,
    obtener_id_activo,
    obtener_precios,
    insertar_precios_lote,
    guardar_similitud,
    guardar_volatilidad,
)


def pipeline_etl():
    """Ejecuta el pipeline completo: Descarga → Limpieza → Carga en PostgreSQL."""
    print("=" * 60)
    print("  BVC ANALYTICS — Pipeline ETL")
    print("=" * 60)

    print("\n[1/3] Registrando activos en la base de datos...")
    insertar_activos()

    print("\n[2/3] Descargando datos históricos (5 años) ...")
    datasets_crudos = descargar_todos(pausa_segundos=1.0)

    print("\n[3/3] Limpiando e insertando en PostgreSQL ...")
    for ticker, filas_crudas in datasets_crudos.items():
        filas_limpias = limpiar_dataset(filas_crudas)
        activo_id = obtener_id_activo(ticker)
        if activo_id and filas_limpias:
            insertar_precios_lote(activo_id, filas_limpias)
        else:
            print(f"[ETL] Saltando {ticker} — sin ID o sin datos limpios.")

    print("\n✅ Pipeline ETL completado exitosamente.")


def pipeline_similitud():
    """Calcula los 4 algoritmos de similitud para todos los pares de activos."""
    from algorithms.similarity import matriz_similitud

    print("\n" + "=" * 60)
    print("  BVC ANALYTICS — Pipeline de Similitud")
    print("=" * 60)

    # Cargar las series de cierre para todos los activos
    series = {}
    for ticker in TICKERS:
        filas = obtener_precios(ticker, "cierre")
        if filas:
            series[ticker] = [float(f["cierre"]) for f in filas]
            print(f"[SIMILITUD] {ticker}: {len(series[ticker])} precios cargados.")
        else:
            print(f"[SIMILITUD] {ticker}: sin datos en BD, saltando.")

    if len(series) < 2:
        print("[SIMILITUD] Se necesitan al menos 2 activos con datos.")
        return

    # Ejecutar los 4 algoritmos
    algoritmos = ["pearson", "coseno", "euclidiana", "dtw"]
    for algo in algoritmos:
        print(f"\n[SIMILITUD] Calculando {algo.upper()} ...")
        # DTW es O(n²) — avisamos que tarda más
        if algo == "dtw":
            print("[SIMILITUD] DTW es O(n²) — esto puede tardar varios minutos...")

        resultados = matriz_similitud(series, algoritmo=algo)
        for r in resultados:
            a1_id = obtener_id_activo(r["ticker1"])
            a2_id = obtener_id_activo(r["ticker2"])
            if a1_id and a2_id:
                guardar_similitud(a1_id, a2_id, r["algoritmo"], r["valor"])

        print(f"[SIMILITUD] {algo}: {len(resultados)} pares calculados y guardados.")

    print("\n✅ Pipeline de Similitud completado.")


def pipeline_volatilidad():
    """Calcula volatilidad y métricas de riesgo para todos los activos."""
    from algorithms.volatility import calcular_volatilidad
    from config import DIAS_VOLATILIDAD

    print("\n" + "=" * 60)
    print("  BVC ANALYTICS — Pipeline de Volatilidad")
    print("=" * 60)

    for ticker in TICKERS:
        filas = obtener_precios(ticker, "cierre")
        if not filas:
            print(f"[VOL] {ticker}: sin datos, saltando.")
            continue

        precios = [float(f["cierre"]) for f in filas]
        fechas  = [str(f["fecha"])    for f in filas]
        activo_id = obtener_id_activo(ticker)

        volatilidades = calcular_volatilidad(precios, DIAS_VOLATILIDAD)
        for i, vol in enumerate(volatilidades):
            idx = vol["indice"]
            if idx < len(fechas):
                guardar_volatilidad(
                    activo_id,
                    fechas[idx],
                    vol["ventana_dias"],
                    vol["volatilidad_anualizada"],
                    vol["retorno_medio"],
                )

        print(f"[VOL] {ticker}: {len(volatilidades)} ventanas de volatilidad guardadas.")

    print("\n✅ Pipeline de Volatilidad completado.")


def pipeline_ordenamiento():
    """
    Requerimiento 2 — Ejecuta los 12 algoritmos de ordenamiento sobre el
    dataset unificado (todos los activos, ordenados por fecha ASC y cierre ASC).
    Genera la Tabla 1 con tamaño y tiempo, y calcula el top-15 por volumen.
    """
    from algorithms.sorting import ejecutar_benchmark, top15_mayor_volumen
    from etl.database import get_connection
    import psycopg2.extras

    print("\n" + "=" * 60)
    print("  BVC ANALYTICS — Pipeline de Ordenamiento (Req. 2)")
    print("=" * 60)

    # Cargar dataset unificado desde BD
    print("\n[SORT] Cargando dataset unificado desde PostgreSQL...")
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT a.ticker, p.fecha, p.apertura, p.maximo,
                       p.minimo, p.cierre, p.volumen
                FROM precios p
                JOIN activos a ON a.id = p.activo_id
                ORDER BY p.fecha ASC, p.cierre ASC;
            """)
            registros = [dict(f) for f in cur.fetchall()]
    finally:
        conn.close()

    print(f"[SORT] Dataset cargado: {len(registros)} registros totales.")

    if not registros:
        print("[SORT] Sin datos en BD. Ejecuta primero: python main.py etl")
        return

    # Ejecutar benchmark de los 12 algoritmos
    print("\n[SORT] Ejecutando benchmark de 12 algoritmos...")
    resultados = ejecutar_benchmark(registros)

    # Imprimir Tabla 1
    print("\n" + "=" * 70)
    print(f"  TABLA 1 — Análisis de Algoritmos de Ordenamiento")
    print(f"  Dataset: {len(registros)} registros")
    print("=" * 70)
    print(f"  {'#':<3} {'Algoritmo':<25} {'Complejidad':<15} {'Tamaño':>8} {'Tiempo (ms)':>12}")
    print("-" * 70)
    for i, r in enumerate(resultados, 1):
        print(f"  {i:<3} {r['algoritmo']:<25} {r['complejidad']:<15} "
              f"{r['tamaño']:>8} {r['tiempo_ms']:>12.3f}")
    print("=" * 70)

    # Top-15 días con mayor volumen
    print("\n[SORT] Calculando top-15 días con mayor volumen...")
    top15 = top15_mayor_volumen(registros)
    print("\n  TOP-15 DÍAS CON MAYOR VOLUMEN DE NEGOCIACIÓN (ASC)")
    print(f"  {'#':<3} {'Ticker':<8} {'Fecha':<12} {'Volumen':>15} {'Cierre':>10}")
    print("-" * 55)
    for i, r in enumerate(top15, 1):
        print(f"  {i:<3} {str(r.get('ticker','')):<8} {str(r.get('fecha','')):<12} "
              f"{int(r.get('volumen',0)):>15,} {float(r.get('cierre',0)):>10.2f}")
    print("=" * 55)

    # Guardar resultados en BD para la API
    _guardar_resultados_sorting(resultados, top15)
    print("\n✅ Pipeline de Ordenamiento completado.")
    return resultados, top15


def _guardar_resultados_sorting(resultados: list, top15: list):
    """Persiste los resultados del benchmark en PostgreSQL."""
    from etl.database import get_connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Tabla de benchmark
            cur.execute("""
                CREATE TABLE IF NOT EXISTS resultados_sorting (
                    id SERIAL PRIMARY KEY,
                    algoritmo VARCHAR(50),
                    complejidad VARCHAR(20),
                    tamanio INTEGER,
                    tiempo_ms NUMERIC(12,6),
                    calculado_en TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("DELETE FROM resultados_sorting;")
            for r in resultados:
                cur.execute(
                    "INSERT INTO resultados_sorting (algoritmo, complejidad, tamanio, tiempo_ms) "
                    "VALUES (%s, %s, %s, %s);",
                    (r["algoritmo"], r["complejidad"], r["tamaño"], r["tiempo_ms"])
                )
            # Tabla top-15 volumen
            cur.execute("""
                CREATE TABLE IF NOT EXISTS top_volumen (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(10),
                    fecha DATE,
                    volumen BIGINT,
                    cierre NUMERIC(12,4),
                    calculado_en TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("DELETE FROM top_volumen;")
            for r in top15:
                cur.execute(
                    "INSERT INTO top_volumen (ticker, fecha, volumen, cierre) "
                    "VALUES (%s, %s, %s, %s);",
                    (r.get("ticker"), r.get("fecha"),
                     int(r.get("volumen", 0)), float(r.get("cierre", 0)))
                )
        conn.commit()
        print("[SORT] Resultados guardados en BD (resultados_sorting, top_volumen).")
    except Exception as e:
        print(f"[SORT] Advertencia al guardar en BD: {e}")
        conn.rollback()
    finally:
        conn.close()


def iniciar_api():
    """Inicia el servidor HTTP de la API (http.server stdlib)."""
    # Inicializar schema al arrancar (idempotente, no falla si ya existe)
    try:
        from etl.database import init_schema
        init_schema()
    except Exception as e:
        print(f"[API] Advertencia al inicializar schema: {e}")
    from api.server import iniciar_servidor
    iniciar_servidor()


if __name__ == "__main__":
    import sys

    modo = sys.argv[1] if len(sys.argv) > 1 else "api"

    modos_disponibles = ["etl", "similitud", "volatilidad", "ordenamiento", "api", "todo"]

    if modo == "etl":
        pipeline_etl()

    elif modo == "similitud":
        pipeline_similitud()

    elif modo == "volatilidad":
        pipeline_volatilidad()

    elif modo == "ordenamiento":
        pipeline_ordenamiento()

    elif modo == "api":
        iniciar_api()

    elif modo == "todo":
        pipeline_etl()
        print("\n⏳ Pausa de 2s antes de los algoritmos...")
        time.sleep(2)
        pipeline_similitud()
        pipeline_volatilidad()
        pipeline_ordenamiento()
        print("\n⏳ Iniciando API en 3 segundos...")
        time.sleep(3)
        iniciar_api()

    else:
        print(f"Modo desconocido: '{modo}'")
        print(f"Modos disponibles: {modos_disponibles}")
