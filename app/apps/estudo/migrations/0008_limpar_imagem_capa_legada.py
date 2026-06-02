# Limpa valores legados de imagem_capa (caminhos de upload antigos)
# que não correspondem aos novos choices de imagens estáticas.
# Registros com valor fora dos choices ficam com "" (sem imagem).

from django.db import migrations

CHOICES_VALIDOS = {"devocional.jpg", "discipulado.jpg", "estudopessoal.jpg"}


def limpar_imagem_capa(apps, schema_editor):
    Modulo = apps.get_model("estudo", "Modulo")
    Modulo.objects.exclude(imagem_capa__in=CHOICES_VALIDOS).update(imagem_capa="")

    HistoricalModulo = apps.get_model("estudo", "HistoricalModulo")
    HistoricalModulo.objects.exclude(imagem_capa__in=CHOICES_VALIDOS).update(imagem_capa="")


class Migration(migrations.Migration):

    dependencies = [
        ("estudo", "0007_imagem_capa_static_choice"),
    ]

    operations = [
        migrations.RunPython(limpar_imagem_capa, migrations.RunPython.noop),
    ]
