"""
Admin do app Configurações.

Dois ModelAdmins singleton (um único registro, sem add/delete):
  - ConfiguracaoSessaoAdmin  → tempo de sessão
  - ConfiguracaoEmailAdmin   → credenciais SMTP

Acesso restrito a superusuários via SuperuserOnlyMixin.
O changelist redireciona automaticamente para o registro existente.
"""

from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from unfold.admin import ModelAdmin as UnfoldModelAdmin

from apps.core.admin import SuperuserOnlyMixin

from .models import ConfiguracaoEmail, ConfiguracaoSessao


# ─────────────────────────────────────────────────────────────────────────────
# Mixin Singleton — redireciona changelist → change view
# ─────────────────────────────────────────────────────────────────────────────

class SingletonAdminMixin:
    """
    Redireciona o changelist direto para o único registro existente.
    Garante que o registro exista antes do redirecionamento.
    """

    def changelist_view(self, request, extra_context=None):
        obj = self.model.get_solo()
        url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[obj.pk],
        )
        return HttpResponseRedirect(url)


# ─────────────────────────────────────────────────────────────────────────────
# Formulário para ConfiguracaoEmail (campo senha virtual)
# ─────────────────────────────────────────────────────────────────────────────

class ConfiguracaoEmailAdminForm(forms.ModelForm):
    """
    Expõe campo 'senha' como PasswordInput em vez do campo criptografado.

    Regra: se o campo senha for enviado em branco, a senha atual é mantida.
    """

    senha = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text=(
            "<br><strong>Gmail / Google Workspace:</strong> use uma <em>Senha de App</em> "
            "(Conta Google → Segurança → Senhas de app), nunca a senha da conta."
            "<br><strong>Outros provedores (Outlook, Yahoo, Zoho, servidor próprio, etc.):</strong> "
            "use a senha normal da conta de e-mail."
        ),
    )

    class Meta:
        model = ConfiguracaoEmail
        exclude = ["senha_criptografada"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        senha = self.cleaned_data.get("senha", "").strip()
        if senha:
            instance.set_senha(senha)
        if commit:
            instance.save()
        return instance


# ─────────────────────────────────────────────────────────────────────────────
# Admins
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(ConfiguracaoSessao)
class ConfiguracaoSessaoAdmin(SuperuserOnlyMixin, SingletonAdminMixin, UnfoldModelAdmin):
    """Admin singleton para tempo de sessão."""

    fieldsets = [
        (
            "Tempo de Sessão",
            {
                "fields": ("tempo_sessao_minutos",),
                "description": (
                    "Define quantos minutos de inatividade encerram a sessão do usuário. "
                    "O valor é aplicado imediatamente (via cache de 60 s) sem reiniciar o servidor."
                ),
            },
        ),
    ]

    compressed_fields = True
    warn_unsaved_changes = True


@admin.register(ConfiguracaoEmail)
class ConfiguracaoEmailAdmin(SuperuserOnlyMixin, SingletonAdminMixin, UnfoldModelAdmin):
    """Admin singleton para configuração SMTP."""

    form = ConfiguracaoEmailAdminForm

    fieldsets = [
        (
            "Servidor SMTP",
            {
                "fields": ("host", "porta", "usar_tls", "usar_ssl", "timeout_segundos"),
                "description": (
                    "Configuração padrão para Gmail/Google Workspace: "
                    "smtp.gmail.com · porta 587 · TLS ativado."
                ),
            },
        ),
        (
            "Credenciais",
            {
                "fields": ("usuario", "senha", "nome_exibicao"),
                "description": (
                    "<strong>Gmail / Google Workspace:</strong> use uma Senha de App — nunca a senha da conta "
                    "(Conta Google → Segurança → Autenticação em duas etapas → Senhas de app)."
                    "<br><strong>Outros provedores:</strong> informe a senha normal da conta "
                    
                ),
            },
        ),
    ]

    compressed_fields = True
    warn_unsaved_changes = True
