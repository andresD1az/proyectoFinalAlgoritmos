@echo off
echo ========================================
echo   Algorit Finance - Detener Servicios
echo   Universidad del Quindio 2026-1
echo ========================================
echo.

echo Deteniendo contenedores Docker...
docker compose -f docker-compose.local.yml down

if %errorlevel% neq 0 (
    echo ERROR: No se pudieron detener los contenedores
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SERVICIOS DETENIDOS
echo ========================================
echo.
echo Los contenedores han sido detenidos.
echo Los datos se mantienen en el volumen de Docker.
echo.
echo Para eliminar tambien los datos, ejecuta:
echo docker compose -f docker-compose.local.yml down -v
echo.
pause
