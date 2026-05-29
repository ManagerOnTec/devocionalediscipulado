"""
Views do app Accounts — autenticação e perfil do usuário.

Views disponíveis:
    CustomLoginView               → login via e-mail
    CustomLogoutView              → logout com mensagem de despedida
    CadastroView                  → registro de novo usuário
    PerfilView                    → edição do próprio perfil
    CustomPasswordChangeView      → alteração de senha (autenticado)
    CustomPasswordChangeDoneView  → confirmação de senha alterada
    CustomPasswordResetView       → solicitação de recuperação de senha
    CustomPasswordResetDoneView   → confirmação de e-mail enviado
    CustomPasswordResetConfirmView → definição da nova senha via token
    CustomPasswordResetCompleteView → recuperação concluída
    ToggleDarkModeView            → alterna dark/light mode (AJAX)

Todas as views são CBV, conforme padrão do projeto.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, UpdateView, View

from .forms import (
    AlterarSenhaForm,
    CustomUserCreationForm,
    LoginForm,
    PerfilForm,
    RecuperarSenhaForm,
)

User = get_user_model()


# ─── Login / Logout ───────────────────────────────────────────────────────────

class CustomLoginView(LoginView):
    """Login via e-mail com mensagem de boas-vindas."""

    template_name = "accounts/login.html"
    form_class = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Entrar"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        primeiro_nome = self.request.user.primeiro_nome
        messages.success(
            self.request,
            f"Bem-vindo(a), {primeiro_nome}! Que seu dia seja abençoado.",
        )
        return response


class CustomLogoutView(LogoutView):
    """Logout com mensagem de despedida."""

    next_page = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Você saiu do sistema. Até logo!")
        return super().dispatch(request, *args, **kwargs)


# ─── Cadastro ─────────────────────────────────────────────────────────────────

class CadastroView(FormView):
    """Registro de novo usuário com e-mail como identificador."""

    template_name = "accounts/cadastro.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        # Usuário já autenticado vai para home
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            "Conta criada com sucesso! Faça login para continuar.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Criar conta"
        return context


# ─── Perfil ───────────────────────────────────────────────────────────────────

class PerfilView(LoginRequiredMixin, UpdateView):
    """Edição do próprio perfil pelo usuário logado."""

    template_name = "accounts/perfil.html"
    form_class = PerfilForm
    success_url = reverse_lazy("accounts:perfil")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Perfil atualizado com sucesso!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Meu Perfil"
        return context


# ─── Alteração de senha ───────────────────────────────────────────────────────

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Alteração de senha pelo usuário autenticado."""

    template_name = "registration/password_change_form.html"
    form_class = AlterarSenhaForm
    success_url = reverse_lazy("accounts:password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Senha alterada com sucesso!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Alterar Senha"
        return context


class CustomPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    """Confirmação de senha alterada."""

    template_name = "registration/password_change_done.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Senha Alterada"
        return context


# ─── Recuperação de senha ─────────────────────────────────────────────────────

class CustomPasswordResetView(PasswordResetView):
    """Solicitar recuperação de senha via e-mail."""

    form_class = RecuperarSenhaForm
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.html"
    subject_template_name = "registration/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(
            self.request,
            "Se este e-mail estiver cadastrado, você receberá as instruções em breve.",
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Recuperar Senha"
        return context


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Confirmação de que o e-mail de recuperação foi enviado."""

    template_name = "registration/password_reset_done.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "E-mail Enviado"
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Definição da nova senha via link do e-mail."""

    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Senha redefinida com sucesso! Faça login com a nova senha.",
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Definir Nova Senha"
        return context


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Recuperação de senha concluída."""

    template_name = "registration/password_reset_complete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Recuperação Concluída"
        return context


# ─── Dark mode (toggle AJAX) ──────────────────────────────────────────────────

class ToggleDarkModeView(LoginRequiredMixin, View):
    """
    Alterna o dark mode do usuário autenticado.

    Método: POST
    Resposta: JSON {"dark_mode": <bool>}
    """

    def post(self, request):
        request.user.dark_mode = not request.user.dark_mode
        request.user.save(update_fields=["dark_mode", "atualizado_em"])
        return JsonResponse({"dark_mode": request.user.dark_mode})
