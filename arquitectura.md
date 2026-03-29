# Documento de Arquitectura  BVC Analytics
## Modelo C4 (Context, Containers, Components, Code)

**Universidad del Quindío**
**Programa de Ingeniería de Sistemas y Computación**
**Análisis de Algoritmos  Proyecto Final**

---

## Nivel 1  Diagrama de Contexto (System Context)

El nivel de contexto muestra el sistema como una caja negra y sus relaciones con usuarios y sistemas externos.

```
─────────────────────────────────────┐
│                        CONTEXTO DEL SISTEMA                         │
└─────────────────────────────────────────────────────────────────────┘

         [Estudiante / Evaluador]
                  │
                  │  Accede al dashboard via navegador web
                  │  Ejecuta pipelines via línea de comandos
                  ▼
    ┌─────────────────────────────┐
    │                             │
    │       BVC ANALYTICS         │  Sistema de análisis financiero
    │                             │  cuantitativo sobre datos históricos
    │  Plataforma web de análisis │  de la BVC y ETFs globales.
    │  financiero algorítmico     │  Implementa 28 algoritmos desde cero.
    │                             │
    └──────────┬──────────────────┘
               │
               │  Peticiones HTTP (urllib.request)
               │  Descarga datos OHLCV históricos
               ▼
    ┌─────────────────────────────┐
    │                             │
    │     Yahoo Finance API v8    │  Sistema externo
    │                             │  URL: query1.finance.yahoo.com
    │  Fuente de datos históricos │  Protocolo: HTTPS / JSON
    │  de precios OHLCV           │  Sin autenticación requerida
    │                             │
    └─────────────────────────────┘
```

**Actores:**
- **Estudiante / Evaluador:** accede al dashboard web para visualizar resultados, ejecuta los pipelines desde la terminal para poblar la base de datos.
- **Yahoo Finance API v8:** sistema externo que provee los datos históricos de precios OHLCV para los 20 activos del portafolio.

---

## Nivel 2 — Diagrama de Contenedores (Containers)

El nivel de contenedores muestra las unidades desplegables del sistema y cómo se comunican.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BVC ANALYTICS                               │
│                                                                     │
│  ┌──────────────────────┐         ┌──────────────────────────────┐  │
│  │                      │         │                              │  │
│  │   DASHBOARD WEB      │  HTTP   │      SERVIDOR API            │  │
│  │                      │◄───────►│                              │  │
│  │  interfaz/index.html │  fetch  │  api/server.py               │  │
│  │                      │         │  Python 3.11 stdlib          │  │
│  │  HTML5 + CSS3 + JS   │         │  http.server                 │  │
│  │  SVG + Canvas API    │         │  Puerto: 8001                │  │
│  │                      │         │                              │  │
│  └──────────────────────┘         └──────────────┬───────────────┘  │
│                                                  │                  │
│                                                  │ psycopg2         │
│                                                  │ SQL queries      │
│                                                  ▼                  │
│                                   ┌──────────────────────────────┐  │
│                                   │                              │  │
│                                   │    BASE DE DATOS             │  │
│                                   │                              │  │
│                                   │  PostgreSQL 15               │  │
│                                   │  Puerto: 5432                │  │
│                                   │                              │  │
│                                   │  Tablas:                     │  │
│                                   │  activos, precios,           │  │
│                                   │  resultados_similitud,       │  │
│                                   │  resultados_volatilidad,     │  │
│                                   │  resultados_sorting,         │  │
│                                   │  top_volumen                 │  │
│                                   │                              │  │
│                                   └─  
                                                                     
     
                     PIPELINE DE DATOS (ETL)                       
                                                                   
    main.py  Orquestador                                          
    Ejecutado manualmente: python main.py [etl|similitud|...]      
                                                                   
     
                                                                     

