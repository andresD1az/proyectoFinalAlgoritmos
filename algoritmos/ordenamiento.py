"""
algoritmoas/sorting.py — 12 Algoritmos de Ordenamiento
Implementados DESDE CERO — SIN sorted(), SIN .sort(), SIN librerías externas

Requerimiento 2 — Análisis de Algoritmos BVC
Cada algoritmo ordena una lista de registros (dicts) con criterio compuesto:
  1. Primario:   fecha de cotización (str 'YYYY-MM-DD') — ASC
  2. Secundario: precio de cierre (float)               — ASC

Complejidades implementadas:
  1.  TimSort              O(n log n)
  2.  Comb Sort            O(n log n)
  3.  Selection Sort       O(n²)
  4.  Tree Sort            O(n log n)
  5.  Pigeonhole Sort      O(n + k)
  6.  Bucket Sort          O(n + k)
  7.  QuickSort            O(n log n) promedio
  8.  HeapSort             O(n log n)
  9.  Bitonic Sort         O(n log² n)
  10. Gnome Sort           O(n²)
  11. Binary Insertion Sort O(n²)
  12. RadixSort            O(nk)
"""

import time
import math

# ──────────────────────────────────────────────────────────────────
# CLAVE DE COMPARACIÓN COMPARTIDA
# ──────────────────────────────────────────────────────────────────

def _clave(registro: dict) -> tuple:
    """
    Extrae la clave de ordenamiento de un registro OHLCV.
    Criterio 1: fecha (str ISO → comparable lexicográficamente)
    Criterio 2: cierre (float)
    """
    return (str(registro.get("fecha", "")), float(registro.get("cierre", 0.0)))

def _menor_o_igual(a: dict, b: dict) -> bool:
    return _clave(a) <= _clave(b)

def _menor(a: dict, b: dict) -> bool:
    return _clave(a) < _clave(b)

# 1. TIMSORT  —  O(n log n)                               #
_TIM_RUN = 32   # Tamaño mínimo de run para inserción

def _insertion_run(arr: list, izq: int, der: int):
    """Insertion sort sobre arr[izq..der] (in-place). Usado internamente por TimSort."""
    for i in range(izq + 1, der + 1):
        temp = arr[i]
        j = i - 1
        while j >= izq and _menor(temp, arr[j]):
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = temp

def _merge_tim(arr: list, izq: int, mid: int, der: int):
    """Merge de dos mitades ordenadas arr[izq..mid] y arr[mid+1..der]."""
    izq_parte = arr[izq: mid + 1]
    der_parte = arr[mid + 1: der + 1]
    i = j = 0
    k = izq
    while i < len(izq_parte) and j < len(der_parte):
        if _menor_o_igual(izq_parte[i], der_parte[j]):
            arr[k] = izq_parte[i]; i += 1
        else:
            arr[k] = der_parte[j]; j += 1
        k += 1
    while i < len(izq_parte):
        arr[k] = izq_parte[i]; i += 1; k += 1
    while j < len(der_parte):
        arr[k] = der_parte[j]; j += 1; k += 1

def timsort(registros: list) -> tuple[list, float]:
    """
    TimSort — O(n log n)
    Divide el arreglo en 'runs' de tamaño RUN, los ordena con Insertion Sort
    y luego los fusiona con Merge Sort. Es el algoritmo de Python internamente,
    pero aquí se implementa de forma explícita.

    Returns: (lista_ordenada, tiempo_segundos)
    """
    arr = list(registros)
    n = len(arr)
    inicio = time.perf_counter()

    # Paso 1: ordenar cada run con insertion sort
    for i in range(0, n, _TIM_RUN):
        _insertion_run(arr, i, min(i + _TIM_RUN - 1, n - 1))

    # Paso 2: merge progresivo duplicando el tamaño del run
    size = _TIM_RUN
    while size < n:
        for izq in range(0, n, 2 * size):
            mid = min(izq + size - 1, n - 1)
            der = min(izq + 2 * size - 1, n - 1)
            if mid < der:
                _merge_tim(arr, izq, mid, der)
        size *= 2

    return arr, time.perf_counter() - inicio

# 2. COMB SORT  —  O(n log n)                             #

