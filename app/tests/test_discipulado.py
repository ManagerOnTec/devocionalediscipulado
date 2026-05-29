"""
Testes do app Discipulado — models (desbloqueio, percentual), views e permissões.
"""

import pytest
from django.urls import reverse

from apps.discipulado.models import ProgressoTema

from .factories import (
    DiscipuladoTemaFactory,
    LiderUserFactory,
    ModuloFactory,
    ProgressoTemaFactory,
    TrilhaFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


# ─────────────────────────────────────────────────────────────────────────────
# Modulo.esta_desbloqueado / percentual_conclusao
# ─────────────────────────────────────────────────────────────────────────────

class TestModuloDesbloqueio:
    def test_primeiro_modulo_sempre_desbloqueado(self):
        trilha = TrilhaFactory()
        modulo = ModuloFactory(trilha=trilha, ordem=0)
        user = UserFactory()
        assert modulo.esta_desbloqueado(user) is True

    def test_segundo_modulo_bloqueado_sem_progresso(self):
        trilha = TrilhaFactory()
        modulo1 = ModuloFactory(trilha=trilha, ordem=0)
        modulo2 = ModuloFactory(trilha=trilha, ordem=1)
        DiscipuladoTemaFactory(modulo=modulo1, ordem=0)
        user = UserFactory()
        assert modulo2.esta_desbloqueado(user) is False

    def test_segundo_modulo_desbloqueado_com_primeiro_completo(self):
        trilha = TrilhaFactory()
        modulo1 = ModuloFactory(trilha=trilha, ordem=0)
        modulo2 = ModuloFactory(trilha=trilha, ordem=1)
        tema = DiscipuladoTemaFactory(modulo=modulo1, ordem=0)
        user = UserFactory()
        ProgressoTemaFactory(usuario=user, tema=tema)
        assert modulo2.esta_desbloqueado(user) is True

    def test_modulo_sem_anterior_esta_desbloqueado(self):
        """Módulo sem nenhum anterior (único na trilha) está sempre desbloqueado."""
        trilha = TrilhaFactory()
        modulo = ModuloFactory(trilha=trilha, ordem=0)
        user = UserFactory()
        assert modulo.esta_desbloqueado(user) is True


class TestModuloPercentualConclusao:
    def test_percentual_zero_sem_temas(self):
        modulo = ModuloFactory()
        user = UserFactory()
        assert modulo.percentual_conclusao(user) == 0

    def test_percentual_zero_sem_progresso(self):
        modulo = ModuloFactory()
        DiscipuladoTemaFactory(modulo=modulo, ordem=0)
        DiscipuladoTemaFactory(modulo=modulo, ordem=1)
        user = UserFactory()
        assert modulo.percentual_conclusao(user) == 0

    def test_percentual_50_percent(self):
        modulo = ModuloFactory()
        tema1 = DiscipuladoTemaFactory(modulo=modulo, ordem=0)
        DiscipuladoTemaFactory(modulo=modulo, ordem=1)
        user = UserFactory()
        ProgressoTemaFactory(usuario=user, tema=tema1)
        assert modulo.percentual_conclusao(user) == 50

    def test_percentual_100_percent(self):
        modulo = ModuloFactory()
        tema1 = DiscipuladoTemaFactory(modulo=modulo, ordem=0)
        tema2 = DiscipuladoTemaFactory(modulo=modulo, ordem=1)
        user = UserFactory()
        ProgressoTemaFactory(usuario=user, tema=tema1)
        ProgressoTemaFactory(usuario=user, tema=tema2)
        assert modulo.percentual_conclusao(user) == 100

    def test_percentual_nao_conta_outros_usuarios(self):
        modulo = ModuloFactory()
        tema1 = DiscipuladoTemaFactory(modulo=modulo, ordem=0)
        tema2 = DiscipuladoTemaFactory(modulo=modulo, ordem=1)
        user = UserFactory()
        outro = UserFactory()
        ProgressoTemaFactory(usuario=outro, tema=tema1)
        ProgressoTemaFactory(usuario=outro, tema=tema2)
        assert modulo.percentual_conclusao(user) == 0


# ─────────────────────────────────────────────────────────────────────────────
# TrilhaListView
# ─────────────────────────────────────────────────────────────────────────────

class TestTrilhaListView:
    def test_lista_trilhas_requer_login(self, client):
        response = client.get(reverse("discipulado:lista_trilhas"))
        assert response.status_code == 302

    def test_lista_trilhas_autenticado(self, client):
        user = UserFactory()
        client.force_login(user)
        TrilhaFactory.create_batch(3)
        response = client.get(reverse("discipulado:lista_trilhas"))
        assert response.status_code == 200
        assert len(response.context["trilhas"]) == 3

    def test_lista_trilhas_sem_trilhas(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("discipulado:lista_trilhas"))
        assert response.status_code == 200
        assert len(response.context["trilhas"]) == 0


# ─────────────────────────────────────────────────────────────────────────────
# TemaDetalheView (discipulado)
# ─────────────────────────────────────────────────────────────────────────────

class TestDiscipuladoTemaDetalheView:
    def test_detalhe_tema_anonimo_redireciona(self, client):
        tema = DiscipuladoTemaFactory()
        response = client.get(
            reverse("discipulado:detalhe_tema", kwargs={"slug": tema.slug})
        )
        assert response.status_code == 302

    def test_detalhe_tema_autenticado(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = DiscipuladoTemaFactory()
        response = client.get(
            reverse("discipulado:detalhe_tema", kwargs={"slug": tema.slug})
        )
        assert response.status_code == 200

    def test_contexto_ja_concluido_falso(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = DiscipuladoTemaFactory()
        response = client.get(
            reverse("discipulado:detalhe_tema", kwargs={"slug": tema.slug})
        )
        assert response.context["ja_concluido"] is False

    def test_contexto_ja_concluido_verdadeiro(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = DiscipuladoTemaFactory()
        ProgressoTemaFactory(usuario=user, tema=tema)
        response = client.get(
            reverse("discipulado:detalhe_tema", kwargs={"slug": tema.slug})
        )
        assert response.context["ja_concluido"] is True


# ─────────────────────────────────────────────────────────────────────────────
# ConcluirTemaView (discipulado)
# ─────────────────────────────────────────────────────────────────────────────

class TestConcluirTemaDiscipuladoView:
    def test_concluir_cria_progresso(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = DiscipuladoTemaFactory()
        response = client.post(
            reverse("discipulado:concluir_tema", kwargs={"slug": tema.slug})
        )
        assert response.status_code == 302
        assert ProgressoTema.objects.filter(usuario=user, tema=tema).exists()

    def test_concluir_idempotente(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = DiscipuladoTemaFactory()
        ProgressoTemaFactory(usuario=user, tema=tema)
        client.post(reverse("discipulado:concluir_tema", kwargs={"slug": tema.slug}))
        assert ProgressoTema.objects.filter(usuario=user, tema=tema).count() == 1

    def test_concluir_get_retorna_405(self, client):
        user = UserFactory()
        client.force_login(user)
        tema = DiscipuladoTemaFactory()
        response = client.get(
            reverse("discipulado:concluir_tema", kwargs={"slug": tema.slug})
        )
        assert response.status_code == 405

    def test_concluir_anonimo_redireciona(self, client):
        tema = DiscipuladoTemaFactory()
        response = client.post(
            reverse("discipulado:concluir_tema", kwargs={"slug": tema.slug})
        )
        assert response.status_code == 302

    def test_concluir_redireciona_para_proximo_tema(self, client):
        """Após concluir, deve redirecionar para o próximo tema do módulo."""
        user = UserFactory()
        client.force_login(user)
        modulo = ModuloFactory()
        tema1 = DiscipuladoTemaFactory(modulo=modulo, ordem=0)
        tema2 = DiscipuladoTemaFactory(modulo=modulo, ordem=1)
        response = client.post(
            reverse("discipulado:concluir_tema", kwargs={"slug": tema1.slug})
        )
        assert response["Location"] == reverse(
            "discipulado:detalhe_tema", kwargs={"slug": tema2.slug}
        )

    def test_concluir_ultimo_redireciona_para_modulo(self, client):
        """Após concluir o último tema, deve redirecionar para o módulo."""
        user = UserFactory()
        client.force_login(user)
        modulo = ModuloFactory()
        tema = DiscipuladoTemaFactory(modulo=modulo, ordem=0)
        response = client.post(
            reverse("discipulado:concluir_tema", kwargs={"slug": tema.slug})
        )
        assert response["Location"] == reverse(
            "discipulado:detalhe_modulo", kwargs={"slug": modulo.slug}
        )

