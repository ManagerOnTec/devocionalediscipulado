"""
Admin do app Accounts — painel de gestão de usuários.

Usa django-unfold + BaseModelAdmin do core como base.
Herda UserAdmin para manter compatibilidade com o sistema de auth do Django
(gerenciamento de senha, permissões, grupos).

Recursos:
    - Seções organizadas: Autenticação, Perfil, Preferências, Permissões, Auditoria
    - Filtros por is_active, is_staff, timezone, dark_mode
    - Busca por email, nome_completo, telefone
    - Ação para ativar/desativar usuários em lote
    - Exibição de foto no list_display
    - Histórico de alterações via django-simple-history
"""

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db import IntegrityError, transaction
from django.utils.html import format_html
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from apps.core.admin import AUDIT_FIELDSET, AUDIT_READONLY_FIELDS, StaffAccessMixin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import User


# ── Filtro: mostra ativos por padrão ──────────────────────────────────────────────

class AtivoPorPadraoFilter(admin.SimpleListFilter):
    """
    Filtro de status com padrão em 'Ativo'.
    Sem parâmetro na URL = exibe apenas usuários ativos.
    """
    title = "Status"
    parameter_name = "ativo"

    def lookups(self, request, model_admin):
        return [
            ("sim", "Ativo"),
            ("nao", "Inativo"),
            ("todos", "Todos"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "nao":
            return queryset.filter(is_active=False)
        if self.value() == "todos":
            return queryset
        # Padrão (None ou "sim"): apenas ativos
        return queryset.filter(is_active=True)

    def choices(self, changelist):
        for lookup, title in [(None, "Ativo"), ("nao", "Inativo"), ("todos", "Todos")]:
            yield {
                "selected": self.value() == lookup or (lookup is None and self.value() is None),
                "query_string": (
                    changelist.get_query_string(remove=[self.parameter_name])
                    if lookup is None
                    else changelist.get_query_string({self.parameter_name: lookup})
                ),
                "display": title,
            }


@admin.register(User)
class CustomUserAdmin(StaffAccessMixin, UnfoldModelAdmin, UserAdmin):
    """
    Admin completo para o modelo User customizado.

    Herda de UnfoldModelAdmin (unfold.admin) + UserAdmin (django.contrib.auth),
    combinando o tema do unfold com o gerenciamento nativo de usuários, mantendo:
    - gerenciamento de hash de senha
    - formulários de criação/alteração separados
    - redefinição de senha pelo admin

    As funcionalidades do BaseModelAdmin (save_model, auditoria, badges)
    foram replicadas manualmente abaixo.
    """

    # ── django-unfold ─────────────────────────────────────────────────────────
    compressed_fields = True
    warn_unsaved_changes = True
    list_filter_submit = True

    # ── Formulários ───────────────────────────────────────────────────────────

    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    # ── Inlines ────────────────────────────────────────────────────

    inlines = []

    # ── Listagem ────────────────────────────────────────────────────

    list_display = (
        "foto_thumbnail",   # miniatura da foto
        "nome_completo",
        "email",
        "telefone",
        "timezone",
        "is_active",        # checkbox editável direto na listagem
        "is_staff",
        "is_superuser",
        "is_lider",
        "dark_mode",
        "criado_em",
    )
    list_display_links = ("foto_thumbnail", "nome_completo", "email")
    list_editable = ("is_active", "is_staff", "is_lider", "dark_mode")
    list_filter = (AtivoPorPadraoFilter, "is_staff", "is_superuser", "is_lider", "timezone", "dark_mode")
    search_fields = ("email", "nome_completo", "telefone")
    ordering = ("nome_completo",)
    list_per_page = 25

    # ── Formulário de edição — fieldsets ──────────────────────────────────────

    fieldsets = (
        (
            "Autenticação",
            {
                "fields": ("email", "password", "link_alterar_senha"),
                "description": "Credenciais de acesso ao sistema.",
            },
        ),
        (
            "Dados Pessoais",
            {
                "fields": ("nome_completo", "foto", "telefone"),
            },
        ),
        (
            "Preferências",
            {
                "fields": ("timezone", "dark_mode"),
            },
        ),
        (
            "Status da Conta",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "is_lider"),
            },
        ),
        (
            "Grupos",
            {
                "fields": ("groups",),
                "classes": ("collapse",),
                "description": (
                    "Grupos de acesso. Os grupos controlam quais trilhas com "
                    "\u201cPermissão específica\u201d o usuário pode acessar."
                ),
            },
        ),
        # Bloco de auditoria — apenas campos que existem no User
        (
            "Auditoria",
            {
                "fields": ("criado_em", "atualizado_em", "last_login"),
                "classes": ("collapse",),
                "description": "Informações de criação e último acesso.",
            },
        ),
    )

    # ── Formulário de criação — fieldsets ─────────────────────────────────────

    add_fieldsets = (
        (
            "Novo Usuário",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "nome_completo",
                    "telefone",
                    "password1",
                    "password2",
                ),
                "description": "Preencha os dados do novo usuário.",
            },
        ),
    )

    # ── Campos somente leitura ────────────────────────────────────────────────

    # Campos de auditoria + last_login são sempre somente leitura
    # User não herda BaseModel → criado_por/atualizado_por/deleted_at não existem
    readonly_fields = ("criado_em", "atualizado_em", "last_login", "link_alterar_senha")

    # ── Controle dinâmico de campos somente leitura ──────────────────────────────────────

    def get_readonly_fields(self, request, obj=None):
        readonly = set(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            # Apenas superusuários podem promover/revogar o nível de superusuário
            readonly.add("is_superuser")
        return tuple(readonly)

    # ── Controle de exclusão ───────────────────────────────────────────────────

    def has_delete_permission(self, request, obj=None):
        """Somente superusuários podem excluir usuários."""
        return request.user.is_superuser

    # ── Ações em lote ─────────────────────────────────────────────────────────

    actions = ["ativar_usuarios", "desativar_usuarios"]

    @admin.action(description="Ativar usuários selecionados")
    def ativar_usuarios(self, request, queryset):
        """Ativa os usuários selecionados (is_active=True)."""
        total = queryset.update(is_active=True)
        self.message_user(request, f"{total} usuário(s) ativado(s) com sucesso.")

    @admin.action(description="Desativar usuários selecionados")
    def desativar_usuarios(self, request, queryset):
        """Desativa os usuários selecionados sem excluí-los (is_active=False)."""
        # Impede o admin de se auto-desativar
        total = queryset.exclude(pk=request.user.pk).update(is_active=False)
        self.message_user(
            request,
            f"{total} usuário(s) desativado(s). O seu próprio usuário foi preservado.",
        )

    # ── Colunas customizadas no list_display ──────────────────────────────────

    @admin.display(description="Foto")
    def foto_thumbnail(self, obj):
        """Exibe miniatura circular da foto de perfil na listagem."""
        if obj.foto:
            return format_html(
                '<img src="{}" width="36" height="36" '
                'style="border-radius:50%;object-fit:cover;" '
                'alt="Foto de {}">',
                obj.foto.url,
                obj.nome_completo,
            )
        # Placeholder com inicial do nome
        inicial = (obj.nome_completo or obj.email)[0].upper()
        return format_html(
            '<div style="width:36px;height:36px;border-radius:50%;'
            'background:#0d6efd;color:#fff;display:flex;'
            'align-items:center;justify-content:center;'
            'font-weight:bold;font-size:14px;">{}</div>',
            inicial,
        )

    @admin.display(description="Status", ordering="is_active")
    def status_badge(self, obj):
        """Badge colorido de Ativo/Inativo para a listagem."""
        if obj.is_active:
            return format_html(
                '<span style="color:#198754;font-weight:bold;">● Ativo</span>'
            )
        return format_html(
            '<span style="color:#dc3545;font-weight:bold;">● Inativo</span>'
        )

    # ── Campo readonly: link para alteração de senha ───────────────────────────

    @admin.display(description="Alterar senha")
    def link_alterar_senha(self, obj):
        """Renderiza link direto para o formulário de alteração de senha."""
        if not obj or not obj.pk:
            return "—"
        return format_html(
            '<a href="../password/" class="button" '
            'style="display:inline-block;padding:6px 14px;border-radius:4px;'
            'background:#0d6efd;color:#fff;text-decoration:none;font-size:13px;">'
            '🔑 Alterar senha deste usuário</a>'
        )

    # ── save_model: preenche auditoria automaticamente ────────────────────────

    def save_model(self, request, obj, form, change):
        """
        Substitui o save_model padrão para registrar quem criou/atualizou.

        Nota: User não herda de BaseModel (para evitar referência circular),
        então a lógica de auditoria é replicada aqui.
        """
        # Nota: criado_por/atualizado_por não existem no User (referência circular).
        # O HistoricalRecords captura o usuário via simple_history middleware.
        super().save_model(request, obj, form, change)

    # ── get_search_results: autocomplete só retorna ativos ────────────────────────

    def get_search_results(self, request, queryset, search_term):
        """Quando chamado via autocomplete (outros admins), filtra apenas ativos."""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if "/autocomplete/" in request.path:
            queryset = queryset.filter(is_active=True)
        return queryset, use_distinct
    # ── delete_model / delete_queryset: trata FK de histórico ────────────────────

    _MSG_EXCLUIR_BLOQUEADO = (
        "Não é possível excluir este usuário pois existem registros históricos ou "
        "outros vínculos associados no banco de dados. "
        "Para desabilitar o acesso, desmarque a opção \u201cAtivo\u201d (is_active)."
    )

    def delete_model(self, request, obj):
        """Exibe mensagem amigável se houver FK impedindo a exclusão."""
        try:
            with transaction.atomic():
                super().delete_model(request, obj)
        except IntegrityError:
            self.message_user(request, self._MSG_EXCLUIR_BLOQUEADO, level=messages.ERROR)

    def delete_queryset(self, request, queryset):
        """Idem para exclusão em lote via action \u201cExcluir selecionados\u201d."""
        try:
            with transaction.atomic():
                super().delete_queryset(request, queryset)
        except IntegrityError:
            self.message_user(
                request,
                (
                    "Não foi possível excluir um ou mais usuários selecionados pois existem "
                    "registros históricos ou outros vínculos associados. "
                    "Desmarque \u201cAtivo\u201d (is_active) para desabilitar o acesso sem excluir."
                ),
                level=messages.ERROR,
            )