def comb_sort(registros: list) -> tuple[list, float]:
    """
    Comb Sort — O(n log n)
    Mejora de Bubble Sort: en lugar de comparar elementos adyacentes,
    usa una brecha (gap) que se reduce con factor 1.3 en cada pasada.
    Elimina 'tortugas' (valores pequeños al final) eficientemente.

    gap_inicial = n
    gap = floor(gap / 1.3)   hasta que gap == 1 (Bubble Sort final)
    """
    arr = list(registros)
    n = len(arr)
    inicio = time.perf_counter()

    gap = n
    factor = 1.3
    ordenado = False

    while not ordenado:
        gap = int(gap / factor)
        if gap <= 1:
            gap = 1
            ordenado = True

        i = 0
        while i + gap < n:
            if _menor(arr[i + gap], arr[i]):
                arr[i], arr[i + gap] = arr[i + gap], arr[i]
                ordenado = False
            i += 1

    return arr, time.perf_counter() - inicio

# 3. SELECTION SORT  —  O(n²)                             #

def selection_sort(registros: list) -> tuple[list, float]:
    """
    Selection Sort — O(n²)
    En cada iteración i, encuentra el mínimo en arr[i..n-1]
    y lo intercambia con arr[i].
    Siempre hace exactamente n*(n-1)/2 comparaciones.
    """
    arr = list(registros)
    n = len(arr)
    inicio = time.perf_counter()

    for i in range(n):
        idx_min = i
        for j in range(i + 1, n):
            if _menor(arr[j], arr[idx_min]):
                idx_min = j
        arr[i], arr[idx_min] = arr[idx_min], arr[i]

    return arr, time.perf_counter() - inicio

# 4. TREE SORT  —  O(n log n)                             #

class _NodoBST:
    """Nodo de un Árbol Binario de Búsqueda (BST)."""
    __slots__ = ("registro", "izq", "der")
    def __init__(self, registro):
        self.registro = registro
        self.izq = None
        self.der = None

def _bst_insertar(raiz: _NodoBST, registro: dict) -> _NodoBST:
    if raiz is None:
        return _NodoBST(registro)
    if _menor(registro, raiz.registro):
        raiz.izq = _bst_insertar(raiz.izq, registro)
    else:
        raiz.der = _bst_insertar(raiz.der, registro)
    return raiz

def _bst_inorden(nodo: _NodoBST, resultado: list):
    """Recorrido in-orden (izq → raíz → der) produce la lista ordenada."""
    if nodo is None:
        return
    _bst_inorden(nodo.izq, resultado)
    resultado.append(nodo.registro)
    _bst_inorden(nodo.der, resultado)

def tree_sort(registros: list) -> tuple[list, float]:
    """
    Tree Sort — O(n log n) promedio, O(n²) peor caso (árbol degenerado)
    Inserta cada elemento en un BST y luego extrae en recorrido in-orden.
    El recorrido in-orden de un BST produce los elementos en orden ascendente.
    """
    inicio = time.perf_counter()
    raiz = None
    for r in registros:
        raiz = _bst_insertar(raiz, r)
    resultado = []
    _bst_inorden(raiz, resultado)
    return resultado, time.perf_counter() - inicio

# 5. PIGEONHOLE SORT  —  O(n + k)                         #

def pigeonhole_sort(registros: list) -> tuple[list, float]:
    """
    Pigeonhole Sort — O(n + k), donde k = rango de valores
    Funciona sobre la clave entera de fecha (YYYYMMDD).
    Crea 'palomares' (cubetas) para cada valor entero en [min, max]
    y distribuye los registros en ellos.

    Restricción: eficiente solo cuando k ≈ n (rango pequeño).
    Para fechas bursátiles de 5 años: k ≈ 1826 días, n ≈ 20*1260 = 25200.
    """
    inicio = time.perf_counter()
    if not registros:
        return [], time.perf_counter() - inicio

    # Convertir fecha a entero YYYYMMDD para indexar palomares
    def fecha_int(r):
        return int(str(r.get("fecha", "19700101")).replace("-", ""))

    min_val = fecha_int(min(registros, key=fecha_int))
    max_val = fecha_int(max(registros, key=fecha_int))
    rango = max_val - min_val + 1

    # Crear palomares
    palomares = [[] for _ in range(rango)]
    for r in registros:
        idx = fecha_int(r) - min_val
        palomares[idx].append(r)

    # Dentro de cada palomar, ordenar por cierre (criterio secundario)
    resultado = []
    for palomar in palomares:
        if len(palomar) > 1:
            # Insertion sort dentro del palomar (pocos elementos)
            for i in range(1, len(palomar)):
                temp = palomar[i]
                j = i - 1
                while j >= 0 and float(palomar[j].get("cierre", 0)) > float(temp.get("cierre", 0)):
                    palomar[j + 1] = palomar[j]
                    j -= 1
                palomar[j + 1] = temp
        resultado.extend(palomar)

    return resultado, time.perf_counter() - inicio

