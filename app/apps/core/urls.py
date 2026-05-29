"""
URLs do app Core.

Namespace: core
"""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    # Página inicial
    path("", views.HomeView.as_view(), name="home"),
]
