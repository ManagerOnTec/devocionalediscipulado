---
description: "Commit, push no git e build + push da imagem Docker para o DockerHub. Use para subir uma nova versão do projeto."
name: "Git + Docker — Subir versão"
argument-hint: "mensagem do commit (ex: feat: adiciona tela de perfil)"
agent: "devops"
tools: ["run_in_terminal"]
---

Execute o fluxo completo de entrega: commit no git e publicação da imagem Docker no DockerHub.

## Argumento recebido

Mensagem de commit: **$ARGUMENTS**

## Pré-requisitos a verificar antes de executar

1. `DOCKER_IMAGE` está exportada no ambiente (ex: `managerontec/devocionalediscipulado`).
2. O usuário está autenticado no DockerHub (`docker login`).
3. Não há migrações pendentes sem commit (`makemigrations --check`).

## Passos a executar (em ordem)

### 1 — Git: stage, commit e push

```bash
cd app
git add -A
git commit -m "$ARGUMENTS"
git push
```

### 2 — Docker: build de produção e push para o DockerHub

Use o target `runtime` do Dockerfile multi-stage e faça tag com `latest` + SHA curto do commit:

```bash
make push-docker
```

> Equivalente a:
> ```bash
> docker build --target runtime \
>   -t $DOCKER_IMAGE:latest \
>   -t $DOCKER_IMAGE:$(git rev-parse --short HEAD) .
> docker push $DOCKER_IMAGE:latest
> docker push $DOCKER_IMAGE:$(git rev-parse --short HEAD)
> ```

### 3 — Confirmação

Após cada etapa, exiba o resultado (exit code, SHA do commit, tags enviadas).  
Se qualquer etapa falhar, **pare imediatamente** e informe o erro antes de continuar.

## Saída esperada

- Commit criado e push confirmado no repositório remoto.
- Imagem `$DOCKER_IMAGE:latest` e `$DOCKER_IMAGE:<sha>` disponíveis no DockerHub.
