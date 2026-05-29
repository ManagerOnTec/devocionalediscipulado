"""
Testes do app Devocional — models, listagem, detalhe, acesso e progresso.
"""

import pytest
from django.urls import reverse

from apps.devocional.models import ProgressoUsuario, Tema

from .factories import (
    DevocionalTemaFactory,
    PrivateDevocionalTemaFactory,
    ProgressoUsuarioFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────

class TestDevocionalModels:
    def test_tema_auto_slug(self):
        tema = DevocionalTemaFactory(titulo="Meu Tema Especial")
        assert tema.slug == "meu-tema-especial"

    def test_tema_slug_collision(self):
        DevocionalTemaFactory(titulo="Tema Igual")
        tema2 = DevocionalTemaFactory(titulo="Tema Igual")
        assert tema2.slug == "tema-igual-2"

    def test_tema_str(self):
        tema = DevocionalTemaFactory(titulo="Fé e Oração")
        assert str(tema) == "Fé e Oração"

    def test_tema_get_absolute_url(self):
        tema = DevocionalTemaFactory(titulo="Fe e Oracao")
        assert tema.get_absolute_url() == reverse(
            "devocional:detalhe", kwargs={"slug": tema.slug}
        )

    def test_progresso_usuario_str(self):
        progresso = ProgressoUsuarioFactory()
        assert str(progresso.usuario) in str(progresso)
        assert str(progresso.tema) in str(progresso)


# ─────────────────────────────────────────────────────────────────────────────
# TemaListView
# ─────────────────────────────────────────────────────────────────────────────

class TestDevocionalListView:
    def test_lista_publica_anonimo(self, client):
        DevocionalTemaFactory.create_batch(3)
        response = client.get(reverse("devocional:lista"))
        assert response.status_code == 200
        assert len(response.context["temas"]) == 3

    def test_lista_apenas_publicados(self, client):
        DevocionalTemaFactory(status=Tema.StatusChoices.RASCUNHO)
        DevocionalTemaFactory(status=Tema.StatusChoices.PUBLICADO)
        response = client.get(reverse("devocional:lista"))
        assert len(response.context["temas"]) == 1

    def test_lista_exclui_rascunhos(self, client):
        DevocionalTemaFactory.create_batch(2, status=Tema.StatusChoices.RASCUNHO)
        DevocionalTemaFactory.create_batch(3, status=Tema.StatusChoices.PUBLICADO)
        response = client.get(reverse("devocional:lista"))
        assert len(response.context["temas"]) == 3

    def test_lista_paginada_usa_context_temas(self, client):
        DevocionalTemaFactory.create_batch(5)
        response = client.get(reverse("devocional:lista"))
        assert response.status_code == 200
        assert "temas" in response.context


# ─────────────────────────────────────────────────────────────────────────────
# TemaDetalheView
# ─────────────────────────────────────────────────────────────────────────────

class TestDevocionalDetalheView:
    def test_acesso_publico_anonimo(self, client):
        tema = DevocionalTemaFactory(acesso=Tema.AcessoChoices.PUBLICO)
        response = client.get(reverse("devocional:detalhe", kwargs={"slug": tema.slug}))
        assert response.status_code == 200

    def test_acesso_login_obrigatorio_anonimo_redireciona(self, client):
        tema = PrivateDevocionalTemaFactory()
        response = client.get(reverse("devocional:detalhe", kwargs={"slug": tema.slug}))
        assert response.status_code == 302
        assert "/contas/entrar/" in response["Location"]

    def test_acesso_login_obrigatorio_autenticado(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = PrivateDevocionalTemaFactory()
        response = client.get(reverse("devocional:detalhe", kwargs={"slug": tema.slug}))
        assert response.status_code == 200

    def test_acesso_permissao_especifica_sem_permissao(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = DevocionalTemaFactory(acesso=Tema.AcessoChoices.PERMISSAO_ESPECIFICA)
        response = client.get(reverse("devocional:detalhe", kwargs={"slug": tema.slug}))
        assert response.status_code == 403

    def test_contexto_ja_concluido_falso_para_anonimo(self, client):
        tema = DevocionalTemaFactory()
        response = client.get(reverse("devocional:detalhe", kwargs={"slug": tema.slug}))
        assert response.context["ja_concluido"] is False

    def test_contexto_ja_concluido_falso_sem_progresso(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = DevocionalTemaFactory()
        response = client.get(reverse("devocional:detalhe", kwargs={"slug": tema.slug}))
        assert response.context["ja_concluido"] is False

    def test_contexto_ja_concluido_verdadeiro(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = DevocionalTemaFactory()
        ProgressoUsuarioFactory(usuario=user, tema=tema)
        response = client.get(reverse("devocional:detalhe", kwargs={"slug": tema.slug}))
        assert response.context["ja_concluido"] is True

    def test_tema_slug_invalido_retorna_404(self, client):
        response = client.get(reverse("devocional:detalhe", kwargs={"slug": "nao-existe"}))
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# ConcluirTemaView
# ─────────────────────────────────────────────────────────────────────────────

class TestConcluirTemaView:
    def test_concluir_cria_progresso(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = DevocionalTemaFactory()
        response = client.post(reverse("devocional:concluir", kwargs={"slug": tema.slug}))
        assert response.status_code == 302
        assert ProgressoUsuario.objects.filter(usuario=user, tema=tema).exists()

    def test_concluir_idempotente(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = DevocionalTemaFactory()
        ProgressoUsuarioFactory(usuario=user, tema=tema)
        client.post(reverse("devocional:concluir", kwargs={"slug": tema.slug}))
        assert ProgressoUsuario.objects.filter(usuario=user, tema=tema).count() == 1

    def test_concluir_get_retorna_405(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = DevocionalTemaFactory()
        response = client.get(reverse("devocional:concluir", kwargs={"slug": tema.slug}))
        assert response.status_code == 405

    def test_concluir_anonimo_redireciona(self, client):
        tema = DevocionalTemaFactory()
        response = client.post(reverse("devocional:concluir", kwargs={"slug": tema.slug}))
        assert response.status_code == 302
        assert "/contas/entrar/" in response["Location"]

    def test_concluir_redireciona_para_detalhe(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = DevocionalTemaFactory()
        response = client.post(reverse("devocional:concluir", kwargs={"slug": tema.slug}))
        assert response["Location"] == reverse(
            "devocional:detalhe", kwargs={"slug": tema.slug}
        )


# ─────────────────────────────────────────────────────────────────────────────
# ProgressoView
# ─────────────────────────────────────────────────────────────────────────────

class TestProgressoView:
    def test_progresso_requer_login(self, client):
        response = client.get(reverse("devocional:progresso"))
        assert response.status_code == 302

    def test_progresso_autenticado(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("devocional:progresso"))
        assert response.status_code == 200

    def test_progresso_lista_apenas_do_usuario(self, client):
        user = UserFactory()
        outro = UserFactory()
        client.force_login(user)
        tema = DevocionalTemaFactory()
        ProgressoUsuarioFactory(usuario=user, tema=tema)
        ProgressoUsuarioFactory(usuario=outro, tema=DevocionalTemaFactory())
        response = client.get(reverse("devocional:progresso"))
        assert response.context["concluidos"] == 1
