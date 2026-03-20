# 📡 Módulo 4: API HTTP & Reportes

## Responsabilidad

Exponer los resultados de los algoritmos a través de un servidor HTTP construido **exclusivamente con la biblioteca estándar de Python** (`http.server`), sin ningún framework web externo.

---

## 📁 Archivos del Módulo

| Archivo | Responsabilidad |
|---------|----------------|
| `api/server.py` | Servidor HTTP, enrutador manual, handlers de endpoints |
| `reports/generator.py` | Generación de reporte técnico en JSON |

---

## 🚀 Tecnología: `http.server` (stdlib)

**Por qué no se usa Flask/FastAPI:**
- Son frameworks que abstraen el protocolo HTTP
- Al usar `BaseHTTPRequestHandler` directamente, se implementa el protocolo desde el nivel de transporte
- Se evidencia el entendimiento de HTTP: métodos, headers, códigos de estado, CORS

### Componentes clave de `http.server` usados:

| Clase / Función | Propósito |
|----------------|-----------|
| `HTTPServer` | Crea el socket TCP y acepta conexiones |
| `BaseHTTPRequestHandler` | Maneja cada petición HTTP entrante |
| `serve_forever()` | Loop bloqueante que mantiene el servidor activo |
| `send_response(código)` | Envía la línea de estado HTTP |
| `send_header(clave, valor)` | Envía headers HTTP |
| `wfile.write(bytes)` | Escribe el cuerpo de la respuesta |

---

## 📡 Endpoints Disponibles

### `GET /health`
Verifica que el servidor esté corriendo.

**Respuesta:**
```json
{
  "estado": "ok",
  "servicio": "BVC Analytics API",
  "version": "1.0.0"
}
```

---

### `GET /activos`
Retorna el catálogo de los 20 instrumentos financieros configurados.

**Respuesta:**
```json
{
  "activos": [
    {"ticker": "EC", "nombre": "Ecopetrol S.A.", "tipo": "accion", "mercado": "NYSE"},
    ...
  ],
  "total": 20
}
```

---

### `GET /precios?ticker={TICKER}&columna={COLUMNA}`

| Parámetro | Requerido | Valores válidos | Default |
|-----------|-----------|----------------|---------|
| `ticker`  | ✅ Sí | EC, SPY, QQQ, ... | — |
| `columna` | ❌ No | cierre, apertura, maximo, minimo | `cierre` |

**Respuesta:**
```json
{
  "ticker": "SPY",
  "columna": "cierre",
  "registros": 1258,
  "datos": [
    {"fecha": "2021-02-22", "cierre": 388.50},
    ...
  ]
}
```

---

### `GET /similitud?algoritmo={ALGORITMO}`

| Parámetro | Valores válidos |
|-----------|----------------|
| `algoritmo` | `euclidiana`, `pearson`, `coseno`, `dtw` |

**Respuesta:**
```json
{
  "algoritmo": "pearson",
  "resultados": [
    {"ticker1": "SPY", "ticker2": "QQQ", "valor": 0.97, ...},
    ...
  ]
}
```

---

### `GET /volatilidad?ticker={TICKER}`
Retorna los últimos 100 registros de volatilidad calculada para un activo.

---

### `GET /patrones?ticker={TICKER}&patron={PATRON}`
Retorna los patrones detectados. El parámetro `patron` es opcional para filtrar.

**Valores de patrón:** `3_dias_alza`, `5_dias_alza`, `3_dias_baja`, `5_dias_baja`, etc.

---

### `GET /reporte`
Genera y retorna el reporte técnico completo del análisis.

---

## 🔒 Códigos de Estado HTTP Usados

| Código | Significado | Cuándo se retorna |
|--------|-------------|-------------------|
| `200` | OK | Petición exitosa |
| `204` | No Content | Preflight CORS |
| `400` | Bad Request | Parámetro faltante o inválido |
| `404` | Not Found | Ruta no existe |
| `500` | Internal Server Error | Error en BD o algoritmo |

---

## 🌐 Configuración CORS

Se implementa CORS básico manualmente añadiendo el header:
```
Access-Control-Allow-Origin: *
```
Esto permite que un frontend (aunque sea `localhost:3000`) consuma la API sin errores de navegador.

---

## ▶️ Cómo ejecutar solo la API

```bash
# En Docker
docker-compose exec bvc_api python main.py api

# Local
python main.py api
```

**Salida esperada:**
```
[API] Servidor BVC Analytics corriendo en http://0.0.0.0:8001
[API] Endpoints disponibles:
       GET /health
       GET /activos
       ...
```

---

## 🧪 Pruebas rápidas con curl

```bash
# Health check
curl http://localhost:8001/health

# Lista de activos
curl http://localhost:8001/activos

# Precios históricos de Ecopetrol
curl "http://localhost:8001/precios?ticker=EC&columna=cierre"

# Similitud por Pearson
curl "http://localhost:8001/similitud?algoritmo=pearson"

# Volatilidad del S&P500
curl "http://localhost:8001/volatilidad?ticker=SPY"
```