# 6. BUCKET SORT  —  O(n + k)                             #

def bucket_sort(registros: list) -> tuple[list, float]:
    """
    Bucket Sort — O(n + k) promedio
    Distribuye los registros en n cubetas según su fecha normalizada [0, 1].
    Cada cubeta se ordena internamente con Insertion Sort.
    Útil cuando los datos están distribuidos uniformemente.

    Normalización de fecha:
        fecha_norm = (fecha_int - min_fecha) / (max_fecha - min_fecha)
    """
    inicio = time.perf_counter()
    n = len(registros)
    if n == 0:
        return [], time.perf_counter() - inicio

    def fecha_int(r):
        return int(str(r.get("fecha", "19700101")).replace("-", ""))

    min_f = fecha_int(min(registros, key=fecha_int))
    max_f = fecha_int(max(registros, key=fecha_int))
    rango = max_f - min_f if max_f != min_f else 1

    # Crear n cubetas
    cubetas = [[] for _ in range(n)]
    for r in registros:
        idx = int((fecha_int(r) - min_f) / rango * (n - 1))
        idx = min(idx, n - 1)
        cubetas[idx].append(r)

    # Ordenar cada cubeta con insertion sort y concatenar
    resultado = []
    for cubeta in cubetas:
        for i in range(1, len(cubeta)):
            temp = cubeta[i]
            j = i - 1
            while j >= 0 and _menor(temp, cubeta[j]):
                cubeta[j + 1] = cubeta[j]
                j -= 1
            cubeta[j + 1] = temp
        resultado.extend(cubeta)

    return resultado, time.perf_counter() - inicio

# 7. QUICKSORT  —  O(n log n) promedio, O(n²) peor caso  #

def _quicksort_rec(arr: list, bajo: int, alto: int):
    """QuickSort recursivo con pivote mediana-de-tres."""
    if bajo < alto:
        pi = _particionar(arr, bajo, alto)
        _quicksort_rec(arr, bajo, pi - 1)
        _quicksort_rec(arr, pi + 1, alto)

def _mediana_tres(arr: list, bajo: int, alto: int) -> int:
    """Selecciona el pivote como la mediana entre primero, medio y último."""
    mid = (bajo + alto) // 2
    # Ordenar los tres candidatos
    if _menor(arr[alto], arr[bajo]):
        arr[bajo], arr[alto] = arr[alto], arr[bajo]
    if _menor(arr[mid], arr[bajo]):
        arr[bajo], arr[mid] = arr[mid], arr[bajo]
    if _menor(arr[alto], arr[mid]):
        arr[mid], arr[alto] = arr[alto], arr[mid]
    # Colocar pivote en alto-1
    arr[mid], arr[alto - 1] = arr[alto - 1], arr[mid]
    return alto - 1

def _particionar(arr: list, bajo: int, alto: int) -> int:
    """Partición de Lomuto con pivote mediana-de-tres."""
    if alto - bajo >= 2:
        pivote_idx = _mediana_tres(arr, bajo, alto)
    else:
        pivote_idx = alto
    pivote = arr[pivote_idx]
    arr[pivote_idx], arr[alto] = arr[alto], arr[pivote_idx]

    i = bajo - 1
    for j in range(bajo, alto):
        if _menor_o_igual(arr[j], pivote):
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[alto] = arr[alto], arr[i + 1]
    return i + 1

def quicksort(registros: list) -> tuple[list, float]:
    """
    QuickSort — O(n log n) promedio, O(n²) peor caso
    Divide el arreglo en torno a un pivote (mediana-de-tres).
    Elementos menores al pivote van a la izquierda, mayores a la derecha.
    Recursión sobre ambas mitades.
    """
    arr = list(registros)
    inicio = time.perf_counter()
    if len(arr) > 1:
        _quicksort_rec(arr, 0, len(arr) - 1)
    return arr, time.perf_counter() - inicio

