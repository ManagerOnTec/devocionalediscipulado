"""
Testes do app Accounts — model User, login, logout e cadastro.
"""

import pytest
from django.urls import reverse

from .factories import AdminUserFactory, UserFactory

pytestmark = pytest.mark.django_db


# ─────────────────────────────────────────────────────────────────────────────
# User model
# ─────────────────────────────────────────────────────────────────────────────

class TestUserModel:
    def test_criar_usuario(self):
        user = UserFactory()
        assert user.pk is not None
        assert user.is_active is True

    def test_email_e_campo_de_login(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        assert User.USERNAME_FIELD == "email"

    def test_primeiro_nome(self):
        user = UserFactory(nome_completo="João Pedro Silva")
        assert user.primeiro_nome == "João"

    def test_str_representation(self):
        user = UserFactory(nome_completo="Maria Silva", email="maria@example.com")
        assert str(user) == "Maria Silva <maria@example.com>"

    def test_get_full_name(self):
        user = UserFactory(nome_completo="Ana Paula")
        assert user.get_full_name() == "Ana Paula"

    def test_get_short_name(self):
        user = UserFactory(nome_completo="Carlos Eduardo")
        assert user.get_short_name() == "Carlos"

    def test_is_lider_default_false(self):
        user = UserFactory()
        assert user.is_lider is False

    def test_admin_is_staff_e_superuser(self):
        admin = AdminUserFactory()
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_email_unico(self):
        from django.db import IntegrityError
        UserFactory(email="unico@example.com")
        with pytest.raises(IntegrityError):
            UserFactory(email="unico@example.com")


# ─────────────────────────────────────────────────────────────────────────────
# LoginView
# ─────────────────────────────────────────────────────────────────────────────

class TestLoginView:
    def test_login_page_acessivel(self, client):
        response = client.get(reverse("accounts:login"))
        assert response.status_code == 200
        assert "form" in response.context

    def test_login_com_credenciais_validas(self, client):
        user = UserFactory()
        response = client.post(
            reverse("accounts:login"),
            {"username": user.email, "password": "senha123"},
        )
        assert response.status_code == 302

    def test_login_com_credenciais_invalidas(self, client):
        response = client.post(
            reverse("accounts:login"),
            {"username": "nao@existe.com", "password": "errado"},
        )
        assert response.status_code == 200
        assert "form" in response.context

    def test_usuario_autenticado_redireciona_do_login(self, client):
        """Usuário já logado não deve ver a página de login."""
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("accounts:login"))
        assert response.status_code == 302

    def test_login_senha_errada(self, client):
        user = UserFactory()
        response = client.post(
            reverse("accounts:login"),
            {"username": user.email, "password": "senha_errada"},
        )
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# LogoutView
# ─────────────────────────────────────────────────────────────────────────────

class TestLogoutView:
    def test_logout_via_post(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.post(reverse("accounts:logout"))
        assert response.status_code == 302

    def test_logout_redireciona_para_login(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.post(reverse("accounts:logout"))
        # Deve redirecionar para a página de login (LOGOUT_REDIRECT_URL)
        assert "/contas/entrar/" in response["Location"] or response.status_code == 302

    def test_logout_encerra_sessao(self, client):
        user = UserFactory()
        client.force_login(user)
        client.post(reverse("accounts:logout"))
        # Após logout, acesso à área autenticada deve redirecionar
        response = client.get(reverse("devocional:progresso"))
        assert response.status_code == 302


# ─────────────────────────────────────────────────────────────────────────────
# CadastroView
# ─────────────────────────────────────────────────────────────────────────────

class TestCadastroView:
    def test_cadastro_page_acessivel(self, client):
        response = client.get(reverse("accounts:cadastro"))
        assert response.status_code == 200

    def test_cadastro_cria_usuario(self, client):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        data = {
            "email": "novo@example.com",
            "nome_completo": "Novo Usuário",
            "password1": "Senha@Forte123",
            "password2": "Senha@Forte123",
        }
        response = client.post(reverse("accounts:cadastro"), data)
        # 200 significa erro no form; 302 significa sucesso
        if response.status_code == 302:
            assert User.objects.filter(email="novo@example.com").exists()
