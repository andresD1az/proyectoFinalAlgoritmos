"""
cms/content.py — Contenido Educativo, Tasas de Cambio y Simulador de Paper Trading

Lecciones de educación financiera: sin trucos, sin palabras raras.
El simulador usa dinero virtual en USD y COP con tasas reales de Yahoo Finance.
"""

import urllib.request
import urllib.parse
import json as _json
from etl.database import get_connection

# ─────────────────────────────────────────────────────────────
# TASA DE CAMBIO USD/COP — Tiempo Real (Yahoo Finance)
# ─────────────────────────────────────────────────────────────

_YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
_HEADERS    = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

TASA_FALLBACK_USD_COP = 4250.0   # Valor de respaldo si Yahoo no responde


def obtener_tasa_usd_cop() -> dict:
    """
    Obtiene la tasa de cambio USD/COP en tiempo real desde Yahoo Finance.
    Ticker: COP=X  →  precio = cuántos COP vale 1 USD

    Sin librerías externas: usa urllib.request (stdlib).
    Guarda en caché de BD para reducir llamadas repetidas.

    Returns:
        {'usd_cop': 4250.0, 'cop_usd': 0.000235, 'fuente': 'Yahoo Finance'}
    """
    url = _YAHOO_BASE.format(ticker='COP=X') + '?interval=1d&range=1d'
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = _json.loads(resp.read().decode('utf-8'))
        precio = float(data['chart']['result'][0]['meta']['regularMarketPrice'])

        # Guardar en caché de BD
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO tasas_cambio (par, valor, fuente)
                    VALUES ('USD_COP', %s, 'Yahoo Finance')
                    ON CONFLICT (par) DO UPDATE
                        SET valor = EXCLUDED.valor,
                            fuente = EXCLUDED.fuente,
                            actualizado_en = NOW();
                """, (precio,))
            conn.commit()
            conn.close()
        except Exception:
            pass  # Si la tabla no existe aún, ignorar

        return {
            'usd_cop': round(precio, 2),
            'cop_usd': round(1 / precio, 8),
            'fuente':  'Yahoo Finance (COP=X)',
        }
    except Exception as e:
        # Intentar recuperar de BD
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT valor FROM tasas_cambio WHERE par = 'USD_COP'")
                fila = cur.fetchone()
            conn.close()
            if fila:
                p = float(fila[0])
                return {'usd_cop': p, 'cop_usd': round(1/p, 8), 'fuente': 'caché BD'}
        except Exception:
            pass
        return {
            'usd_cop': TASA_FALLBACK_USD_COP,
            'cop_usd': round(1 / TASA_FALLBACK_USD_COP, 8),
            'fuente':  f'fallback local ({e})',
        }


# ─────────────────────────────────────────────────────────────
# LECCIONES (CMS)
# ─────────────────────────────────────────────────────────────

LECCIONES = [
    {
        "id": 1,
        "titulo": "¿Qué es la Bolsa de Valores?",
        "categoria": "Fundamentos",
        "icono": "🏦",
        "duracion": "5 min",
        "contenido": """
## ¿Qué es la Bolsa de Valores?

Imagina un mercado de pulgas gigante, pero en vez de ropa y artículos usados, la gente compra y vende **partes de empresas**.

Cuando una empresa quiere crecer pero no tiene suficiente dinero, en vez de ir al banco, puede dividirse en millones de pequeñas partes llamadas **acciones** y venderlas a personas como tú.

### 🔑 Conceptos clave

**Acción:** Es una parte proporcional de una empresa. Si compras 1 acción de Ecopetrol, literalmente eres dueño de una pequeñísima fracción.

**Precio de la acción:** Sube cuando mucha gente quiere comprarla (hay confianza en la empresa) y baja cuando todos quieren venderla (hay desconfianza o malas noticias).

**Bolsa de Valores:** Es el lugar (hoy 100% digital) donde se realizan esas compras y ventas de forma ordenada y transparente.

### 🇨🇴 La BVC — Bolsa de Valores de Colombia

Es el mercado oficial de Colombia, donde cotizan empresas como:
- **Ecopetrol (EC)** → La empresa petrolera más grande del país
- **Bancolombia (CIB)** → Uno de los bancos más importantes
- **Grupo Nutresa** → La empresa de alimentos más conocida

