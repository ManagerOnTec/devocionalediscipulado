"""
Formulários do app Accounts.

Forms disponíveis:
    LoginForm               → login via e-mail com attrs Bootstrap
    CustomUserCreationForm  → criação de novo usuário (usado no admin e cadastro)
    CustomUserChangeForm    → alteração de usuário (usado no admin)
    PerfilForm              → edição do próprio perfil pelo usuário logado
    AlterarSenhaForm        → alteração de senha com confirmação

Todas as validações ficam nos forms, conforme padrão do projeto.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    UserChangeForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError

User = get_user_model()


# ─── Formulário de criação de usuário ────────────────────────────────────────

class CustomUserCreationForm(UserCreationForm):
    """
    Formulário de criação de novo usuário com e-mail como login.

    Usado no admin Django e na view de cadastro público.
    Herda a validação de senha do UserCreationForm padrão.
    """

    class Meta:
        model = User
        fields = ("email", "nome_completo", "telefone")
        widgets = {
            "email": forms.EmailInput(attrs={
                "placeholder": "seu@email.com",
                "autocomplete": "email",
            }),
            "nome_completo": forms.TextInput(attrs={
                "placeholder": "Nome e sobrenome",
                "autocomplete": "name",
            }),
            "telefone": forms.TextInput(attrs={
                "placeholder": "(11) 99999-9999",
            }),
        }

    def clean_email(self):
        """Normaliza o e-mail para lowercase e verifica unicidade."""
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Já existe uma conta com este e-mail.")
        return email

    def clean_nome_completo(self):
        """Garante que o nome completo tenha pelo menos duas palavras."""
        nome = self.cleaned_data.get("nome_completo", "").strip()
        if len(nome.split()) < 2:
            raise ValidationError("Informe o nome e o sobrenome.")
        return nome.title()


# ─── Formulário de alteração de usuário (admin) ───────────────────────────────

class CustomUserChangeForm(UserChangeForm):
    """
    Formulário de edição de usuário para o painel admin.

    Herda a lógica de senha do UserChangeForm padrão do Django.
    """

    class Meta:
        model = User
        fields = (
            "email",
            "nome_completo",
            "foto",
            "telefone",
            "timezone",
            "dark_mode",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )


# ─── Formulário de perfil (pelo próprio usuário) ──────────────────────────────

class PerfilForm(forms.ModelForm):
    """
    Formulário para o usuário logado editar o próprio perfil.

    Não expõe campos sensíveis como is_staff, is_superuser, permissões.
    Para alterar senha, usar AlterarSenhaForm separadamente.
    """

    class Meta:
        model = User
        fields = ("nome_completo", "foto", "telefone", "timezone", "dark_mode")
        widgets = {
            "nome_completo": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nome e sobrenome",
            }),
            "foto": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/jpeg,image/png,image/webp",
            }),
            "telefone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "(11) 99999-9999",
            }),
            "timezone": forms.Select(attrs={
                "class": "form-select",
            }),
            "dark_mode": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def clean_nome_completo(self):
        """Garante que o nome completo tenha pelo menos duas palavras."""
        nome = self.cleaned_data.get("nome_completo", "").strip()
        if len(nome.split()) < 2:
            raise ValidationError("Informe o nome e o sobrenome.")
        return nome.title()

    def clean_foto(self):
        """
        Valida o arquivo de foto enviado.

        Restrições:
            - Tamanho máximo: 2 MB
            - Formatos aceitos: JPEG, PNG
        """
        foto = self.cleaned_data.get("foto")

        # Se não enviou nova foto ou marcou para remover, retorna sem validar
        if not foto or not hasattr(foto, "content_type"):
            return foto

        # Valida o tipo de arquivo por MIME type
        tipos_aceitos = ("image/jpeg", "image/png", "image/webp")
        if foto.content_type not in tipos_aceitos:
            raise ValidationError("Formato inválido. Use JPG, PNG ou WebP.")

        # Valida o tamanho (máximo 2 MB)
        tamanho_maximo = 2 * 1024 * 1024  # 2 MB em bytes
        if foto.size > tamanho_maximo:
            raise ValidationError("A imagem deve ter no máximo 2 MB.")

        return foto


# ─── Formulário de login ──────────────────────────────────────────────────────

class LoginForm(AuthenticationForm):
    """
    Formulário de login via e-mail com atributos Bootstrap.

    Personaliza o campo 'username' do AuthenticationForm para
    exibir label 'E-mail' e usar EmailInput com autocomplete correto.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "E-mail"
        self.fields["username"].widget = forms.EmailInput(attrs={
            "class": "form-control form-control-lg",
            "placeholder": "seu@email.com",
            "autocomplete": "email",
            "autofocus": True,
        })
        self.fields["password"].widget = forms.PasswordInput(attrs={
            "class": "form-control form-control-lg",
            "placeholder": "••••••••",
            "autocomplete": "current-password",
        })


# ─── Formulário de alteração de senha ────────────────────────────────────────

class AlterarSenhaForm(PasswordChangeForm):
    """
    Formulário de alteração de senha pelo usuário autenticado.

    Adiciona classes Bootstrap a todos os campos herdados do PasswordChangeForm.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            existing_class = widget.attrs.get("class", "")
            if "form-control" not in existing_class:
                widget.attrs["class"] = f"form-control {existing_class}".strip()


# ─── Formulário de recuperação de senha ──────────────────────────────────────

class RecuperarSenhaForm(PasswordResetForm):
    """
    Recuperação de senha via e-mail.

    Valida que o endereço informado está cadastrado no banco de dados.
    Exibe erro explícito caso não seja encontrado — comportamento
    solicitado pelo administrador do sistema.
    """

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not User.objects.filter(email=email, is_active=True).exists():
            raise ValidationError(
                "Não encontramos nenhuma conta ativa com este e-mail."
            )
        return email
