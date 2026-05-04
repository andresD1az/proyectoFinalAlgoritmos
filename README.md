# BVC Analytics

**Sistema de Análisis Financiero Cuantitativo**

Universidad del Quindío — Análisis de Algoritmos 2026-1  
Autores: Sarita Londoño Perdomo · Eyner Andrés Díaz Díaz

---

## 📊 Descripción

BVC Analytics es un sistema completo de análisis financiero que procesa y analiza datos históricos de 25 activos financieros con 5 años de historia diaria. Implementa 28 algoritmos desde cero en Python puro, sin dependencias externas de análisis de datos.

### Características principales:

- **ETL automatizado:** Descarga y limpieza de datos desde Yahoo Finance
- **Análisis de similitud:** 4 algoritmos (Pearson, Coseno, Euclidiana, DTW)
- **Detección de patrones:** Ventana deslizante, Golden/Death Cross
- **Análisis de riesgo:** Volatilidad, VaR, Sharpe Ratio, Max Drawdown
- **12 algoritmos de ordenamiento:** Implementados desde cero con benchmark
- **Dashboard interactivo:** Visualizaciones en tiempo real con filtros avanzados

---

## 🚀 Inicio Rápido

### Requisitos previos:
- Docker y Docker Compose
- Python 3.11+ (opcional, para desarrollo local)

### Instalación:

```bash
# 1. Clonar el repositorio
git clone <repository-url>
cd proyectoFinalAlgoritmos

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Levantar contenedores
docker compose -f docker-compose.local.yml up -d

# 4. Ejecutar pipelines de datos
docker exec bvc_api python main.py etl
docker exec bvc_api python main.py similitud

# 5. Acceder al dashboard
# http://localhost:8001
```

---

## 📁 Estructura del Proyecto

```
proyectoFinalAlgoritmos/
├── algoritmos/          # 28 algoritmos implementados desde cero
│   ├── ordenamiento.py  # 12 algoritmos de ordenamiento
│   ├── similitud.py     # Pearson, Coseno, Euclidiana, DTW
│   ├── patrones.py      # Ventana deslizante, Golden/Death Cross
│   └── volatilidad.py   # Volatilidad, VaR, Sharpe, Drawdown
├── api/                 # Servidor HTTP (stdlib puro)
├── etl/                 # Descarga, limpieza y persistencia
├── interfaz/            # Dashboard web (HTML/CSS/JS vanilla)
├── reportes/            # Generación de reportes
├── basedatos/           # Scripts SQL
├── documentacion/       # Documentación técnica detallada
├── config.py            # Configuración centralizada
├── main.py              # Punto de entrada
└── requirements.txt     # Dependencias (solo psycopg2)
```

---

## 🎯 Portafolio de Activos

**25 activos financieros** organizados en 5 categorías:

### Colombia (3)
- **EC** — Ecopetrol S.A.
- **CIB** — Bancolombia S.A.
- **GXG** — iShares MSCI Colombia

### Latinoamérica (4)
- **ILF** — iShares Latin America 40
- **EWZ** — iShares MSCI Brazil
- **EWW** — iShares MSCI Mexico
- **ECH** — iShares MSCI Chile

### Globales (7)
- **SPY** — S&P 500 ETF
- **QQQ** — Nasdaq 100 ETF
- **DIA** — Dow Jones ETF
- **EEM** — Emerging Markets ETF
- **VT** — Vanguard Total World
- **IEMG** — Core Emerging Markets
- **VEA** — Vanguard Developed Markets

### Sectores (8)
- **XLE** — Energy Select Sector
- **XLF** — Financial Select Sector
- **XLK** — Technology Select Sector
- **VNQ** — Vanguard Real Estate
- **XLV** — Health Care Select Sector
- **XLI** — Industrial Select Sector
- **XLP** — Consumer Staples Sector

### Commodities (3)
- **GLD** — SPDR Gold Shares
- **SLV** — iShares Silver Trust
- **USO** — US Oil Fund
- **TLT** — iShares 20Y Treasury

---

## 🔧 Tecnologías

### Backend:
- **Python 3.11** — Lenguaje principal
- **PostgreSQL 15** — Base de datos
- **http.server** — Servidor HTTP (stdlib)
- **urllib** — Descarga de datos (stdlib)
- **psycopg2** — Driver PostgreSQL (única dependencia)

