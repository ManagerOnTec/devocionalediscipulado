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
        ESTUDO_PESSOAL = "estudopessoal.jpg", "Estudo Pessoal"

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


# ─────────────────────────────────────────────────────────────────────────────
# Topico — agrupa EstudoPessoal (como Trilha agrupa Módulos)
# ─────────────────────────────────────────────────────────────────────────────

class Topico(models.Model):
    """Pasta/categoria que organiza Estudos Pessoais. A permissão do Tópico se aplica a todos os estudos dentro dele."""

    class PermissaoChoices(models.TextChoices):
        SOMENTE_SUPERADMIN = "SOMENTE_SUPERADMIN", "Somente Superadmin"
        LOGIN_OBRIGATORIO  = "LOGIN_OBRIGATORIO",  "Login obrigatório"
        PUBLICO            = "PUBLICO",            "Público"

    class ImagemChoices(models.TextChoices):
        ESTUDO_PESSOAL = "estudopessoal.jpg", "Estudo Pessoal"
        DEVOCIONAL     = "devocional.jpg",    "Devocional"
        DISCIPULADO    = "discipulado.jpg",   "Discipulado"

    titulo = models.CharField(
        max_length=200,
        verbose_name="Título",
        help_text="Ex.: 'Evangelhos', 'Cartas de Paulo', 'Sermões sobre Fé'.",
    )
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição",
    )
    imagem_capa = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default="estudopessoal.jpg",
        choices=ImagemChoices.choices,
        verbose_name="Imagem de Capa",
        help_text="Imagem exibida nos cards (escolha da lista de imagens estáticas).",
    )
    permissao = models.CharField(
        max_length=30,
        choices=PermissaoChoices.choices,
        default=PermissaoChoices.SOMENTE_SUPERADMIN,
        verbose_name="Permissão de Acesso",
        help_text="Define quem pode visualizar todos os estudos deste tópico. Aplica-se a todos os EstudoPessoal dentro dele.",
    )
    ordem = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="Ordem",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Tópico"
        verbose_name_plural = "Tópicos de Estudos Pessoais"
        ordering = ["ordem", "titulo"]

    def __str__(self):
        return self.titulo

    @property
    def imagem_capa_url(self) -> str:
        """Retorna a URL estática da imagem selecionada, ou string vazia."""
        if not self.imagem_capa:
            return ""
        return static(f"images/{self.imagem_capa}")


# ─────────────────────────────────────────────────────────────────────────────
# EstudoPessoal  (visível apenas para superadmin)
# ─────────────────────────────────────────────────────────────────────────────

