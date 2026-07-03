"""
Configurações BASE do Django — compartilhadas entre todos os ambientes.

Não use este arquivo diretamente.
Use config.settings.dev  → desenvolvimento
Use config.settings.prod → produção
"""

from pathlib import Path

from decouple import Csv, config
from django.templatetags.static import static
from django.urls import reverse_lazy

# ─── Diretórios ──────────────────────────────────────────────────────────────

# Raiz do projeto Django (app/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─── Segurança ───────────────────────────────────────────────────────────────

# Chave secreta obrigatoriamente via variável de ambiente — NUNCA hardcode
SECRET_KEY = config("SECRET_KEY")

# Hosts permitidos via variável de ambiente (CSV: "localhost,meudominio.com")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# ─── Aplicações instaladas ───────────────────────────────────────────────────

DJANGO_APPS = [
    # django-unfold deve vir ANTES do contrib.admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.import_export",
    # Apps padrão do Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "rest_framework",       # API REST
    "django_filters",       # Filtros para queries
    "crispy_forms",         # Formulários Bootstrap
    "crispy_bootstrap5",    # Tema Bootstrap 5
    "simple_history",       # Auditoria de alterações
    "import_export",        # Import/Export de dados
    "storages",             # django-storages (GCS media em produção)
]

# Apps locais do projeto (dentro da pasta apps/)
LOCAL_APPS = [
    "apps.core",
    "apps.accounts",  # User customizado — deve vir antes de outros apps que referenciam User
    "apps.estudo",    # Unifica Devocional e Discipulado
    "apps.configuracoes",  # Configurações globais do sistema (singleton)
    "apps.sac",       # SAC / Suporte ao usuário
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─── Middlewares ──────────────────────────────────────────────────────────────

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise DEVE vir logo após SecurityMiddleware para servir estáticos
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Auditoria: registra o usuário que fez cada alteração no histórico
    "simple_history.middleware.HistoryRequestMiddleware",
    # Sessão configurável via banco de dados (deve vir após AuthenticationMiddleware)
    "apps.configuracoes.middleware.SessaoConfiguravelMiddleware",
]

# ─── URLs ─────────────────────────────────────────────────────────────────────

ROOT_URLCONF = "config.urls"

# ─── Templates ───────────────────────────────────────────────────────────────

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Diretório global de templates (base.html, componentes, etc.)
        "DIRS": [BASE_DIR / "templates"],
        # Também carrega templates dentro de cada app (app/templates/)
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Injeta dark_mode_active e dark_mode_theme em todos os templates
                "apps.accounts.context_processors.dark_mode",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ─── Banco de dados ───────────────────────────────────────────────────────────

# PostgreSQL — configurado via variáveis de ambiente
# DATABASE_URL tem prioridade (Neon / Cloud SQL via URL).
# Se não definida, usa as variáveis individuais DB_* (Docker Compose local).
_DATABASE_URL = config("DATABASE_URL", default="")
if _DATABASE_URL:
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.parse(
            _DATABASE_URL,
            conn_max_age=60,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME", default="devocionalediscipulado"),
            "USER": config("DB_USER", default="postgres"),
            "PASSWORD": config("DB_PASSWORD", default="postgres"),
            "HOST": config("DB_HOST", default="db"),
            "PORT": config("DB_PORT", default="5432"),
            "CONN_MAX_AGE": 60,
        }
    }

# ─── Modelo de usuário customizado ──────────────────────────────────────────

# Substitui o User padrão do Django pelo User customizado do app accounts.
# IMPORTANTE: deve ser definido antes de qualquer migration que referencie User.
AUTH_USER_MODEL = "accounts.User"

# ─── Validação de senhas ──────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── Internacionalização ──────────────────────────────────────────────────────

# Idioma: Português do Brasil
LANGUAGE_CODE = "pt-br"

# Fuso horário: São Paulo (UTC-3 / horário de Brasília)
TIME_ZONE = "America/Sao_Paulo"

# Ativa tradução de textos do Django para pt-br
USE_I18N = True

# Ativa suporte a fuso horário (armazena em UTC, exibe em TIME_ZONE)
USE_TZ = True

# ─── Arquivos estáticos ───────────────────────────────────────────────────────

# URL de acesso aos estáticos
STATIC_URL = "/static/"

# Destino do collectstatic (não commitado; gerado no build)
STATIC_ROOT = BASE_DIR / "staticfiles"

# Diretório com estáticos do projeto (CSS, JS, imagens globais)
STATICFILES_DIRS = [BASE_DIR / "static"]

# Backend de storage: WhiteNoise comprime e adiciona hash ao nome do arquivo
# CompressedManifestStaticFilesStorage → gera .gz e .br, fallback automático
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ─── Arquivos de mídia (uploads) ─────────────────────────────────────────────

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ─── Chave primária padrão ───────────────────────────────────────────────────

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Formulários (Crispy Forms + Bootstrap 5) ────────────────────────────────

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ─── Django REST Framework ───────────────────────────────────────────────────

