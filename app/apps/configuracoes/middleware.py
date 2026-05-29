"""
Middleware de sessão configurável.

Aplica o tempo de expiração definido em ConfiguracaoSessao (banco de dados)
a cada request de usuário autenticado.

O valor é cacheado por 60 s para evitar uma query a cada requisição.
Deve ser posicionado APÓS AuthenticationMiddleware no settings.MIDDLEWARE.
"""


class SessaoConfiguravelMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # hasattr protege contra middlewares que não expõem request.user
        if hasattr(request, "user") and request.user.is_authenticated:
            from apps.configuracoes.models import ConfiguracaoSessao

            request.session.set_expiry(ConfiguracaoSessao.get_tempo_segundos())
        return self.get_response(request)
