"""
auth/auth.py — Sistema de Autenticación
SIN librerías externas: hashlib + secrets + hmac (todos stdlib de Python)

Estrategia:
  - Contraseñas: SHA-256 con salt aleatorio (32 bytes hex)
  - Sesiones: token aleatorio de 64 bytes hex, guardado en PostgreSQL
  - Duración de sesión: 24 horas
"""

import hashlib
import secrets
import hmac
from datetime import datetime, timedelta
from etl.database import get_connection

SESSION_DURACION_HORAS = 24
BALANCE_INICIAL = 100_000.0   # USD virtuales para el simulador


# ─────────────────────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────────────────────

def _generar_salt() -> str:
    """Genera un salt aleatorio de 32 bytes (64 caracteres hex)."""
    return secrets.token_hex(32)


def _hash_password(password: str, salt: str) -> str:
    """
    Hashea una contraseña con SHA-256 + salt.
    SIN bcrypt ni argon2 — solo stdlib.

    Proceso:
      1. Concatenar salt + password
      2. Codificar a bytes UTF-8
      3. Aplicar SHA-256
      4. Retornar hex digest (64 caracteres)
    """
    combined = (salt + password).encode('utf-8')
    return hashlib.sha256(combined).hexdigest()


def _verificar_password(password: str, salt: str, stored_hash: str) -> bool:
    """
    Comparación segura usando hmac.compare_digest para evitar timing attacks.
    Un timing attack podría revelar cuántos caracteres coinciden si se usa ==.
    """
    computed = _hash_password(password, salt)
    return hmac.compare_digest(computed, stored_hash)


def _generar_token() -> str:
    """Token de sesión cryptográficamente seguro — 64 bytes = 128 chars hex."""
    return secrets.token_hex(64)


# ─────────────────────────────────────────────────────────────
# REGISTRO
# ─────────────────────────────────────────────────────────────

def registrar_usuario(username: str, email: str, password: str) -> dict:
    """
    Registra un nuevo usuario.

    Returns:
        {'ok': True, 'usuario_id': int}  o  {'error': str}
    """
    username = username.strip().lower()
    email    = email.strip().lower()

    if len(password) < 6:
        return {'error': 'La contraseña debe tener al menos 6 caracteres.'}
    if len(username) < 3:
        return {'error': 'El nombre de usuario debe tener al menos 3 caracteres.'}

    salt     = _generar_salt()
    pw_hash  = _hash_password(password, salt)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Verificar si ya existe
            cur.execute('SELECT id FROM usuarios WHERE username=%s OR email=%s',
                        (username, email))
            if cur.fetchone():
                return {'error': 'El usuario o correo ya existe.'}

            # Insertar nuevo usuario
            cur.execute("""
                INSERT INTO usuarios (username, email, password_hash, salt)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (username, email, pw_hash, salt))
            usuario_id = cur.fetchone()[0]

            # Crear portafolio virtual con balance inicial
            cur.execute("""
                INSERT INTO portafolio_balance (usuario_id, saldo_usd)
                VALUES (%s, %s);
            """, (usuario_id, BALANCE_INICIAL))

        conn.commit()
        return {'ok': True, 'usuario_id': usuario_id, 'username': username}
    except Exception as e:
        conn.rollback()
        return {'error': str(e)}
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────

def login_usuario(username: str, password: str) -> dict:
    """
    Autentica un usuario y crea una sesión.

    Returns:
        {'ok': True, 'token': str, 'username': str, 'usuario_id': int}
        o {'error': str}
    """
    username = username.strip().lower()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, password_hash, salt, username, email
                FROM usuarios
                WHERE username = %s;
            """, (username,))
            fila = cur.fetchone()

        if not fila:
            return {'error': 'Usuario o contraseña incorrectos.'}

        usuario_id, pw_hash, salt, uname, email = fila

        if not _verificar_password(password, salt, pw_hash):
            return {'error': 'Usuario o contraseña incorrectos.'}

        # Crear sesión
        token    = _generar_token()
        expira   = datetime.utcnow() + timedelta(hours=SESSION_DURACION_HORAS)

        with conn.cursor() as cur:
            # Limpiar sesiones anteriores del usuario
            cur.execute('DELETE FROM sesiones WHERE usuario_id = %s', (usuario_id,))
            cur.execute("""
                INSERT INTO sesiones (token, usuario_id, expira_en)
                VALUES (%s, %s, %s);
            """, (token, usuario_id, expira))

        conn.commit()
        return {
            'ok':         True,
            'token':      token,
            'usuario_id': usuario_id,
            'username':   uname,
            'email':      email,
            'expira_en':  expira.isoformat() + 'Z',
        }
    except Exception as e:
        conn.rollback()
        return {'error': str(e)}
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# VERIFICAR SESIÓN
# ─────────────────────────────────────────────────────────────

def verificar_sesion(token: str) -> dict | None:
    """
    Verifica que un token de sesión sea válido y no haya expirado.

    Returns:
        dict con info del usuario, o None si la sesión es inválida
    """
    if not token or len(token) != 128:
        return None

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.usuario_id, s.expira_en, u.username, u.email
                FROM sesiones s
                JOIN usuarios u ON u.id = s.usuario_id
                WHERE s.token = %s;
            """, (token,))
            fila = cur.fetchone()

        if not fila:
            return None

        usuario_id, expira, username, email = fila

        if datetime.utcnow() > expira:
            # Sesión expirada — limpiar
            with conn.cursor() as cur:
                cur.execute('DELETE FROM sesiones WHERE token = %s', (token,))
            conn.commit()
            return None

        return {
            'usuario_id': usuario_id,
            'username':   username,
            'email':      email,
        }
    except Exception as e:
        return None
    finally:
        conn.close()


def logout_usuario(token: str) -> None:
    """Invalida una sesión eliminando el token."""
    if not token:
        return
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM sesiones WHERE token = %s', (token,))
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def obtener_token_de_headers(handler) -> str | None:
    """
    Extrae el token de sesión desde la cookie 'bvc_session'.
    Parsea manualmente el header Cookie sin librerías externas.
    """
    cookie_header = handler.headers.get('Cookie', '')
    if not cookie_header:
        return None
    for parte in cookie_header.split(';'):
        nombre, _, valor = parte.strip().partition('=')
        if nombre.strip() == 'bvc_session':
            return valor.strip()
    return None
