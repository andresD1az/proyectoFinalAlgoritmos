-- database/migrate_v2.sql
-- Migración completa: auth + simulador dual-moneda (USD + COP)
-- Ejecutar: docker exec bvc_db psql -U bvc_user -d bvc_db -f /app/database/migrate_v2.sql

-- ─── AUTH ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usuarios (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    email         VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(64)  NOT NULL,
    salt          VARCHAR(64)  NOT NULL,
    creado_en     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sesiones (
    token       VARCHAR(128) PRIMARY KEY,
    usuario_id  INTEGER      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    expira_en   TIMESTAMP    NOT NULL,
    creada_en   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sesiones_usuario ON sesiones(usuario_id);

-- ─── PORTAFOLIO VIRTUAL DUAL-MONEDA ───────────────────────────
-- Cada usuario tiene saldo en USD (internacional) y COP (colombiano)
CREATE TABLE IF NOT EXISTS portafolio_balance (
    usuario_id  INTEGER PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
    saldo_usd   NUMERIC(18, 4) NOT NULL DEFAULT 100000.00,
    saldo_cop   NUMERIC(20, 2) NOT NULL DEFAULT 250000000.00,
    actualizado TIMESTAMP DEFAULT NOW()
);

-- ─── POSICIONES ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS portafolio_posiciones (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER        NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    ticker          VARCHAR(10)    NOT NULL,
    cantidad        NUMERIC(14, 6) NOT NULL,
    precio_promedio NUMERIC(14, 4) NOT NULL,
    total_invertido NUMERIC(18, 4) NOT NULL,
    moneda          VARCHAR(3)     NOT NULL DEFAULT 'USD',  -- 'USD' o 'COP'
    UNIQUE(usuario_id, ticker)
);

-- ─── TRANSACCIONES ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS portafolio_transacciones (
    id         SERIAL PRIMARY KEY,
    usuario_id INTEGER        NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo       VARCHAR(10)    NOT NULL,
    ticker     VARCHAR(10)    NOT NULL,
    cantidad   NUMERIC(14, 6) NOT NULL,
    precio     NUMERIC(14, 4) NOT NULL,
    total      NUMERIC(18, 4) NOT NULL,
    moneda     VARCHAR(3)     NOT NULL DEFAULT 'USD',
    fecha      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transacciones_usuario
    ON portafolio_transacciones(usuario_id, fecha DESC);

-- ─── TASAS DE CAMBIO CACHE ────────────────────────────────────
-- Guarda la última tasa consultada para no re-descargar cada vez
CREATE TABLE IF NOT EXISTS tasas_cambio (
    par            VARCHAR(10) PRIMARY KEY,  -- ej: 'USD_COP'
    valor          NUMERIC(12, 4) NOT NULL,
    fuente         VARCHAR(50),
    actualizado_en TIMESTAMP DEFAULT NOW()
);

-- Insertar tasa inicial (referencia, se actualiza con Yahoo Finance)
INSERT INTO tasas_cambio (par, valor, fuente)
VALUES ('USD_COP', 4250.00, 'seed')
ON CONFLICT (par) DO NOTHING;

-- ─── ACTUALIZAR activos si columna mercado no existe ──────────
ALTER TABLE activos ADD COLUMN IF NOT EXISTS mercado VARCHAR(20) DEFAULT 'NYSE';
