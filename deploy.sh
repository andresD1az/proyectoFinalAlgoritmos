#!/bin/bash
# =============================================================
# BVC Analytics — Script de despliegue en VPS propio
# =============================================================
# PASO 1 — desde tu PC, copiar el proyecto al VPS:
#   rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='EXPOSICION.md' ./ root@TU_IP:/opt/bvc-analytics/
#
# PASO 2 — conectarse al VPS y ejecutar este script:
#   ssh root@TU_IP "bash /opt/bvc-analytics/deploy.sh"
# =============================================================

set -e

APP_DIR="/opt/bvc-analytics"
VPS_IP=$(curl -s ifconfig.me 2>/dev/null || echo "TU_IP")

echo "=================================================="
echo "  BVC Analytics — Despliegue en VPS"
echo "  IP: $VPS_IP"
echo "=================================================="

# ── 1. Docker ─────────────────────────────────────────────────
if ! command -v docker &> /dev/null; then
    echo "[1/5] Instalando Docker..."
    apt-get update -qq
    apt-get install -y -qq docker.io
    systemctl enable docker
    systemctl start docker
    # docker compose plugin
    apt-get install -y -qq docker-compose-plugin 2>/dev/null || \
    apt-get install -y -qq docker-compose 2>/dev/null || true
    echo "[OK] Docker instalado"
else
    echo "[1/5] Docker ya instalado ✓"
fi

# ── 2. Directorio y .env ──────────────────────────────────────
echo "[2/5] Preparando directorio..."
mkdir -p $APP_DIR
cd $APP_DIR

if [ ! -f "$APP_DIR/.env" ]; then
    echo "[INFO] Creando .env desde .env.example..."
    cp .env.example .env
    # Cambiar password por defecto
    sed -i 's/pon_aqui_tu_password_seguro/BVC_Deploy_2025!/g' .env
    # Asegurarse que DB_HOST apunte al contenedor
    sed -i 's/DB_HOST=localhost/DB_HOST=bvc_db/g' .env
    echo "[OK] .env creado"
else
    echo "[2/5] .env ya existe ✓"
fi

# ── 3. Nginx ──────────────────────────────────────────────────
echo "[3/5] Configurando Nginx..."
apt-get install -y -qq nginx 2>/dev/null

cat > /etc/nginx/sites-available/bvc-analytics << NGINX
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass         http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        proxy_connect_timeout 10s;
        client_max_body_size 10M;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/bvc-analytics /etc/nginx/sites-enabled/bvc-analytics
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

if nginx -t 2>/dev/null; then
    systemctl enable nginx
    systemctl reload nginx
    echo "[OK] Nginx configurado"
else
    echo "[WARN] Error en Nginx, revisa manualmente"
fi

# ── 4. Levantar contenedores ──────────────────────────────────
echo "[4/5] Levantando contenedores Docker..."
cd $APP_DIR

# Intentar con docker compose (plugin) o docker-compose (legacy)
DC="docker compose"
if ! docker compose version &>/dev/null 2>&1; then
    DC="docker-compose"
fi

$DC -f docker-compose.local.yml down 2>/dev/null || true
$DC -f docker-compose.local.yml up --build -d

echo "[INFO] Esperando que PostgreSQL esté listo..."
sleep 15

# Verificar que los contenedores estén corriendo
$DC -f docker-compose.local.yml ps

# ── 5. Pipelines de datos ─────────────────────────────────────
echo "[5/5] Iniciando pipelines de datos en background..."
echo "[INFO] Esto puede tardar 15-30 minutos dependiendo del VPS."
echo "[INFO] Puedes monitorear con: docker logs -f bvc_api"

# Correr todo en background para no bloquear el script
nohup bash -c "
  docker exec bvc_api python main.py etl        && echo '[DONE] ETL completado'        && \
  docker exec bvc_api python main.py similitud  && echo '[DONE] Similitud completada'  && \
  docker exec bvc_api python main.py volatilidad && echo '[DONE] Volatilidad completada' && \
  docker exec bvc_api python main.py ordenamiento && echo '[DONE] Ordenamiento completado' && \
  echo '[DONE] ✅ Todos los pipelines completados'
" > /var/log/bvc-pipelines.log 2>&1 &

PIPELINE_PID=$!
echo "[INFO] Pipelines corriendo en background (PID: $PIPELINE_PID)"
echo "[INFO] Ver progreso: tail -f /var/log/bvc-pipelines.log"

echo ""
echo "=================================================="
echo "  ✅ BVC Analytics desplegado!"
echo "=================================================="
echo ""
echo "  🌐 Dashboard:     http://$VPS_IP"
echo "  🔌 API directa:   http://$VPS_IP:8001"
echo "  📊 Estado ETL:    http://$VPS_IP/etl/status"
echo "  ❤️  Health check:  http://$VPS_IP/health"
echo ""
echo "  📋 Ver logs API:      docker logs -f bvc_api"
echo "  📋 Ver logs pipelines: tail -f /var/log/bvc-pipelines.log"
echo "  🔄 Reiniciar:         docker compose -f docker-compose.local.yml restart"
echo "=================================================="
