"""URLs do app Estudo."""

from django.urls import path

from . import views

app_name = "estudo"

urlpatterns = [
    # Lista de trilhas publicadas
    path("", views.TrilhaListView.as_view(), name="lista_trilhas"),

    # Progresso pessoal
    path("meu-progresso/", views.MeuProgressoView.as_view(), name="meu_progresso"),

    # ── Estudos Pessoais — ANTES do <slug:slug>/ ───────────────────────
    path("estudos-pessoais/", views.EstudoPessoalListView.as_view(), name="estudopessoal_lista"),
    path("estudos-pessoais/<int:pk>/", views.EstudoPessoalDetalheView.as_view(), name="estudopessoal_detalhe"),

    # Detalhe de módulo / tema  (prefixados, sem conflito)
    path("modulo/<slug:slug>/", views.ModuloDetalheView.as_view(), name="detalhe_modulo"),
    path("tema/<slug:slug>/", views.TemaDetalheView.as_view(), name="detalhe_tema"),
    path("tema/<slug:slug>/concluir/", views.ConcluirTemaView.as_view(), name="concluir_tema"),
    path("tema/<slug:slug>/desconcluir/", views.DesconcluirTemaView.as_view(), name="desconcluir_tema"),

    # Detalhe de trilha — slug genérico por último
    path("<slug:slug>/", views.TrilhaDetalheView.as_view(), name="detalhe_trilha"),
]
