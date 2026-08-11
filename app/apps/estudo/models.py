"""
Models do app Estudo (unificação de Devocional e Discipulado).

Hierarquia:
    Trilha(BaseModel)                      ← agrupa módulos; define tipo, acesso e status
    Modulo(BaseModel)                      ← unidade de estudo dentro de uma Trilha; tem imagem
    Tema(BaseModel)                        ← lição/tópico dentro de um Módulo; tem seções ativáveis
    ProgressoTema(TimeStampedModel)        ← conclusão de um Tema por usuário
"""

from django.conf import settings
from django.db import models
from django.templatetags.static import static
from django.utils.text import slugify

from apps.core.models import BaseModel, TimeStampedModel


# ─────────────────────────────────────────────────────────────────────────────
# Trilha
# ─────────────────────────────────────────────────────────────────────────────

class Trilha(BaseModel):
    """
    Agrupa módulos de estudo. Pode representar uma trilha de discipulado
    (com líder/discípulo) ou uma coleção devocional (acesso livre).
    """

    class TipoChoices(models.TextChoices):
        DEVOCIONAL    = "DEVOCIONAL",    "Devocional"
        DISCIPULADO   = "DISCIPULADO",   "Discipulado"
        
    class StatusChoices(models.TextChoices):
        RASCUNHO  = "RASCUNHO",  "Rascunho"
        PUBLICADO = "PUBLICADO", "Publicado"
        ARQUIVADO = "ARQUIVADO", "Arquivado"

    class AcessoChoices(models.TextChoices):
        PUBLICO              = "PUBLICO",              "Público"
        LOGIN_OBRIGATORIO    = "LOGIN_OBRIGATORIO",    "Login obrigatório"
        PERMISSAO_ESPECIFICA = "PERMISSAO_ESPECIFICA", "Permissão específica"
        SOMENTE_PROPRIETARIO = "SOMENTE_PROPRIETARIO", "Somente proprietário"

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

    professores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        verbose_name="Professores",
        related_name="trilhas_como_professor",
        limit_choices_to={"is_staff": True},
        help_text="Usuários staff que podem marcar presença dos alunos nesta trilha.",
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

    class ImagemCapaChoices(models.TextChoices):
        DEVOCIONAL     = "devocional.jpg",    "Devocional"
        DISCIPULADO    = "discipulado.jpg",   "Discipulado"

    # Escolha de imagem pré-definida em static/images/ — sem upload, sem media.
    imagem_capa = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default="",
        choices=ImagemCapaChoices.choices,
        verbose_name="Imagem de Capa",
        help_text="Escolha a imagem que representa o tipo de conteúdo deste módulo.",
    )

    @property
    def imagem_capa_url(self) -> str:
        """Retorna a URL estática da imagem selecionada, ou string vazia."""
        if not self.imagem_capa:
            return ""
        return static(f"images/{self.imagem_capa}")

    ordem = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="Ordem",
    )
    acesso = models.CharField(
        max_length=30,
        choices=Trilha.AcessoChoices.choices,
        default=Trilha.AcessoChoices.PUBLICO,
        verbose_name="Acesso",
        help_text="Controle fino de acesso. SOMENTE_PROPRIETARIO = apenas o criador vê este módulo.",
    )
    professores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        verbose_name="Professores",
        related_name="modulos_como_professor",
        limit_choices_to={"is_staff": True},
        help_text="Usuários staff que podem marcar presença dos alunos neste módulo.",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"
        ordering = ["trilha", "ordem"]
        unique_together = [("trilha", "ordem")]
        indexes = [models.Index(fields=["trilha", "ordem"])]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo)
            slug = base
            n = 2
            while Modulo.all_objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

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
        choices=Trilha.AcessoChoices.choices,
        default=Trilha.AcessoChoices.PUBLICO,
        verbose_name="Acesso",
        help_text="Controle fino de acesso; permissão por grupo é definida na Trilha.",
    )
    professores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        verbose_name="Professores",
        related_name="temas_como_professor",
        limit_choices_to={"is_staff": True},
        help_text="Usuários staff que podem marcar presença dos alunos neste tema.",
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

    # ── Estudo   ────────────────────────────────────────────────────
    tem_estudo = models.BooleanField(
        default=False,
        verbose_name="Tem Estudo  ?",
    )
    estudo = models.TextField(
        blank=True,
        verbose_name="Estudo  ",
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
    marcado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="progressos_marcados_como_professor",
        verbose_name="Marcado por (Professor)",
        help_text="Professor que registrou esta conclusão. Null = registrado pelo próprio aluno.",
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
