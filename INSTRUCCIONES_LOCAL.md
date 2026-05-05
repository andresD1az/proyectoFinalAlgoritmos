# 🚀 Cómo Correr Algorit Finance en Local

**Proyecto:** Algorit Finance  
**Universidad del Quindío** — Análisis de Algoritmos 2026-1

---

## ✅ Requisitos Previos

Antes de empezar, asegúrate de tener instalado:

1. **Docker Desktop** (Windows/Mac) o **Docker Engine** (Linux)
   - Descargar: https://www.docker.com/products/docker-desktop
   - Verificar instalación: `docker --version`

2. **Docker Compose** (incluido en Docker Desktop)
   - Verificar: `docker compose version`

---

## 📦 Paso 1: Preparar el Proyecto

### 1.1 Abrir terminal en la carpeta del proyecto

```bash
cd proyectoFinalAlgoritmos
```

### 1.2 Verificar que existe el archivo `.env`

Si no existe, crear uno basado en `.env.example`:

```bash
cp .env.example .env
```

---

## 🐳 Paso 2: Levantar los Contenedores

### 2.1 Construir y levantar los servicios

```bash
docker compose -f docker-compose.local.yml up -d
```

**Esto va a:**
- Crear el contenedor de PostgreSQL (base de datos)
- Crear el contenedor de la API (Python)
- Levantar ambos servicios en segundo plano

**Tiempo estimado:** 2-3 minutos la primera vez

### 2.2 Verificar que los contenedores están corriendo

```bash
docker ps
```

Deberías ver algo como:

```
CONTAINER ID   IMAGE              STATUS         PORTS                    NAMES
abc123def456   bvc_api           Up 30 seconds  0.0.0.0:8001->8001/tcp   bvc_api
xyz789ghi012   postgres:15       Up 30 seconds  0.0.0.0:5432->5432/tcp   bvc_postgres
```

---

## 📊 Paso 3: Cargar los Datos

### 3.1 Ejecutar el pipeline ETL (Descarga de datos)

```bash
docker exec bvc_api python main.py etl
```

**Esto va a:**
- Descargar datos de 25 activos desde Yahoo Finance
- Limpiar los datos (interpolación, outliers)
- Guardar en PostgreSQL

**Tiempo estimado:** 3-5 minutos  
**Verás:** Barras de progreso para cada activo

### 3.2 Calcular similitudes (correlaciones)

```bash
docker exec bvc_api python main.py similitud
```

**Esto va a:**
- Calcular 300 pares de correlaciones (Pearson, Coseno, Euclidiana, DTW)
- Guardar en la tabla `correlaciones`

**Tiempo estimado:** 2-3 minutos

### 3.3 Calcular volatilidad y riesgo

```bash
docker exec bvc_api python main.py volatilidad
```

**Esto va a:**
- Calcular volatilidad, VaR, Sharpe Ratio, Max Drawdown
- Clasificar activos por riesgo

**Tiempo estimado:** 1 minuto

### 3.4 Ejecutar benchmark de algoritmos de ordenamiento

```bash
docker exec bvc_api python main.py ordenamiento
```

**Esto va a:**
- Ejecutar 12 algoritmos de ordenamiento
- Medir tiempos de ejecución
- Guardar resultados

**Tiempo estimado:** 30 segundos

---

## 🌐 Paso 4: Abrir el Dashboard

### 4.1 Abrir en el navegador

```
http://localhost:8001
```

### 4.2 Explorar las secciones

El dashboard tiene 10 secciones:

1. **Overview** — KPIs y resumen general
2. **Portafolio** — 25 gráficos individuales
3. **Comparar Activos** — Análisis de similitud
4. **Mapa de Calor** — Matriz de correlaciones 25×25
5. **Patrones** — Detección de patrones por activo
6. **Clasificación de Riesgo** — Ranking por volatilidad
7. **Tabla 1 + Barras** — Benchmark de ordenamiento
8. **Top-15 Volumen** — Días con mayor volumen
9. **Velas OHLC** — Gráfico de velas con SMAs
10. **Reporte/PDF** — Reporte técnico completo

