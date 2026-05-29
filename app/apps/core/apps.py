"""
Configuração do app Core.

O app core fornece:
- Models abstratos com campos de auditoria (TimeStampedModel)
- Página inicial
- Utilitários compartilhados entre todos os outros apps
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self):
        """Registra sinais ao inicializar o app."""
        pass  # importar sinais aqui quando necessário: import apps.core.signals