```

**Contenedores:**

| Contenedor | Tecnología | Responsabilidad |
|---|---|---|
| Dashboard Web | HTML5 + CSS3 + JS vanilla | Interfaz visual del usuario. Consume la API via fetch(). |
| Servidor API | Python 3.11, http.server | Expone 18 endpoints REST. Sirve el dashboard. |
| Base de Datos | PostgreSQL 15 | Persiste activos, precios OHLCV y resultados algorítmicos. |
| Pipeline ETL | Python 3.11 | Descarga, limpia y carga datos. Se ejecuta desde la terminal. |

**Comunicaciones:**
- Dashboard  API: HTTP/JSON via `fetch()` del navegador
- API  BD: TCP/IP via psycopg2 (driver PostgreSQL)
- Pipeline  Yahoo Finance: HTTPS via `urllib.request`
- Pipeline  BD: TCP/IP via psycopg2

---

## Nivel 3  Diagrama de Componentes (Components)

El nivel de componentes desglosa cada contenedor en sus módulos internos.

### Componentes del Servidor API (`api/server.py`)

```

                        SERVIDOR API                                 
                    api/server.py                                    
                                                                     
       
     Router GET         Router POST       Helpers HTTP        
                                                              
    do_GET()           do_POST()          _respuesta_json()   
    18 rutas           1 ruta             _parsear_query()    
       
                                                                   
      
                       HANDLERS DE ENDPOINTS                       
                                                                 │  │
│    │  _app()              → sirve interfaz/index.html            │  │
│    │  _health()           → estado del sistema                   │  │
│    │  _etl_status()       → registros en BD                      │  │
│    │  _etl_iniciar()      → dispara ETL en hilo separado         │  │
│    │  _activos()          → lista de 20 activos                  │  │
│    │  _precios()          → precios históricos por ticker        │  │
│    │  _ohlcv()            → datos OHLCV para velas               │  │
│    │  _similitud()        → resultados de similitud              │  │
│    │  _correlacion_matriz()→ matriz 20x20 para heatmap           │  │
│    │  _patrones()         → ventana deslizante en tiempo real    │  │
│    │  _cruces_medias()    → Golden/Death Cross                   │  │
│    │  _clasificacion_riesgo()→ ranking de riesgo                 │  │
│    │  _sorting_benchmark()→ Tabla 1 desde BD                     │  │
│    │  _sorting_top_volumen()→ Top-15 mayor volumen               │  │
│    │  _reporte()          → reporte JSON                         │  │
│    │  _reporte_txt()      → reporte texto plano                  │  │
│    │  _monedas_tasa()     → tasa USD/COP en tiempo real          │  │
│    │                                                             │  │
│    └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Componentes del Pipeline ETL

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PIPELINE ETL                                 │
│                         main.py                                     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      ORQUESTADOR                             │   │
│  │                                                              │   │
│  │  pipeline_etl()          → Req 1: descarga + limpieza + BD   │   │
│  │  pipeline_similitud()    → Req 2: 4 algoritmos × 190 pares      
    pipeline_volatilidad()   Req 3: VaR, Sharpe, Drawdown         
    pipeline_ordenamiento()  Req 1: benchmark 12 algoritmos       
    iniciar_api()            Req 5: inicia servidor HTTP          
                                                                   
     
                                                                 
                                                                 
       
   DESCARGADOR     LIMPIEZA       DATABASE     ALGORITMOS  
                                                           
  descargador.py  limpieza.py    database.py   algoritmos  
                                               /           
  urllib.request Interpolación  psycopg2                   
  Yahoo Finance  lineal O(n)    INSERT lote    ordenam.    
  3 reintentos   Z-Score O(n)   ON CONFLICT    similitud   
                                DO NOTHING     patrones    
     volatilid.  
                                                        

