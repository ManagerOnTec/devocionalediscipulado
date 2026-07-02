"""
Views do app Core — página inicial e páginas institucionais.

Todas as views usam CBV (Class-Based Views) conforme padrão do projeto.
"""

from django.views.generic import TemplateView


class HomeView(TemplateView):
    """
    Página inicial do sistema.

    Exibe o dashboard ou redireciona conforme o perfil do usuário.
    """

    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        """Adiciona dados de contexto ao template."""
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Devocional e Discipulado"
        context["subtitulo"] = "Sistema de gestão de devocionais e discipulado"
        if self.request.user.is_authenticated and self.request.user.is_superuser:
            try:
                from apps.estudo.models import Topico
                context["topicos_estudo_pessoal"] = list(
                    Topico.objects.order_by("ordem", "titulo")[:6]
                )
            except Exception:
                context["topicos_estudo_pessoal"] = []
        return context
