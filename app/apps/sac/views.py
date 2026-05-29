"""
Views do app SAC / Suporte.

SacSuporteCreateView → formulário de contato (LoginRequired)
SacSucessoView       → confirmação de envio (LoginRequired)
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import SacSuporteForm
from .models import SacSuporte


class SacSuporteCreateView(LoginRequiredMixin, CreateView):
    """Formulário de contato/suporte — apenas para usuários autenticados."""

    model = SacSuporte
    form_class = SacSuporteForm
    template_name = "sac/formulario.html"
    success_url = reverse_lazy("sac:sucesso")

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "SAC / Suporte"
        return context


class SacSucessoView(LoginRequiredMixin, TemplateView):
    """Página de confirmação após envio de mensagem ao SAC."""

    template_name = "sac/sucesso.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Mensagem Enviada"
        return context
