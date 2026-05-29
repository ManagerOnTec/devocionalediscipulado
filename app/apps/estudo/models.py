"""
Models do app Estudo (unificação de Devocional e Discipulado).

Hierarquia:
    Trilha(BaseModel)                      ← agrupa módulos; define tipo, acesso e status
    Modulo(BaseModel)                      ← unidade de estudo dentro de uma Trilha; tem imagem
    Tema(BaseModel)                        ← lição/tópico dentro de um Módulo; tem seções ativáveis
    ProgressoTema(TimeStampedModel)        ← conclusão de um Tema por usuário
"""

import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from apps.core.models import BaseModel, TimeStampedModel


# ─────────────────────────────────────────────────────────────────────────────
# Validador de imagem de capa
# ─────────────────────────────────────────────────────────────────────────────

def validar_formato_imagem(arquivo):
    """
    Aceita somente JPEG (.jpg / .jpeg) e PNG (.png).
    A mensagem de erro é exibida diretamente no formulário do admin.
    """
    ext = os.path.splitext(arquivo.name)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        raise ValidationError(
            "Formato inválido. Envie apenas arquivos JPEG (.jpg, .jpeg) ou PNG (.png)."
        )
    if hasattr(arquivo, "content_type"):
        tipos_aceitos = ("image/jpeg", "image/png")
        if arquivo.content_type not in tipos_aceitos:
            raise ValidationError(
                "Formato inválido. Envie apenas arquivos JPEG (.jpg, .jpeg) ou PNG (.png)."
            )


# ─────────────────────────────────────────────────────────────────────────────
# Trilha
# ─────────────────────────────────────────────────────────────────────────────

class Trilha(BaseModel):
    """
    Agrupa módulos de estudo. Pode representar uma trilha de discipulado
    (com líder/discípulo) ou uma coleção devocional (acesso livre).
    """

    class TipoChoices(models.TextChoices):
        DEVOCIONAL   = "DEVOCIONAL",   "Devocional"
        DISCIPULADO  = "DISCIPULADO",  "Discipulado"

    class StatusChoices(models.TextChoices):
        RASCUNHO  = "RASCUNHO",  "Rascunho"
        PUBLICADO = "PUBLICADO", "Publicado"
        ARQUIVADO = "ARQUIVADO", "Arquivado"

    class AcessoChoices(models.TextChoices):
        PUBLICO              = "PUBLICO",              "Público"
        LOGIN_OBRIGATORIO    = "LOGIN_OBRIGATORIO",    "Login obrigatório"
        PERMISSAO_ESPECIFICA = "PERMISSAO_ESPECIFICA", "Permissão específica"

    titulo = models.CharField(
        max_length=200,
        verbose_name="Título",
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        verbose_name="Slug",
    )
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoChoices.choices,
        default=TipoChoices.DEVOCIONAL,
        verbose_name="Tipo",
        help_text="Devocional = acesso por permissão; Discipulado = envolve líder/discípulo.",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.RASCUNHO,
        verbose_name="Status",
    )
    acesso = models.CharField(
        max_length=30,
        choices=AcessoChoices.choices,
        default=AcessoChoices.PUBLICO,
        verbose_name="Acesso",
    )
    grupos = models.ManyToManyField(
        "auth.Group",
        blank=True,
        verbose_name="Grupos com acesso",
        related_name="trilhas_acessiveis",
        help_text=(
            "Ativo somente quando Acesso = \"Permissão específica\". "
            "O usuário precisa pertencer a pelo menos um dos grupos listados. "
            "Lembre-se de adicionar o grupo ao usuário no seu cadastro."
        ),
    )
    ordem = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="Ordem",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Trilha"
        verbose_name_plural = "Trilhas"
        ordering = ["ordem", "titulo"]
        permissions = [
            ("ver_trilha_restrita", "Pode ver trilhas com permissão específica"),
        ]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo)
            slug = base
            n = 2
            while Trilha.all_objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# Modulo
