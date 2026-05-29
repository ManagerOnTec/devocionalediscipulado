"""
Models abstratos do app Core.

Hierarquia de herança recomendada para todos os models do projeto:

    MeuModel(BaseModel)          ← com usuário responsável + soft delete + histórico
    MeuModel(TimeStampedModel)   ← apenas timestamps, sem usuário (ex: logs)

Regras do projeto:
    - Sempre usar BaseModel como base dos models de domínio.
    - Nunca deletar registros fisicamente — usar soft delete (is_active=False).
    - Auditoria completa via django-simple-history (HistoricalRecords).
    - Timestamps armazenados em UTC; exibidos em America/Sao_Paulo (configurado em settings).
"""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


# ─────────────────────────────────────────────────────────────────────────────
# QuerySet com suporte a soft delete
# ─────────────────────────────────────────────────────────────────────────────

class SoftDeleteQuerySet(models.QuerySet):
    """
    QuerySet customizado que redireciona delete() para soft delete.

    Métodos disponíveis:
        .active()       → filtra apenas registros ativos (is_active=True)
        .deleted()      → filtra apenas registros desativados (is_active=False)
        .delete()       → soft delete em lote (is_active=False + deleted_at)
        .hard_delete()  → deleção física irreversível (usar com cuidado)
    """

    def active(self):
        """Retorna apenas registros não deletados."""
        return self.filter(is_active=True)

    def deleted(self):
        """Retorna apenas registros marcados como deletados."""
        return self.filter(is_active=False)

    def delete(self):
        """
        Soft delete em lote: marca todos como inativos.
        Preserva os dados no banco para auditoria.
        """
        return self.update(is_active=False, deleted_at=timezone.now())

    def hard_delete(self):
        """
        Deleção física irreversível.
        Usar apenas quando estritamente necessário (ex: LGPD, dados de teste).
        """
        return super().delete()


# ─────────────────────────────────────────────────────────────────────────────
# Managers
# ─────────────────────────────────────────────────────────────────────────────

class ActiveManager(models.Manager):
    """
    Manager padrão: retorna APENAS registros ativos (is_active=True).

    Usado como `objects` no BaseModel.
    Garante que queries acidentais não retornem dados deletados.
    """

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).active()


class AllObjectsManager(models.Manager):
    """
    Manager alternativo: retorna TODOS os registros (ativos e deletados).

    Acessível via `MeuModel.all_objects.all()`.
    Útil para relatórios de auditoria e painel admin.
    """

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


# ─────────────────────────────────────────────────────────────────────────────
# Model base de timestamps (mínimo — sem usuário, sem soft delete)
# ─────────────────────────────────────────────────────────────────────────────

class TimeStampedModel(models.Model):
    """
    Model abstrato com campos de data/hora automáticos.

    Usar quando NÃO for necessário rastrear usuário responsável.
    Ex: logs de sistema, tokens, notificações.

    Campos:
        criado_em    → preenchido automaticamente na criação
        atualizado_em → atualizado automaticamente a cada save()
    """

    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
        # Armazenado em UTC; exibido em America/Sao_Paulo via USE_TZ=True
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    class Meta:
        abstract = True
        ordering = ["-criado_em"]


# ─────────────────────────────────────────────────────────────────────────────
# BaseModel — modelo base completo para todos os domínios do projeto
# ─────────────────────────────────────────────────────────────────────────────

class BaseModel(models.Model):
    """
    Model abstrato base do projeto Devocional e Discipulado.

    Fornece de forma padronizada:
        ✔ Timestamps automáticos  (criado_em, atualizado_em)
        ✔ Rastreamento de usuário (criado_por, atualizado_por)
        ✔ Soft delete             (is_active, deleted_at)
        ✔ Auditoria completa      (HistoricalRecords — django-simple-history)

    Uso:
        class Devocional(BaseModel):
            titulo = models.CharField(max_length=200)

            class Meta(BaseModel.Meta):
                verbose_name = "Devocional"
                verbose_name_plural = "Devocionais"

    Managers disponíveis:
        Devocional.objects          → somente ativos (padrão)
        Devocional.all_objects      → todos, inclusive deletados
        Devocional.objects.deleted()→ somente deletados

    Notas de timezone:
        - Todos os DateTimeField são armazenados em UTC no banco.
        - A exibição no admin e templates usa o fuso America/Sao_Paulo,
          configurado em settings.TIME_ZONE.
    """

    # ── Timestamps ────────────────────────────────────────────────────────────

    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
        help_text="Data e hora de criação (UTC, exibido em horário de Brasília).",
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
        help_text="Data e hora da última alteração (UTC, exibido em horário de Brasília).",
    )

    # ── Rastreamento de usuário ───────────────────────────────────────────────

    criado_por = models.ForeignKey(
        # Referência lazy ao modelo User — compatível com AUTH_USER_MODEL customizado
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_criados",
        verbose_name="Criado por",
        help_text="Usuário que criou este registro.",
    )
    atualizado_por = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_atualizados",
        verbose_name="Atualizado por",
        help_text="Último usuário a alterar este registro.",
    )

    # ── Soft delete ───────────────────────────────────────────────────────────

    is_active = models.BooleanField(
        default=True,
        db_index=True,          # índice para queries frequentes por is_active
        verbose_name="Ativo",
        help_text=(
            "Desmarque para desativar o registro sem excluí-lo do banco. "
            "Registros inativos não aparecem nas listagens padrão."
        ),
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,         # não exibir no formulário admin
        verbose_name="Deletado em",
        help_text="Preenchido automaticamente ao desativar o registro.",
    )

    # ── Auditoria completa (django-simple-history) ────────────────────────────

    # Registra TODAS as alterações (create/update/delete) com usuário e timestamp.
    # Acessível via: instancia.history.all()
    history = HistoricalRecords(inherit=True)

    # ── Managers ──────────────────────────────────────────────────────────────

    # Manager padrão: filtra somente ativos — evita retornar dados deletados por engano
    objects = ActiveManager()

    # Manager auxiliar: retorna todos os registros (inclusive inativos)
    all_objects = AllObjectsManager()

    # ── Meta ──────────────────────────────────────────────────────────────────

    class Meta:
        abstract = True
        ordering = ["-criado_em"]

    # ── Soft delete — métodos de instância ────────────────────────────────────

    def delete(self, using=None, keep_parents=False):
        """
        Sobrescreve delete() para realizar SOFT DELETE.

        Em vez de remover o registro do banco, marca:
            is_active = False
            deleted_at = agora (UTC)

        Para deleção física, usar hard_delete().
        """
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_active", "deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        """
        Deleção física irreversível do banco de dados.

        Usar somente quando necessário por obrigação legal (LGPD)
        ou em scripts de limpeza controlados.
        """
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """
        Restaura um registro previamente deletado via soft delete.

        Exemplo:
            obj = Devocional.all_objects.get(pk=1)
            obj.restore()
        """
        self.is_active = True
        self.deleted_at = None
        self.save(update_fields=["is_active", "deleted_at"])

    # ── Propriedades ──────────────────────────────────────────────────────────

    @property
    def is_deleted(self):
        """Retorna True se o registro foi marcado como deletado."""
        return not self.is_active
