#!/bin/bash
cd /opt/bvc-analytics
sleep 5
docker compose exec -T bvc_api python -c "
import psycopg2
conn = psycopg2.connect(host='bvc_db', port=5432, dbname='bvc_analytics', user='bvc_user', password='BVC_Seguro_2024!')
cur = conn.cursor()
cur.execute(open('/app/database/migrate_v2.sql').read())
conn.commit()
cur.close()
conn.close()
print('Migration OK')
" 2>&1 || echo "Migration already done"

docker compose exec -T bvc_api python scripts/crear_superadmin.py 2>&1 || echo "Superadmin exists"

docker compose exec -T -d bvc_api python main.py descargar 2>/dev/null &
echo "Data download started in background"

echo ""
echo "========================================="
echo "  BVC deployed at http://38.242.225.58:8001"
echo "========================================="
