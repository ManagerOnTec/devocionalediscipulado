"""
conftest.py — Fixtures globais do pytest para o projeto.

Fixtures disponíveis em todos os testes sem necessidade de importação.
"""

import pytest
from tests.factories import AdminUserFactory, UserFactory


@pytest.fixture
def usuario(db):
    """
    Fixture: usuário padrão autenticado para testes.

    Uso:
        def test_minha_view(client, usuario):
            client.force_login(usuario)
            response = client.get('/')
            assert response.status_code == 200
    """
    return UserFactory()


@pytest.fixture
def usuario_admin(db):
    """Fixture: superusuário para testes de admin."""
    return AdminUserFactory()


@pytest.fixture
def client_autenticado(client, usuario):
    """Fixture: client HTTP já autenticado com o usuário padrão."""
    client.force_login(usuario)
    return client
