"""
Views do app Estudo (unificação de Devocional e Discipulado).

Hierarquia:
    TrilhaListView         → /estudo/
    TrilhaDetalheView      → /estudo/<slug>/
    ModuloDetalheView      → /estudo/modulo/<slug>/
    TemaDetalheView        → /estudo/tema/<slug>/
    ConcluirTemaView       → /estudo/tema/<slug>/concluir/  [POST]
    MeuProgressoView       → /estudo/meu-progresso/
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .models import Modulo, ProgressoTema, Tema, Trilha, EstudoPessoal, Topico

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Mixins
# ─────────────────────────────────────────────────────────────────────────────

class AcessoTrilhaMixin:
    """
    Controla acesso às trilhas conforme campo `acesso`:
      PUBLICO              → qualquer visitante
      LOGIN_OBRIGATORIO    → redireciona para login
      PERMISSAO_ESPECIFICA → exige estudo.ver_trilha_restrita
    """

    def dispatch(self, request, *args, **kwargs):
        self._trilha = get_object_or_404(Trilha, slug=kwargs.get("trilha_slug"))
        acesso = self._trilha.acesso
        tipo = self._trilha.get_tipo_display().lower()

        if acesso == Trilha.AcessoChoices.LOGIN_OBRIGATORIO:
            if not request.user.is_authenticated:
                messages.warning(
                    request,
                    f"Para acessar este {tipo}, é necessário fazer login.",
                )
                return redirect_to_login(request.get_full_path())
        elif acesso == Trilha.AcessoChoices.PERMISSAO_ESPECIFICA:
            if not request.user.is_authenticated:
                messages.warning(
                    request,
                    f"Para acessar este {tipo}, é necessário fazer login com uma conta autorizada.",
                )
                return redirect_to_login(request.get_full_path())
            if not _usuario_tem_acesso_restrito(request, trilha=self._trilha):
                messages.error(
                    request,
                    f"Você não tem permissão para acessar este {tipo}.",
                )
                return redirect("estudo:lista_trilhas")

        return super().dispatch(request, *args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_ACESSO_PRIORITY = {
    Trilha.AcessoChoices.PUBLICO: 0,
    Trilha.AcessoChoices.LOGIN_OBRIGATORIO: 1,
    Trilha.AcessoChoices.PERMISSAO_ESPECIFICA: 2,
}


def _acesso_efetivo(*valores):
    """Retorna o valor de acesso mais restritivo de uma lista de valores."""
    return max(valores, key=lambda a: _ACESSO_PRIORITY.get(a, 0))


def _usuario_tem_acesso_restrito(request, trilha=None):
    """
    Retorna True se o usuário pode acessar conteúdo com PERMISSAO_ESPECIFICA.

    Critérios (qualquer um satisfaz):
      1. is_superuser
      2. is_staff
      3. permissão explícita estudo.ver_trilha_restrita
      4. pertence a pelo menos um dos grupos listados na trilha
    """
    if request.user.is_superuser or request.user.is_staff:
        return True
    if request.user.has_perm("estudo.ver_trilha_restrita"):
        return True
    if trilha is not None and trilha.grupos.filter(user=request.user).exists():
        return True
    return False


def _verificar_acesso(request, acesso, nome_conteudo="este conteúdo", trilha=None):
    """
    Verifica se a requisição satisfaz o nível de acesso indicado.
    Retorna uma resposta de redirecionamento se negado, ou None se permitido.

    Passe ``trilha`` para habilitar a verificação por grupo M2M.
    """
    if acesso == Trilha.AcessoChoices.LOGIN_OBRIGATORIO:
        if not request.user.is_authenticated:
            messages.warning(
                request,
                f"Para acessar {nome_conteudo}, é necessário fazer login.",
            )
            return redirect_to_login(request.get_full_path())
    elif acesso == Trilha.AcessoChoices.PERMISSAO_ESPECIFICA:
        if not request.user.is_authenticated:
            messages.warning(
                request,
                f"Para acessar {nome_conteudo}, é necessário fazer login com uma conta autorizada.",
            )
            return redirect_to_login(request.get_full_path())
        if not _usuario_tem_acesso_restrito(request, trilha=trilha):
            messages.error(
                request,
                f"Você não tem permissão para acessar {nome_conteudo}.",
            )
            return redirect("estudo:lista_trilhas")
    return None

def _build_progresso_context(usuario):
    """
    Constrói o contexto de progresso para um usuário.
    Retorna uma lista de dicts (não anota atributos '_privados' em objetos ORM,
    pois Django templates bloqueiam acesso a atributos com underscore).
    """
    concluidos_ids = set(
        ProgressoTema.objects.filter(usuario=usuario).values_list("tema_id", flat=True)
    )

    trilhas_qs = Trilha.objects.filter(
        status=Trilha.StatusChoices.PUBLICADO,
    ).prefetch_related("modulos__temas").order_by("ordem")

    trilhas_progresso = []
    for trilha in trilhas_qs:
        modulos_progresso = []
        for modulo in trilha.modulos.prefetch_related("temas").order_by("ordem"):
            temas_ids = set(modulo.temas.values_list("id", flat=True))
            total = len(temas_ids)
            concluidos = len(temas_ids & concluidos_ids)
            modulos_progresso.append({
                "obj": modulo,
                "percentual": int((concluidos / total) * 100) if total > 0 else 0,
                "desbloqueado": modulo.esta_desbloqueado(usuario),
            })
        trilhas_progresso.append({
            "obj": trilha,
            "modulos": modulos_progresso,
        })

    return {
        "trilhas_progresso": trilhas_progresso,
        "concluidos_ids": concluidos_ids,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Views de listagem / detalhe
# ─────────────────────────────────────────────────────────────────────────────

class TrilhaListView(ListView):
    template_name = "estudo/lista_trilhas.html"
    context_object_name = "trilhas"

    def get_queryset(self):
        return (
            Trilha.objects.filter(status=Trilha.StatusChoices.PUBLICADO)
            .prefetch_related("modulos")
            .order_by("ordem")
        )


class TrilhaDetalheView(DetailView):
    template_name = "estudo/detalhe_trilha.html"
    context_object_name = "trilha"

    def get_queryset(self):
        return Trilha.objects.filter(
            status=Trilha.StatusChoices.PUBLICADO,
        ).prefetch_related("modulos__temas")

    def dispatch(self, request, *args, **kwargs):
        # Verifica acesso antes de exibir a trilha
        trilha = get_object_or_404(Trilha, slug=kwargs.get("slug"))
        resp = _verificar_acesso(
            request, trilha.acesso,
            f"este {trilha.get_tipo_display().lower()}",
            trilha=trilha,
        )
        if resp:
            return resp
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user

        concluidos_ids = set()
        if usuario.is_authenticated:
            concluidos_ids = set(
                ProgressoTema.objects.filter(usuario=usuario).values_list("tema_id", flat=True)
            )

        # Constrói lista de dicts para evitar underscore-attributes no template
        modulos_progresso = []
        for modulo in self.object.modulos.prefetch_related("temas").order_by("ordem"):
            temas_ids = set(modulo.temas.values_list("id", flat=True))
            total = len(temas_ids)
            concluidos = len(temas_ids & concluidos_ids)
            modulos_progresso.append({
                "obj": modulo,
                "percentual": int((concluidos / total) * 100) if total > 0 else 0,
                "desbloqueado": modulo.esta_desbloqueado(usuario) if usuario.is_authenticated else True,
            })

        context["modulos_progresso"] = modulos_progresso
        return context


class ModuloDetalheView(DetailView):
    template_name = "estudo/detalhe_modulo.html"
    context_object_name = "modulo"

    def get_queryset(self):
        return Modulo.objects.select_related("trilha").prefetch_related("temas")

    def dispatch(self, request, *args, **kwargs):
        obj = get_object_or_404(
            Modulo.objects.select_related("trilha"), slug=kwargs.get("slug")
        )
        # Acesso efetivo = mais restritivo entre módulo e trilha
        acesso = _acesso_efetivo(obj.acesso, obj.trilha.acesso)
        resp = _verificar_acesso(
            request, acesso,
            f"este {obj.trilha.get_tipo_display().lower()}",
            trilha=obj.trilha,
        )
        if resp:
            return resp
        # Desbloqueio sequencial só se aplica a usuários autenticados
        if request.user.is_authenticated and not obj.esta_desbloqueado(request.user):
            messages.warning(request, "Conclua o módulo anterior para desbloquear este.")
            return redirect("estudo:detalhe_trilha", slug=obj.trilha.slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            concluidos_ids = set(
                ProgressoTema.objects.filter(usuario=self.request.user).values_list(
                    "tema_id", flat=True
                )
            )
        else:
            concluidos_ids = set()
        # Lista de dicts para o template — sem underscore
        temas_progresso = []
        for tema in self.object.temas.order_by("ordem"):
            temas_progresso.append({
                "obj": tema,
                "concluido": tema.id in concluidos_ids,
            })
        context["temas_progresso"] = temas_progresso
        return context


class TemaDetalheView(DetailView):
    template_name = "estudo/detalhe_tema.html"
    context_object_name = "tema"

    def get_queryset(self):
        return Tema.objects.select_related("modulo__trilha")

    def dispatch(self, request, *args, **kwargs):
        obj = get_object_or_404(
            Tema.objects.select_related("modulo__trilha"), slug=kwargs.get("slug")
        )
        # Acesso efetivo = mais restritivo entre tema, módulo e trilha
        acesso = _acesso_efetivo(obj.acesso, obj.modulo.acesso, obj.modulo.trilha.acesso)
        resp = _verificar_acesso(
            request, acesso,
            f"este {obj.modulo.trilha.get_tipo_display().lower()}",
            trilha=obj.modulo.trilha,
        )
        if resp:
            return resp
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tema = self.object
        context["ja_concluido"] = (
            self.request.user.is_authenticated
            and ProgressoTema.objects.filter(usuario=self.request.user, tema=tema).exists()
        )
        context["tema_anterior"] = (
            Tema.objects.filter(modulo=tema.modulo, ordem__lt=tema.ordem)
            .order_by("-ordem")
            .first()
        )
        context["proximo_tema"] = (
            Tema.objects.filter(modulo=tema.modulo, ordem__gt=tema.ordem)
            .order_by("ordem")
            .first()
        )
        return context


# ─────────────────────────────────────────────────────────────────────────────
# Concluir tema
# ─────────────────────────────────────────────────────────────────────────────

class ConcluirTemaView(LoginRequiredMixin, View):
    def post(self, request, slug):
        tema = get_object_or_404(Tema, slug=slug, is_active=True)
        _, created = ProgressoTema.objects.get_or_create(
            usuario=request.user, tema=tema
        )
        if created:
            messages.success(request, "Parabéns! Tema concluído com sucesso.")
        else:
            messages.info(request, "Você já havia concluído este tema.")
        return redirect("estudo:detalhe_tema", slug=slug)

    def get(self, request, slug):
        return HttpResponseNotAllowed(["POST"])


class DesconcluirTemaView(LoginRequiredMixin, View):
    def post(self, request, slug):
        tema = get_object_or_404(Tema, slug=slug, is_active=True)
        deleted, _ = ProgressoTema.objects.filter(usuario=request.user, tema=tema).delete()
        if deleted:
            messages.success(request, "Conclusão removida. Você pode rever este tema quando quiser.")
        else:
            messages.info(request, "Este tema não estava marcado como concluído.")
        return redirect("estudo:detalhe_tema", slug=slug)

    def get(self, request, slug):
        return HttpResponseNotAllowed(["POST"])


# ─────────────────────────────────────────────────────────────────────────────
# Progresso do usuário
# ─────────────────────────────────────────────────────────────────────────────

class MeuProgressoView(LoginRequiredMixin, TemplateView):
    template_name = "estudo/meu_progresso.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_build_progresso_context(self.request.user))
        return context


# ─────────────────────────────────────────────────────────────────────────────
# EstudoPessoal — helpers de permissão
# ─────────────────────────────────────────────────────────────────────────────

_PERMISSAO_PRIORIDADE = {
    "SOMENTE_SUPERADMIN": 2,
    "LOGIN_OBRIGATORIO":  1,
    "PUBLICO":            0,
}


def _permissao_efetiva(estudo):
    """
    Retorna a permissão mais restritiva entre o tópico (superior) e o estudo.
    Se o tópico tiver permissão definida, ela prevalece quando for mais restritiva.
    """
    ep = estudo.permissao or "SOMENTE_SUPERADMIN"
    if estudo.topico_id:
        tp = estudo.topico.permissao or "SOMENTE_SUPERADMIN"
        return tp if _PERMISSAO_PRIORIDADE.get(tp, 2) >= _PERMISSAO_PRIORIDADE.get(ep, 2) else ep
    return ep


def _verificar_permissao_estudo(request, permissao):
    """
    Verifica acesso com base na permissão efetiva de um EstudoPessoal.
    Retorna True se o acesso é permitido.
    """
    if request.user.is_superuser:
        return True
    if permissao == "SOMENTE_SUPERADMIN":
        return False
    if permissao == "LOGIN_OBRIGATORIO":
        return request.user.is_authenticated
    return True  # PUBLICO


# ─────────────────────────────────────────────────────────────────────────────
# EstudoPessoal — views
# ─────────────────────────────────────────────────────────────────────────────

class EstudoPessoalListView(LoginRequiredMixin, ListView):
    """Lista de tópicos de estudo pessoal — apenas superadmin."""

    model = Topico
    template_name = "estudo/estudopessoal_lista.html"
    context_object_name = "topicos"
    ordering = ["ordem", "titulo"]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estudos_sem_topico"] = (
            EstudoPessoal.objects
            .filter(topico__isnull=True)
            .order_by("-criado_em")
        )
        return context


class TopicoDetalheView(LoginRequiredMixin, DetailView):
    """Estudos de um tópico — apenas superadmin."""

    model = Topico
    template_name = "estudo/topico_detalhe.html"
    context_object_name = "topico"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estudos"] = self.object.estudos.order_by("-criado_em")
        return context


class EstudoPessoalDetalheView(LoginRequiredMixin, DetailView):
    """Detalhe completo de um estudo pessoal.

    Acesso controlado pela permissão efetiva: a do Tópico (superior)
    prevalece sobre a do próprio EstudoPessoal quando mais restritiva.
    """

    model = EstudoPessoal
    template_name = "estudo/estudopessoal_detalhe.html"
    context_object_name = "estudo"

    def get_queryset(self):
        return EstudoPessoal.objects.select_related("topico")

    def dispatch(self, request, *args, **kwargs):
        obj = get_object_or_404(
            EstudoPessoal.objects.select_related("topico"),
            pk=kwargs["pk"],
        )
        permissao = _permissao_efetiva(obj)
        if not _verificar_permissao_estudo(request, permissao):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["topicos"] = self.object.topicos.filter(incluir=True).order_by("ordem")
        return context
