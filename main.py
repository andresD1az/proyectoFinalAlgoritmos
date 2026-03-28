"""
main.py — Punto de entrada principal del proyecto BVC Analytics
Requerimientos: ETL | Similitud | Patrones/Volatilidad | Dashboard | Despliegue
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
    from algorithms.similarity import matriz_similitud

    print("\n" + "=" * 60)
    print("  BVC ANALYTICS — Pipeline de Similitud (Requerimiento 2)")
    print("=" * 60)

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
    from algorithms.volatility import calcular_volatilidad
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
    modos = ["etl", "similitud", "volatilidad", "api", "todo"]

    if modo == "etl":
        pipeline_etl()
    elif modo == "similitud":
        pipeline_similitud()
    elif modo == "volatilidad":
        pipeline_volatilidad()
    elif modo == "api":
        iniciar_api()
    elif modo == "todo":
        pipeline_etl()
        print("\n⏳ Pausa de 2s...")
        time.sleep(2)
        pipeline_similitud()
        pipeline_volatilidad()
        print("\n⏳ Iniciando API en 3 segundos...")
        time.sleep(3)
        iniciar_api()
    else:
        print(f"Modo desconocido: '{modo}'")
        print(f"Modos disponibles: {modos}")
