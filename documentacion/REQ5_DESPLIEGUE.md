# Requerimiento 5 — Despliegue y Documentación Técnica

## Enunciado

> Finalmente, el proyecto deberá estar desplegado como una aplicación web funcional.

---

## Archivos Involucrados

| Archivo | Función |
|---|---|
| `render.yaml` | Configuración de despliegue en Render |
| `docker-compose.local.yml` | Entorno de desarrollo local |
| `Dockerfile.local` | Imagen Docker para desarrollo |
| `deploy.sh` | Script de despliegue |
| `api/server.py` | Servidor HTTP (http.server stdlib) |
| `requirements.txt` | Dependencias del proyecto |
| `.env.example` | Plantilla de variables de entorno |

---

## Servidor HTTP (`api/server.py`)

Implementado con `http.server.ThreadingHTTPServer` de la biblioteca estándar de Python. Sin Flask, FastAPI, Django ni ningún framework externo.

### Arquitectura del Servidor

```python
class BVCHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        ruta = urllib.parse.urlparse(self.path).path
        params = _parsear_query(self.path)
        rutas = {
            "/":                     self._app,
            "/activos":              self._activos,
            "/precios":              self._precios,
            "/similitud":            self._similitud,
            "/correlacion/matriz":   self._correlacion_matriz,
            "/patrones":             self._patrones,
            "/riesgo/clasificacion": self._clasificacion_riesgo,
            "/reporte":              self._reporte,
            "/reporte/txt":          self._reporte_txt,
            "/ordenamiento/benchmark":   self._sorting_benchmark,
            "/ordenamiento/top-volumen": self._sorting_top_volumen,
            "/monedas/tasa":         self._monedas_tasa,
            ...
        }
        handler = rutas.get(ruta)
        if handler:
            handler(params)

servidor = ThreadingHTTPServer((API_HOST, API_PORT), BVCHandler)
servidor.serve_forever()
```

**Concurrencia:** `ThreadingHTTPServer` crea un hilo por petición. Adecuado para carga académica y demostraciones.

**CORS:** Todas las respuestas incluyen `Access-Control-Allow-Origin: *` para permitir acceso desde el frontend.

---

## Despliegue en Render (Producción)

### Configuración (`render.yaml`)

```yaml
services:
  - type: web
    name: bvc-analytics
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py api
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: bvc-db
          property: connectionString
      - key: PORT
        value: 8001

databases:
  - name: bvc-db
    databaseName: bvc_analytics
    user: bvc_user
    plan: free
```

### Variables de Entorno en Render

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | URL de conexión PostgreSQL (inyectada automáticamente) |
| `PORT` | Puerto del servidor (asignado por Render) |

### Parseo de DATABASE_URL

El sistema parsea `DATABASE_URL` manualmente sin dependencias externas:

```python
import re
_m = re.match(
    r"postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)",
    _DATABASE_URL
)
if _m:
    DB_CONFIG = {
        "host":     _m.group(3),
        "port":     int(_m.group(4)),
        "dbname":   _m.group(5),
        "user":     _m.group(1),
        "password": _m.group(2),
    }
```

---

## Desarrollo Local con Docker

### Configuración (`docker-compose.local.yml`)

```yaml
services:
  bvc_db:
    image: postgres:15-alpine
    container_name: bvc_db
    environment:
      POSTGRES_DB: bvc_analytics
      POSTGRES_USER: bvc_user
      POSTGRES_PASSWORD: changeme
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bvc_user -d bvc_analytics"]
      interval: 5s
      timeout: 5s
      retries: 5

  bvc_api:
    build:
      context: .
      dockerfile: Dockerfile.local
    container_name: bvc_api
    command: python main.py api
    ports:
      - "8001:8001"
    depends_on:
      bvc_db:
        condition: service_healthy
    environment:
      DB_HOST: bvc_db
      DB_PORT: 5432
      DB_NAME: bvc_analytics
      DB_USER: bvc_user
      DB_PASSWORD: changeme
```

### Comandos de Desarrollo

```bash
# Levantar el entorno
docker compose -f docker-compose.local.yml up --build -d

# Verificar estado
docker ps --filter "name=bvc"

# Ejecutar pipelines
docker exec bvc_api python main.py etl
docker exec bvc_api python main.py similitud
docker exec bvc_api python main.py volatilidad
docker exec bvc_api python main.py ordenamiento

# Ver logs
docker logs bvc_api -f

# Detener
docker compose -f docker-compose.local.yml down
```

---

## Dependencias (`requirements.txt`)

```
psycopg2-binary==2.9.9
```

**Política de dependencias:** Solo drivers de conectividad. Cero librerías algorítmicas, de análisis de datos o de visualización.

**Prohibido por el enunciado:**
- `pandas`, `numpy`, `scipy`, `sklearn`
- `yfinance`, `pandas_datareader`
- `flask`, `fastapi`, `django`
- `matplotlib`, `plotly`, `bokeh`

**Permitido por el enunciado:**
- Librerías estándar para solicitudes HTTP (`urllib`)
- Lectura de archivos CSV o JSON (`json`, `csv`)
- Manejo de estructuras de datos básicas
- Drivers de conectividad a base de datos (`psycopg2`)

---

## Variables de Entorno (`.env.example`)

```bash
# Base de datos (desarrollo local)
DB_HOST=bvc_db
DB_PORT=5432
DB_NAME=bvc_analytics
DB_USER=bvc_user
DB_PASSWORD=changeme

# O usar DATABASE_URL (producción Render)
# DATABASE_URL=postgresql://user:password@host:5432/dbname

# Servidor HTTP
API_HOST=0.0.0.0
API_PORT=8001
```

---

## Reproducibilidad

El sistema cumple el requisito de reproducibilidad del enunciado:

> "Un evaluador debe poder ejecutar el proyecto siguiendo la documentación proporcionada y obtener resultados equivalentes sin necesidad de ajustes manuales."

**Pasos para reproducir desde cero:**

```bash
# 1. Clonar el repositorio
git clone <url>
cd proyectoFinalAlgoritmos

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Levantar el entorno
docker compose -f docker-compose.local.yml up --build -d

# 4. Ejecutar todos los pipelines
docker exec bvc_api python main.py etl
docker exec bvc_api python main.py similitud
docker exec bvc_api python main.py volatilidad
docker exec bvc_api python main.py ordenamiento

# 5. Acceder al dashboard
# http://localhost:8001
```

**Nota:** Los datos se descargan en tiempo real desde Yahoo Finance. Los resultados pueden variar ligeramente según la fecha de ejecución, pero el proceso es completamente automatizado y reproducible.
