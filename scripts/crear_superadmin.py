"""
scripts/crear_superadmin.py — Crea el usuario administrador del sistema

Ejecutar UNA SOLA VEZ después de levantar los contenedores:
  docker-compose exec bvc_api python scripts/crear_superadmin.py

Credenciales del superadmin:
  Usuario:    admin
  Contraseña: Admin2024!
  Email:      admin@bvc-analytics.local
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from autenticacion.auth import registrar_usuario
from etl.database import get_connection

ADMIN_USERNAME = "admin"
ADMIN_EMAIL    = "admin@bvc-analytics.local"
ADMIN_PASSWORD = "Admin2024!"

# Balance inicial del superadmin (más alto para pruebas)
BALANCE_USD_ADMIN = 1_000_000.00   # $1M USD virtuales
BALANCE_COP_ADMIN = 5_000_000_000  # $5.000M COP virtuales


def main():
    print("=" * 50)
    print("  BVC Analytics — Crear Superadmin")
    print("=" * 50)

    resultado = registrar_usuario(ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD)

    if 'error' in resultado:
        if 'ya existe' in resultado['error']:
            print(f"[INFO] El usuario '{ADMIN_USERNAME}' ya existe. Actualizando balance...")
            _actualizar_balance_admin()
        else:
            print(f"[ERROR] {resultado['error']}")
            sys.exit(1)
    else:
        print(f"[OK] Usuario '{ADMIN_USERNAME}' creado (ID: {resultado['usuario_id']})")
        _actualizar_balance_admin()

    print("\n¡Superadmin listo!")
    print(f"  Usuario:     {ADMIN_USERNAME}")
    print(f"  Contraseña:  {ADMIN_PASSWORD}")
    print(f"  Saldo USD:   ${BALANCE_USD_ADMIN:,.2f}")
    print(f"  Saldo COP:   ${BALANCE_COP_ADMIN:,.0f}")
    print(f"\nAbre: http://localhost:8001 e inicia sesión con estas credenciales.")


def _actualizar_balance_admin():
    """Ajusta el balance del admin a los valores de superadmin."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE portafolio_balance
                SET saldo_usd = %s, saldo_cop = %s
                WHERE usuario_id = (SELECT id FROM usuarios WHERE username = %s);
            """, (BALANCE_USD_ADMIN, BALANCE_COP_ADMIN, ADMIN_USERNAME))
        conn.commit()
        print(f"[OK] Balance de superadmin actualizado.")
    except Exception as e:
        print(f"[WARN] No se pudo actualizar balance: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