REST_FRAMEWORK = {
    # Autenticação via sessão (cookie) — adequado para SPA e API interna
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    # Apenas usuários autenticados acessam a API por padrão
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Filtros usando django-filter
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    # Paginação padrão
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# ─── Sessão ──────────────────────────────────────────────────────────────────

# Tempo padrão de expiração da sessão (em segundos) — 120 minutos.
# Sobrescrito por SessaoConfiguravelMiddleware via ConfiguracaoSessao (banco).
SESSION_COOKIE_AGE = 120 * 60

# ─── E-mail ───────────────────────────────────────────────────────────────────

# Backend SMTP configurado via banco de dados (ConfiguracaoEmail).
# Em settings/dev.py o ConsoleEmailBackend sobrescreve esta configuração.
EMAIL_BACKEND = "apps.configuracoes.email_backend.DBEmailBackend"

# Remetente padrão — deve coincidir com o usuário configurado em ConfiguracaoEmail.
DEFAULT_FROM_EMAIL = "Devocional e Discipulado <admin@managerontecsolutions.com.br>"

# ─── Autenticação ────────────────────────────────────────────────────────────

# Usa URL nomeada — Django 3.2+ suporta reverse lazy em LOGIN_URL
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "accounts:login"

# ─── Django Unfold Admin ──────────────────────────────────────────────────────

UNFOLD = {
    # ── CSS customizado injetado no admin ─────────────────────────────────
    "STYLES": [
        lambda request: static("css/admin_overrides.css"),
    ],

    # ── Identidade do site ────────────────────────────────────────────────
    "SITE_TITLE": "Devocional e Discipulado",
    "SITE_HEADER": "Devocional e Discipulado",
    "SITE_URL": "/",
    # Ícone do Material Symbols exibido ao lado do site_header
    "SITE_SYMBOL": "menu_book",
    # Logo e favicons (livro aberto em static/images/)
    "SITE_LOGO": lambda request: static("images/logo.svg"),
    "SITE_FAVICONS": [
        {
            "href": lambda request: static("images/favicon.svg"),
            "rel": "icon",
            "type": "image/svg+xml",
        },
    ],

    # ── Funcionalidades ───────────────────────────────────────────────────
    "SHOW_HISTORY": True,           # Botão de histórico django-simple-history
    "SHOW_VIEW_ON_SITE": True,      # Botão "Ver no site" nas change views

    # ── Callbacks ─────────────────────────────────────────────────────────
    # Badge de ambiente (Desenvolvimento / Produção) no cabeçalho
    "ENVIRONMENT": "apps.core.admin_callbacks.environment_callback",
    # Indicadores KPI no dashboard
    "DASHBOARD_CALLBACK": "apps.core.admin_callbacks.dashboard_callback",

    # ── Paleta de cores — alinhada ao Bootstrap primary (#0d6efd) ─────────
    "COLORS": {
        "font": {
            "subtle-light": "107 114 128",
            "subtle-dark": "156 163 175",
            "default-light": "75 85 99",
            "default-dark": "209 213 219",
            "important-light": "17 24 39",
            "important-dark": "243 244 246",
        },
        "primary": {
            "50": "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
            "950": "23 37 84",
        },
    },

    # ── Barra lateral ─────────────────────────────────────────────────────
    "SIDEBAR": {
        "show_search": True,           # Campo de busca no topo da sidebar
        "show_all_applications": False, # Oculta o link "Ver todos os apps"
        "navigation": [
            {
                "title": "Painel",
                "separator": False,
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "Usuários & Acesso",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Usuários",
                        "icon": "people",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                        "permission": lambda request: request.user.is_staff or request.user.has_perm(
                            "accounts.view_user"
                        ),
                    },
                    {
                        "title": "Grupos de permissões",
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": lambda request: request.user.is_staff or request.user.has_perm(
                            "auth.view_group"
                        ),
                    },
                ],
            },
            {
                "title": "Estudos",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Trilhas",
                        "icon": "route",
                        "link": reverse_lazy("admin:estudo_trilha_changelist"),
                        "permission": lambda request: request.user.is_staff or request.user.has_perm(
                            "estudo.view_trilha"
                        ),
                    },
                    {
                        "title": "Módulos",
                        "icon": "view_module",
                        "link": reverse_lazy("admin:estudo_modulo_changelist"),
                        "permission": lambda request: request.user.is_staff or request.user.has_perm(
                            "estudo.view_modulo"
                        ),
                    },
                    {
                        "title": "Temas",
                        "icon": "article",
                        "link": reverse_lazy("admin:estudo_tema_changelist"),
                        "permission": lambda request: request.user.is_staff or request.user.has_perm(
                            "estudo.view_tema"
                        ),
                    },
                    {
                        "title": "Progressos",
                        "icon": "trending_up",
                        "link": reverse_lazy("admin:estudo_progressotema_changelist"),
                        "permission": lambda request: request.user.is_staff or request.user.has_perm(
                            "estudo.view_progressotema"
                        ),
                    },
                ],
            },
            {
                "title": "SAC / Suporte",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Mensagens recebidas",
                        "icon": "headset_mic",
                        "link": reverse_lazy("admin:sac_sacsuporte_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                ],
            },
            {
                "title": "Configurações",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Sessão",
                        "icon": "timer",
                        "link": reverse_lazy("admin:configuracoes_configuracaosessao_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "E-mail (SMTP)",
                        "icon": "mail",
                        "link": reverse_lazy("admin:configuracoes_configuracaoemail_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                ],
            },
        ],
    },

    # ── Abas de modelos relacionados (a ser expandido em etapas futuras) ──
    "TABS": [],
}
