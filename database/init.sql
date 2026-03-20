-- =============================================================
-- database/init.sql — Esquema inicial de la base de datos
-- Se ejecuta automáticamente al crear el contenedor por primera vez
-- =============================================================

-- ─── TABLA: activos ──────────────────────────────────────────
-- Catálogo de los 20 instrumentos financieros a analizar
CREATE TABLE IF NOT EXISTS activos (
    id        SERIAL PRIMARY KEY,
    ticker    VARCHAR(10)  NOT NULL UNIQUE,
    nombre    VARCHAR(100) NOT NULL,
    tipo      VARCHAR(20)  NOT NULL,   -- 'accion' | 'etf'
    mercado   VARCHAR(20)  NOT NULL,   -- 'NYSE' | 'NASDAQ' | etc.
    creado_en TIMESTAMP DEFAULT NOW()
);

-- ─── TABLA: precios ──────────────────────────────────────────
-- Datos OHLCV históricos (Open, High, Low, Close, Volume)
CREATE TABLE IF NOT EXISTS precios (
    id         SERIAL PRIMARY KEY,
    activo_id  INTEGER     NOT NULL REFERENCES activos(id) ON DELETE CASCADE,
    fecha      DATE        NOT NULL,
    apertura   NUMERIC(12, 4),
    maximo     NUMERIC(12, 4),
    minimo     NUMERIC(12, 4),
    cierre     NUMERIC(12, 4) NOT NULL,
    volumen    BIGINT,
    UNIQUE(activo_id, fecha)   -- No duplicar el mismo día para el mismo activo
);

CREATE INDEX IF NOT EXISTS idx_precios_activo_fecha
    ON precios(activo_id, fecha DESC);

-- ─── TABLA: resultados_similitud ─────────────────────────────
-- Almacena los resultados de los 4 algoritmos de similitud
CREATE TABLE IF NOT EXISTS resultados_similitud (
    id           SERIAL PRIMARY KEY,
    activo1_id   INTEGER     NOT NULL REFERENCES activos(id),
    activo2_id   INTEGER     NOT NULL REFERENCES activos(id),
    algoritmo    VARCHAR(20) NOT NULL,  -- 'euclidiana' | 'pearson' | 'coseno' | 'dtw'
    valor        NUMERIC(10, 6) NOT NULL,
    calculado_en TIMESTAMP DEFAULT NOW()
);

-- ─── TABLA: resultados_patrones ──────────────────────────────
-- Resultados del algoritmo de ventana deslizante
CREATE TABLE IF NOT EXISTS resultados_patrones (
    id           SERIAL PRIMARY KEY,
    activo_id    INTEGER      NOT NULL REFERENCES activos(id),
    fecha_inicio DATE         NOT NULL,
    fecha_fin    DATE         NOT NULL,
    patron       VARCHAR(50)  NOT NULL,  -- ej. '3_dias_alza', '5_dias_baja'
    valor_inicio NUMERIC(12, 4),
    valor_fin    NUMERIC(12, 4),
    variacion_pct NUMERIC(8, 4),
    calculado_en TIMESTAMP DEFAULT NOW()
);

-- ─── TABLA: resultados_volatilidad ───────────────────────────
CREATE TABLE IF NOT EXISTS resultados_volatilidad (
    id             SERIAL PRIMARY KEY,
    activo_id      INTEGER       NOT NULL REFERENCES activos(id),
    fecha          DATE          NOT NULL,
    ventana_dias   INTEGER       NOT NULL,
    volatilidad    NUMERIC(10, 6) NOT NULL,
    retorno_medio  NUMERIC(10, 6),
    calculado_en   TIMESTAMP DEFAULT NOW(),
    UNIQUE(activo_id, fecha, ventana_dias)
);

-- ─── TABLA: usuarios ──────────────────────────────────────────
-- Autenticación sin librerías externas: SHA-256 + salt manual
CREATE TABLE IF NOT EXISTS usuarios (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    email         VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(64)  NOT NULL,  -- SHA-256 hex digest
    salt          VARCHAR(64)  NOT NULL,  -- salt aleatorio 32 bytes
    creado_en     TIMESTAMP DEFAULT NOW()
);

-- ─── TABLA: sesiones ──────────────────────────────────────────
-- Tokens de sesión con expiración (24 horas por defecto)
CREATE TABLE IF NOT EXISTS sesiones (
    token       VARCHAR(128) PRIMARY KEY,  -- secrets.token_hex(64)
    usuario_id  INTEGER      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    expira_en   TIMESTAMP    NOT NULL,
    creada_en   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sesiones_usuario
    ON sesiones(usuario_id);

-- ─── TABLA: portafolio_balance ────────────────────────────────
-- Saldo virtual de cada usuario en el simulador
CREATE TABLE IF NOT EXISTS portafolio_balance (
    usuario_id  INTEGER PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
    saldo_usd   NUMERIC(14, 4) NOT NULL DEFAULT 100000.00,
    actualizado TIMESTAMP DEFAULT NOW()
);

-- ─── TABLA: portafolio_posiciones ────────────────────────────
-- Posiciones abiertas del usuario (acciones en su poder virtual)
CREATE TABLE IF NOT EXISTS portafolio_posiciones (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER        NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    ticker          VARCHAR(10)    NOT NULL,
    cantidad        NUMERIC(12, 4) NOT NULL,
    precio_promedio NUMERIC(12, 4) NOT NULL,  -- costo promedio ponderado
    total_invertido NUMERIC(14, 4) NOT NULL,
    UNIQUE(usuario_id, ticker)
);

-- ─── TABLA: portafolio_transacciones ─────────────────────────
-- Historial de operaciones del simulador
CREATE TABLE IF NOT EXISTS portafolio_transacciones (
    id         SERIAL PRIMARY KEY,
    usuario_id INTEGER        NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo       VARCHAR(10)    NOT NULL,  -- 'compra' | 'venta'
    ticker     VARCHAR(10)    NOT NULL,
    cantidad   NUMERIC(12, 4) NOT NULL,
    precio     NUMERIC(12, 4) NOT NULL,
    total      NUMERIC(14, 4) NOT NULL,
    fecha      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transacciones_usuario
    ON portafolio_transacciones(usuario_id, fecha DESC);

