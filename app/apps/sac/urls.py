"""
URLs do app SAC / Suporte.

Namespace: sac

Rotas:
    /sac/           → formulário de contato
    /sac/enviado/   → confirmação de envio
"""

from django.urls import path

from .views import SacSucessoView, SacSuporteCreateView

app_name = "sac"

urlpatterns = [
    path("", SacSuporteCreateView.as_view(), name="formulario"),
    path("enviado/", SacSucessoView.as_view(), name="sucesso"),
]
