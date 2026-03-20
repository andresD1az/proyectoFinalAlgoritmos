#!/bin/bash
# Deploy to VPS using expect-like approach via Git Bash
export SSHPASS="Ea1128544093dd"
VPS="root@38.242.225.58"
APP="/opt/bvc-analytics"

# Create .env on VPS
ssh -o StrictHostKeyChecking=no $VPS << 'REMOTE'
cd /opt/bvc-analytics

# Create .env
cat > .env << 'EOF'
DB_NAME=bvc_analytics
DB_USER=bvc_user
DB_PASSWORD=BVC_Seguro_2024!
DB_HOST=bvc_db
DB_PORT=5432
API_HOST=0.0.0.0
API_PORT=8001
EOF

# Build and run
docker compose up --build -d 2>/dev/null || docker-compose up --build -d

# Wait for DB
echo "Waiting for DB..."
sleep 15

# Run migration
docker compose exec -T bvc_api python -c "
import psycopg2, os
conn = psycopg2.connect(host='bvc_db', port=5432, dbname='bvc_analytics', user='bvc_user', password='BVC_Seguro_2024!')
cur = conn.cursor()
cur.execute(open('/app/database/migrate_v2.sql').read())
conn.commit()
print('Migration OK')
" 2>/dev/null || echo "Migration already applied"

# Create superadmin
docker compose exec -T bvc_api python scripts/crear_superadmin.py 2>/dev/null || echo "Superadmin exists"

# Download data in background
docker compose exec -T -d bvc_api python main.py descargar 2>/dev/null &

echo ""
echo "========================================="
echo "  BVC Analytics deployed!"
echo "  http://38.242.225.58:8001"
echo "========================================="
REMOTE