```

### Componentes del Módulo de Algoritmos

```

                      MÓDULO DE ALGORITMOS                           
                         algoritmos/                                 
                                                                     
     
                     ordenamiento.py                               
                                                                   
    _clave()               criterio compuesto (fecha, cierre)     
    timsort()              O(n log n)  runs + merge              
    comb_sort()            O(n log n)  gap factor 1.3            
    selection_sort()       O(n)  mínimo en cada iteración       
    tree_sort()            O(n log n)  BST + inorden             
    pigeonhole_sort()      O(n+k)  palomares por fecha           
    bucket_sort()          O(n+k)  cubetas normalizadas          
    quicksort()            O(n log n)  mediana de tres           
    heapsort()             O(n log n)  max-heap                  
    bitonic_sort()         O(n logn)  secuencias bitónicas      
    gnome_sort()           O(n)  índice sube y baja             
    binary_insertion_sort() O(n)  búsqueda binaria              
    radix_sort()           O(nk)  LSD 8 dígitos                  
    ejecutar_benchmark()   mide tiempos con perf_counter()        
    top15_mayor_volumen()  HeapSort manual por volumen            
     
                                                                     
     
                      similitud.py                                 
                                                                   
    normalizar_minmax()        escala [0,1] para Euclidiana       
    distancia_euclidiana()     O(n)  Σ(Aᵢ-Bᵢ)                
    correlacion_pearson()      O(n)  cov(A,B)/(σAσB)           
    similitud_coseno()         O(n)  (AB)/(AB)            
    dtw()                      O(n)  prog. dinámica             
    matriz_similitud()         O(nm)  190 pares                
     
                                                                     
     
                      patrones.py                                  
                                                                   
    detectar_patrones()        O(nk)  ventana deslizante        
    _clasificar_segmento()     O(k)  alza/baja/rebote/neutro     
    detectar_picos_valles()    O(n)  máximos/mínimos locales     
    media_movil_simple()       O(nk)  SMA manual                
    detectar_cruces_medias()   O(n)  Golden/Death Cross          
     
                                                                     
     
                     volatilidad.py                                
                                                                   
    calcular_retornos_log()    O(n)  ln(Pᵢ/Pᵢ)               
    calcular_volatilidad()     O(n)  std muestral  252         
    calcular_max_drawdown()    O(n)  caída pico a valle          
    calcular_var_historico()   O(n log n)  percentil 5%          
    calcular_sharpe()          O(n)  retorno/riesgo              
    resumen_riesgo()           agrega todas las métricas          
     

```

---

## Nivel 4  Diagrama de Código (Code)

El nivel de código muestra las estructuras de datos y relaciones clave dentro de los componentes más importantes.

### Modelo de Datos  PostgreSQL

```
activos                          precios
            
id        SERIAL PK          id        SERIAL PK
ticker    VARCHAR(10)           activo_id INTEGER FK 
nombre    VARCHAR(100)          fecha     DATE
tipo      VARCHAR(20)           apertura  NUMERIC(12,4)
mercado   VARCHAR(20)           maximo    NUMERIC(12,4)
                                minimo    NUMERIC(12,4)
                                cierre    NUMERIC(12,4)
                                volumen   BIGINT
                                UNIQUE(activo_id, fecha)
                          
resultados_similitud            resultados_volatilidad
          
id         SERIAL PK            id           SERIAL PK
activo1_id INTEGER FK       activo_id    INTEGER FK 
activo2_id INTEGER FK       fecha        DATE
algoritmo  VARCHAR(30)           ventana_dias INTEGER
valor      NUMERIC(10,6)         volatilidad  NUMERIC(12,6)
calculado_en TIMESTAMP           retorno_medio NUMERIC(12,6)
                                 UNIQUE(activo_id, fecha, ventana_dias)

resultados_sorting               top_volumen
           
id          SERIAL PK            id      SERIAL PK
algoritmo   VARCHAR(50)          ticker  VARCHAR(10)
complejidad VARCHAR(20)          fecha   DATE
tamanio     INTEGER              volumen BIGINT
tiempo_ms   NUMERIC(12,6)        cierre  NUMERIC(12,4)
calculado_en TIMESTAMP           calculado_en TIMESTAMP
```

### Estructura de un Registro OHLCV (dict Python)

```python
# Estructura interna usada en todo el pipeline
registro = {
    "ticker":   "SPY",          # str   símbolo del activo
    "fecha":    "2024-01-15",   # str   formato ISO 8601
    "apertura": 478.25,         # float  precio de apertura
    "maximo":   481.50,         # float  precio máximo del día
    "minimo":   476.80,         # float  precio mínimo del día
    "cierre":   480.10,         # float  precio de cierre ajustado
    "volumen":  52341200,       # int    volumen de negociación
}
```

### Clave de Ordenamiento Compuesta

```python
# algoritmos/ordenamiento.py  función _clave()
# Criterio 1: fecha ASC (str ISO es comparable lexicográficamente)
# Criterio 2: cierre ASC (desempate cuando dos registros tienen la misma fecha)