class EstudoPessoal(models.Model):
    """
    Ferramenta de estudo bíblico   — uso exclusivo do superadmin.
    Estrutura metodológica completa: texto, contexto, hermenêutica,
    teologia e desenvolvimento homilético.
    """

    # ── Identificação ────────────────────────────────────────────────────────
    topico = models.ForeignKey(
        "Topico",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estudos",
        verbose_name="Tópico",
        help_text="Tópico ao qual este estudo pertence. A permissão do tópico se aplica a este estudo.",
    )
    titulo = models.CharField(
        max_length=300,
        blank=True, null=True,
        verbose_name="Título do Estudo",
        help_text="Ex.: 'Estudo de João 3:16 — O Amor de Deus'.",
    )
    referencia = models.CharField(
        max_length=100,
        blank=True, null=True,
        verbose_name="Referência Bíblica",
        help_text="Ex.: João 3:16 · Romanos 8:1-11 · Salmo 23.",
    )

    # ── Texto e contexto ─────────────────────────────────────────────────────
    texto_biblico = models.TextField(
        blank=True, null=True,
        verbose_name="Texto Bíblico",
        help_text="Cole aqui o(s) versículo(s) que serão estudados.",
    )

    # incluir no admin a sessao de contexto imediato / para contexto anterior e posterior
    contexto_anterior = models.TextField(
        blank=True, null=True,
        verbose_name="Contexto Anterior",
        help_text="Contexto Imediato e anterior ao versículo citado.",
    )
    contexto_posterior = models.TextField(
        blank=True, null=True,
        verbose_name="Contexto Posterior",
        help_text="Contexto Imediato e posterior ao versículo citado.",
    )

    contexto_geral_escrituras = models.TextField(
        blank=True, null=True,
        verbose_name="Contexto Geral das Escrituras",
        help_text="Como este texto se encaixa no contexto geral da Bíblia? Ex.: Capítulo inteiro, livro, etc.",
    )


    versiculos_relacionados = models.TextField(
        blank=True, null=True,
        verbose_name="Versículos Relacionados",
        help_text="Concordância bíblica: liste referências que tratam do mesmo tema ou palavra-chave.",
    )



    # ── Palavras-chave ────────────────────────────────────────────────────────
    palavra_central = models.CharField(
        max_length=200,
        blank=True, null=True,
        verbose_name="Palavra Central",
        help_text="A palavra mais importante do texto; eixo do estudo.",
    )

    # ── Traduções ─────────────────────────────────────────────────────────────
    traducoes = models.TextField(
        blank=True, null=True,
        verbose_name="Tradução / Hebraico / Grego / Latim / Inglês",
        help_text="Sentido do termo no hebraico original (para textos do AT). Use Strong's ou léxico BDB.",
    )
    observacoes_portugues = models.TextField(
        blank=True, null=True,
        verbose_name="Observações para o Português",
        help_text="Nuances da tradução para o português: diferenças entre ARC, ARA, NVI, NVT, etc.",
    )


    uso_antigo_novo_testamento = models.TextField(
        blank=True, null=True,
        verbose_name="Uso no Antigo e Novo Testamento",
        help_text="Como este texto/palavra/tema é tratado no AT e NT? Há prefigurações, tipos ou citações?",
    )

    # ── Teologia e contexto histórico ────────────────────────────────────────
    onde_esta_cristo = models.TextField(
        blank=True, null=True,
        verbose_name="Onde Está Cristo",
        help_text="Leitura cristológica do texto: como ele aponta para Cristo (AT) ou revela Cristo (NT)?",
    )


    # ── Perguntas hermenêuticas ──────────────────────────────────────────────
    quem_fala = models.CharField(
        max_length=300,
        blank=True, null=True,
        verbose_name="AUTOR/Quem está falando?",
        help_text="Identifique o locutor: Deus, um profeta, o apóstolo, um personagem da narrativa.",
    )
    personagens = models.TextField(
        blank=True, null=True,
        verbose_name="Personagens",
        help_text="Liste os personagens presentes no texto: protagonistas, antagonistas e figuras secundárias.",
    )
    para_quem = models.CharField(
        max_length=300,
        blank=True, null=True,
        verbose_name="Público Original/Para quem?",
        help_text="Identifique o(s) destinatário(s) original(is).",
    )
    sobre_o_que = models.TextField(
        blank=True, null=True,
        verbose_name="Sobre o quê?",
        help_text="Qual é o assunto central que o texto aborda?",
    )
    qual_objetivo = models.TextField(
        blank=True, null=True,
        verbose_name="Qual o objetivo?",
        help_text="O texto visa ensinar, corrigir, consolar, exortar, profetizar? Qual a finalidade?",
    )


    o_que_exige_de_mim = models.TextField(
        blank=True, null=True,
        verbose_name="O que exige de mim?",
        help_text="Qual a demanda prática, espiritual ou ética que este texto impõe ao leitor?",
    )

    # ── Controle de inclusão por grupo ───────────────────────────────────────
    incluir_hermeneutica = models.BooleanField(
        default=True,
        verbose_name="Incluir Hermenêutica",
        help_text="Marque para incluir toda a seção de Hermenêutica na exportação.",
    )
    incluir_exegese = models.BooleanField(
        default=True,
        verbose_name="Incluir Exegese",
        help_text="Marque para incluir toda a seção de Exegese na exportação.",
    )

    # ── Desenvolvimento — seções opcionais ───────────────────────────────────
    incluir_introducao = models.BooleanField(
        default=True,
        verbose_name="Incluir Introdução",
        help_text="Marque para incluir esta seção na exportação e no template.",
    )
    introducao = models.TextField(
        blank=True, null=True,
        verbose_name="Introdução",
        help_text="Contextualize o tema para o ouvinte/leitor: gancho, problema, relevância.",
    )

    incluir_explicacao = models.BooleanField(
        default=True,
        verbose_name="Incluir Explicação",
        help_text="Marque para incluir esta seção na exportação e no template.",
    )
    explicacao = models.TextField(
        blank=True, null=True,
        verbose_name="Explicação",
        help_text="O que o texto diz? Exegese e exposição versículo a versículo.",
    )

    incluir_aplicacao = models.BooleanField(
        default=True,
        verbose_name="Incluir Aplicação",
        help_text="Marque para incluir esta seção na exportação e no template.",
    )
    aplicacao = models.TextField(
        blank=True, null=True,
        verbose_name="Aplicação",
        help_text="Como este texto deve transformar a vida do ouvinte? Exemplos concretos.",
    )

    incluir_conclusao = models.BooleanField(
        default=True,
        verbose_name="Incluir Conclusão",
        help_text="Marque para incluir esta seção na exportação e no template.",
    )
    conclusao = models.TextField(
        blank=True, null=True,
        verbose_name="Conclusão",
        help_text="Fechamento do estudo: síntese, chamada à ação ou convite.",
    )

    incluir_oracao = models.BooleanField(
        default=True,
        verbose_name="Incluir Oração",
        help_text="Marque para incluir esta seção na exportação e no template.",
    )
    oracao = models.TextField(
        blank=True, null=True,
        verbose_name="Oração",
        help_text="Sugestão de oração para encerrar o estudo ou o culto.",
    )

    # ── Permissão de acesso ───────────────────────────────────────────────────

    class PermissaoChoices(models.TextChoices):
        SOMENTE_SUPERADMIN = "SOMENTE_SUPERADMIN", "Somente Superadmin"
        LOGIN_OBRIGATORIO  = "LOGIN_OBRIGATORIO",  "Login obrigatório"
        PUBLICO            = "PUBLICO",            "Público"

    permissao = models.CharField(
        max_length=30,
        choices=PermissaoChoices.choices,
        default=PermissaoChoices.SOMENTE_SUPERADMIN,
        verbose_name="Permissão de Acesso",
        help_text="Define quem pode visualizar este estudo nos templates.",
    )

    # ── Auditoria ─────────────────────────────────────────────────────────────
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")


    class Meta:
        verbose_name = "Estudo Pessoal"
        verbose_name_plural = "Estudos Pessoais"
        ordering = ["-criado_em"]
        permissions = [
            ("ver_estudopessoal", "Pode visualizar estudos pessoais"),
            ("ver_hermeneutica_estudopessoal", "Pode ver seção Hermenêutica"),
            ("ver_exegese_estudopessoal", "Pode ver seção Exegese"),
            ("ver_homiletica_estudopessoal", "Pode ver seção Homilética"),
            ("ver_topicos_estudopessoal", "Pode ver tópicos do estudo"),
            ("exportar_estudopessoal", "Pode exportar estudos pessoais"),
        ]

    def __str__(self):
        ref = self.referencia or "(sem referência)"
        titulo = self.titulo or "(sem título)"
        return f"{ref} — {titulo}"


class TopicoEstudo(models.Model):
    """
    Tópico/ponto de pregação dentro de um EstudoPessoal.
    Quantidade variável — adicionados via Inline no admin.
    """

    estudo = models.ForeignKey(
        EstudoPessoal,
        on_delete=models.CASCADE,
        related_name="topicos",
        verbose_name="Estudo",
    )
    incluir = models.BooleanField(
        default=True,
        verbose_name="Incluir",
        help_text="Desmarque para ocultar este tópico na exportação e no template.",
    )
    titulo = models.CharField(
        max_length=300,
        verbose_name="Título do Tópico",
        help_text="Ex.: 'A soberania de Deus na criação'.",
    )
    conteudo = models.TextField(
        blank=True,
        verbose_name="Conteúdo",
        help_text="Desenvolvimento do tópico: pontos de apoio, versículos, ilustrações.",
    )
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordem",
        help_text="Define a sequência de apresentação dos tópicos.",
    )

    class Meta:
        verbose_name = "Tópico"
        verbose_name_plural = "Tópicos"
        ordering = ["ordem"]

    def __str__(self):
        return f"[{self.ordem}] {self.titulo}"
