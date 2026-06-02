"""URLs do app Estudo."""

from django.urls import path

from . import views

app_name = "estudo"

urlpatterns = [
    # Lista de trilhas publicadas
    path("", views.TrilhaListView.as_view(), name="lista_trilhas"),

    # Progresso pessoal (antes dos slugs para não ser capturado)
    path("meu-progresso/", views.MeuProgressoView.as_view(), name="meu_progresso"),

    # Detalhe de trilha
    path("<slug:slug>/", views.TrilhaDetalheView.as_view(), name="detalhe_trilha"),

    # Detalhe de módulo
    path("modulo/<slug:slug>/", views.ModuloDetalheView.as_view(), name="detalhe_modulo"),

    # Detalhe de tema
    path("tema/<slug:slug>/", views.TemaDetalheView.as_view(), name="detalhe_tema"),

    # Concluir tema [POST]
    path("tema/<slug:slug>/concluir/", views.ConcluirTemaView.as_view(), name="concluir_tema"),

    # Desmarcar conclusão de tema [POST]
    path("tema/<slug:slug>/desconcluir/", views.DesconcluirTemaView.as_view(), name="desconcluir_tema"),

    # ── Estudos Pessoais (superadmin only) ───────────────────────────────────
    path("estudos-pessoais/", views.EstudoPessoalListView.as_view(), name="estudopessoal_lista"),
    path("estudos-pessoais/<int:pk>/", views.EstudoPessoalDetalheView.as_view(), name="estudopessoal_detalhe"),
]