def _clave(registro: dict) -> tuple:
    return (
        str(registro.get("fecha", "")),      # "2024-01-15" < "2024-01-16"
        float(registro.get("cierre", 0.0))   # 480.10 < 481.50
    )
```

### Flujo de Datos en el Pipeline ETL

```python
# main.py  pipeline_etl()

# PASO 1: Descarga (etl/descargador.py)
datasets_crudos = descargar_todos()
#  {"SPY": [{"fecha": "2020-01-02", "cierre": 324.87, ...}, ...], ...}

# PASO 2: Limpieza (etl/limpieza.py)
filas_limpias = limpiar_dataset(filas_crudas)
#  Rellena None con interpolación lineal
#  Elimina cierres <= 0
#  Rellena volumen nulo con 0

# PASO 3: Persistencia (etl/database.py)
insertar_precios_lote(activo_id, filas_limpias)
#  INSERT INTO precios ... ON CONFLICT DO NOTHING
```

### Recurrencia DTW (Dynamic Time Warping)

```
Matriz de programación dinámica (n+1)  (m+1):

         B[0]  B[1]  B[2]  ...  B[m]
A[0]  [  0    inf   inf   ...  inf  ]
A[1]  [ inf    ?     ?    ...   ?   ]
A[2]  [ inf    ?     ?    ...   ?   ]
...
A[n]  [ inf    ?     ?    ...  DTW  ]

Recurrencia:
  costo = |A[i] - B[j]|
  matriz[i][j] = costo + min(
      matriz[i-1][j],     inserción
      matriz[i][j-1],     eliminación
      matriz[i-1][j-1]    coincidencia
  )

Ventana Sakoe-Chiba (10%):
  Solo se calculan celdas donde |i - j| <= window
  Reduce O(n) a O(nw) donde w = 0.1  n
```

---

## Resumen de Decisiones Arquitectónicas

| Decisión | Alternativa descartada | Justificación |
|---|---|---|
| `http.server` stdlib | Flask, FastAPI | Restricción del enunciado: sin frameworks |
| `urllib.request` stdlib | requests, httpx | Restricción: sin librerías de descarga |
| PostgreSQL 15 | SQLite, MongoDB | Soporte NUMERIC(12,4), concurrencia, consultas analíticas |
| Retornos logarítmicos | Retornos simples | Aditividad temporal, distribución más normal |
| Ventana 5,000 para benchmark | Dataset completo (25,579) | Algoritmos O(n) tardarían horas con n completo |
| Sakoe-Chiba 10% en DTW | DTW sin restricción | Reduce O(n) a O(nk) sin pérdida significativa de precisión |
| Corrección de Bessel (k-1) | Varianza poblacional (k) | Estimador insesgado de la varianza muestral |
| Normalización Min-Max en Euclidiana | Sin normalización | Activos con escalas muy distintas (EC: $5-15 vs SPY: $300-500) |

---

## Despliegue

### Entorno de Desarrollo (Docker Compose)

```

              docker-compose.local.yml               
                                                     
         
      bvc_api                 bvc_db             
                                                 
    Python 3.11       PostgreSQL 15          
    Puerto: 8001          Puerto: 5432           
    Dockerfile.local      Volumen persistente    
         
                                                     
  Red interna: bvc_network                           
  DB_HOST=bvc_db (nombre del servicio Docker)        

```

### Entorno de Producción (Render)

```

                    render.yaml                      
                                                     
     
    bvc-analytics-api (Web Service)                
                                                   
    Runtime: Python 3.11 nativo (sin Docker)       
    Build: pip install -r requirements.txt         
    Start: python main.py api                      
    Puerto: $PORT (asignado por Render)            
    URL: bvc-analytics-api.onrender.com            
     
                     DATABASE_URL                    
                                                     
     
    bvc-analytics-db (PostgreSQL)                  
                                                   
    Plan: Free (90 días)                           
    DATABASE_URL inyectada automáticamente         
     

```

---

*Universidad del Quindío  Análisis de Algoritmos  2025*