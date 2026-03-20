# =============================================================
# Dockerfile — Imagen Python para BVC Analytics API
# Base: python:3.11-slim (ligera, sin extras innecesarios)
# =============================================================

FROM python:3.11-slim

# Metadatos
LABEL maintainer="BVC Analytics"
LABEL description="API de análisis financiero BVC & ETFs"

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar dependencias primero (capa cacheada por Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Puerto expuesto (debe coincidir con API_PORT en config.py)
EXPOSE 8001

# Comando de inicio
CMD ["python", "main.py"]
