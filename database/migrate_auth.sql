-- database/migrate_auth.sql
-- Migración segura para agregar auth y simulador a una BD existente
-- Ejecutar: docker-compose exec bvc_db psql -U bvc_user -d bvc_db -f /docker-entrypoint-initdb.d/migrate_auth.sql

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

CREATE TABLE IF NOT EXISTS portafolio_balance (
    usuario_id  INTEGER PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
    saldo_usd   NUMERIC(14, 4) NOT NULL DEFAULT 100000.00,
    actualizado TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS portafolio_posiciones (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER        NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    ticker          VARCHAR(10)    NOT NULL,
    cantidad        NUMERIC(12, 4) NOT NULL,
    precio_promedio NUMERIC(12, 4) NOT NULL,
    total_invertido NUMERIC(14, 4) NOT NULL,
    UNIQUE(usuario_id, ticker)
);

CREATE TABLE IF NOT EXISTS portafolio_transacciones (
    id         SERIAL PRIMARY KEY,
    usuario_id INTEGER        NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo       VARCHAR(10)    NOT NULL,
    ticker     VARCHAR(10)    NOT NULL,
    cantidad   NUMERIC(12, 4) NOT NULL,
    precio     NUMERIC(12, 4) NOT NULL,
    total      NUMERIC(14, 4) NOT NULL,
    fecha      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transacciones_usuario
    ON portafolio_transacciones(usuario_id, fecha DESC);

-- Agregar columna mercado a activos si no existe
ALTER TABLE activos ADD COLUMN IF NOT EXISTS mercado VARCHAR(20) DEFAULT 'NYSE';