# ─────────────────────────────────────────────────────────────────────────────

class Modulo(BaseModel):
    """
    Unidade de estudo dentro de uma Trilha.
    A imagem de capa fica aqui (não nos Temas individuais).
    Cada seção de conteúdo pode ser ativada/desativada individualmente.
    """

    trilha = models.ForeignKey(
        "Trilha",
        on_delete=models.CASCADE,
        related_name="modulos",
        verbose_name="Trilha",
    )
    titulo = models.CharField(
        max_length=200,
        verbose_name="Título",
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        verbose_name="Slug",
    )
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição",
    )
    # Imagem fica apenas no Módulo — não nos temas individuais
    # Convenção: 800×450 px (16:9) — redimensionada automaticamente ao salvar.
    imagem_capa = models.ImageField(
        upload_to="estudo/modulos/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="Imagem de Capa",
        validators=[validar_formato_imagem],
        help_text="Formatos aceitos: JPEG (.jpg, .jpeg) e PNG (.png). "
                  "A imagem será redimensionada para 800×450 px (16:9) automaticamente.",
    )
    ordem = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="Ordem",
    )
    acesso = models.CharField(
        max_length=30,
        choices=[
            (Trilha.AcessoChoices.PUBLICO, "Público"),
            (Trilha.AcessoChoices.LOGIN_OBRIGATORIO, "Login obrigatório"),
        ],
        default=Trilha.AcessoChoices.PUBLICO,
        verbose_name="Acesso",
        help_text="Controle fino de acesso; permissão por grupo é definida na Trilha.",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"
        ordering = ["trilha", "ordem"]
        unique_together = [("trilha", "ordem")]
        indexes = [models.Index(fields=["trilha", "ordem"])]

    def __str__(self):
        return f"{self.trilha} — {self.titulo}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo)
            slug = base
            n = 2
            while Modulo.all_objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug

        # Rastreia se a imagem foi alterada
        _imagem_anterior = None
        if self.pk:
            try:
                anterior = Modulo.objects.get(pk=self.pk)
                _imagem_anterior = anterior.imagem_capa.name if anterior.imagem_capa else None
            except Modulo.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        imagem_atual = self.imagem_capa.name if self.imagem_capa else None
        if imagem_atual and imagem_atual != _imagem_anterior:
            self._redimensionar_capa()

    def _redimensionar_capa(self):
        """
        Redimensiona a imagem de capa para 800×450 px (proporção 16:9),
        cortando o excesso centralmente (equivalente a object-fit: cover).
        """
        from PIL import Image, ImageOps

        caminho = self.imagem_capa.path
        ext = os.path.splitext(caminho)[1].lower()
        fmt = "PNG" if ext == ".png" else "JPEG"

        with Image.open(caminho) as img:
            if fmt == "JPEG" and img.mode != "RGB":
                img = img.convert("RGB")
            img_final = ImageOps.fit(img, (800, 450), Image.LANCZOS)
            save_kwargs = {"optimize": True}
            if fmt == "JPEG":
                save_kwargs["quality"] = 85
            img_final.save(caminho, format=fmt, **save_kwargs)

    def esta_desbloqueado(self, usuario) -> bool:
        """O primeiro módulo da trilha é sempre desbloqueado.
        Os demais exigem que o módulo anterior esteja 100% concluído."""
        primeiro = (
            Modulo.objects.filter(trilha=self.trilha)
            .order_by("ordem")
            .values("id")
            .first()
        )
        if primeiro and primeiro["id"] == self.id:
            return True
        modulo_anterior = (
            Modulo.objects.filter(trilha=self.trilha, ordem__lt=self.ordem)
            .order_by("-ordem")
            .first()
        )
        if modulo_anterior is None:
            return True
        return modulo_anterior.percentual_conclusao(usuario) == 100

    def percentual_conclusao(self, usuario) -> int:
        """Percentual de temas concluídos pelo usuário neste módulo."""
        total = self.temas.count()
        if total == 0:
            return 0
        concluidos = ProgressoTema.objects.filter(
            usuario=usuario,
            tema__modulo=self,
            tema__is_active=True,
        ).count()
        return int((concluidos / total) * 100)


# ─────────────────────────────────────────────────────────────────────────────
# Tema
# ─────────────────────────────────────────────────────────────────────────────

class Tema(BaseModel):
    """
    Lição/tópico dentro de um Módulo.
    Cada seção de conteúdo pode ser ativada individualmente via campo booleano.
    """

    modulo = models.ForeignKey(
        "Modulo",
        on_delete=models.CASCADE,
        related_name="temas",
        verbose_name="Módulo",
    )
    titulo = models.CharField(
        max_length=200,
        verbose_name="Título",
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        verbose_name="Slug",
    )
    ordem = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="Ordem",
    )
    duracao_estimada = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Duração estimada (min)",
    )
    acesso = models.CharField(
        max_length=30,
        choices=[
            (Trilha.AcessoChoices.PUBLICO, "Público"),
            (Trilha.AcessoChoices.LOGIN_OBRIGATORIO, "Login obrigatório"),
        ],
        default=Trilha.AcessoChoices.PUBLICO,
        verbose_name="Acesso",
        help_text="Controle fino de acesso; permissão por grupo é definida na Trilha.",
    )

    # ── Conteúdo principal (sempre presente) ─────────────────────────────────
    texto_base = models.TextField(
        verbose_name="Texto Base",
    )

    # ── Oração ────────────────────────────────────────────────────────────────
    tem_oracao = models.BooleanField(
        default=False,
        verbose_name="Tem Oração?",
    )
    oracao = models.TextField(
        blank=True,
        verbose_name="Oração",
    )

    # ── Referências cruzadas ──────────────────────────────────────────────────
    tem_referencias = models.BooleanField(
        default=False,
        verbose_name="Tem Referências Cruzadas?",
    )
    referencias_cruzadas = models.TextField(
        blank=True,
        verbose_name="Referências Cruzadas",
    )

    # ── Estudo aprofundado ────────────────────────────────────────────────────
    tem_estudo = models.BooleanField(
        default=False,
        verbose_name="Tem Estudo Aprofundado?",
    )
    estudo = models.TextField(
        blank=True,
        verbose_name="Estudo Aprofundado",
    )

    # ── Exemplo prático ───────────────────────────────────────────────────────
    tem_exemplo = models.BooleanField(
        default=False,
        verbose_name="Tem Exemplo Prático?",
    )
    exemplo_pratico = models.TextField(
        blank=True,
        verbose_name="Exemplo Prático",
    )

    # ── Conclusão ─────────────────────────────────────────────────────────────
    tem_conclusao = models.BooleanField(
        default=True,
        verbose_name="Tem Conclusão?",
    )
    conclusao = models.TextField(
        blank=True,
        verbose_name="Conclusão",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Tema"
        verbose_name_plural = "Temas"
        ordering = ["modulo", "ordem"]
        unique_together = [("modulo", "ordem")]
        indexes = [models.Index(fields=["modulo", "ordem"])]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo)
            slug = base
            n = 2
            while Tema.all_objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# ProgressoTema
# ─────────────────────────────────────────────────────────────────────────────

class ProgressoTema(TimeStampedModel):
    """Registra a conclusão de um Tema por um usuário."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progressos_estudo",
        verbose_name="Usuário",
    )
    tema = models.ForeignKey(
        "Tema",
        on_delete=models.CASCADE,
        related_name="progressos",
        verbose_name="Tema",
    )
    data_conclusao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Conclusão",
    )

    class Meta:
        verbose_name = "Progresso de Tema"
        verbose_name_plural = "Progressos de Temas"
        unique_together = [("usuario", "tema")]
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["usuario", "tema"]),
            models.Index(fields=["usuario"]),
        ]

    def __str__(self):
        return f"{self.usuario} → {self.tema}"
