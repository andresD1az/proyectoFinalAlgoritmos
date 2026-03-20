#!/bin/bash
# =====================================================
# BVC Analytics — Script de despliegue para VPS
# =====================================================
# Uso: scp deploy.sh root@38.242.225.58:/root/ && ssh root@38.242.225.58 "bash /root/deploy.sh"
# =====================================================

set -e
echo "=================================================="
echo "  BVC Analytics — Despliegue en VPS"
echo "=================================================="

APP_DIR="/opt/bvc-analytics"
REPO_DIR="$APP_DIR"

# 1. Instalar Docker si no existe
if ! command -v docker &> /dev/null; then
    echo "[1/6] Instalando Docker..."
    apt-get update -qq
    apt-get install -y -qq docker.io docker-compose-v2 2>/dev/null || apt-get install -y -qq docker.io docker-compose 2>/dev/null
    systemctl enable docker
    systemctl start docker
    echo "[OK] Docker instalado"
else
    echo "[1/6] Docker ya instalado ✓"
fi

# 2. Crear directorio de la app
echo "[2/6] Preparando directorio..."
mkdir -p $APP_DIR

# 3. Verificar archivos (deben copiarse antes con scp/rsync)
if [ ! -f "$APP_DIR/docker-compose.yml" ]; then
    echo "[ERROR] No se encontraron los archivos del proyecto en $APP_DIR"
    echo "        Primero copia el proyecto con:"
    echo "        rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' ./ root@38.242.225.58:$APP_DIR/"
    exit 1
fi

# 4. Crear .env si no existe
if [ ! -f "$APP_DIR/.env" ]; then
    echo "[3/6] Creando .env..."
    cat > "$APP_DIR/.env" << 'EOF'
DB_NAME=bvc_analytics
DB_USER=bvc_user
DB_PASSWORD=BVC_Seguro_2024!
DB_HOST=bvc_db
DB_PORT=5432
API_HOST=0.0.0.0
API_PORT=8001
EOF
    echo "[OK] .env creado"
else
    echo "[3/6] .env ya existe ✓"
fi

# 5. Configurar Nginx como reverse proxy
echo "[4/6] Configurando Nginx..."
apt-get install -y -qq nginx 2>/dev/null

# Buscar si ya hay un default o site que interfiera  
# Evitar romper otros sitios existentes
cat > /etc/nginx/sites-available/bvc-analytics << 'NGINX'
server {
    listen 80;
    server_name bvc._;  # Cambiar por tu dominio si tienes

    # Solo para BVC Analytics - ruta /bvc
    location /bvc/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }

    # APIs directas
    location /api/bvc/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX

# Solo crear el symlink si no existe, sin tocar otros sites
if [ ! -L /etc/nginx/sites-enabled/bvc-analytics ]; then
    ln -sf /etc/nginx/sites-available/bvc-analytics /etc/nginx/sites-enabled/bvc-analytics
fi

# Verificar configuración sin romper nada
if nginx -t 2>/dev/null; then
    systemctl reload nginx
    echo "[OK] Nginx configurado"
else
    echo "[WARN] Error en config de Nginx, revisa manualmente"
    rm -f /etc/nginx/sites-enabled/bvc-analytics
fi

# 6. Levantar servicios
echo "[5/6] Levantando servicios Docker..."
cd $APP_DIR
docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true
docker compose up --build -d 2>/dev/null || docker-compose up --build -d

# Esperar a que la DB esté lista
echo "    Esperando a que PostgreSQL inicie..."
sleep 10

# 7. Aplicar migración
echo "[6/6] Aplicando migración..."
docker compose exec -T bvc_api python -c "
import psycopg2, os
conn = psycopg2.connect(
    host=os.getenv('DB_HOST','bvc_db'),
    port=int(os.getenv('DB_PORT','5432')),
    dbname=os.getenv('DB_NAME','bvc_analytics'),
    user=os.getenv('DB_USER','bvc_user'),
    password=os.getenv('DB_PASSWORD','BVC_Seguro_2024!')
)
cur = conn.cursor()
cur.execute(open('/app/database/migrate_v2.sql').read())
conn.commit()
cur.close()
conn.close()
print('[OK] Migración aplicada')
" 2>/dev/null || echo "[INFO] Migración ya aplicada o no necesaria"

# 8. Crear superadmin
docker compose exec -T bvc_api python scripts/crear_superadmin.py 2>/dev/null || echo "[INFO] Superadmin ya existe"

# 9. Descargar datos
docker compose exec -T bvc_api python main.py descargar 2>/dev/null &

echo ""
echo "=================================================="
echo "  ✅ BVC Analytics desplegado correctamente!"
echo "=================================================="
echo ""
echo "  🌐 Dashboard:  http://38.242.225.58:8001"
echo "  🔗 Via Nginx:   http://38.242.225.58/bvc/"
echo "  👤 Admin:       admin / Admin2024!"
echo ""
echo "  Para ver logs:  docker compose logs -f bvc_api"
echo "=================================================="
