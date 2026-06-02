"""
Configurações de PRODUÇÃO.

DEBUG=False, HTTPS obrigatório, HSTS, Sentry, Cloud Run (GCP).
Segredos via Secret Manager GCP ou variáveis de ambiente.

Uso:
    DJANGO_SETTINGS_MODULE=config.settings.prod
"""

from datetime import timedelta

import sentry_sdk
from decouple import config
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F401, F403




# ─── Debug ────────────────────────────────────────────────────────────────────

# NUNCA ativar DEBUG em produção — expõe informações sensíveis
DEBUG = False

# ─── Sentry — monitoramento de erros ─────────────────────────────────────────

SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        # Amostragem de 10% das transações para performance (ajuste conforme uso)
        traces_sample_rate=0.1,
        # Não enviar dados pessoais do usuário para o Sentry
        send_default_pii=False,
        environment="production",
    )

# ─── Segurança HTTPS ─────────────────────────────────────────────────────────

# Cloud Run termina o TLS no load balancer; redireciona HTTP→HTTPS via proxy
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)

# Cookies seguros (HTTPS only)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Headers de segurança
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HSTS: instrui o browser a usar HTTPS por 1 ano
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cloud Run usa proxy reverso — lê o header X-Forwarded-Proto para HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Política de Referer: envia origem apenas para requests same-origin e HTTPS cross-origin
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# ─── E-mail via SMTP ─────────────────────────────────────────────────────────
# Todas as variáveis são obrigatórias — sem defaults em código.
# Gmail: ative verificação em 2 etapas e gere uma "Senha de app" (16 chars) em:
#   Conta Google → Segurança → Senhas de app
# Use a senha de app em EMAIL_HOST_PASSWORD — nunca a senha da conta.
#
# Variáveis obrigatórias no Cloud Run:
#   EMAIL_HOST          → smtp.gmail.com
#   EMAIL_PORT          → 587
#   EMAIL_USE_TLS       → True
#   EMAIL_USE_SSL       → False
#   EMAIL_HOST_USER     → seuemail@gmail.com
#   EMAIL_HOST_PASSWORD → senha-de-app-16-chars
#   DEFAULT_FROM_EMAIL  → Nome <seuemail@gmail.com>
#   SERVER_EMAIL        → seuemail@gmail.com

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", cast=int)
# TLS (porta 587) e SSL (porta 465) são mutuamente exclusivos.
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = config("SERVER_EMAIL")

# ─── GCS — armazenamento de arquivos de mídia (uploads) ─────────────────────
# Estáticos são servidos pelo WhiteNoise (sem GCS).
# Mídia (imagens de capa, uploads) vai para um bucket GCS.

GS_BUCKET_NAME = config("GS_BUCKET_NAME", default="")

if GS_BUCKET_NAME:
    GS_PROJECT_ID = config("GS_PROJECT_ID", default="")
    GS_DEFAULT_ACL = None                      # Sem ACL pública — acesso via URLs assinadas
    GS_QUERYSTRING_AUTH = False                 # Gera URLs assinadas temporárias
    GS_EXPIRATION = timedelta(minutes=120)     # Validade das URLs assinadas
    GS_FILE_OVERWRITE = False                  # Nunca sobrescreve arquivos com mesmo nome
    GS_MAX_MEMORY_SIZE = 5 * 1024 * 1024      # 5 MB — acima disso usa arquivo temp

    # Django 5: STORAGES dict substitui DEFAULT_FILE_STORAGE e STATICFILES_STORAGE
    STORAGES = {
        "default": {
            "BACKEND": "config.storage_backends.PrivateMediaStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/"

# ─── Logs de produção ────────────────────────────────────────────────────────

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            # Cloud Run coleta logs do stdout/stderr automaticamente
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
