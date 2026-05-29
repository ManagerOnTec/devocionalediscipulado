"""
Management command: wait_for_db

Aguarda o banco de dados ficar disponível antes de iniciar o servidor.
Útil no entrypoint do Docker para evitar erros de conexão na inicialização.

Uso:
    python manage.py wait_for_db
"""

import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Aguarda o banco de dados estar disponível."""

    help = "Aguarda a disponibilidade do banco de dados"

    def handle(self, *args, **options):
        """Tenta conectar ao banco em loop até ter sucesso."""
        self.stdout.write("Aguardando banco de dados...")
        db_conn = None
        tentativas = 0
        max_tentativas = 30  # ~30 segundos

        while not db_conn and tentativas < max_tentativas:
            try:
                db_conn = connections["default"]
                db_conn.cursor()
            except OperationalError:
                tentativas += 1
                self.stdout.write(
                    f"Banco indisponível, tentativa {tentativas}/{max_tentativas}..."
                )
                time.sleep(1)

        if tentativas >= max_tentativas:
            self.stderr.write(self.style.ERROR("Banco de dados não disponível após timeout."))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("Banco de dados disponível!"))