---

## 🔍 Paso 5: Verificar que Todo Funciona

### 5.1 Verificar datos en la base de datos

```bash
docker exec -it bvc_postgres psql -U bvc_user -d bvc_db -c "SELECT COUNT(*) FROM precios;"
```

**Deberías ver:** ~31,000 registros

### 5.2 Verificar correlaciones

```bash
docker exec -it bvc_postgres psql -U bvc_user -d bvc_db -c "SELECT COUNT(*) FROM correlaciones;"
```

**Deberías ver:** 300 registros

### 5.3 Verificar volatilidad

```bash
docker exec -it bvc_postgres psql -U bvc_user -d bvc_db -c "SELECT COUNT(*) FROM volatilidad;"
```

**Deberías ver:** 25 registros

---

## 📝 Comandos Útiles

### Ver logs de la API

```bash
docker logs bvc_api --tail 50 -f
```

### Ver logs de PostgreSQL

```bash
docker logs bvc_postgres --tail 50 -f
```

### Reiniciar los servicios

```bash
docker compose -f docker-compose.local.yml restart
```

### Detener los servicios

```bash
docker compose -f docker-compose.local.yml down
```

### Detener y eliminar todo (incluyendo datos)

```bash
docker compose -f docker-compose.local.yml down -v
```

---

## ❌ Solución de Problemas

### Problema: "Port 8001 is already in use"

**Solución:** Cambiar el puerto en `docker-compose.local.yml`:

```yaml
ports:
  - "8002:8001"  # Cambiar 8001 por 8002
```

Luego acceder a: `http://localhost:8002`

---

### Problema: "Port 5432 is already in use"

**Solución:** Ya tienes PostgreSQL corriendo localmente. Cambiar el puerto:

```yaml
ports:
  - "5433:5432"  # Cambiar 5432 por 5433
```

---

### Problema: "Cannot connect to database"

**Solución:** Esperar 10 segundos y reintentar. PostgreSQL tarda en iniciar.

```bash
docker compose -f docker-compose.local.yml restart bvc_api
```

---

### Problema: "No data in dashboard"

**Solución:** Ejecutar los pipelines en orden:

```bash
docker exec bvc_api python main.py etl
docker exec bvc_api python main.py similitud
docker exec bvc_api python main.py volatilidad
docker exec bvc_api python main.py ordenamiento
```

---

## 🎓 Resumen de Comandos (Copiar y Pegar)

```bash
# 1. Levantar servicios
docker compose -f docker-compose.local.yml up -d

# 2. Cargar datos
docker exec bvc_api python main.py etl
docker exec bvc_api python main.py similitud
docker exec bvc_api python main.py volatilidad
docker exec bvc_api python main.py ordenamiento

# 3. Abrir navegador
# http://localhost:8001

# 4. Ver logs (opcional)
docker logs bvc_api --tail 50 -f

# 5. Detener servicios (cuando termines)
docker compose -f docker-compose.local.yml down
```

---

## ✅ Checklist de Verificación

- [ ] Docker Desktop está corriendo
- [ ] Contenedores levantados (`docker ps`)
- [ ] Pipeline ETL ejecutado (datos descargados)
- [ ] Pipeline similitud ejecutado (correlaciones calculadas)
- [ ] Pipeline volatilidad ejecutado (riesgo calculado)
- [ ] Pipeline ordenamiento ejecutado (benchmark completo)
- [ ] Dashboard abre en `http://localhost:8001`
- [ ] Todas las secciones muestran datos
- [ ] Gráficos se renderizan correctamente

---

**¡Listo!** Tu proyecto **Algorit Finance** está corriendo en local. 🚀

Universidad del Quindío — Análisis de Algoritmos 2026-1  
**Autores:** Sarita Londoño Perdomo · Eyner Andrés Díaz Díaz
