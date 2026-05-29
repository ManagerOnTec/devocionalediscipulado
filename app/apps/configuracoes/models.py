"""
Models do app Configurações.

Fornece dois registros singleton (um único registro por modelo):
  - ConfiguracaoSessao  → tempo de expiração da sessão
  - ConfiguracaoEmail   → credenciais SMTP com senha criptografada (Fernet)

Regra de negócio:
  - Apenas superusuários podem alterar esses registros.
  - Os registros são criados automaticamente com valores padrão via post_migrate.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


# ─────────────────────────────────────────────────────────────────────────────
# Criptografia Fernet — chave derivada de SECRET_KEY
# ─────────────────────────────────────────────────────────────────────────────

def _get_fernet() -> Fernet:
    """Retorna instância Fernet com chave de 32 bytes derivada de SECRET_KEY."""
    raw = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(raw))


# ─────────────────────────────────────────────────────────────────────────────
# Mixin Singleton
# ─────────────────────────────────────────────────────────────────────────────

class SingletonModel(models.Model):
    """
    Modelo base para registros únicos (singleton).

    Garante pk=1 em qualquer save() e impede delete().
    Use get_solo() para obter ou criar o registro padrão.
    """

    id = models.PositiveSmallIntegerField(
        primary_key=True,
        default=1,
        editable=False,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        self._invalidar_cache()

    def delete(self, *args, **kwargs):
        """Proíbe exclusão do registro singleton."""

    def _invalidar_cache(self):
        """Subclasses sobrescrevem para invalidar cache ao salvar."""

    @classmethod
    def get_solo(cls):
        """Retorna o registro único, criando-o com defaults se não existir."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ─────────────────────────────────────────────────────────────────────────────
# ConfiguracaoSessao
# ─────────────────────────────────────────────────────────────────────────────

class ConfiguracaoSessao(SingletonModel):
    """
    Tempo de expiração da sessão autenticada (em minutos).

    Injetado por SessaoConfiguravelMiddleware em cada request autenticado.
    Somente superusuários podem alterar. Padrão: 120 min.
    """

    tempo_sessao_minutos = models.PositiveIntegerField(
        default=120,
        verbose_name="Tempo de sessão (minutos)",
        help_text=(
            "Tempo de inatividade antes de encerrar a sessão automaticamente. "
            "Padrão: 120 minutos. Somente superusuários podem alterar."
        ),
    )

    class Meta:
        verbose_name = "Sessão"
        verbose_name_plural = "Sessão"

    def __str__(self):
        return f"Sessão: {self.tempo_sessao_minutos} min"

    def _invalidar_cache(self):
        from django.core.cache import cache

        cache.delete("cfg_sessao_segundos")

    @classmethod
    def get_tempo_segundos(cls) -> int:
        """
        Retorna o timeout em segundos.
        O valor é cacheado por 60 s para evitar query a cada request.
        """
        from django.core.cache import cache

        timeout = cache.get("cfg_sessao_segundos")
        if timeout is None:
            config = cls.get_solo()
            timeout = config.tempo_sessao_minutos * 60
            cache.set("cfg_sessao_segundos", timeout, 60)
        return timeout


# ─────────────────────────────────────────────────────────────────────────────
# ConfiguracaoEmail
# ─────────────────────────────────────────────────────────────────────────────

class ConfiguracaoEmail(SingletonModel):
    """
    Configuração SMTP para envio de e-mails (ex.: recuperação de senha).

    A senha é armazenada criptografada com Fernet (chave derivada de SECRET_KEY).
    Padrão configurado para Google Workspace / Gmail (smtp.gmail.com:587 + TLS).

    Use Senha de App do Google, nunca a senha da conta:
      Conta Google → Segurança → Senhas de app
    """

    host = models.CharField(
        max_length=255,
        default="smtp.gmail.com",
        verbose_name="Servidor SMTP",
    )
    porta = models.PositiveIntegerField(
        default=587,
        verbose_name="Porta",
        help_text="587 para TLS (recomendado) · 465 para SSL · 25 para sem criptografia.",
    )
    usuario = models.EmailField(
        default="admin@managerontecsolutions.com.br",
        verbose_name="Usuário (e-mail remetente)",
    )
    senha_criptografada = models.TextField(
        blank=True,
        default="",
        verbose_name="Senha (criptografada)",
        editable=False,
    )
    usar_tls = models.BooleanField(
        default=True,
        verbose_name="Usar TLS",
        help_text="Recomendado para a porta 587 (Gmail/Google Workspace).",
    )
    usar_ssl = models.BooleanField(
        default=False,
        verbose_name="Usar SSL",
        help_text="Use para a porta 465. Não ative junto com TLS.",
    )
    nome_exibicao = models.CharField(
        max_length=100,
        default="Devocional e Discipulado",
        verbose_name="Nome de exibição",
        help_text="Nome que aparece no campo 'De:' dos e-mails enviados.",
    )
    timeout_segundos = models.PositiveIntegerField(
        default=30,
        verbose_name="Timeout de conexão (segundos)",
    )

    class Meta:
        verbose_name = "E-mail"
        verbose_name_plural = "E-mail"

    def __str__(self):
        return f"E-mail: {self.usuario} via {self.host}:{self.porta}"

    # ── Senha ─────────────────────────────────────────────────────────────

    def set_senha(self, senha_plaintext: str) -> None:
        """Criptografa e armazena a senha."""
        fernet = _get_fernet()
        self.senha_criptografada = fernet.encrypt(senha_plaintext.encode()).decode()

    def get_senha(self) -> str:
        """Decriptografa e retorna a senha em texto puro."""
        if not self.senha_criptografada:
            return ""
        try:
            fernet = _get_fernet()
            return fernet.decrypt(self.senha_criptografada.encode()).decode()
        except (InvalidToken, Exception):
            return ""

    @property
    def from_email(self) -> str:
        """Endereço 'De:' formatado para uso no send_mail()."""
        if self.nome_exibicao:
            return f"{self.nome_exibicao} <{self.usuario}>"
        return self.usuario
