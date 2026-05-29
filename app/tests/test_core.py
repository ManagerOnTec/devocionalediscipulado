"""
Testes do app Core — views, BaseModel e soft delete.
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.models import BaseModel, SoftDeleteQuerySet, TimeStampedModel

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Modelo concreto para testes (não vai para o banco real — apenas para unit tests)
# ─────────────────────────────────────────────────────────────────────────────

class ModeloTeste(BaseModel):
    """Model concreto mínimo para testar o BaseModel em memória."""

    nome = models.CharField(max_length=100, default="teste")

    class Meta(BaseModel.Meta):
        # app_label garante que o Django não tente criar migration para esse model
        app_label = "core"


# ─────────────────────────────────────────────────────────────────────────────
# Testes: BaseModel — campos e estrutura
# ─────────────────────────────────────────────────────────────────────────────

class TestBaseModelCampos:
    """Verifica que o BaseModel declara todos os campos obrigatórios."""

    def test_possui_campo_criado_em(self):
        campo = BaseModel._meta.get_field("criado_em")
        assert campo is not None

    def test_possui_campo_atualizado_em(self):
        campo = BaseModel._meta.get_field("atualizado_em")
        assert campo is not None

    def test_possui_campo_criado_por(self):
        campo = BaseModel._meta.get_field("criado_por")
        assert campo is not None

    def test_possui_campo_atualizado_por(self):
        campo = BaseModel._meta.get_field("atualizado_por")
        assert campo is not None

    def test_possui_campo_is_active(self):
        campo = BaseModel._meta.get_field("is_active")
        assert campo is not None

    def test_possui_campo_deleted_at(self):
        campo = BaseModel._meta.get_field("deleted_at")
        assert campo is not None

    def test_is_active_default_true(self):
        campo = BaseModel._meta.get_field("is_active")
        assert campo.default is True

    def test_is_active_tem_db_index(self):
        campo = BaseModel._meta.get_field("is_active")
        assert campo.db_index is True

    def test_deleted_at_nao_editavel(self):
        campo = BaseModel._meta.get_field("deleted_at")
        assert campo.editable is False

    def test_e_abstrato(self):
        assert BaseModel._meta.abstract is True

    def test_possui_manager_objects(self):
        """objects deve ser o ActiveManager (filtra apenas ativos)."""
        from apps.core.models import ActiveManager
        assert isinstance(ModeloTeste.objects, ActiveManager)

    def test_possui_manager_all_objects(self):
        """all_objects deve ser o AllObjectsManager (retorna todos)."""
        from apps.core.models import AllObjectsManager
        assert isinstance(ModeloTeste.all_objects, AllObjectsManager)


# ─────────────────────────────────────────────────────────────────────────────
# Testes: Soft Delete
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSoftDelete:
    """Testes de comportamento do soft delete."""

    def test_delete_marca_is_active_false(self, usuario):
        obj = ModeloTeste.objects.create(nome="para deletar", criado_por=usuario)
        obj.delete()
        # Recarrega do banco via all_objects (objects filtra ativos)
        obj.refresh_from_db()
        assert obj.is_active is False

    def test_delete_preenche_deleted_at(self, usuario):
        antes = timezone.now()
        obj = ModeloTeste.objects.create(nome="soft", criado_por=usuario)
        obj.delete()
        obj.refresh_from_db()
        assert obj.deleted_at is not None
        assert obj.deleted_at >= antes

    def test_objeto_deletado_nao_aparece_no_manager_padrao(self, usuario):
        obj = ModeloTeste.objects.create(nome="invisível", criado_por=usuario)
        pk = obj.pk
        obj.delete()
        assert not ModeloTeste.objects.filter(pk=pk).exists()

    def test_objeto_deletado_aparece_no_all_objects(self, usuario):
        obj = ModeloTeste.objects.create(nome="ainda existe", criado_por=usuario)
        pk = obj.pk
        obj.delete()
        assert ModeloTeste.all_objects.filter(pk=pk).exists()

    def test_restore_reativa_registro(self, usuario):
        obj = ModeloTeste.objects.create(nome="recuperar", criado_por=usuario)
        obj.delete()
        obj.restore()
        obj.refresh_from_db()
        assert obj.is_active is True
        assert obj.deleted_at is None

    def test_restore_faz_registro_aparecer_no_objects(self, usuario):
        obj = ModeloTeste.objects.create(nome="volta", criado_por=usuario)
        pk = obj.pk
        obj.delete()
        obj.restore()
        assert ModeloTeste.objects.filter(pk=pk).exists()

    def test_property_is_deleted(self, usuario):
        obj = ModeloTeste.objects.create(nome="prop", criado_por=usuario)
        assert obj.is_deleted is False
        obj.delete()
        assert obj.is_deleted is True

    def test_queryset_delete_em_lote(self, usuario):
        ModeloTeste.objects.create(nome="lote1", criado_por=usuario)
        ModeloTeste.objects.create(nome="lote2", criado_por=usuario)
        ModeloTeste.objects.filter(nome__startswith="lote").delete()
        assert ModeloTeste.objects.filter(nome__startswith="lote").count() == 0

    def test_hard_delete_remove_fisicamente(self, usuario):
        obj = ModeloTeste.objects.create(nome="fisico", criado_por=usuario)
        pk = obj.pk
        obj.hard_delete()
        assert not ModeloTeste.all_objects.filter(pk=pk).exists()


# ─────────────────────────────────────────────────────────────────────────────
# Testes: HomeView
# ─────────────────────────────────────────────────────────────────────────────

class TestHomeView:
    """Testes para a HomeView."""

    def test_home_retorna_200(self, client):
        url = reverse("core:home")
        response = client.get(url)
        assert response.status_code == 200

    def test_home_usa_template_correto(self, client):
        url = reverse("core:home")
        response = client.get(url)
        assert "core/home.html" in [t.name for t in response.templates]

    def test_home_contem_titulo_no_contexto(self, client):
        url = reverse("core:home")
        response = client.get(url)
        assert "titulo" in response.context
