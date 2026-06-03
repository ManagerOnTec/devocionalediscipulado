"""
Configurações de DESENVOLVIMENTO.

Ativa DEBUG, ferramentas de dev (debug toolbar, ipython),
banco de dados local via Docker Compose.

Uso:
    DJANGO_SETTINGS_MODULE=config.settings.dev
"""

from decouple import config

from .base import *  # noqa: F401, F403

# ─── Debug ────────────────────────────────────────────────────────────────────

# Em desenvolvimento, DEBUG=True por padrão
DEBUG = config("DEBUG", default=True, cast=bool)

# ─── Apps extras de desenvolvimento ──────────────────────────────────────────

INSTALLED_APPS += [  # noqa: F405
    "debug_toolbar",
]

# ─── Middlewares extras de desenvolvimento ───────────────────────────────────

# Debug Toolbar deve ser inserido logo após CommonMiddleware
MIDDLEWARE.insert(  # noqa: F405
    MIDDLEWARE.index("django.middleware.common.CommonMiddleware") + 1,  # noqa: F405
    "debug_toolbar.middleware.DebugToolbarMiddleware",
)

# IPs que podem ver o Debug Toolbar
INTERNAL_IPS = ["127.0.0.1", "::1"]

# ─── Arquivos estáticos ───────────────────────────────────────────────────────

# Em dev, usa StaticFilesStorage simples — sem manifesto, sem collectstatic.
# base.py usa CompressedManifestStaticFilesStorage (manifesto obrigatório), que
# causaria ValueError ao chamar static() em Python quando staticfiles/ não existe.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ─── E-mail ───────────────────────────────────────────────────────────────────

# Imprime e-mails no console em vez de enviá-los
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ─── Logs detalhados em desenvolvimento ─────────────────────────────────────

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        # Reduz verbosidade de libs externas
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
