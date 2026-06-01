from storages.backends.gcloud import GoogleCloudStorage


class PrivateMediaStorage(GoogleCloudStorage):
    """
    Storage para arquivos de mídia privados no GCS.
    Gera URLs assinadas temporárias — compatível com política de organização
    que bloqueia acesso público (allUsers).

    bucket_name é herdado de GoogleCloudStorage, que lê settings.GS_BUCKET_NAME
    via django.conf.settings no __init__, evitando acesso antecipado a settings
    na importação do módulo.
    """

    file_overwrite = False
