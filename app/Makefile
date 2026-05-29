# ─────────────────────────────────────────────────────────────────────────────
# Makefile — Atalhos para operações comuns do projeto
#
# Uso: make <comando>
# Exemplos:
#   make up          → sobe os containers
#   make migrate     → aplica migrações
#   make test        → executa os testes
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help build up down restart logs shell bash \
        migrate makemigrations collectstatic \
        test lint format \
        createsuperuser psql \
        docker-build-prod docker-push \
        push-docker deploy-cloudrun

# Comando base do Docker Compose
DC = docker compose

# ── Ajuda ─────────────────────────────────────────────────────────────────────

help: ## Exibe esta mensagem de ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── Docker ────────────────────────────────────────────────────────────────────

build: ## Constrói (ou reconstrói) as imagens Docker
	$(DC) build

up: ## Inicia os containers em segundo plano
	$(DC) up -d

down: ## Para e remove os containers (mantém volumes)
	$(DC) down

restart: ## Reinicia todos os containers
	$(DC) restart

logs: ## Exibe logs em tempo real (Ctrl+C para sair)
	$(DC) logs -f

ps: ## Lista o status dos containers
	$(DC) ps

# ── Django ────────────────────────────────────────────────────────────────────

shell: ## Abre o shell Python do Django (manage.py shell)
	$(DC) exec web python manage.py shell

bash: ## Abre um bash dentro do container web
	$(DC) exec web bash

migrate: ## Aplica todas as migrações pendentes
	$(DC) exec web python manage.py migrate --noinput

makemigrations: ## Cria novas migrações a partir das alterações nos models
	$(DC) exec web python manage.py makemigrations

collectstatic: ## Coleta e comprime os arquivos estáticos
	$(DC) exec web python manage.py collectstatic --noinput --clear

createsuperuser: ## Cria um superusuário do Django Admin
	$(DC) exec web python manage.py createsuperuser

# ── Banco de dados ────────────────────────────────────────────────────────────

psql: ## Acessa o banco de dados via psql
	$(DC) exec db psql -U postgres -d devocionalediscipulado

# ── Qualidade de código ───────────────────────────────────────────────────────

test: ## Executa a suite completa de testes com pytest
	$(DC) exec web pytest -v --tb=short

test-coverage: ## Executa testes com relatório de cobertura
	$(DC) exec web pytest --cov=apps --cov-report=html --cov-report=term-missing

lint: ## Verifica estilo de código com flake8
	$(DC) exec web flake8 apps/ config/

format: ## Formata o código com black e isort
	$(DC) exec web black apps/ config/
	$(DC) exec web isort apps/ config/

# ── CI/CD — DockerHub + Cloud Run ────────────────────────────────────────────

# Configurar antes de usar:
#   export DOCKER_IMAGE=seu-usuario/devocionalediscipulado
#   export CLOUDRUN_SERVICE=devocionalediscipulado
#   export GCP_REGION=southamerica-east1
#   export GCP_PROJECT=seu-projeto-gcp

docker-build-prod: ## Build da imagem de produção (stage runtime, sem ferramentas de dev)
	docker build --target runtime -t $(DOCKER_IMAGE):latest .

docker-push: ## Tag e push da imagem já construída para o DockerHub
	docker tag $(DOCKER_IMAGE):latest $(DOCKER_IMAGE):$(shell git rev-parse --short HEAD)
	docker push $(DOCKER_IMAGE):latest
	docker push $(DOCKER_IMAGE):$(shell git rev-parse --short HEAD)

push-docker: ## Build e push da imagem de produção para o DockerHub
	docker build --target runtime -t $(DOCKER_IMAGE):latest -t $(DOCKER_IMAGE):$(shell git rev-parse --short HEAD) .
	docker push $(DOCKER_IMAGE):latest
	docker push $(DOCKER_IMAGE):$(shell git rev-parse --short HEAD)

deploy-cloudrun: ## Deploy da imagem mais recente no Cloud Run
	gcloud run deploy $(CLOUDRUN_SERVICE) \
		--image $(DOCKER_IMAGE):latest \
		--region $(GCP_REGION) \
		--project $(GCP_PROJECT) \
		--platform managed \
		--allow-unauthenticated \
		--set-env-vars DJANGO_SETTINGS_MODULE=config.settings.prod
