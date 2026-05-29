ETAPA 1 — BASE PROJETO
PARA: Developer Agent
Crie a estrutura inicial completa do projeto Django com:

- Django
- PostgreSQL
- Docker Compose
- Cloud Run
- DockerHub
- requirements/base.txt
- requirements/dev.txt
- requirements/prod.txt
- settings/base.py
- settings/dev.py
- settings/prod.py
- .env
- .env.example
- .gitignore
- .dockerignore
- Makefile
- collectstatic automático
- whitenoise
- gunicorn
- timezone São Paulo
- idioma pt-br
- pasta apps
- pasta templates
- pasta static
- pasta media
- comentários no código
- usando decouple
- docker otimizado

Seguir instruções:
.github/instructions/
docs/



ETAPA 2 — BASEMODEL
PARA: Developer Agent
Crie BaseModel abstrato com:

- created_at
- updated_at
- created_by
- updated_by
- is_active
- soft delete
- auditoria
- comentários código
- compatível admin
- timezone São Paulo

Seguir:
global.instructions.md
backend.instructions.md

ETAPA 3 — USER CUSTOMIZADO
PARA: Developer Agent
Crie User customizado com:

- email login
- nome completo
- foto opcional
- telefone
- timezone
- dark_mode
- ativo
- auditoria

Criar:
- model
- manager
- admin
- forms
- migrations

ETAPA 4 — AUTENTICAÇÃO
PARA: Developer Agent
Crie autenticação completa com:

- login
- logout
- cadastro
- recuperação senha
- alteração senha
- mensagens Django
- responsividade
- dark/light mode
- templates
- CBVs
- forms


ETAPA 5 — TEMPLATE BASE
PARA: UIUX Agent
Crie estrutura frontend base com:

- base.html
- navbar
- sidebar
- dark mode
- light mode
- responsividade
- mobile first
- componentes reutilizáveis
- mensagens Django estilizadas
- loading
- acessibilidade


ETAPA 6 — ADMIN BASE
PARA: Developer Agent
Configure admin avançado usando:

- django-unfold
- django-simple-history
- filtros ocultáveis e reezibidos por click
- paginação
- busca
- auditoria
- indicadores
- dashboards
- dark mode

ETAPA 7 — DOCKER
PARA: DevOps Agent
Crie:

- Dockerfile
- docker-compose.yml
- entrypoint.sh
- collectstatic automático
- PostgreSQL dockerizado
- volumes persistentes
- configuração Cloud Run
- configuração DockerHub
- otimização build


ETAPA 8 — APP DEVOCIONAL
PARA: Planner Agent
Planeje arquitetura completa app devocional com:

- models
- permissões híbridas
- progresso usuário
- tema público/privado
- subtítulos opcionais
- ativação tema dia
- estrutura URLs
- admin
- UX leitura


ETAPA 9 — MODEL DEVOCIONAL
PARA: Developer Agent
Crie models app devocional:

- Tema
- SubtituloTema
- ProgressoUsuario

Com:
- auditoria
- permissões híbridas
- ordem
- slug
- status
- imagem opcional
- progresso usuário

ETAPA 10 — ADMIN DEVOCIONAL
PARA: Developer Agent
Crie admin completo app devocional com:

- filtros ocultáveis e reexibidos por click
- ações massa
- ativar/desativar temas
- indicadores
- progresso usuários
- ordenação
- busca
- relatórios exportados por pdf ou xls nas acoes do admin


ETAPA 11 — FORMS DEVOCIONAL
PARA: Developer Agent
Crie forms app devocional com:

- validações
- mensagens amigáveis
- sanitização
- ModelForms

ETAPA 12 — VIEWS DEVOCIONAL
PARA: Developer Agent
Crie CBVs app devocional:

- listagem
- detalhe
- concluir tema
- progresso usuário
- controle acesso híbrido
- context_data
- messages Django


ETAPA 13 — TEMPLATES DEVOCIONAL
PARA: UIUX Agent
Crie templates app devocional com:

- leitura confortável
- dark/light mode
- responsivo
- mobile first
- cards
- progresso
- conclusão tema
- acessibilidade


ETAPA 14 — APP DISCIPULADO
PARA: Planner Agent
Planeje arquitetura app discipulado com:

- trilhas
- módulos
- progresso
- desbloqueio progressivo
- acompanhamento liderança
- gamificação futura
- certificados futuros
- quizzes futuros


ETAPA 15 — MODELS DISCIPULADO
PARA: Developer Agent
Crie models app discipulado:

- Trilha
- Modulo
- Tema
- Progresso
- PermissaoModulo

Com:
- auditoria
- progressão
- desbloqueio
- ordem
- slug


ETAPA 16 — ADMIN DISCIPULADO
PARA: Developer Agent
Crie admin app discipulado com:

- progresso alunos
- filtros
- indicadores
- dashboards
- ações massa
- acompanhamento liderança


ETAPA 17 — VIEWS DISCIPULADO
PARA: Developer Agent
Crie CBVs app discipulado:

- trilhas
- módulos
- progresso
- desbloqueio
- permissões
- acompanhamento


ETAPA 18 — TEMPLATES DISCIPULADO
PARA: UIUX Agent
Crie templates app discipulado com:

- trilhas visuais
- progresso
- responsividade
- dark/light
- UX moderna
- gamificação preparada


ETAPA 19 — SEGURANÇA
PARA: Security Agent
Audite todo projeto verificando:

- permissões
- variáveis ambiente
- uploads
- autenticação
- CSRF
- exposição dados
- DEBUG produção
- secrets


ETAPA 20 — TESTES
PARA: Reviewer Agent
Crie testes completos para:

- models
- forms
- views
- permissões
- autenticação
- progresso usuário


ETAPA 21 — CI/CD
PARA: DevOps Agent
Crie pipeline CI/CD com:

- GitHub Actions
- build Docker
- push DockerHub
- deploy Cloud Run
- variáveis ambiente
- validação testes


ETAPA 22 — DOCUMENTAÇÃO
PARA: Documentation Agent
Atualize documentação completa:

- README
- instalação
- deploy
- arquitetura
- apps
- fluxos
- troubleshooting

FLUXO DIÁRIO
SEMPRE
Primeiro
Planner Agent
Depois
Developer Agent
Depois
Reviewer Agent
Depois
Security Agent
Depois
DevOps Agent
REGRA MAIS IMPORTANTE
SEMPRE pedir:
- model
- form
- admin
- views
- urls
- templates
- testes

Na mesma tarefa.

REGRA MAIS IMPORTANTE 2
SEMPRE incluir:
Seguir:
.github/instructions/
docs/
apps/modulo/
