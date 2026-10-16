# syntax=docker/dockerfile:1

# =====================================================================
# Etapa 1: builder -> compila dependencias (asyncmy requiere Cython/GCC
# porque no publica wheels para Python 3.14).
# =====================================================================
FROM python:3.14.6-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Herramientas de compilación necesarias para construir asyncmy desde el
# codigo fuente (extensiones Cython -> C).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv "$VIRTUAL_ENV"

RUN pip install --upgrade pip setuptools wheel cython

WORKDIR /build
COPY requirements.txt ./
RUN pip install -r requirements.txt

# =====================================================================
# Etapa 2: runtime -> imagen final ligera sin toolchain de compilacion.
# =====================================================================
FROM python:3.14.6-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Usuario sin privilegios para ejecutar la aplicacion.
RUN groupadd --system app && useradd --system --gid app --home /app app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY app ./app
COPY schema.sql ./schema.sql

USER app

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
