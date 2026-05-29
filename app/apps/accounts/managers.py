"""
Manager customizado para o modelo User.

Sobrescreve create_user e create_superuser para usar
email como identificador principal (em vez de username).
"""

from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Manager que usa email como campo de login.

    Substitui o UserManager padrão do Django que usa username.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Cria e salva um usuário com o email e senha fornecidos.

        Args:
            email:     E-mail do usuário (obrigatório, único).
            password:  Senha em texto plano (será hasheada).
            **extra_fields: Campos adicionais do modelo User.

        Returns:
            User: instância salva no banco.

        Raises:
            ValueError: se o e-mail não for fornecido.
        """
        if not email:
            raise ValueError("O campo e-mail é obrigatório.")

        # Normaliza o domínio do e-mail para lowercase
        email = self.normalize_email(email)

        extra_fields.setdefault("is_active", True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Cria e salva um superusuário com todas as permissões.

        Uso:
            python manage.py createsuperuser
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superusuário precisa ter is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superusuário precisa ter is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
