"""
Admin do app SAC / Suporte.

SacSuporteAdmin — visível e gerenciável apenas por superusuários.
Registros são criados via formulário público; o admin permite
leitura e exclusão.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from .models import SacSuporte


@admin.register(SacSuporte)
class SacSuporteAdmin(UnfoldModelAdmin):
    """Admin read-only de mensagens SAC — exclusivo para superusuários."""

    # ── Listagem ──────────────────────────────────────────────────────────────
    list_display = ("usuario", "tipo", "criado_em")
    list_filter = ("tipo", "criado_em")
    search_fields = ("usuario__email", "usuario__nome_completo", "mensagem")
    date_hierarchy = "criado_em"
    ordering = ("-criado_em",)

    # ── Detalhe somente leitura ───────────────────────────────────────────────
    readonly_fields = ("usuario", "tipo", "mensagem", "criado_em")
    fieldsets = (
        (None, {"fields": ("usuario", "tipo", "criado_em")}),
        ("Mensagem", {"fields": ("mensagem",)}),
    )

    # ── Permissões ────────────────────────────────────────────────────────────
    def has_module_perms(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False  # inserção somente via formulário público

    def has_change_permission(self, request, obj=None):
        return False  # registro imutável

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
