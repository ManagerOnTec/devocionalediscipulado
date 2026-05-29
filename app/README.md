# Devocional e Discipulado

> Plataforma de conteúdo devocional e trilhas de discipulado cristão.

![CI](https://github.com/SEU_USUARIO/devocionalediscipulado/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.x-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## Sobre

Sistema web para disponibilizar conteúdo devocional e trilhas de discipulado. Permite acesso público ou restrito a devocionais e progressão em trilhas de estudo com desbloqueio sequencial por módulo.

## Tecnologias

- Python 3.12 + Django 5.x
- PostgreSQL 16
- Bootstrap 5.3.3 + Bootstrap Icons 1.11.3
- django-unfold (admin moderno)
- django-simple-history (auditoria completa)
- Gunicorn + WhiteNoise (produção)
- Docker + Docker Compose
- GitHub Actions + Google Cloud Run (CI/CD)

## Pré-requisitos

- Docker e Docker Compose (recomendado)
- Python 3.12+ e PostgreSQL 16 (alternativa sem Docker)

## Instalação com Docker (recomendado)

```bash
git clone <REPO_URL>
cd devocionalediscipulado/app
cp .env.example .env
# Edite .env com suas credenciais
docker compose up --build
# Acesse http://localhost:8000
```

## Instalação Local (sem Docker)

```bash
cd devocionalediscipulado/app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env
# Edite .env com suas credenciais
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta Django — gere com `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `True` em dev, `False` em prod |
| `ALLOWED_HOSTS` | Hosts permitidos separados por vírgula (ex: `localhost,127.0.0.1`) |
| `DB_NAME` | Nome do banco PostgreSQL (padrão: `devocionalediscipulado`) |
| `DB_USER` / `DB_PASSWORD` | Credenciais do PostgreSQL |
| `DB_HOST` / `DB_PORT` | Host e porta do banco (padrão: `db` / `5432`) |
| `EMAIL_HOST` | Servidor SMTP (ex: `smtp.gmail.com`) |
| `EMAIL_PORT` | Porta SMTP (ex: `587`) |
| `EMAIL_HOST_USER` | Endereço de e-mail remetente |
| `EMAIL_HOST_PASSWORD` | Senha de app para autenticação SMTP |
| `DEFAULT_FROM_EMAIL` | E-mail padrão de envio (ex: `noreply@devocional.com.br`) |
| `SENTRY_DSN` | DSN do Sentry para monitoramento de erros em produção |
| `SECURE_SSL_REDIRECT` | Redirecionar HTTP → HTTPS (`False` em dev) |
| `PORT` | Porta do Gunicorn (padrão: `8080`) |
| `GUNICORN_WORKERS` | Número de workers do Gunicorn (padrão: `2`) |
| `GUNICORN_THREADS` | Número de threads por worker (padrão: `4`) |
| `DOCKERHUB_IMAGE` | Imagem DockerHub para build/push (ex: `usuario/devocionalediscipulado`) |
| `CLOUD_RUN_SERVICE` | Nome do serviço no Google Cloud Run |
| `CLOUD_RUN_REGION` | Região do Cloud Run (padrão: `southamerica-east1`) |

## Estrutura do Projeto

```
app/
├── apps/
│   ├── core/          # BaseModel, soft delete, mixins base
│   ├── accounts/      # Autenticação por email, perfil, dark mode
│   ├── devocional/    # Devocionais com acesso híbrido e progresso
│   └── discipulado/   # Trilhas com desbloqueio progressivo e liderança
├── config/            # Settings, URLs, WSGI/ASGI
├── templates/         # Templates HTML (base + por app)
├── static/            # CSS e JS estáticos
├── tests/             # Suite de testes (pytest + factory-boy)
├── requirements/      # base.txt, dev.txt, prod.txt
├── docker/            # Configuração Nginx para produção
├── scripts/           # entrypoint.sh do container
└── docs/              # Documentação técnica
```

## Apps

### core
Modelos abstratos `BaseModel` (soft delete, auditoria, histórico via `django-simple-history`) e `TimeStampedModel`. Base para todos os apps de domínio.

### accounts
Autenticação por e-mail (sem username), perfil com foto, timezone, dark mode nativo (Bootstrap 5) e suporte a líderes de discipulado.

### devocional
Temas devocionais com controle de acesso híbrido (público, login obrigatório, permissão específica). Progresso por usuário. Seções configuráveis por tema (subtítulos, referências, exemplo prático, conclusão, oração).

### discipulado
Trilhas > Módulos > Temas (lições). Desbloqueio progressivo por módulo. Acompanhamento de líderes sobre progresso de discípulos vinculados.

## Comandos Úteis (Makefile)

| Comando | Descrição |
|---|---|
| `make help` | Exibe todos os comandos disponíveis |
| `make build` | Constrói (ou reconstrói) as imagens Docker |
| `make up` | Inicia os containers em segundo plano |
| `make down` | Para e remove os containers (mantém volumes) |
| `make restart` | Reinicia todos os containers |
| `make logs` | Exibe logs em tempo real |
| `make shell` | Abre o shell Python do Django |
| `make bash` | Abre bash dentro do container web |
| `make migrate` | Aplica todas as migrações pendentes |
| `make makemigrations` | Cria novas migrações a partir dos models |
| `make collectstatic` | Coleta e comprime arquivos estáticos |
| `make createsuperuser` | Cria superusuário do Django Admin |
| `make psql` | Acessa o banco de dados via psql |
| `make test` | Executa a suite completa de testes |
| `make test-coverage` | Executa testes com relatório de cobertura HTML |
| `make lint` | Verifica estilo de código com flake8 |
| `make format` | Formata código com black e isort |
| `make push-docker` | Build e push da imagem para DockerHub |
| `make deploy-cloudrun` | Deploy da imagem no Google Cloud Run |

## Testes

```bash
# Via Makefile (dentro do Docker)
make test
make test-coverage

# Localmente
pytest
pytest --cov=apps --cov-report=html
```

## Deploy

Ver [docs/README_IMPLANTACAO.md](docs/README_IMPLANTACAO.md).

## Licença

MIT
