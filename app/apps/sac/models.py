"""
Models do app SAC / Suporte.

SacSuporte — registra mensagens de usuários autenticados:
    dúvidas, sugestões, reclamações e elogios.

Somente leitura no admin (inserções via formulário público).
"""

from django.conf import settings
from django.db import models


class SacSuporte(models.Model):
    """Mensagem enviada por um usuário autenticado ao SAC."""

    class Tipo(models.TextChoices):
        DUVIDA = "duvida", "Dúvida"
        SUGESTAO = "sugestao", "Sugestão"
        RECLAMACAO = "reclamacao", "Reclamação"
        ELOGIO = "elogio", "Elogio"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sac_mensagens",
        verbose_name="Usuário",
    )
    tipo = models.CharField(
        max_length=12,
        choices=Tipo.choices,
        verbose_name="Tipo",
    )
    mensagem = models.TextField(verbose_name="Mensagem")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Enviado em")

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Mensagem SAC"
        verbose_name_plural = "Mensagens SAC"

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} de {self.usuario} — {self.criado_em:%d/%m/%Y %H:%M}"
