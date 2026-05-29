"""
Callbacks para o painel administrativo Django — integração com django-unfold.

Funções:
    environment_callback  → badge de ambiente no cabeçalho do admin
    dashboard_callback    → injeta indicadores (KPIs) no dashboard

Referenciados em UNFOLD settings:
    UNFOLD["ENVIRONMENT"]          = "apps.core.admin_callbacks.environment_callback"
    UNFOLD["DASHBOARD_CALLBACK"]   = "apps.core.admin_callbacks.dashboard_callback"
"""

from django.contrib.auth import get_user_model


def environment_callback(request):
    """
    Exibe badge de ambiente no cabeçalho do admin.

    Retorna:
        [label, variante_cor]
        variante_cor: "info" | "warning" | "danger" | "success"
    """
    from django.conf import settings

    if settings.DEBUG:
        return ["Desenvolvimento", "warning"]
    return ["Produção", "danger"]


def dashboard_callback(request, context):
    """
    Adiciona cards de indicadores (KPIs) ao dashboard do admin.

    Injeta `context["indicators"]` com métricas de usuários.
    Reordena os modelos do app "estudo" na grade do dashboard.
    Recebe e retorna o dict de contexto do template admin/index.html.
    """
    User = get_user_model()

    total = User.objects.count()
    ativos = User.objects.filter(is_active=True).count()
    admins = User.objects.filter(is_staff=True).count()

    context["indicators"] = [
        {
            "title": "Total de Usuários",
            "metric": str(total),
            "icon": "people",
            "description": "Usuários cadastrados no sistema",
        },
        {
            "title": "Usuários Ativos",
            "metric": str(ativos),
            "icon": "check_circle",
            "description": "Com acesso ativo",
        },
        {
            "title": "Administradores",
            "metric": str(admins),
            "icon": "admin_panel_settings",
            "description": "Com acesso ao painel admin",
        },
    ]

    # Reordena modelos do app estudo: Trilha → Módulo → Tema → Progressos → Relação
    _ESTUDO_ORDER = ["Trilha", "Modulo", "Tema", "ProgressoTema"]
    for app in context.get("app_list", []):
        if app.get("app_label") == "estudo":
            app["models"].sort(
                key=lambda m: (
                    _ESTUDO_ORDER.index(m["object_name"])
                    if m["object_name"] in _ESTUDO_ORDER
                    else len(_ESTUDO_ORDER)
                )
            )
            break

    return context
