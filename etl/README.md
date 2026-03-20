# 📥 Módulo 1: ETL Custom — Extracción, Transformación y Carga

## Responsabilidad

Descargar, limpiar y almacenar **5 años de datos OHLCV** para los 20 activos configurados (BVC ADRs + ETFs globales), usando exclusivamente herramientas de la biblioteca estándar de Python y sin librerías de extracción de datos.

---

## 📁 Archivos del Módulo

| Archivo | Responsabilidad |
|---------|----------------|
| `downloader.py` | Descarga HTTP pura vía `urllib` hacia Yahoo Finance |
| `cleaner.py` | Interpolación lineal + detección de outliers (Z-score) |
| `database.py` | CRUD sobre PostgreSQL con `psycopg2` puro (sin ORM) |

---

## 🔄 Flujo del Pipeline

```
Yahoo Finance (HTTP JSON)
        │
        ▼
  downloader.py
  ┌─────────────────────────────────────┐
  │  urllib.request → JSON raw           │
  │  Parseo manual de timestamps UNIX    │
  │  Extrae: fecha, O, H, L, C, Vol     │
  └──────────────────┬──────────────────┘
                     │  lista[dict] cruda
                     ▼
  cleaner.py
  ┌─────────────────────────────────────┐
  │  1. Ordenar por fecha (ASC)          │
  │  2. Eliminar cierres ≤ 0            │
  │  3. Interpolación Lineal (None→val) │
  │  4. Rellenar volumen nulo con 0     │
  └──────────────────┬──────────────────┘
                     │  lista[dict] limpia
                     ▼
  database.py
  ┌─────────────────────────────────────┐
  │  insertar_precios_lote()            │
  │  executemany() → ON CONFLICT IGNORE │
  └─────────────────────────────────────┘
```

---

## 🧮 Algoritmo 1: Interpolación Lineal

**Archivo:** `cleaner.py` → función `interpolar_linealmente()`

### Problema que resuelve
Yahoo Finance devuelve `null` para días festivos o sin negociación. Estos huecos deben rellenarse para que los algoritmos de similitud puedan comparar series de igual longitud.

### Fórmula matemática

Para un valor faltante en la posición `i`, entre dos vecinos conocidos en `izq` y `der`:

$$V_i = V_{izq} + \frac{(V_{der} - V_{izq}) \cdot (i - izq)}{der - izq}$$

### Casos especiales
| Situación | Solución |
|-----------|----------|
| Nulos al **inicio** de la serie | Backward fill con el primer valor conocido |
| Nulos al **final** de la serie | Forward fill con el último valor conocido |
| Nulos en el **medio** | Interpolación lineal entre vecinos |
| Serie vacía | Retorna lista vacía sin error |

### Complejidad
- **Tiempo:** O(n) — un único recorrido de la lista
- **Espacio:** O(n) — copia de la lista original

---

## 🧮 Algoritmo 2: Detección de Outliers por Z-Score

**Archivo:** `cleaner.py` → función `detectar_outliers_zscore()`

### Problema que resuelve
Identificar precios anómalos (errores de datos, splits no ajustados) antes de alimentarlos a los algoritmos de similitud.

### Fórmulas matemáticas

**Media aritmética:**
$$\bar{x} = \frac{\sum_{i=1}^{n} x_i}{n}$$

**Desviación estándar poblacional:**
$$\sigma = \sqrt{\frac{\sum_{i=1}^{n}(x_i - \bar{x})^2}{n}}$$

**Z-Score de cada valor:**
$$z_i = \frac{x_i - \bar{x}}{\sigma}$$

Un valor es **outlier** si $|z_i| > 3.5$ (umbral conservador para series financieras).

### Complejidad
- **Tiempo:** O(n) — dos recorridos lineales (media + varianza)
- **Espacio:** O(1) adicional

---

## 📡 Fuente de Datos: Yahoo Finance

**URL base:**
```
https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}
```

**Parámetros de la petición:**
| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `period1` | Unix timestamp | Fecha de inicio (5 años atrás) |
| `period2` | Unix timestamp | Fecha fin (hoy) |
| `interval` | `1d` | Datos diarios |
| `events`  | `history` | Solo datos históricos |

**Por qué no se usa `yfinance`:** Esta librería encapsula la construcción de la URL, el parseo del JSON y la conversión de timestamps. Al hacerlo manualmente, se demuestra el entendimiento del protocolo HTTP y la estructura de datos subyacente.

---

## 🗄️ Esquema de Base de Datos Relevante

```sql
-- Precios históricos (tabla principal del módulo)
CREATE TABLE precios (
    id        SERIAL PRIMARY KEY,
    activo_id INTEGER  NOT NULL REFERENCES activos(id),
    fecha     DATE     NOT NULL,
    apertura  NUMERIC(12,4),
    maximo    NUMERIC(12,4),
    minimo    NUMERIC(12,4),
    cierre    NUMERIC(12,4) NOT NULL,
    volumen   BIGINT,
    UNIQUE(activo_id, fecha)
);
```

---

## ▶️ Cómo ejecutar solo el ETL

```bash
# Desde el contenedor
docker-compose exec bvc_api python main.py etl

# O directamente en local (con .env configurado)
python main.py etl
```

**Salida esperada:**
```
[1/3] Registrando activos en la base de datos...
[DB] 20 activos registrados correctamente.

[2/3] Descargando datos históricos (5 años) ...
[DOWNLOAD] (1/20) Descargando EC ...
[DOWNLOAD] EC: 1258 días descargados.
...
[3/3] Limpiando e insertando en PostgreSQL ...
✅ Pipeline ETL completado exitosamente.
```
