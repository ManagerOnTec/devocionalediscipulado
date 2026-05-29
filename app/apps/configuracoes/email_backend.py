"""
Backend SMTP com credenciais carregadas do banco de dados.

Usa ConfiguracaoEmail (singleton) para obter host, porta, usuário e senha.
A senha é armazenada criptografada com Fernet e decriptografada em tempo
de execução — nunca em plaintext no banco.

Configurar em settings/base.py:
    EMAIL_BACKEND = "apps.configuracoes.email_backend.DBEmailBackend"

Em settings/dev.py o ConsoleEmailBackend continua sendo o padrão para
desenvolvimento, sobrescrevendo esta configuração.
"""

from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


class DBEmailBackend(SMTPBackend):
    """
    Backend SMTP configurado pelo banco de dados (ConfiguracaoEmail).

    Prioridade dos parâmetros:
      1. kwargs explícitos passados pelo chamador
      2. Valores de ConfiguracaoEmail (banco de dados)
    """

    def __init__(self, **kwargs):
        from apps.configuracoes.models import ConfiguracaoEmail

        config = ConfiguracaoEmail.get_solo()
        kwargs.setdefault("host", config.host)
        kwargs.setdefault("port", config.porta)
        kwargs.setdefault("username", config.usuario)
        kwargs.setdefault("password", config.get_senha())
        kwargs.setdefault("use_tls", config.usar_tls)
        kwargs.setdefault("use_ssl", config.usar_ssl)
        kwargs.setdefault("timeout", config.timeout_segundos)
        super().__init__(**kwargs)