# 8. HEAPSORT  —  O(n log n)                              #

def _heapify(arr: list, n: int, i: int):
    """
    Mantiene la propiedad de max-heap en el subárbol con raíz i.
    Nodo i tiene hijos en 2i+1 (izq) y 2i+2 (der).
    """
    mayor = i
    izq = 2 * i + 1
    der = 2 * i + 2

    if izq < n and _menor(arr[mayor], arr[izq]):
        mayor = izq
    if der < n and _menor(arr[mayor], arr[der]):
        mayor = der

    if mayor != i:
        arr[i], arr[mayor] = arr[mayor], arr[i]
        _heapify(arr, n, mayor)

def heapsort(registros: list) -> tuple[list, float]:
    """
    HeapSort — O(n log n)
    Fase 1 (Build Max-Heap): convierte el arreglo en un max-heap — O(n)
    Fase 2 (Extract): extrae el máximo n veces, colocándolo al final — O(n log n)

    Invariante: arr[0] siempre es el mayor elemento del heap activo.
    """
    arr = list(registros)
    n = len(arr)
    inicio = time.perf_counter()

    # Fase 1: construir max-heap (de abajo hacia arriba)
    for i in range(n // 2 - 1, -1, -1):
        _heapify(arr, n, i)

    # Fase 2: extraer elementos del heap uno a uno
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]   # mover raíz (máximo) al final
        _heapify(arr, i, 0)               # restaurar heap en el resto

    return arr, time.perf_counter() - inicio

# 9. BITONIC SORT  —  O(n log² n)                         #

def _bitonic_compare(arr: list, i: int, j: int, ascendente: bool):
    """Compara e intercambia arr[i] y arr[j] según la dirección."""
    if ascendente == _menor(arr[j], arr[i]):
        arr[i], arr[j] = arr[j], arr[i]

def _bitonic_merge(arr: list, bajo: int, cnt: int, ascendente: bool):
    """Fusiona una secuencia bitónica de longitud cnt a partir de bajo."""
    if cnt > 1:
        k = cnt // 2
        for i in range(bajo, bajo + k):
            _bitonic_compare(arr, i, i + k, ascendente)
        _bitonic_merge(arr, bajo, k, ascendente)
        _bitonic_merge(arr, bajo + k, k, ascendente)

def _bitonic_sort_rec(arr: list, bajo: int, cnt: int, ascendente: bool):
    """Genera y fusiona secuencias bitónicas recursivamente."""
    if cnt > 1:
        k = cnt // 2
        _bitonic_sort_rec(arr, bajo, k, True)          # primera mitad ASC
        _bitonic_sort_rec(arr, bajo + k, k, False)     # segunda mitad DESC
        _bitonic_merge(arr, bajo, cnt, ascendente)     # fusionar

def _siguiente_potencia_2(n: int) -> int:
    """Retorna la menor potencia de 2 >= n."""
    p = 1
    while p < n:
        p <<= 1
    return p

def bitonic_sort(registros: list) -> tuple[list, float]:
    """
    Bitonic Sort — O(n log² n)
    Requiere que n sea potencia de 2. Si no lo es, se rellena con
    un centinela máximo y se elimina al final.

    Genera secuencias bitónicas (primero creciente, luego decreciente)
    y las fusiona. Muy eficiente en hardware paralelo (GPU/FPGA).
    """
    inicio = time.perf_counter()
    n_orig = len(registros)
    if n_orig == 0:
        return [], time.perf_counter() - inicio

    # Rellenar hasta potencia de 2 con centinela máximo
    p2 = _siguiente_potencia_2(n_orig)
    centinela = {"fecha": "9999-99-99", "cierre": float("inf")}
    arr = list(registros) + [centinela] * (p2 - n_orig)

    _bitonic_sort_rec(arr, 0, p2, True)

    # Eliminar centinelas
    resultado = [r for r in arr if r.get("fecha") != "9999-99-99"]
    return resultado, time.perf_counter() - inicio

# 10. GNOME SORT  —  O(n²)                                #

