"""
URLs do app Accounts — autenticação e perfil.

Namespace: accounts

Rotas disponíveis:
    /contas/entrar/                   → login
    /contas/sair/                     → logout
    /contas/cadastro/                 → registro
    /contas/perfil/                   → edição de perfil
    /contas/senha/alterar/            → alteração de senha
    /contas/senha/alterar/concluido/  → confirmação de senha alterada
    /contas/senha/recuperar/          → solicitar recuperação de senha
    /contas/senha/recuperar/enviado/  → confirmação de e-mail enviado
    /contas/senha/redefinir/<uidb64>/<token>/ → definir nova senha
    /contas/senha/redefinir/concluido/ → recuperação concluída
    /contas/dark-mode/                → toggle dark mode (AJAX POST)
"""

from django.urls import path

from .views import (
    CadastroView,
    CustomLoginView,
    CustomLogoutView,
    CustomPasswordChangeDoneView,
    CustomPasswordChangeView,
    CustomPasswordResetCompleteView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetDoneView,
    CustomPasswordResetView,
    PerfilView,
    ToggleDarkModeView,
)

app_name = "accounts"

urlpatterns = [
    # ── Autenticação básica ───────────────────────────────────────────────
    path("entrar/", CustomLoginView.as_view(), name="login"),
    path("sair/", CustomLogoutView.as_view(), name="logout"),
    path("cadastro/", CadastroView.as_view(), name="cadastro"),

    # ── Perfil ────────────────────────────────────────────────────────────
    path("perfil/", PerfilView.as_view(), name="perfil"),

    # ── Alteração de senha (usuário logado) ───────────────────────────────
    path("senha/alterar/", CustomPasswordChangeView.as_view(), name="password_change"),
    path(
        "senha/alterar/concluido/",
        CustomPasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),

    # ── Recuperação de senha (usuário esqueceu) ───────────────────────────
    path("senha/recuperar/", CustomPasswordResetView.as_view(), name="password_reset"),
    path(
        "senha/recuperar/enviado/",
        CustomPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "senha/redefinir/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "senha/redefinir/concluido/",
        CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),

    # ── Dark mode (AJAX) ──────────────────────────────────────────────────
    path("dark-mode/", ToggleDarkModeView.as_view(), name="toggle_dark_mode"),
]
