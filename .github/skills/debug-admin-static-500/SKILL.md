---
name: debug-admin-static-500
description: "Diagnose and fix Django admin 500 errors caused by static image files missing from the ManifestStaticFilesStorage (whitenoise/CompressedManifest) manifest. Use when: admin list/change view gives 500, static images work in regular templates, prod uses whitenoise or ManifestStaticFilesStorage, error is ValueError about missing staticfiles manifest entry, newly added static files not resolving in production."
argument-hint: "model name or admin page that gives 500"
---

# Debug: Admin 500 com imagens estáticas (ManifestStaticFilesStorage)

## Quando Usar

- Admin list ou change view retorna 500 após adicionar imagens estáticas
- Funcionou em dev mas quebra em prod
- Templates comuns com as mesmas imagens funcionam normalmente
- `list_display` ou `readonly_fields` chama propriedade que usa `static()`

## Contexto do Projeto

- **Storage base/prod**: `whitenoise.storage.CompressedManifestStaticFilesStorage` (definido em `base.py`)
- **Storage dev (após fix)**: `django.contrib.staticfiles.storage.StaticFilesStorage` (override em `dev.py`)
- **Padrão implementado**: `CharField` com `choices` → `@property imagem_capa_url` → `static('images/<nome>.jpg')`
- **Arquivo de manifesto**: `staticfiles.json` gerado por `collectstatic`

---

## Por Que o Admin Quebra Mas Templates Funcionam

**Admin `list_display`**: O método `imagem_preview` é uma callable Python. Quando Django admin renderiza a listagem, chama o método diretamente via `lookup_field` (`django/contrib/admin/utils.py`). Se a callable levanta uma exceção, ela propaga como 500.

**Templates HTML**: `{{ modulo.imagem_capa_url }}` passa pelo engine de templates do Django, que **silencia exceções** na resolução de variáveis e atributos — retorna string vazia em vez de propagar o erro.

```
# Traceback típico no admin
File "django/contrib/admin/utils.py", line X, in lookup_field
    ...
File "apps/estudo/admin.py", line X, in imagem_preview
    url = obj.imagem_capa_url
File "apps/estudo/models.py", line X, in imagem_capa_url
    return static(f"images/{self.imagem_capa}")
ValueError: Missing staticfiles manifest entry for 'images/devocional.jpg'
```

---

## Diagnóstico

### 1. Confirmar que o storage usa manifesto

```bash
grep -r "CompressedManifest\|ManifestStaticFiles" config/settings/
```

Se aparecer em `base.py`, afeta **dev e prod** — esse é o problema raiz.

### 2. Confirmar que o manifesto não existe

```bash
ls staticfiles/staticfiles.json 2>/dev/null || echo "manifesto ausente"
```

### 3. Verificar se os arquivos JPG estão no manifesto (se ele existir)

```bash
python -c "
import json
with open('staticfiles/staticfiles.json') as f:
    data = json.load(f)
imgs = [k for k in data.get('paths', {}) if 'images/' in k]
print(imgs)
"
```

### 4. Reproduzir o erro

```bash
docker compose exec web python manage.py shell -c "
from django.contrib.staticfiles.storage import staticfiles_storage
print(staticfiles_storage.url('images/devocional.jpg'))
"
```

---

## Causa Raiz Mais Comum: Imagem de Produção Desatualizada

`collectstatic` roda **durante o build da imagem Docker** (no `Dockerfile`, stage `runtime`). Se novos arquivos estáticos foram adicionados e comitados no git **mas a imagem não foi reconstruída e redeployada**, o container em execução não os tem — o manifesto `staticfiles.json` não contém as entradas → `static()` levanta `ValueError` → admin 500.

Confirmar verificando o histórico de commits vs. a data do último deploy:

```bash
git log --oneline -5 -- static/images/
# Se o commit é mais recente que o último deploy → imagem desatualizada
```

### Fix: Rebuild e Redeploy

```bash
cd app
export DOCKER_IMAGE=<usuario>/devocionalediscipulado
export CLOUDRUN_SERVICE=devocionalediscipulado
export GCP_REGION=southamerica-east1
export GCP_PROJECT=<projeto-gcp>

make push-docker       # rebuild com os novos arquivos
make deploy-cloudrun   # substitui o container em execução
```

O `Dockerfile` já roda `python manage.py collectstatic --noinput` no stage `runtime` — a nova imagem terá os arquivos e o manifesto correto.

---

## Causa Secundária: Dev com Manifesto Obrigatório

Se `base.py` usa `CompressedManifestStaticFilesStorage`, **dev também exige o manifesto**. Desenvolvedores raramente rodam `collectstatic` localmente → mesmo 500 em dev.

**Fix permanente em `dev.py`:**

```python
# Em dev, usa StaticFilesStorage simples — sem manifesto, sem collectstatic.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
```

Ou rodar uma vez localmente:

```bash
make collectstatic
```

---

## Verificação Pós-Fix

```bash
# 1. Reiniciar container com novo dev.py
docker compose restart web

# 2. Acessar /admin/estudo/modulo/ — deve retornar 200

# 3. Em prod: confirmar que collectstatic ainda roda no deploy
docker compose exec web python manage.py collectstatic --noinput --dry-run
```

---

## Checklist de Prevenção

- [ ] `dev.py` usa `StaticFilesStorage` (sem manifesto)
- [ ] `base.py` ou `prod.py` usa `CompressedManifestStaticFilesStorage`
- [ ] `collectstatic` está no `entrypoint.sh` ou `Dockerfile`
- [ ] Novos arquivos em `static/` são comitados (não ignorados no `.dockerignore`)
- [ ] Callables em `list_display` que chamam `static()` estão protegidas ou o storage não exige manifesto em dev

---

## Padrão no Projeto

```
static/images/devocional.jpg      ← ImagemCapaChoices.DEVOCIONAL
static/images/discipulado.jpg     ← ImagemCapaChoices.DISCIPULADO
static/images/estudopessoal.jpg   ← ImagemCapaChoices.ESTUDO_PESSOAL
```

Storage base/prod: `whitenoise.storage.CompressedManifestStaticFilesStorage` (`config/settings/base.py`)
Storage dev (fix): `django.contrib.staticfiles.storage.StaticFilesStorage` (`config/settings/dev.py`)

# COMANDOS

source app/.venv/bin/activate && echo "venv ativado: $VIRTUAL_ENV"
venv ativado: /home/resid/projetos_managerontec/devocionalediscipulado/app/.venv