def gnome_sort(registros: list) -> tuple[list, float]:
    """
    Gnome Sort — O(n²)
    Similar a Insertion Sort pero sin bucle interno explícito.
    El 'gnomo' avanza si el elemento actual >= anterior,
    retrocede e intercambia si es menor.

    Índice i:
      - Si arr[i] >= arr[i-1]: avanzar (i += 1)
      - Si arr[i] <  arr[i-1]: intercambiar y retroceder (i -= 1)
    """
    arr = list(registros)
    n = len(arr)
    inicio = time.perf_counter()

    i = 0
    while i < n:
        if i == 0 or _menor_o_igual(arr[i - 1], arr[i]):
            i += 1
        else:
            arr[i], arr[i - 1] = arr[i - 1], arr[i]
            i -= 1

    return arr, time.perf_counter() - inicio

# 11. BINARY INSERTION SORT  —  O(n²)                     #

def _busqueda_binaria_pos(arr: list, item: dict, izq: int, der: int) -> int:
    """
    Búsqueda binaria de la posición de inserción correcta para `item`
    en arr[izq..der]. Retorna el índice donde insertar.
    Complejidad de la búsqueda: O(log n)
    """
    while izq < der:
        mid = (izq + der) // 2
        if _menor(item, arr[mid]):
            der = mid
        else:
            izq = mid + 1
    return izq

def binary_insertion_sort(registros: list) -> tuple[list, float]:
    """
    Binary Insertion Sort — O(n²) tiempo, O(log n) comparaciones por elemento
    Mejora Insertion Sort usando búsqueda binaria para encontrar la posición
    de inserción (reduce comparaciones de O(n) a O(log n) por elemento),
    pero el desplazamiento sigue siendo O(n) → total O(n²).
    """
    arr = list(registros)
    n = len(arr)
    inicio = time.perf_counter()

    for i in range(1, n):
        temp = arr[i]
        pos = _busqueda_binaria_pos(arr, temp, 0, i)
        # Desplazar elementos para hacer espacio
        j = i
        while j > pos:
            arr[j] = arr[j - 1]
            j -= 1
        arr[pos] = temp

    return arr, time.perf_counter() - inicio

# 12. RADIX SORT  —  O(nk)                                #

