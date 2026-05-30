from storages.backends.gcloud import GoogleCloudStorage
from django.conf import settings


class PrivateMediaStorage(GoogleCloudStorage):
    """
    Storage para arquivos de mídia privados no GCS.
    Gera URLs assinadas temporárias — compatível com política de organização
    que bloqueia acesso público (allUsers).
    """
    bucket_name = settings.GS_BUCKET_NAME
    file_overwrite = False  # Nunca sobrescreve arquivos com mesmo nome
