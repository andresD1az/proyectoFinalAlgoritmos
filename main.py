"""
main.py — Punto de entrada principal del proyecto BVC Analytics
Requerimientos: ETL | Similitud | Patrones/Volatilidad | Dashboard | Despliegue
"""

import time
from config import ACTIVOS, TICKERS
from etl.descargador import descargar_todos
from etl.limpieza    import limpiar_dataset
from etl.database   import (
    insertar_activos,
    obtener_id_activo,
    obtener_precios,
    insertar_precios_lote,
    guardar_similitud,
    guardar_volatilidad,
)

def pipeline_etl():
    """Req 1 — Descarga → Limpieza → Carga en PostgreSQL."""
    print("=" * 60)
    print("  BVC ANALYTICS — Pipeline ETL (Requerimiento 1)")
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
    print("\n✅ Pipeline ETL completado.")

def pipeline_similitud():
    """Req 2 — Calcula los 4 algoritmos de similitud para todos los pares."""
    from algoritmos.similitud import matriz_similitud
    from etl.database import obtener_series_alineadas

    print("\n" + "=" * 60)
    print("  BVC ANALYTICS — Pipeline de Similitud (Requerimiento 2)")
    print("=" * 60)

    print("\n[SIMILITUD] Alineando series por fecha exacta (intersección de calendarios)...")
    series = obtener_series_alineadas(TICKERS)

    if len(series) < 2:
        print("[SIMILITUD] Se necesitan al menos 2 activos con datos.")
        return

    # Reportar cobertura
    longitudes = {t: len(v) for t, v in series.items()}
    dias_comunes = list(longitudes.values())[0] if longitudes else 0
    print(f"[SIMILITUD] {len(series)} activos alineados — {dias_comunes} días comunes.")
    for ticker, n in longitudes.items():
        print(f"[SIMILITUD]   {ticker}: {n} días")

    for algo in ["pearson", "coseno", "euclidiana", "dtw"]:
        print(f"\n[SIMILITUD] Calculando {algo.upper()} ...")
        if algo == "dtw":
            print("[SIMILITUD] DTW es O(n²) — puede tardar varios minutos...")
        resultados = matriz_similitud(series, algoritmo=algo)
        for r in resultados:
            a1_id = obtener_id_activo(r["ticker1"])
            a2_id = obtener_id_activo(r["ticker2"])
            if a1_id and a2_id:
                guardar_similitud(a1_id, a2_id, r["algoritmo"], r["valor"])
        print(f"[SIMILITUD] {algo}: {len(resultados)} pares calculados y guardados.")

    print("\n✅ Pipeline de Similitud completado.")

def pipeline_volatilidad():
    """Req 3 — Calcula volatilidad y métricas de riesgo para todos los activos."""
    from algoritmos.volatilidad import calcular_volatilidad
    from config import DIAS_VOLATILIDAD

    print("\n" + "=" * 60)
    print("  BVC ANALYTICS — Pipeline de Volatilidad (Requerimiento 3)")
    print("=" * 60)

    for ticker in TICKERS:
        filas = obtener_precios(ticker, "cierre")
        if not filas:
            print(f"[VOL] {ticker}: sin datos, saltando.")
            continue
        precios   = [float(f["cierre"]) for f in filas]
        fechas    = [str(f["fecha"])    for f in filas]
        activo_id = obtener_id_activo(ticker)
        volatilidades = calcular_volatilidad(precios, DIAS_VOLATILIDAD)
        for vol in volatilidades:
            idx = vol["indice"]
            if idx < len(fechas):
                guardar_volatilidad(
                    activo_id, fechas[idx],
                    vol["ventana_dias"],
                    vol["volatilidad_anualizada"],
                    vol["retorno_medio"],
                )
        print(f"[VOL] {ticker}: {len(volatilidades)} ventanas guardadas.")

    print("\n✅ Pipeline de Volatilidad completado.")

def pipeline_ordenamiento():
    """
    Req 1 (parte visual) — Ejecuta los 12 algoritmos de ordenamiento sobre el
    dataset unificado. Genera Tabla 1 (tamaño + tiempo) y top-15 por volumen.
    """
    from algoritmos.ordenamiento import ejecutar_benchmark, top15_mayor_volumen
    from etl.database import get_connection
    import psycopg2.extras

    print("\n" + "=" * 60)
    print("  BVC ANALYTICS — Pipeline de Ordenamiento")
    print("=" * 60)

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

    if not registros:
        print("[SORT] Sin datos. Ejecuta primero: python main.py etl")
        return

    print(f"[SORT] Dataset: {len(registros)} registros.")
    print("\n[SORT] Ejecutando benchmark de 12 algoritmos...")
    resultados = ejecutar_benchmark(registros)

    print("\n" + "=" * 70)
    print("  TABLA 1 — Algoritmos de Ordenamiento")
    print(f"  {'#':<3} {'Algoritmo':<25} {'Complejidad':<15} {'Tamaño':>8} {'Tiempo (ms)':>12}")
    print("-" * 70)
    for i, r in enumerate(resultados, 1):
        print(f"  {i:<3} {r['algoritmo']:<25} {r['complejidad']:<15} "
              f"{r['tamaño']:>8} {r['tiempo_ms']:>12.3f}")
    print("=" * 70)

    print("\n[SORT] Calculando top-15 días con mayor volumen...")
    top15 = top15_mayor_volumen(registros)

    # Persistir en BD
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS resultados_sorting (
                    id SERIAL PRIMARY KEY, algoritmo VARCHAR(50),
                    complejidad VARCHAR(20), tamanio INTEGER,
                    tiempo_ms NUMERIC(12,6), calculado_en TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("DELETE FROM resultados_sorting;")
            for r in resultados:
                cur.execute(
                    "INSERT INTO resultados_sorting (algoritmo, complejidad, tamanio, tiempo_ms) "
                    "VALUES (%s, %s, %s, %s);",
                    (r["algoritmo"], r["complejidad"], r["tamaño"], r["tiempo_ms"])
                )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS top_volumen (
                    id SERIAL PRIMARY KEY, ticker VARCHAR(10), fecha DATE,
                    volumen BIGINT, cierre NUMERIC(12,4), calculado_en TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("DELETE FROM top_volumen;")
            for r in top15:
                cur.execute(
                    "INSERT INTO top_volumen (ticker, fecha, volumen, cierre) VALUES (%s,%s,%s,%s);",
                    (r.get("ticker"), r.get("fecha"), int(r.get("volumen", 0)), float(r.get("cierre", 0)))
                )
        conn.commit()
        print("[SORT] Resultados guardados en BD.")
    except Exception as e:
        print(f"[SORT] Error al guardar: {e}")
        conn.rollback()
    finally:
        conn.close()

    print("\n✅ Pipeline de Ordenamiento completado.")
    return resultados, top15

def iniciar_api():
    """Req 5 — Inicia el servidor HTTP."""
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
    modos = ["etl", "similitud", "volatilidad", "ordenamiento", "api", "todo"]

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
        print("\n⏳ Pausa de 2s...")
        time.sleep(2)
        pipeline_similitud()
        pipeline_volatilidad()
        pipeline_ordenamiento()
        print("\n⏳ Iniciando API en 3 segundos...")
        time.sleep(3)
        iniciar_api()
    else:
        print(f"Modo desconocido: '{modo}'")
        print(f"Modos disponibles: {modos}")