def _counting_sort_por_digito(arr: list, exp: int, base: int = 10):
    """
    Counting Sort estable sobre el dígito en posición `exp` (1, 10, 100...).
    Usado como subrutina de RadixSort.
    Complejidad: O(n + base)
    """
    n = len(arr)
    salida = [None] * n
    conteo = [0] * base

    # Extraer dígito: usamos fecha como entero YYYYMMDD
    def digito(r):
        return (int(str(r.get("fecha", "19700101")).replace("-", "")) // exp) % base

    for r in arr:
        conteo[digito(r)] += 1

    # Acumular conteos (posición final de cada dígito)
    for i in range(1, base):
        conteo[i] += conteo[i - 1]

    # Construir salida de derecha a izquierda (estabilidad)
    for i in range(n - 1, -1, -1):
        d = digito(arr[i])
        conteo[d] -= 1
        salida[conteo[d]] = arr[i]

    for i in range(n):
        arr[i] = salida[i]

def radix_sort(registros: list) -> tuple[list, float]:
    """
    Radix Sort — O(nk), donde k = número de dígitos de la clave
    Ordena por la clave entera de fecha (YYYYMMDD = 8 dígitos → k=8).
    Aplica Counting Sort estable dígito a dígito, del menos al más significativo (LSD).

    Para el criterio secundario (cierre), dentro de cada fecha igual
    se aplica un paso adicional de ordenamiento por cierre.
    """
    inicio = time.perf_counter()
    arr = list(registros)
    if not arr:
        return arr, time.perf_counter() - inicio

    # Paso 1: RadixSort por fecha (8 dígitos decimales)
    for exp in [1, 10, 100, 1000, 10000, 100000, 1000000, 10000000]:
        _counting_sort_por_digito(arr, exp)

    # Paso 2: dentro de cada grupo de misma fecha, ordenar por cierre
    # (Insertion Sort sobre grupos pequeños — O(g²) donde g << n)
    i = 0
    while i < len(arr):
        j = i + 1
        while j < len(arr) and arr[j].get("fecha") == arr[i].get("fecha"):
            j += 1
        # Ordenar arr[i..j-1] por cierre
        for k in range(i + 1, j):
            temp = arr[k]
            m = k - 1
            while m >= i and float(arr[m].get("cierre", 0)) > float(temp.get("cierre", 0)):
                arr[m + 1] = arr[m]
                m -= 1
            arr[m + 1] = temp
        i = j

    return arr, time.perf_counter() - inicio

# ──────────────────────────────────────────────────────────────────
# BENCHMARK — Tabla 1 del Requerimiento 2
# ──────────────────────────────────────────────────────────────────

ALGORITMOS = [
    ("TimSort",              timsort,               "O(n log n)"),
    ("Comb Sort",            comb_sort,             "O(n log n)"),
    ("Selection Sort",       selection_sort,        "O(n²)"),
    ("Tree Sort",            tree_sort,             "O(n log n)"),
    ("Pigeonhole Sort",      pigeonhole_sort,       "O(n + k)"),
    ("Bucket Sort",          bucket_sort,           "O(n + k)"),
    ("QuickSort",            quicksort,             "O(n log n)"),
    ("HeapSort",             heapsort,              "O(n log n)"),
    ("Bitonic Sort",         bitonic_sort,          "O(n log² n)"),
    ("Gnome Sort",           gnome_sort,            "O(n²)"),
    ("Binary Insertion Sort",binary_insertion_sort, "O(n²)"),
    ("RadixSort",            radix_sort,            "O(nk)"),
]

def ejecutar_benchmark(registros: list) -> list[dict]:
    """
    Ejecuta los 12 algoritmos sobre la MISMA muestra de tamaño fijo.
    Todos usan exactamente N_BENCHMARK registros para que los tiempos
    sean comparables entre sí y reflejen la diferencia de complejidad.

    N_BENCHMARK = 5000 registros:
      - O(n log n): < 1 segundo
      - O(n²):      2-4 minutos (demostrable sin esperar horas)
    """
    N_BENCHMARK = 5000
    muestra = registros[:N_BENCHMARK]
    n = len(muestra)
    resultados = []

    for nombre, funcion, complejidad in ALGORITMOS:
        print(f"[SORT] Ejecutando {nombre} sobre {n} registros...")
        try:
            _, tiempo = funcion(muestra)
        except RecursionError:
            import sys
            sys.setrecursionlimit(max(sys.getrecursionlimit(), n * 2))
            _, tiempo = funcion(muestra)

        resultados.append({
            "algoritmo":   nombre,
            "complejidad": complejidad,
            "tamaño":      n,
            "tiempo_seg":  round(tiempo, 6),
            "tiempo_ms":   round(tiempo * 1000, 3),
        })
        print(f"[SORT]   {nombre}: {tiempo*1000:.3f} ms")

    resultados.sort(key=lambda x: x["tiempo_seg"])
    return resultados

def top15_mayor_volumen(registros: list) -> list[dict]:
    """
    Obtiene los 15 días con mayor volumen de negociación usando HeapSort.
    Ordena el dataset completo por volumen DESC y retorna los primeros 15,
    luego los reordena ASC para presentación.

    Complejidad: O(n log n)

    Returns:
        Lista de 15 registros ordenados ASC por volumen.
    """
    if not registros:
        return []

    # Crear copia con clave de volumen para HeapSort
    arr = list(registros)
    n = len(arr)

    # HeapSort por volumen DESC (max-heap)
    def _heapify_vol(a, size, i):
        mayor = i
        izq = 2 * i + 1
        der = 2 * i + 2
        if izq < size and int(a[izq].get("volumen", 0)) > int(a[mayor].get("volumen", 0)):
            mayor = izq
        if der < size and int(a[der].get("volumen", 0)) > int(a[mayor].get("volumen", 0)):
            mayor = der
        if mayor != i:
            a[i], a[mayor] = a[mayor], a[i]
            _heapify_vol(a, size, mayor)

    # Build max-heap
    for i in range(n // 2 - 1, -1, -1):
        _heapify_vol(arr, n, i)

    # Extraer los 15 mayores
    top = []
    limite = min(15, n)
    for _ in range(limite):
        top.append(arr[0])
        arr[0] = arr[n - 1]
        n -= 1
        _heapify_vol(arr, n, 0)

    # Reordenar los 15 de forma ASC por volumen (para presentación)
    for i in range(1, len(top)):
        temp = top[i]
        j = i - 1
        while j >= 0 and int(top[j].get("volumen", 0)) > int(temp.get("volumen", 0)):
            top[j + 1] = top[j]
            j -= 1
        top[j + 1] = temp

    return top