### 💡 ¿Por qué existe?

Sin bolsa, si quisieras invertir en una empresa, tendrías que ir directamente a negociar con ella. La bolsa centraliza todo: un lugar donde cualquier persona puede participar con una comisión pequeña.

### 🔗 Recursos oficiales
- [Bolsa de Valores Colombia](https://www.bvc.com.co)
- [Superintendencia Financiera](https://www.superfinanciera.gov.co)
- [Educación financiera BVC](https://www.bvc.com.co/nueva/aprendamos)
        """
    },
    {
        "id": 2,
        "titulo": "Precio, Oferta y Demanda",
        "categoria": "Fundamentos",
        "icono": "📊",
        "duracion": "7 min",
        "contenido": """
## Cómo se forma el precio de una acción

El precio de cualquier activo en la bolsa se determina por **oferta y demanda**, exactamente igual que en cualquier mercado.

### ¿Qué mueve el precio?

**Hacia arriba (sube la demanda):**
- La empresa publicó ganancias mayores a las esperadas
- Hay una noticia positiva (nuevo contrato, expansión)
- El sector está en auge (ej. sube el petróleo → sube Ecopetrol)
- El mercado en general está optimista

**Hacia abajo (sube la oferta):**
- La empresa tuvo pérdidas
- Hay un escándalo o mala noticia
- El sector está en problemas
- El mercado en general está nervioso (ej. una crisis)

### 📈 El libro de órdenes (Order Book)

Detrás de cada precio hay una "subasta continua":

```
COMPRADORES          PRECIO         VENDEDORES
Quiero 100 acciones  $44.50 ←→      Tengo 50 acciones
Quiero 200 acciones  $44.45 ←→      Tengo 300 acciones
```

El precio al que más compradores y vendedores se ponen de acuerdo es el **precio de mercado**.

### 💡 Lección clave

El precio NO es la "realidad" de lo que vale una empresa. Es solo el **acuerdo** al que llegaron los últimos comprador y vendedor. Una empresa puede estar subvalorada o sobrevaluada durante años.

**Warren Buffett** basa toda su filosofía en encontrar empresas donde el precio de mercado es menor que el valor real — y esperar a que el mercado lo reconozca.

### 🔗 Recursos
- [Cómo funciona la BVC](https://www.bvc.com.co/pps/tibco/portalbvc/Home/Mercados/enlinea/acciones)
- [Investing.com — precios en tiempo real](https://es.investing.com/equities/colombia)
        """
    },
    {
        "id": 3,
        "titulo": "ETFs: Invierte en el mercado completo",
        "categoria": "Instrumentos",
        "icono": "🧺",
        "duracion": "6 min",
        "contenido": """
## ¿Qué es un ETF?

Un **ETF (Exchange-Traded Fund)** es como una canasta que contiene muchas acciones a la vez. En vez de comprar 500 empresas individualmente, compras 1 "canasta" que las representa a todas.

### Ejemplos reales que usamos en este proyecto

| ETF | Qué contiene | Precio aprox |
|-----|-------------|--------------|
| **SPY** | Las 500 empresas más grandes de EE.UU. (S&P 500) | ~$480 USD |
| **QQQ** | Las 100 tecnológicas más grandes (NASDAQ) | ~$400 USD |
| **GLD** | Sigue el precio del oro físico | ~$180 USD |
| **EWZ** | Acciones de las mayores empresas de Brasil | ~$30 USD |
| **GXG** | Acciones de las mayores empresas de Colombia | ~$15 USD |

### ¿Por qué son tan populares?

**1. Diversificación automática:** Si una empresa de SPY quiebra, te afecta solo 0.2% (porque hay 500 empresas).

**2. Bajo costo:** Un ETF cobra 0.03% anual. Un fondo de inversión tradicional cobra 1-2%.

**3. Líquidos:** Se compran y venden igual que una acción, en cualquier momento del horario del mercado.

### 💡 La estrategia más sencilla que existe

Muchos estudios académicos demuestran que comprar mensualmente el **SPY** (S&P&nbsp;500) y **no hacer nada más** ha superado históricamente al 90% de los gestores profesionales.

Esta estrategia se llama **Dollar-Cost Averaging (DCA)** o promedio del costo en dólares.

### 🔗 Recursos
- [iShares ETFs](https://www.ishares.com/us)
- [SPDR ETFs (SPY, GLD)](https://www.ssga.com/us/en/institutional/etfs)
        """
    },
    {
        "id": 4,
        "titulo": "Riesgo y Rentabilidad",
        "categoria": "Conceptos Clave",
        "icono": "⚖️",
        "duracion": "8 min",
        "contenido": """
## La Regla de Oro de las Inversiones

> **A mayor rentabilidad esperada, mayor riesgo asumido. No hay forma de escapar de esto.**

Esta es la regla más importante de las finanzas y la base de cualquier decisión de inversión seria.

### ¿Qué es el riesgo en una inversión?

En términos simples: la probabilidad de que tu dinero pierda valor, y cuánto puede perder.

En términos matemáticos: la **volatilidad** (σ) — qué tanto oscila el precio del activo.

### El espectro de riesgo/rentabilidad

```
MENOS RIESGO ←────────────────────────────→ MÁS RIESGO
MENOS RETORNO                               MÁS RETORNO

[Cuenta de ahorros] [TES/Bonos] [ETFs] [Acciones] [Crypto]
    ~3% anual          ~8%        ~10%    ~12-15%    0-1000%
```

### ¿Qué mide este proyecto?

**Volatilidad Anualizada (σ):** Qué tan fuerte "rebota" el precio.
- **<15%** → Conservador (ej. TLT, GLD)
- **15-30%** → Moderado (ej. SPY, QQQ)
- **>30%** → Agresivo (ej. acciones individuales, crypto)

**VaR (Value at Risk):** "¿Cuánto es lo máximo que puedo perder en un día malo con 95% de confianza?"
- Ejemplo: VaR 95% = -2.5% significa que en el 95% de los días, no perderás más del 2.5%

**Sharpe Ratio:** ¿Me pagan bien por el riesgo que asumo?
- <0: Peor que poner el dinero en un CDT
- 0-1: Aceptable pero mejorable
- >1: Excelente relación riesgo/retorno

### 💡 La trampa más común

**"Esta inversión garantiza el X% mensual sin riesgo"** → Esto es una ESTAFA o pirámide. No existe rentabilidad sin riesgo. Si te la prometen, te están mintiendo.

### 🔗 Recursos
- [AMV - Autorregulador del Mercado de Valores Colombia](https://www.amvcolombia.org.co)
- [Educación financiera Superfinanciera](https://www.superfinanciera.gov.co/inicio/consumidor-financiero/educacion-financiera)
        """
    },
    {
        "id": 5,
        "titulo": "Leer una Vela Japonesa (Candlestick)",
        "categoria": "Análisis Técnico",
        "icono": "🕯️",
        "duracion": "10 min",
        "contenido": """
## El lenguaje visual de los traders: las velas japonesas

Un gráfico de velas japonesas muestra 4 datos en una sola figura, inventado en el siglo XVIII por un comerciante de arroz japonés llamado Munehisa Homma.

### Anatomía de una vela

```
       │     ← Mecha superior: precio máximo del día
    ┌──┴──┐
    │     │  ← Cuerpo verde: el precio SUBIÓ (cierre > apertura)
    │     │     Cuerpo rojo: el precio BAJÓ (cierre < apertura)
    └──┬──┘
       │     ← Mecha inferior: precio mínimo del día
```

**Los 4 datos de cada vela:**
- **A (Apertura/Open):** Precio al que abrió el mercado ese día
- **M (Máximo/High):** Precio más alto alcanzado
- **m (Mínimo/Low):** Precio más bajo alcanzado
- **C (Cierre/Close):** Precio al que cerró el mercado ese día

### ¿Verde o rojo?

**🟢 Vela verde (alcista):** Cierre > Apertura. El precio subió durante el día.
**🔴 Vela roja (bajista):** Cierre < Apertura. El precio bajó durante el día.

### Patrones famosos (los que detecta nuestra plataforma)

**Golden Cross (Cruz Dorada) ✨**
La media móvil de 10 días cruza hacia arriba a la de 30 días.
Señal de que hay momentum alcista de corto plazo. Muchos traders compran aquí.

**Death Cross (Cruz de la Muerte) 💀**
La media móvil de 10 días cruza hacia abajo a la de 30 días.
Señal de que el mercado está perdiendo fuerza. Muchos traders venden aquí.

### ⚠️ Advertencia importante

**El análisis técnico NO es magia.** Los patrones son probabilísticos, no determinísticos. Una señal de compra puede fallar. Úsalos como UNA herramienta más, no como la única.

El análisis técnico funciona mejor cuando:
- El mercado tiene alta liquidez (muchos participantes)
- Se combina con análisis fundamental (fortaleza real de la empresa)
- Se establece un stop-loss (límite de pérdida aceptable)

### 🔗 Recursos
- [TradingView — practica gratis](https://www.tradingview.com/chart/)
- [Investopedia — candlestick patterns](https://www.investopedia.com/trading/candlestick-charting-what-is-it/)
        """
    },
    {
        "id": 6,
        "titulo": "Diversificación y Correlación",
        "categoria": "Estrategia",
        "icono": "🌐",
        "duracion": "9 min",
        "contenido": """
## No pongas todos los huevos en la misma canasta

Esta es la frase más repetida en finanzas porque es profundamente verdadera. Este principio tiene nombre: **diversificación**.

### ¿Por qué funciona?

Si inviertes todo en una sola empresa y esa empresa quiebra, pierdes todo.
Si inviertes en 20 empresas de diferentes sectores y países, y una quiebra, pierdes solo el 5%.

### La correlación: el ingrediente secreto

Aquí viene el concepto que pocas personas entienden bien: **no basta con tener muchas inversiones, deben moverse de forma diferente.**

**Correlación alta (r cercano a 1.0):**
Dos activos suben y bajan casi al mismo tiempo. Ej: SPY y QQQ.
Si el mercado cae, caen los dos → mala diversificación.

**Correlación baja o negativa (r cercano a 0 o -1):**
Dos activos se mueven independientemente o en dirección opuesta. Ej: Acciones de EE.UU. y Oro.
Si el mercado de acciones cae, el oro suele subir → buena diversificación.

### Lo que muestra el mapa de calor de esta plataforma

El mapa de calor 20×20 te muestra exactamente esto. Los colores más oscuros (rojo) significan correlación baja o negativa — esos activos se diversifican bien entre sí. Los colores verdes intensos (como SPY-QQQ) significan alta correlación — no aportan mucha diversificación.

### Portafolio bien diversificado (ejemplo)

| Activo | Clase | Peso | Por qué |
|--------|-------|------|---------|
| SPY | Acciones EE.UU. | 40% | Crecimiento de largo plazo |
| GLD | Oro | 20% | Protección en crisis |
| TLT | Bonos EE.UU. 20Y | 20% | Estabilidad, correlación negativa con acciones |
| EWZ | Acciones Brasil | 10% | Exposición a mercados emergentes |
| EC | Acciones Colombia | 10% | Mercado local |

### 🔗 Recursos
- [Modern Portfolio Theory — Investopedia](https://www.investopedia.com/terms/m/modernportfoliotheory.asp)
- [Portfolios Visualizer — simulación gratuita](https://www.portfoliovisualizer.com)
        """
    },
    {
        "id": 7,
        "titulo": "Cómo usar el Simulador (Paper Trading)",
        "categoria": "Práctica",
        "icono": "🎮",
        "duracion": "5 min",
        "contenido": """
## Paper Trading: aprende a invertir sin arriesgar dinero real

El **paper trading** es la práctica de simular compras y ventas de activos financieros con dinero ficticio («papel»), para aprender sin consecuencias reales.

Todos los grandes traders profesionales empezaron aquí. Es imposible aprender a manejar el riesgo sin experimentarlo primero en un ambiente seguro.

### Tu cuenta en el simulador

Comienzas con **$100,000 USD virtuales**. No es dinero real. No puedes perder nada. Pero los precios SÍ son reales (actualizados desde Yahoo Finance).

### Cómo operar

**Comprar un activo:**
1. Ve a la sección "💼 Simulador" en el menú
2. Selecciona un ticker (ej: SPY)
3. Ingresa la cantidad de acciones que quieres comprar
4. Haz clic en "Comprar"
5. Tu saldo se reducirá por el precio actual × cantidad

**Vender un activo:**
1. En la tabla de tu portafolio, busca el activo
2. Ingresa cuántas acciones quieres vender
3. Haz clic en "Vender"
4. Tu saldo se incrementará por el precio actual × cantidad

### Métricas de tu portafolio

- **P&L (Profit & Loss):** Cuánto has ganado o perdido en total
- **P&L %:** El porcentaje de ganancia/pérdida sobre tu inversión
- **Precio promedio:** Tu precio de compra promedio si compraste en varias ocasiones

### 💡 Retos para practicar

**Reto 1 - El conservador:** Construye un portafolio con σ < 15% y mantén una rentabilidad positiva por 1 mes.

**Reto 2 - El diversificador:** Compra activos que en el mapa de calor tengan correlación < 0.5 entre sí.

**Reto 3 - El técnico:** Solo compra cuando el algoritmo detecte un Golden Cross y vende en el Death Cross.

### ⚠️ Por qué el paper trading no es idéntico al trading real

La diferencia más grande es **la psicología**. Ver tu dinero real bajar un 10% causa pánico; ver tu dinero virtual bajar no te afecta igual. Por eso, cuando pases al trading real, empieza con cantidades muy pequeñas.
        """
    },
    {
        "id": 8,
        "titulo": "Mercados Internacionales: ¿Qué son y cómo acceder?",
        "categoria": "Mercados",
        "icono": "🌍",
        "duracion": "8 min",
        "contenido": """
## Los principales mercados del mundo

Aunque el mercado colombiano (BVC) es nuestro mercado local, los mercados globales ofrecen acceso a miles de empresas e instrumentos.

### Los 5 mercados más importantes

**🇺🇸 NYSE — New York Stock Exchange**
El más grande del mundo por capitalización bursátil.
Aquí cotizan: Coca-Cola, JPMorgan, Ecopetrol ADR (EC).
[→ www.nyse.com](https://www.nyse.com)

**🇺🇸 NASDAQ**
Especializado en tecnología. Aquí cotizan las grandes tech.
Amazon, Apple, Google, Meta, Netflix, Nvidia.
[→ www.nasdaq.com](https://www.nasdaq.com)

**🇬🇧 London Stock Exchange**
El mercado europeo más importante. Empresas como HSBC, BP, Shell.
[→ www.londonstockexchange.com](https://www.londonstockexchange.com)

**🇨🇳 Shanghai & Shenzhen Stock Exchange**
Los mercados asiáticos más relevantes. Acceso más limitado para extranjeros.

**🇧🇷 B3 — Bolsa de Brasil**
El mercado latinoamericano más grande. Accesible vía ETF EWZ.
[→ www.b3.com.br](https://www.b3.com.br)

### ¿Cómo accedo desde Colombia?

**Opción 1 — ETFs a través de tu bróker:**
Los ETFs como EWZ (Brasil), EWW (México), SPY (EE.UU.) ya cotizan en NYSE. Los puedes comprar como si fueran acciones colombianas a través de un bróker internacional.

**Opción 2 — Brókers habilitados en Colombia:**
- Acciones de EE.UU.: Davivienda Corredores, Bancolombia Capital
- Internacional completo: Interactive Brokers, XTB, Degiro

### Horarios de mercado

| Mercado | Hora Colombia |
|---------|--------------|
| NYSE / NASDAQ | 9:30 AM - 4:00 PM |
| BVC | 9:00 AM - 3:55 PM |
| London | 4:30 AM - 1:30 PM |

### 🔗 Recursos para traders colombianos
- [AMV — cómo invertir en Colombia](https://www.amvcolombia.org.co/para-todos/invertir-en-colombia/)
- [Deceval — depósito de valores Colombia](https://www.deceval.com.co)
- [Trading 212 — paper trading gratuito](https://www.trading212.com)
- [Yahoo Finance — datos globales gratuitos](https://finance.yahoo.com)
        """
    },
]


def obtener_lecciones():
    """Retorna la lista de todas las lecciones (sin contenido completo)."""
    return [{
        'id':       l['id'],
        'titulo':   l['titulo'],
        'categoria': l['categoria'],
        'icono':    l['icono'],
        'duracion': l['duracion'],
    } for l in LECCIONES]


def obtener_leccion(leccion_id: int) -> dict | None:
    """Retorna una lección completa por ID."""
    for l in LECCIONES:
        if l['id'] == leccion_id:
            return l
    return None


# ─────────────────────────────────────────────────────────────
# SIMULADOR DE PAPER TRADING
# ─────────────────────────────────────────────────────────────

def obtener_portafolio(usuario_id: int) -> dict:
    """
    Retorna el portafolio virtual del usuario:
    - Saldo USD disponible
    - Lista de posiciones (ticker, cantidad, precio_compra_promedio)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Saldo disponible
            cur.execute('SELECT saldo_usd FROM portafolio_balance WHERE usuario_id = %s',
                        (usuario_id,))
            fila = cur.fetchone()
            saldo = float(fila[0]) if fila else 0.0

            # Posiciones abiertas
            cur.execute("""
                SELECT ticker, cantidad, precio_promedio, total_invertido
                FROM portafolio_posiciones
                WHERE usuario_id = %s AND cantidad > 0
                ORDER BY ticker;
            """, (usuario_id,))
            posiciones = [
                {
                    'ticker':          row[0],
                    'cantidad':        float(row[1]),
                    'precio_promedio': float(row[2]),
                    'total_invertido': float(row[3]),
                }
                for row in cur.fetchall()
            ]

            # Historial de transacciones (últimas 20)
            cur.execute("""
                SELECT tipo, ticker, cantidad, precio, total, fecha
                FROM portafolio_transacciones
                WHERE usuario_id = %s
                ORDER BY fecha DESC
                LIMIT 20;
            """, (usuario_id,))
            transacciones = [
                {
                    'tipo':     row[0],
                    'ticker':   row[1],
                    'cantidad': float(row[2]),
                    'precio':   float(row[3]),
                    'total':    float(row[4]),
                    'fecha':    row[5].isoformat() if row[5] else '',
                }
                for row in cur.fetchall()
            ]

        return {
            'saldo_usd':     saldo,
            'posiciones':    posiciones,
            'transacciones': transacciones,
        }
    except Exception as e:
        return {'error': str(e), 'saldo_usd': 0, 'posiciones': [], 'transacciones': []}
    finally:
        conn.close()


def comprar_activo(usuario_id: int, ticker: str, cantidad: float) -> dict:
    """
    Simula la compra de un activo al precio actual de la BD.
    Descuenta el costo del saldo virtual del usuario.
    """
    from etl.database import obtener_precios
    ticker = ticker.upper().strip()

    if cantidad <= 0:
        return {'error': 'La cantidad debe ser mayor a 0.'}

    # Obtener precio actual (último registro en BD)
    precios = obtener_precios(ticker, 'cierre')
    if not precios:
        return {'error': f'No hay datos de precio para {ticker}.'}

    precio_actual = float(precios[-1]['cierre'])
    costo_total   = precio_actual * cantidad

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Verificar saldo
            cur.execute('SELECT saldo_usd FROM portafolio_balance WHERE usuario_id = %s',
                        (usuario_id,))
            fila = cur.fetchone()
            if not fila or float(fila[0]) < costo_total:
                return {'error': f'Saldo insuficiente. Tienes ${float(fila[0] if fila else 0):.2f} USD, necesitas ${costo_total:.2f} USD.'}

            saldo_nuevo = float(fila[0]) - costo_total

            # Actualizar saldo
            cur.execute('UPDATE portafolio_balance SET saldo_usd = %s WHERE usuario_id = %s',
                        (saldo_nuevo, usuario_id))

            # Actualizar posición (upsert)
            cur.execute("""
                INSERT INTO portafolio_posiciones
                    (usuario_id, ticker, cantidad, precio_promedio, total_invertido)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (usuario_id, ticker) DO UPDATE SET
                    cantidad        = portafolio_posiciones.cantidad + EXCLUDED.cantidad,
                    precio_promedio = (portafolio_posiciones.total_invertido + EXCLUDED.total_invertido) /
                                      (portafolio_posiciones.cantidad + EXCLUDED.cantidad),
                    total_invertido = portafolio_posiciones.total_invertido + EXCLUDED.total_invertido;
            """, (usuario_id, ticker, cantidad, precio_actual, costo_total))

            # Registrar transacción
            cur.execute("""
                INSERT INTO portafolio_transacciones
                    (usuario_id, tipo, ticker, cantidad, precio, total)
                VALUES (%s, 'compra', %s, %s, %s, %s);
            """, (usuario_id, ticker, cantidad, precio_actual, costo_total))

        conn.commit()
        return {
            'ok':          True,
            'ticker':      ticker,
            'cantidad':    cantidad,
            'precio':      precio_actual,
            'costo_total': costo_total,
            'saldo_nuevo': saldo_nuevo,
            'mensaje':     f'✅ Compraste {cantidad} acciones de {ticker} a ${precio_actual:.2f} cada una.',
        }
    except Exception as e:
        conn.rollback()
        return {'error': str(e)}
    finally:
        conn.close()


def vender_activo(usuario_id: int, ticker: str, cantidad: float) -> dict:
    """Simula la venta de un activo al precio actual de la BD."""
    from etl.database import obtener_precios
    ticker = ticker.upper().strip()

    if cantidad <= 0:
        return {'error': 'La cantidad debe ser mayor a 0.'}

    precios = obtener_precios(ticker, 'cierre')
    if not precios:
        return {'error': f'No hay datos de precio para {ticker}.'}

    precio_actual = float(precios[-1]['cierre'])
    valor_venta   = precio_actual * cantidad

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Verificar posición
            cur.execute("""
                SELECT cantidad, precio_promedio, total_invertido
                FROM portafolio_posiciones
                WHERE usuario_id = %s AND ticker = %s;
            """, (usuario_id, ticker))
            pos = cur.fetchone()
            if not pos or float(pos[0]) < cantidad:
                return {'error': f'No tienes suficientes acciones de {ticker}. Tienes {float(pos[0]) if pos else 0}.'}

            cant_restante    = float(pos[0]) - cantidad
            precio_promedio  = float(pos[1])
            pnl              = (precio_actual - precio_promedio) * cantidad
            total_restante   = precio_promedio * cant_restante

            # Actualizar posición o eliminar si se vendió todo
            if cant_restante > 0:
                cur.execute("""
                    UPDATE portafolio_posiciones
                    SET cantidad = %s, total_invertido = %s
                    WHERE usuario_id = %s AND ticker = %s;
                """, (cant_restante, total_restante, usuario_id, ticker))
            else:
                cur.execute("""
                    DELETE FROM portafolio_posiciones
                    WHERE usuario_id = %s AND ticker = %s;
                """, (usuario_id, ticker))

            # Actualizar saldo
            cur.execute("""
                UPDATE portafolio_balance
                SET saldo_usd = saldo_usd + %s
                WHERE usuario_id = %s
                RETURNING saldo_usd;
            """, (valor_venta, usuario_id))
            saldo_nuevo = float(cur.fetchone()[0])

            # Registrar transacción
            cur.execute("""
                INSERT INTO portafolio_transacciones
                    (usuario_id, tipo, ticker, cantidad, precio, total)
                VALUES (%s, 'venta', %s, %s, %s, %s);
            """, (usuario_id, ticker, cantidad, precio_actual, valor_venta))

        conn.commit()
        return {
            'ok':         True,
            'ticker':     ticker,
            'cantidad':   cantidad,
            'precio':     precio_actual,
            'valor_venta': valor_venta,
            'pnl':        pnl,
            'saldo_nuevo': saldo_nuevo,
            'mensaje':    f'✅ Vendiste {cantidad} acciones de {ticker} a ${precio_actual:.2f}. P&L: ${pnl:+.2f}',
        }
    except Exception as e:
        conn.rollback()
        return {'error': str(e)}
    finally:
        conn.close()
