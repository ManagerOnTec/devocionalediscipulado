"""
Configuração WSGI para o projeto Devocional e Discipulado.

Usado pelo Gunicorn em produção:
    gunicorn config.wsgi:application

https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Define o módulo de settings padrão (sobrescrito pela variável de ambiente)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_wsgi_application()
