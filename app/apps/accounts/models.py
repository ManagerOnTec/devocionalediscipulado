"""
Model User customizado do projeto Devocional e Discipulado.

IMPORTANTE:
    - Este model substitui o User padrão do Django.
    - Em settings: AUTH_USER_MODEL = 'accounts.User'
    - Deve ser definido ANTES de qualquer outra migration que referencie User.
    - Login via e-mail (USERNAME_FIELD = 'email').

Campos de perfil:
    nome_completo, foto, telefone, timezone, dark_mode

Auditoria:
    HistoricalRecords (django-simple-history) registra todas as alterações.

Timezone:
    Todos os DateTimeField armazenam UTC.
    O fuso exibido na interface é controlado por User.timezone (por usuário)
    e pelo TIME_ZONE global (America/Sao_Paulo) em settings.
"""

import re

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from .managers import CustomUserManager

# ─── Opções de fuso horário ───────────────────────────────────────────────────

# Principais fusos horários do Brasil para exibição no perfil do usuário
TIMEZONES_BRASIL = [
    ("America/Sao_Paulo",   "Brasília / São Paulo (UTC-3)"),
    ("America/Fortaleza",   "Fortaleza / Recife (UTC-3)"),
    ("America/Bahia",       "Salvador (UTC-3)"),
    ("America/Belem",       "Belém (UTC-3)"),
    ("America/Manaus",      "Manaus (UTC-4)"),
    ("America/Cuiaba",      "Cuiabá (UTC-4)"),
    ("America/Porto_Velho", "Porto Velho (UTC-4)"),
    ("America/Boa_Vista",   "Boa Vista (UTC-4)"),
    ("America/Rio_Branco",  "Rio Branco (UTC-5)"),
    ("America/Noronha",     "Fernando de Noronha (UTC-2)"),
]


# ─── Validadores ─────────────────────────────────────────────────────────────

def validate_telefone(value):
    """
    Valida formato de telefone brasileiro.

    Aceita formatos como:
        (11) 99999-9999
        +55 11 99999-9999
        11999999999
    """
    if not value:
        return
    pattern = r"^\+?[\d\s\(\)\-]{8,20}$"
    if not re.match(pattern, value):
        raise ValidationError(
            "Telefone inválido. Use o formato: (11) 99999-9999",
            code="telefone_invalido",
        )


# ─── Model User ───────────────────────────────────────────────────────────────

class User(AbstractBaseUser, PermissionsMixin):
    """
    Usuário customizado do projeto.

    Diferenças em relação ao User padrão do Django:
        ✔ Login via e-mail (não username)
        ✔ Campo nome_completo (em vez de first_name + last_name)
        ✔ Foto de perfil opcional
        ✔ Telefone com validação
        ✔ Fuso horário individual por usuário
        ✔ Preferência de dark mode
        ✔ Auditoria completa via HistoricalRecords
        ✔ Timestamps criado_em / atualizado_em

    Como criar usuário programaticamente:
        User.objects.create_user(
            email='user@example.com',
            password='senha123',
            nome_completo='João da Silva',
        )
    """

    # ── Autenticação ──────────────────────────────────────────────────────────

    email = models.EmailField(
        unique=True,
        verbose_name="E-mail",
        help_text="Usado para login. Deve ser único no sistema.",
    )

    # ── Dados pessoais ────────────────────────────────────────────────────────

    nome_completo = models.CharField(
        max_length=200,
        verbose_name="Nome completo",
        help_text="Nome e sobrenome do usuário.",
    )
    foto = models.ImageField(
        upload_to="usuarios/fotos/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="Foto de perfil",
        help_text="Formatos aceitos: JPG, PNG. Tamanho máximo: 2 MB.",
    )
    telefone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Telefone",
        validators=[validate_telefone],
        help_text="Formato: (11) 99999-9999",
    )

    # ── Preferências ─────────────────────────────────────────────────────────

    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONES_BRASIL,
        default="America/Sao_Paulo",
        verbose_name="Fuso horário",
        help_text="Fuso horário usado para exibição de datas e horários.",
    )
    dark_mode = models.BooleanField(
        default=False,
        verbose_name="Modo escuro",
        help_text="Ativa o tema escuro na interface do sistema.",
    )
    is_lider = models.BooleanField(
        default=False,
        verbose_name="É líder",
        help_text="Permite acompanhar o progresso de discípulos vinculados.",
    )

    # ── Flags de status (padrão Django Auth) ─────────────────────────────────

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text=(
            "Desmarque para desativar a conta sem excluir o usuário. "
            "Usuários inativos não conseguem fazer login."
        ),
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Acesso ao admin",
        help_text="Permite acesso ao painel administrativo Django.",
    )

    # ── Auditoria de timestamps ───────────────────────────────────────────────

    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
        # Armazenado em UTC; exibido conforme TIME_ZONE do settings ou User.timezone
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    # ── Histórico completo de alterações ─────────────────────────────────────

    # Registra toda criação, alteração e exclusão com usuário responsável e timestamp.
    # Acessível via: user_instance.history.all()
    history = HistoricalRecords()

    # ── Manager customizado ───────────────────────────────────────────────────

    objects = CustomUserManager()

    # ── Configuração de autenticação ─────────────────────────────────────────

    # Campo usado como identificador de login (substitui username)
    USERNAME_FIELD = "email"

    # Campos obrigatórios ao criar via createsuperuser (além de email e password)
    REQUIRED_FIELDS = ["nome_completo"]

    # ── Meta ──────────────────────────────────────────────────────────────────

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["nome_completo"]

    # ── Representação ─────────────────────────────────────────────────────────

    def __str__(self):
        return f"{self.nome_completo} <{self.email}>"

    # ── Compatibilidade com o sistema de auth do Django ──────────────────────

    def get_full_name(self):
        """Retorna o nome completo. Usado pelo Django internamente."""
        return self.nome_completo

    def get_short_name(self):
        """Retorna o primeiro nome para saudações e notificações."""
        return self.nome_completo.split()[0] if self.nome_completo else self.email

    # ── Propriedades auxiliares ───────────────────────────────────────────────

    @property
    def primeiro_nome(self):
        """Primeiro nome para uso em templates: 'Olá, {{ user.primeiro_nome }}!'"""
        return self.get_short_name()

    @property
    def tem_foto(self):
        """Verifica se o usuário possui foto de perfil cadastrada."""
        return bool(self.foto)
