"""Formulários do app SAC / Suporte."""

from django import forms

from .models import SacSuporte


class SacSuporteForm(forms.ModelForm):
    """Formulário público para envio de mensagem ao SAC."""

    class Meta:
        model = SacSuporte
        fields = ("tipo", "mensagem")
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select form-select-lg"}),
            "mensagem": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Descreva sua mensagem com o máximo de detalhes...",
            }),
        }
        labels = {
            "tipo": "Tipo de contato",
            "mensagem": "Sua mensagem",
        }
