"""
Configuração do app Accounts.

Responsável por autenticação, cadastro e perfil de usuário.
Substitui o modelo padrão de User do Django via AUTH_USER_MODEL.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Contas"

    def ready(self):
        """Registra sinais do app ao inicializar."""
        pass  # importar sinais aqui quando necessário: import apps.accounts.signals
