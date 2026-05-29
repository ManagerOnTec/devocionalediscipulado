"""
Admin base do app Core.

Fornece BaseModelAdmin — classe mixin para o admin de todos os models
que herdam de BaseModel.

Responsabilidades:
    - Preencher criado_por / atualizado_por automaticamente ao salvar.
    - Exibir campos de auditoria como somente leitura.
    - Filtrar somente registros ativos por padrão.
    - Permitir restaurar registros deletados via soft delete.

Uso:
    @admin.register(Devocional)
    class DevocionalAdmin(BaseModelAdmin):
        list_display = ["titulo", "is_active", "criado_por", "criado_em"]
"""

from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin as UnfoldModelAdmin


# ─────────────────────────────────────────────────────────────────────────────
# Campos de auditoria — sempre read-only
# ─────────────────────────────────────────────────────────────────────────────

# Campos exibidos como somente leitura em todos os formulários do admin
AUDIT_READONLY_FIELDS = (
    "criado_em",
    "atualizado_em",
    "criado_por",
    "atualizado_por",
    "deleted_at",
)

# Fieldset padrão de auditoria para inserir no final de todo ModelAdmin
AUDIT_FIELDSET = (
    "Auditoria",
    {
        "fields": AUDIT_READONLY_FIELDS,
        "classes": ("collapse",),  # colapsado por padrão para não poluir o form
        "description": "Informações de criação e alteração preenchidas automaticamente.",
    },
)


# ─────────────────────────────────────────────────────────────────────────────
# Mixin de acesso para usuários staff
# ─────────────────────────────────────────────────────────────────────────────

class StaffAccessMixin:
    """
    Concede acesso de visualização, adição e edição a qualquer usuário com
    is_staff, sem exigir permissões explícitas no banco de dados.

    A exclusão permanece restrita a superusuários (has_delete_permission deve
    ser definido separadamente em cada admin ou no BaseModelAdmin).

    Aplicar a ModelAdmins e InlineModelAdmins que devem seguir esta política.
    """

    def has_module_perms(self, request):
        # Garante que o app apareça no índice do admin para is_staff.
        return request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_add_permission(self, request, obj=None):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff


# ─────────────────────────────────────────────────────────────────────────────
# SuperuserOnlyMixin — acesso exclusivo a superusuários
# ─────────────────────────────────────────────────────────────────────────────

class SuperuserOnlyMixin:
    """
    Restringe visualização e edição a superusuários.
    Impede adição e exclusão (adequado para singletons de configuração).
    """

    def has_module_perms(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request, obj=None):
        return False  # singleton — não permite novo registro

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False  # singleton — não permite exclusão


# ─────────────────────────────────────────────────────────────────────────────
# BaseModelAdmin — mixin base para todos os ModelAdmins do projeto
# ─────────────────────────────────────────────────────────────────────────────

class BaseModelAdmin(StaffAccessMixin, UnfoldModelAdmin):
    """
    ModelAdmin base para models que herdam de BaseModel.

    Funcionalidades incluídas:
        - readonly_fields: todos os campos de auditoria são somente leitura.
        - save_model:      preenche criado_por e atualizado_por com o usuário logado.
        - get_queryset:    exibe somente registros ativos (is_active=True).
        - list_filter:     inclui filtro por is_active.
        - actions:         ação de soft-delete e restauração em lote.
        - get_fieldsets:   adiciona o bloco "Auditoria" automaticamente ao final.

    Como usar:
        @admin.register(MeuModel)
        class MeuModelAdmin(BaseModelAdmin):
            list_display = ["__str__", "is_active", "criado_em"]
            # Adicionar seus fieldsets ANTES de chamar super(), se necessário.
    """

    # ── django-unfold ─────────────────────────────────────────────────────────
    # Campos compactados verticalmente no formulário
    compressed_fields = True
    # Alerta ao tentar sair com alterações não salvas
    warn_unsaved_changes = True
    # Botão Submit nos filtros laterais (aplica vários filtros de uma vez)
    list_filter_submit = True

    # ── Campos sempre somente leitura ─────────────────────────────────────────
    readonly_fields = AUDIT_READONLY_FIELDS

    # ── Filtros padrão ────────────────────────────────────────────────────────
    list_filter = ("is_active",)

    # ── Ações em lote ─────────────────────────────────────────────────────────
    actions = ["action_desativar", "action_restaurar"]

    # ── QuerySet: somente ativos por padrão ───────────────────────────────────

    def get_queryset(self, request):
        """
        Retorna somente registros ativos por padrão.
        Para ver todos (inclusive deletados), sobrescrever e usar all_objects.
        """
        # Usa o manager padrão (ActiveManager) — filtra is_active=True
        return self.model.objects.all()

    # ── Preencher usuário responsável ─────────────────────────────────────────

    def save_model(self, request, obj, form, change):
        """
        Preenche criado_por (apenas na criação) e atualizado_por (sempre).
        O usuário logado no admin é automaticamente registrado.
        """
        if not change:
            # Criação: registra o usuário que criou
            obj.criado_por = request.user

        # Atualização: sempre registra quem atualizou por último
        obj.atualizado_por = request.user

        super().save_model(request, obj, form, change)

    # ── Fieldsets: injeta bloco de auditoria ao final ─────────────────────────

    def get_fieldsets(self, request, obj=None):
        """Adiciona o fieldset de Auditoria ao final do formulário."""
        fieldsets = list(super().get_fieldsets(request, obj))

        # Evita duplicação se a subclasse já incluiu o fieldset de auditoria
        fieldset_titles = [fs[0] for fs in fieldsets]
        if "Auditoria" not in fieldset_titles:
            fieldsets.append(AUDIT_FIELDSET)

        return fieldsets

    # ── readonly_fields: mescla com os da subclasse ───────────────────────────

    def get_readonly_fields(self, request, obj=None):
        """Garante que os campos de auditoria sejam sempre somente leitura."""
        readonly = set(super().get_readonly_fields(request, obj))
        readonly.update(AUDIT_READONLY_FIELDS)
        return tuple(readonly)

    # ── Controle de exclusão: somente superusuários ────────────────────────────

    def has_delete_permission(self, request, obj=None):
        """
        Somente superusuários podem excluir registros no admin.
        Usuários com is_staff (sem is_superuser) podem editar mas não excluir.
        """
        return request.user.is_superuser

    # ── Ações em lote ─────────────────────────────────────────────────────────

    @admin.action(description="Desativar selecionados (soft delete)")
    def action_desativar(self, request, queryset):
        """Soft delete em lote: marca is_active=False sem deletar do banco."""
        total = queryset.count()
        queryset.delete()  # chama SoftDeleteQuerySet.delete()
        self.message_user(
            request,
            f"{total} registro(s) desativado(s) com sucesso.",
        )

    @admin.action(description="Restaurar selecionados")
    def action_restaurar(self, request, queryset):
        """Restaura registros previamente desativados via soft delete."""
        total = queryset.count()
        queryset.update(is_active=True, deleted_at=None)
        self.message_user(
            request,
            f"{total} registro(s) restaurado(s) com sucesso.",
        )

    # ── Exibição: indicador visual de status ativo/inativo ───────────────────

    @admin.display(description="Status", ordering="is_active")
    def status_badge(self, obj):
        """
        Exibe um badge colorido de Ativo/Inativo na listagem do admin.

        Adicionar 'status_badge' ao list_display da subclasse para usar.
        """
        if obj.is_active:
            return format_html(
                '<span style="color:#198754;font-weight:bold;">● Ativo</span>'
            )
        return format_html(
            '<span style="color:#dc3545;font-weight:bold;">● Inativo</span>'
        )
