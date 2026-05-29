from django.apps import AppConfig


class ConfiguracoesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.configuracoes"
    verbose_name = "Configurações"

    def ready(self):
        from django.db.models.signals import post_migrate

        post_migrate.connect(_criar_defaults, sender=self)


def _criar_defaults(sender, **kwargs):
    """Garante que os registros singleton existam após cada migração."""
    try:
        from apps.configuracoes.models import ConfiguracaoEmail, ConfiguracaoSessao

        ConfiguracaoSessao.get_solo()
        ConfiguracaoEmail.get_solo()
    except Exception:
        pass
