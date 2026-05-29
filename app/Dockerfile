# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Devocional e Discipulado
#
# Build multi-stage otimizado para Cloud Run / DockerHub:
#   Stage 1 (builder): compila dependências Python
#   Stage 2 (runtime): imagem mínima de produção
#
# Uso local (Docker Compose usa target=builder):
#   docker build -t devocionalediscipulado .
#
# Uso produção (Cloud Run):
#   docker build --target runtime -t IMAGE_URL .
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Evita bytecode .pyc e garante logs imediatos no stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Desabilita cache do pip para reduzir tamanho
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instala dependências de compilação (libpq-dev para psycopg2)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas os arquivos de requirements para aproveitar o cache de camadas
COPY requirements/ requirements/

# Instala dependências em /install para copiar no stage runtime
RUN pip install --prefix=/install -r requirements/prod.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Variáveis de ambiente para produção
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Settings de produção por padrão
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    # Porta padrão do Cloud Run
    PORT=8080

WORKDIR /app

# Instala apenas a runtime lib do PostgreSQL (menor que o dev package)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copia os pacotes Python já instalados pelo builder
COPY --from=builder /install /usr/local

# Cria usuário não-root por segurança (evita rodar como root no container)
RUN groupadd --system appuser && useradd --system --gid appuser appuser

# Copia o código fonte da aplicação
COPY --chown=appuser:appuser . .

# Cria diretórios necessários com as permissões corretas
RUN mkdir -p staticfiles media \
    && chown -R appuser:appuser staticfiles media

# Coleta arquivos estáticos durante o build (WhiteNoise serve em produção)
# Variáveis mínimas necessárias para o collectstatic
RUN SECRET_KEY=build-only-not-used \
    python manage.py collectstatic --noinput

# Torna o entrypoint executável
RUN chmod +x scripts/entrypoint.sh

# Muda para o usuário não-root
USER appuser

# Documenta a porta exposta (Cloud Run usa a variável PORT)
EXPOSE 8080

# Ponto de entrada: aplica migrações e inicia Gunicorn
ENTRYPOINT ["sh", "scripts/entrypoint.sh"]
