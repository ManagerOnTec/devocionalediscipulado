#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint do container Django
#
# Executado ao iniciar o container. Responsável por:
#   1. Aplicar migrações pendentes
#   2. Iniciar Gunicorn (produção) ou runserver (via override no compose)
# ─────────────────────────────────────────────────────────────────────────────

# Falha imediatamente se qualquer comando retornar erro
set -e

echo "==> Aguardando banco de dados ficar disponível..."
# Tenta conectar no banco antes de iniciar (retry simples)
python manage.py wait_for_db 2>/dev/null || true

echo "==> Aplicando migrações..."
python manage.py migrate --noinput

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "==> Iniciando Gunicorn na porta ${PORT:-8080}..."
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --timeout 120 \
    --keep-alive 5 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