### Frontend:
- **HTML5 + CSS3** — Estructura y estilos
- **JavaScript vanilla** — Lógica e interactividad
- **SVG + Canvas 2D** — Gráficos sin librerías externas

### Infraestructura:
- **Docker + Docker Compose** — Contenedorización
- **Nginx** — Reverse proxy (producción)

---

## 📊 Algoritmos Implementados

### Ordenamiento (12):
TimSort, Comb Sort, Selection Sort, Tree Sort, Pigeonhole Sort, Bucket Sort, QuickSort, HeapSort, Bitonic Sort, Gnome Sort, Binary Insertion Sort, RadixSort

### Similitud (4):
- **Pearson** — Correlación lineal O(n)
- **Coseno** — Similitud direccional O(n)
- **Euclidiana** — Distancia normalizada O(n)
- **DTW** — Dynamic Time Warping O(n²) con Sakoe-Chiba

### Análisis de Riesgo (5):
- Volatilidad histórica anualizada
- VaR histórico (95%)
- Sharpe Ratio
- Max Drawdown
- Clasificación por riesgo

### Detección de Patrones (4):
- Ventana deslizante (20 días)
- Picos y valles
- Media móvil simple (SMA)
- Golden Cross / Death Cross

---

## 📈 Dashboard

El dashboard incluye 10 secciones interactivas:

1. **Overview** — KPIs, sparklines, estadísticas generales
2. **Portafolio** — 25 gráficos individuales con filtros
3. **Comparar Activos** — Análisis de similitud con 4 algoritmos
4. **Mapa de Calor** — Matriz 25×25 de correlaciones con filtros
5. **Patrones** — Detección de patrones por activo
6. **Clasificación de Riesgo** — Ranking por volatilidad
7. **Tabla 1 + Barras** — Benchmark de algoritmos de ordenamiento
8. **Top-15 Volumen** — Días con mayor volumen
9. **Velas OHLC** — Gráfico de velas con SMAs configurables
10. **Reporte/PDF** — Reporte técnico completo

---

## 🔬 Cumplimiento de Requisitos

### Restricciones técnicas:
✅ Sin pandas, numpy, scipy, sklearn  
✅ Sin yfinance, requests  
✅ Sin Flask, FastAPI, Django  
✅ Sin matplotlib, plotly, Chart.js  
✅ Algoritmos implementados desde cero  
✅ Datos obtenidos automáticamente  
✅ 5 años de datos históricos  
✅ Reproducibilidad garantizada (Docker)

### Complejidades documentadas:
Cada algoritmo incluye su complejidad temporal en notación Big-O y fórmulas matemáticas en los docstrings.

---

## 📚 Documentación

La documentación técnica detallada se encuentra en la carpeta `documentacion/`:

- **ARQUITECTURA_C4.md** — Diagramas de arquitectura (4 niveles)
- **REQ1_ETL.md** — Pipeline de extracción y limpieza
- **REQ2_SIMILITUD.md** — Algoritmos de similitud
- **REQ3_PATRONES_VOLATILIDAD.md** — Patrones y análisis de riesgo
- **REQ4_DASHBOARD.md** — Interfaz web y visualizaciones
- **REQ5_DESPLIEGUE.md** — Despliegue en producción
- **EXPOSICION_COMPLETA.md** — Guía para la presentación

---

## 🧪 Comandos Útiles

```bash
# Ejecutar pipelines individuales
docker exec bvc_api python main.py etl           # Descargar datos
docker exec bvc_api python main.py similitud     # Calcular similitudes
docker exec bvc_api python main.py volatilidad   # Calcular volatilidad
docker exec bvc_api python main.py ordenamiento  # Benchmark de ordenamiento

# Ver logs
docker logs bvc_api --tail 50 -f

# Reiniciar servicios
docker compose -f docker-compose.local.yml restart

# Detener servicios
docker compose -f docker-compose.local.yml down
```

---

## 👥 Autores

**Sarita Londoño Perdomo** — 1091884459  
**Eyner Andrés Díaz Díaz** — 1128544093

**Profesor:** Sergio Augusto Cardona Torres  
**Universidad del Quindío** — Ingeniería de Sistemas y Computación  
**Curso:** Análisis de Algoritmos 2026-1

---

## 📄 Licencia

Este proyecto es de uso académico para la Universidad del Quindío.
