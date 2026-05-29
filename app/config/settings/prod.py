"""
Configurações de PRODUÇÃO.

DEBUG=False, HTTPS obrigatório, HSTS, Sentry, Cloud Run (GCP).
Segredos via Secret Manager GCP ou variáveis de ambiente.

Uso:
    DJANGO_SETTINGS_MODULE=config.settings.prod
"""

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

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@example.com")

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
