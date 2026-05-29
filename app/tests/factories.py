"""
factories.py — Factory Boy factories para todos os models principais.

Importar nos testes:
    from tests.factories import UserFactory, DevocionalTemaFactory, ...
"""

import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from apps.devocional.models import ProgressoUsuario
from apps.devocional.models import SubtituloTema
from apps.devocional.models import Tema as DevocionalTema
from apps.discipulado.models import Modulo
from apps.discipulado.models import ProgressoTema
from apps.discipulado.models import Tema as DiscipuladoTema
from apps.discipulado.models import Trilha

User = get_user_model()


# ─── Accounts ────────────────────────────────────────────────────────────────

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@test.com")
    nome_completo = factory.Faker("name", locale="pt_BR")
    is_active = True
    password = factory.PostGenerationMethodCall("set_password", "senha123")


class AdminUserFactory(UserFactory):
    is_staff = True
    is_superuser = True


class LiderUserFactory(UserFactory):
    is_lider = True


# ─── Devocional ───────────────────────────────────────────────────────────────

class DevocionalTemaFactory(DjangoModelFactory):
    class Meta:
        model = DevocionalTema

    titulo = factory.Sequence(lambda n: f"Tema Devocional {n}")
    # slug é auto-gerado pelo save() quando vazio
    status = DevocionalTema.StatusChoices.PUBLICADO
    acesso = DevocionalTema.AcessoChoices.PUBLICO
    texto_base = factory.Faker("paragraph", locale="pt_BR")
    ordem = factory.Sequence(lambda n: n)


class PrivateDevocionalTemaFactory(DevocionalTemaFactory):
    acesso = DevocionalTema.AcessoChoices.LOGIN_OBRIGATORIO


class SubtituloTemaFactory(DjangoModelFactory):
    class Meta:
        model = SubtituloTema

    tema = factory.SubFactory(DevocionalTemaFactory)
    titulo = factory.Sequence(lambda n: f"Subtítulo {n}")
    ordem = factory.Sequence(lambda n: n)


class ProgressoUsuarioFactory(DjangoModelFactory):
    class Meta:
        model = ProgressoUsuario

    usuario = factory.SubFactory(UserFactory)
    tema = factory.SubFactory(DevocionalTemaFactory)


# ─── Discipulado ──────────────────────────────────────────────────────────────

class TrilhaFactory(DjangoModelFactory):
    class Meta:
        model = Trilha

    titulo = factory.Sequence(lambda n: f"Trilha {n}")
    descricao = factory.Faker("paragraph", locale="pt_BR")
    ordem = factory.Sequence(lambda n: n)


class ModuloFactory(DjangoModelFactory):
    class Meta:
        model = Modulo

    trilha = factory.SubFactory(TrilhaFactory)
    titulo = factory.Sequence(lambda n: f"Módulo {n}")
    # ordem é único por trilha; usa Sequence global — cada ModuloFactory com a
    # mesma trilha em testes explícitos deve receber ordem= diferente.
    ordem = factory.Sequence(lambda n: n)


class DiscipuladoTemaFactory(DjangoModelFactory):
    class Meta:
        model = DiscipuladoTema

    modulo = factory.SubFactory(ModuloFactory)
    titulo = factory.Sequence(lambda n: f"Tema Discipulado {n}")
    conteudo = factory.Faker("paragraph", locale="pt_BR")
    ordem = factory.Sequence(lambda n: n)


class ProgressoTemaFactory(DjangoModelFactory):
    class Meta:
        model = ProgressoTema

    usuario = factory.SubFactory(UserFactory)
    tema = factory.SubFactory(DiscipuladoTemaFactory)
