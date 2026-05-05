@echo off
echo ========================================
echo   Algorit Finance - Inicio Rapido
echo   Universidad del Quindio 2026-1
echo ========================================
echo.

echo [1/5] Levantando contenedores Docker...
docker compose -f docker-compose.local.yml up -d
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron levantar los contenedores
    echo Verifica que Docker Desktop este corriendo
    pause
    exit /b 1
)
echo OK - Contenedores levantados
echo.

echo Esperando 10 segundos para que PostgreSQL inicie...
timeout /t 10 /nobreak > nul
echo.

echo [2/5] Ejecutando pipeline ETL (descarga de datos)...
echo Esto puede tardar 3-5 minutos...
docker exec bvc_api python main.py etl
if %errorlevel% neq 0 (
    echo ERROR: Fallo el pipeline ETL
    pause
    exit /b 1
)
echo OK - Datos descargados
echo.

echo [3/5] Calculando similitudes (correlaciones)...
echo Esto puede tardar 2-3 minutos...
docker exec bvc_api python main.py similitud
if %errorlevel% neq 0 (
    echo ERROR: Fallo el calculo de similitudes
    pause
    exit /b 1
)
echo OK - Correlaciones calculadas
echo.

echo [4/5] Calculando volatilidad y riesgo...
docker exec bvc_api python main.py volatilidad
if %errorlevel% neq 0 (
    echo ERROR: Fallo el calculo de volatilidad
    pause
    exit /b 1
)
echo OK - Volatilidad calculada
echo.

echo [5/5] Ejecutando benchmark de ordenamiento...
docker exec bvc_api python main.py ordenamiento
if %errorlevel% neq 0 (
    echo ERROR: Fallo el benchmark
    pause
    exit /b 1
)
echo OK - Benchmark completado
echo.

echo ========================================
echo   PROYECTO LISTO!
echo ========================================
echo.
echo Dashboard disponible en: http://localhost:8001
echo.
echo Presiona cualquier tecla para abrir el navegador...
pause > nul
start http://localhost:8001
