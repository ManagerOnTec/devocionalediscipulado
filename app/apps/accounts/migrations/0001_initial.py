"""
Migration inicial do app accounts — cria o modelo User customizado.

Gerada automaticamente pelo Django. Não editar manualmente.

Inclui:
    - User         → modelo principal de autenticação
    - HistoricalUser → tabela de auditoria gerada pelo django-simple-history
"""

import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
import simple_history.models
from django.conf import settings
from django.db import migrations, models

import apps.accounts.managers
import apps.accounts.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        # Dependência das permissões padrão do Django Auth
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [

        # ── Cria o modelo User ────────────────────────────────────────────────
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                # Campo de senha gerenciado pelo AbstractBaseUser
                (
                    "password",
                    models.CharField(max_length=128, verbose_name="password"),
                ),
                # Último login — preenchido pelo Django Auth automaticamente
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="last login",
                    ),
                ),
                # Superusuário — herança do PermissionsMixin
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text=(
                            "Designates that this user has all permissions "
                            "without explicitly assigning them."
                        ),
                        verbose_name="superuser status",
                    ),
                ),
                # ── Campos customizados ───────────────────────────────────────
                (
                    "email",
                    models.EmailField(
                        help_text="Usado para login. Deve ser único no sistema.",
                        max_length=254,
                        unique=True,
                        verbose_name="E-mail",
                    ),
                ),
                (
                    "nome_completo",
                    models.CharField(
                        help_text="Nome e sobrenome do usuário.",
                        max_length=200,
                        verbose_name="Nome completo",
                    ),
                ),
                (
                    "foto",
                    models.ImageField(
                        blank=True,
                        help_text="Formatos aceitos: JPG, PNG. Tamanho máximo: 2 MB.",
                        null=True,
                        upload_to="usuarios/fotos/%Y/%m/",
                        verbose_name="Foto de perfil",
                    ),
                ),
                (
                    "telefone",
                    models.CharField(
                        blank=True,
                        help_text="Formato: (11) 99999-9999",
                        max_length=20,
                        validators=[apps.accounts.models.validate_telefone],
                        verbose_name="Telefone",
                    ),
                ),
                (
                    "timezone",
                    models.CharField(
                        choices=[
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
                        ],
                        default="America/Sao_Paulo",
                        help_text="Fuso horário usado para exibição de datas e horários.",
                        max_length=50,
                        verbose_name="Fuso horário",
                    ),
                ),
                (
                    "dark_mode",
                    models.BooleanField(
                        default=False,
                        help_text="Ativa o tema escuro na interface do sistema.",
                        verbose_name="Modo escuro",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text=(
                            "Desmarque para desativar a conta sem excluir o usuário. "
                            "Usuários inativos não conseguem fazer login."
                        ),
                        verbose_name="Ativo",
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Permite acesso ao painel administrativo Django.",
                        verbose_name="Acesso ao admin",
                    ),
                ),
                # Timestamps de auditoria
                (
                    "criado_em",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Criado em",
                    ),
                ),
                (
                    "atualizado_em",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Atualizado em",
                    ),
                ),
                # M2M — grupos de permissão
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text=(
                            "The groups this user belongs to. A user will get all "
                            "permissions granted to each of their groups."
                        ),
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                # M2M — permissões individuais
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "Usuário",
                "verbose_name_plural": "Usuários",
                "ordering": ["nome_completo"],
            },
            managers=[
                ("objects", apps.accounts.managers.CustomUserManager()),
            ],
        ),

        # ── Cria o modelo HistoricalUser (django-simple-history) ──────────────
        migrations.CreateModel(
            name="HistoricalUser",
            fields=[
                # PK própria do histórico (não referencia o User diretamente)
                (
                    "history_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                # Cópia do id do registro original (para rastreamento)
                (
                    "id",
                    models.BigIntegerField(blank=True, db_index=True),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(blank=True, null=True, verbose_name="last login"),
                ),
                (
                    "is_superuser",
                    models.BooleanField(default=False, verbose_name="superuser status"),
                ),
                (
                    "email",
                    models.EmailField(db_index=True, max_length=254, verbose_name="E-mail"),
                ),
                (
                    "nome_completo",
                    models.CharField(max_length=200, verbose_name="Nome completo"),
                ),
                # ImageField é armazenado como TextField no histórico
                (
                    "foto",
                    models.TextField(blank=True, max_length=100, verbose_name="Foto de perfil"),
                ),
                (
                    "telefone",
                    models.CharField(blank=True, max_length=20, verbose_name="Telefone"),
                ),
                (
                    "timezone",
                    models.CharField(
                        choices=[
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
                        ],
                        default="America/Sao_Paulo",
                        max_length=50,
                        verbose_name="Fuso horário",
                    ),
                ),
                (
                    "dark_mode",
                    models.BooleanField(default=False, verbose_name="Modo escuro"),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Ativo"),
                ),
                (
                    "is_staff",
                    models.BooleanField(default=False, verbose_name="Acesso ao admin"),
                ),
                # Timestamps — nullable no histórico pois auto_now não se aplica
                (
                    "criado_em",
                    models.DateTimeField(
                        blank=True,
                        editable=False,
                        verbose_name="Criado em",
                    ),
                ),
                (
                    "atualizado_em",
                    models.DateTimeField(
                        blank=True,
                        editable=False,
                        verbose_name="Atualizado em",
                    ),
                ),
                # ── Campos de controle do simple_history ─────────────────────
                (
                    "history_date",
                    models.DateTimeField(db_index=True),
                ),
                (
                    "history_change_reason",
                    models.TextField(null=True),
                ),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                # FK para o usuário que fez a alteração (pode ser nulo)
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical Usuário",
                "verbose_name_plural": "historical Usuários",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
