import pytest
from django.contrib import admin
from django.urls import reverse

from apps.estudo.admin import TemaAdmin
from apps.estudo.models import Modulo, Tema, Trilha


pytestmark = pytest.mark.django_db


class TestTemaAdmin:
    def test_fieldsets_seguem_ordem_visual_solicitada(self, rf):
        request = rf.get("/admin/estudo/tema/add/")
        model_admin = TemaAdmin(Tema, admin.site)

        fieldset_titles = [fieldset[0] for fieldset in model_admin.get_fieldsets(request)]

        assert fieldset_titles == [
            "Identificação",
            "Conteúdo Principal",
            "Referências Cruzadas",
            "Estudo",
            "Conclusão",
            "Exemplo Prático",
            "Oração",
            "Professores",
            "Auditoria",
        ]


class TestTemaDetalheTemplate:
    def test_template_renderiza_secoes_na_ordem_solicitada(self, client):
        trilha = Trilha.objects.create(
            titulo="Trilha de Teste",
            slug="trilha-de-teste",
            status=Trilha.StatusChoices.PUBLICADO,
            acesso=Trilha.AcessoChoices.PUBLICO,
        )
        modulo = Modulo.objects.create(
            trilha=trilha,
            titulo="Módulo de Teste",
            slug="modulo-de-teste",
            acesso=Trilha.AcessoChoices.PUBLICO,
        )
        tema = Tema.objects.create(
            modulo=modulo,
            titulo="Tema de Teste",
            slug="tema-de-teste",
            acesso=Trilha.AcessoChoices.PUBLICO,
            texto_base="Texto base",
            tem_referencias=True,
            referencias_cruzadas="Referências",
            tem_estudo=True,
            estudo="Estudo",
            tem_conclusao=True,
            conclusao="Conclusão",
            tem_exemplo=True,
            exemplo_pratico="Exemplo",
            tem_oracao=True,
            oracao="Oração",
        )

        response = client.get(reverse("estudo:detalhe_tema", kwargs={"slug": tema.slug}))

        assert response.status_code == 200

        content = response.content.decode()
        ordem_renderizada = [
            content.index("Texto Base"),
            content.index("Referências Cruzadas"),
            content.index("Estudo"),
            content.index("Conclusão"),
            content.index("Exemplo Prático"),
            content.index("Oração"),
        ]

        assert ordem_renderizada == sorted(ordem_renderizada)
