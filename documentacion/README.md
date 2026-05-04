# 📚 Documentación Técnica — BVC Analytics

Esta carpeta contiene la documentación esencial del proyecto.

---

## 📋 Documentos Disponibles

### 🏗️ Arquitectura del Sistema

**[ARQUITECTURA_C4.md](ARQUITECTURA_C4.md)**
- Diagramas de arquitectura en 4 niveles (Modelo C4)
- Nivel 1: Contexto del sistema
- Nivel 2: Contenedores (Docker)
- Nivel 3: Componentes (módulos Python)
- Nivel 4: Flujo de datos (código)
- Schema de base de datos PostgreSQL
- Decisiones de arquitectura
- Restricciones técnicas cumplidas

---

### 📖 Cumplimiento de Requerimientos

**[REQ1_ETL.md](REQ1_ETL.md)** — Pipeline de Extracción, Transformación y Carga
- Descarga automática desde Yahoo Finance (urllib)
- Limpieza de datos (interpolación lineal, outliers Z-Score)
- Persistencia en PostgreSQL
- Sin pandas, numpy, yfinance

**[REQ2_SIMILITUD.md](REQ2_SIMILITUD.md)** — Algoritmos de Similitud
- Correlación de Pearson O(n)
- Similitud por Coseno O(n)
- Distancia Euclidiana O(n)
- DTW (Dynamic Time Warping) O(n²) con Sakoe-Chiba
- 300 pares de correlaciones (25 activos)

**[REQ3_PATRONES_VOLATILIDAD.md](REQ3_PATRONES_VOLATILIDAD.md)** — Patrones y Análisis de Riesgo
- Ventana deslizante (20 días)
- Detección de picos y valles
- Golden Cross / Death Cross
- Volatilidad histórica anualizada
- VaR histórico (95%)
- Sharpe Ratio
- Max Drawdown

**[REQ4_DASHBOARD.md](REQ4_DASHBOARD.md)** — Interfaz Web Interactiva
- Dashboard con 10 secciones
- Gráficos SVG + Canvas 2D (sin librerías)
- Mapa de calor 25×25 con filtros
- Velas OHLC con SMAs configurables
- Comparación de activos con interpretaciones
- Sin React, Vue, Angular, jQuery

**[REQ5_DESPLIEGUE.md](REQ5_DESPLIEGUE.md)** — Despliegue en Producción
- Docker + Docker Compose
- PostgreSQL 15
- Servidor HTTP (http.server stdlib)
- Nginx como reverse proxy
- Reproducibilidad garantizada

---

### 🎓 Guía de Exposición

**[EXPOSICION.md](EXPOSICION.md)**
- Flujo de ejecución (comandos Docker)
- Orden de exposición archivo por archivo
- Qué decir en cada sección
- Complejidades algorítmicas
- Restricciones cumplidas
- Timing sugerido (6 minutos)

---

### 📄 Documento Entregable

**Proyecto final algoritmos_Andres_Diaz_Sarita_Londoño.docx**
- Documento académico completo del proyecto

---

## 📖 Orden de Lectura Recomendado

### Para entender el proyecto completo:
1. **README.md** (raíz del proyecto) — Visión general
2. **ARQUITECTURA_C4.md** — Estructura y diseño del sistema
3. **REQ1_ETL.md** → **REQ2_SIMILITUD.md** → **REQ3_PATRONES_VOLATILIDAD.md** → **REQ4_DASHBOARD.md** → **REQ5_DESPLIEGUE.md**

### Para la exposición:
1. **EXPOSICION.md** — Guía completa con timing y qué decir
2. **ARQUITECTURA_C4.md** — Referencia para preguntas técnicas

---

## 🎯 Resumen del Proyecto

### Estadísticas:
- **25 activos** financieros (Colombia, LATAM, Globales, Sectores, Commodities)
- **300 pares** de correlaciones C(25,2)
- **28 algoritmos** implementados desde cero
- **5 años** de datos históricos (~1,274 días de negociación)
- **31,000+** registros OHLCV en PostgreSQL
- **1 dependencia** externa (psycopg2)
- **10 secciones** interactivas en el dashboard

### Restricciones Cumplidas:
✅ Sin pandas, numpy, scipy, sklearn  
✅ Sin yfinance, requests  
✅ Sin Flask, FastAPI, Django  
✅ Sin matplotlib, plotly, Chart.js  
✅ Algoritmos implementados desde cero  
✅ Datos obtenidos automáticamente  
✅ 5 años de datos históricos  
✅ Reproducibilidad garantizada (Docker)

---

## 🔍 Búsqueda Rápida

**¿Necesitas información sobre...?**

| Tema | Documento |
|------|-----------|
| Arquitectura general | ARQUITECTURA_C4.md |
| Cómo funciona el ETL | REQ1_ETL.md |
| Algoritmos de similitud | REQ2_SIMILITUD.md |
| Detección de patrones | REQ3_PATRONES_VOLATILIDAD.md |
| Dashboard y visualizaciones | REQ4_DASHBOARD.md |
| Despliegue con Docker | REQ5_DESPLIEGUE.md |
| Cómo presentar | EXPOSICION.md |
| Schema de base de datos | ARQUITECTURA_C4.md (sección Schema) |
| Complejidades algorítmicas | EXPOSICION.md (tabla de complejidades) |

---

Universidad del Quindío — Análisis de Algoritmos 2026-1  
**Autores:** Sarita Londoño Perdomo · Eyner Andrés Díaz Díaz  
**Profesor:** Sergio Augusto Cardona Torres
