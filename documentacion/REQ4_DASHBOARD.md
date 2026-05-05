# Requerimiento 4 — Dashboard Visual y Reporte Técnico

## Enunciado

> El sistema deberá incluir un componente visual que facilite la interpretación de los resultados algorítmicos. Se deberán generar: una matriz de correlación representada como mapa de calor, gráficos de velas (candlestick) para activos seleccionados incorporando medias móviles simples calculadas algorítmicamente, y la exportación de un reporte técnico en formato PDF.

---

## Archivos Involucrados

| Archivo | Función |
|---|---|
| `interfaz/index.html` | Dashboard SPA completo |
| `reportes/generador.py` | Generador de reporte JSON y HTML |
| `api/server.py → _ohlcv(), _correlacion_matriz(), _reporte_txt()` | Endpoints |

---

## Dashboard SPA (`interfaz/index.html`)

Aplicación de página única implementada en HTML5 + CSS3 + JavaScript vanilla. Sin React, Vue, Angular ni ninguna librería de UI o gráficos.

### Secciones del Dashboard

| Sección | Descripción |
|---|---|
| Overview | KPIs, sparklines de 25 activos, heatmap preview, distribución de riesgo |
| Portafolio | Gráficos individuales de los 25 activos con filtros |
| Comparar Activos | Comparación de 2 activos con los 4 algoritmos de similitud |
| Mapa de Calor | Matriz de correlación 25×25 interactiva |
| Patrones | Ventana deslizante + Golden/Death Cross por ticker |
| Clasificación Riesgo | Ranking de 25 activos por volatilidad anualizada |
| Tabla 1 + Barras | Benchmark de 12 algoritmos de ordenamiento |
| Top-15 Volumen | Días con mayor volumen de negociación |
| Velas OHLC | Gráfico candlestick con SMA configurable |
| Reporte / PDF | Reporte técnico exportable |
| Tasa USD/COP | Conversor de divisas en tiempo real |

---

## Visualización 1: Mapa de Calor de Correlación

**Sección:** Mapa de Calor

**Implementación:** SVG generado dinámicamente en JavaScript

**Datos:** Matriz 20×20 de correlaciones Pearson desde `/correlacion/matriz`

**Escala de colores:**
```
r = -1  →  Rojo    (#f43f5e)
r =  0  →  Gris    (#334155)
r = +1  →  Verde   (#10b981)
```

**Función de color:**
```javascript
function corColor(v) {
    if (v >= 0) {
        return `rgb(${Math.round(16 + (240-16)*(1-v))}, 185, ${Math.round(129*v)})`;
    }
    const t = -v;
    return `rgb(244, ${Math.round(63 + 90*(1-t))}, ${Math.round(94*(1-t))})`;
}
```

**Interactividad:** Tooltip al pasar el mouse sobre cada celda mostrando los tickers y el valor exacto de correlación.

---

## Visualización 2: Gráfico de Velas OHLC

**Sección:** Velas OHLC

**Implementación:** Canvas 2D API de HTML5

**Datos:** Endpoint `/precios/ohlcv?ticker=SPY&n=120`

**Componentes del gráfico:**
- Velas alcistas (cierre ≥ apertura): color verde `#10b981`
- Velas bajistas (cierre < apertura): color rojo `#f43f5e`
- Mecha superior e inferior: línea vertical en el color de la vela
- SMA rápida (configurable, default 10 días): línea azul `#38bdf8`
- SMA lenta (configurable, default 30 días): línea naranja `#f59e0b`
- Etiquetas del eje Y: precios
- Etiquetas del eje X: fechas (cada N días)

**Cálculo de SMA en el frontend:**
```javascript
function sma(arr, w) {
    return arr.map((_, i) =>
        i < w - 1 ? null :
        arr.slice(i - w + 1, i + 1).reduce((a, b) => a + b, 0) / w
    );
}
```

**Parámetros configurables:**
- Ticker (selector de los 25 activos)
- SMA rápida: 2-50 días
- SMA lenta: 5-200 días
- Período: 60, 120, 180 días o 1 año

---

## Visualización 3: Sparklines del Portafolio

**Sección:** Overview y Portafolio

**Implementación:** SVG path generado dinámicamente

**Datos:** Endpoint `/precios?ticker=X&columna=cierre`

**Componentes:**
- Línea de precio (verde si rendimiento positivo, rojo si negativo)
- Área rellena bajo la línea (color semitransparente)
- Línea de referencia punteada (precio inicial del período)
- Etiquetas de precio mínimo, medio y máximo
- Etiquetas de fecha inicio y fin

**Interactividad:** Clic en cualquier gráfico navega a "Velas OHLC" con ese ticker preseleccionado.

---

## Reporte Técnico (`reportes/generador.py`)

### Estructura del Reporte

El reporte consolida los resultados de todos los módulos del sistema:

**Sección 1 — Cobertura de Datos (ETL)**
- Total de activos analizados
- Total de registros OHLCV en base de datos
- Cobertura por activo (ticker, días, fecha inicio, fecha fin)

**Sección 2 — Similitud de Series de Tiempo**
- Top-5 pares más similares para cada algoritmo (Pearson, Coseno, Euclidiana, DTW)

**Sección 3 — Ranking de Volatilidad**
- Activos ordenados por volatilidad anualizada
- Clasificación en Conservador / Moderado / Agresivo

**Sección 4 — Métricas de Riesgo Individual**
- Volatilidad anualizada, Sharpe Ratio, VaR 95%, Máximo Drawdown

**Sección 5 — Patrones Detectados**
- Distribución de patrones por activo
- Conteo de picos y valles

### Exportación a PDF

El reporte se genera en HTML con estilos inline optimizados para impresión. La exportación a PDF se realiza mediante `window.print()` del navegador, que permite guardar como PDF en todos los sistemas operativos.

```javascript
function exportPDF() {
    const frame = document.getElementById('rep-frame');
    if (frame.contentWindow) {
        frame.contentWindow.print();
    }
}
```

---

## Endpoints API

```
GET /precios/ohlcv?ticker=SPY&n=120  → Datos OHLCV para gráfico de velas
GET /correlacion/matriz              → Matriz 20×20 para heatmap
GET /reporte                         → Reporte técnico completo (JSON)
GET /reporte/txt                     → Reporte técnico en HTML (para PDF)
```
