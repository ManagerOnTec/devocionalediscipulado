"""
URLs principais do projeto Devocional e Discipulado.

Inclui:
- Django Admin
- Apps locais
- Arquivos de mídia (apenas em desenvolvimento)
- Debug Toolbar (apenas em desenvolvimento)
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Painel administrativo do Django
    path("admin/", admin.site.urls),

    # Autenticação e perfil (login, logout, cadastro, senha, dark mode)
    path("contas/", include("apps.accounts.urls", namespace="accounts")),

    # App core (página inicial e rotas base)
    path("", include("apps.core.urls", namespace="core")),

    # App Estudo (unificação de Devocional e Discipulado)
    path("estudo/", include("apps.estudo.urls", namespace="estudo")),

    # SAC / Suporte ao usuário (formulário de contato — apenas autenticados)
    path("sac/", include("apps.sac.urls", namespace="sac")),
]

# Em desenvolvimento: serve arquivos de mídia e ativa Debug Toolbar
if settings.DEBUG:
    # Servir uploads localmente
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug Toolbar
    import debug_toolbar  # noqa: E402

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
