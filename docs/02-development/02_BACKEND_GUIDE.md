# BACKEND DEVELOPMENT GUIDE

**Documento:** `02_BACKEND_GUIDE.md`

**Versão:** 2.0.0

**Estado:** Guia Oficial de Desenvolvimento Backend

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento descreve o processo oficial de desenvolvimento backend do Bolayetu.

Todos os módulos deverão seguir este guia para garantir:

* consistência;
* qualidade;
* escalabilidade;
* baixo acoplamento;
* facilidade de manutenção.

---

# 2. Stack Oficial

## Linguagem

* Python 3.12+

## Framework

* Django 5+
* Django REST Framework

## Base de Dados

* PostgreSQL

## Cache

* Redis

## Processamento Assíncrono

* Celery
* Celery Beat

## Armazenamento

* Cloudflare R2

## Containerização

* Docker

---

# 3. Estrutura do Projeto

```text
backend/

apps/
common/
core/
config/
tests/

manage.py
requirements/
pyproject.toml
```

---

# 4. Estrutura de um Módulo

Cada domínio deverá possuir exatamente esta estrutura.

```text
players/

admin/

constants/

exceptions/

filters/

migrations/

models/

permissions/

schemas/

selectors/

serializers/

services/

signals/

tasks/

tests/

urls/

validators/

views/

apps.py
```

---

# 5. Ordem de Desenvolvimento

Sempre seguir esta sequência.

```text
Requirements

↓

Models

↓

Migrations

↓

Validators

↓

Selectors

↓

Services

↓

Permissions

↓

Serializers

↓

Views

↓

URLs

↓

Tests
```

Nunca começar pelas Views.

---

# 6. Models

Os Models representam apenas persistência.

Permitido:

* campos;
* relacionamentos;
* propriedades simples;
* métodos utilitários.

Proibido:

* regras complexas;
* envio de emails;
* chamadas HTTP;
* notificações.

---

# 7. BaseModel

Todos os Models deverão herdar de um modelo comum.

Exemplo:

```python
class BaseModel(UUIDModel, TimeStampedModel):
    ...
```

Campos recomendados:

* id (UUID)
* created_at
* updated_at
* created_by
* updated_by

Quando aplicável:

* deleted_at
* deleted_by

---

# 8. Services

Toda regra de negócio pertence aos Services.

Exemplo:

```python
PlayerService.create()

PlayerService.transfer()

PlayerService.retire()
```

Os Services deverão:

* ser pequenos;
* ser reutilizáveis;
* ser testáveis.

---

# 9. Selectors

Todos os Selectors são apenas leitura.

Exemplo:

```python
PlayerSelector.active()

PlayerSelector.by_club()

PlayerSelector.top_scorers()
```

Nunca alterar dados.

---

# 10. Serializers

Responsabilidades:

* validação;
* serialização;
* transformação.

Nunca executar regras de negócio.

Separar:

```text
CreateSerializer

UpdateSerializer

ReadSerializer

ListSerializer
```

---

# 11. Views

As Views apenas coordenam.

Fluxo:

```text
Request

↓

Serializer

↓

Permission

↓

Service

↓

Response
```

Máximo recomendado:

50 linhas por método.

---

# 12. Permissions

Toda autorização deverá ser implementada em classes específicas.

Exemplos:

```text
IsOrganizationAdmin

IsClubManager

IsPlayer

IsTenantMember
```

Nunca espalhar verificações de permissões pelo código.

---

# 13. Validators

Centralizar validações reutilizáveis.

Exemplos:

* idade mínima;
* regulamentos;
* número da camisola;
* limite de inscrições.

---

# 14. Tasks

Todo processamento pesado deverá utilizar Celery.

Exemplos:

* emails;
* thumbnails;
* PDFs;
* exportações;
* estatísticas.

Nunca bloquear a resposta HTTP.

---

# 15. Signals

Utilização restrita.

Permitido:

* auditoria;
* logging;
* sincronizações simples.

Evitar lógica crítica em Signals.

---

# 16. Tratamento de Exceções

Criar exceções específicas.

Exemplo:

```python
PlayerAlreadyRegistered

CompetitionClosed

TransferNotAllowed
```

Evitar exceções genéricas.

---

# 17. APIs

Todas as APIs deverão seguir REST.

Exemplo:

```text
GET     /api/v1/players

GET     /api/v1/players/{id}

POST    /api/v1/players

PATCH   /api/v1/players/{id}

DELETE  /api/v1/players/{id}
```

---

# 18. Respostas

Formato padrão:

```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {}
}
```

Erro:

```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {}
}
```

---

# 19. Paginação

Utilizar paginação padrão em todas as listagens.

Formato recomendado:

```json
{
  "count": 120,
  "next": "...",
  "previous": "...",
  "results": []
}
```

---

# 20. Filtros

Utilizar:

* django-filter;
* ordering;
* search.

Evitar filtros implementados manualmente.

---

# 21. Base de Dados

Boas práticas:

* `select_related()`;
* `prefetch_related()`;
* índices adequados;
* consultas eficientes.

Evitar consultas N+1.

---

# 22. Multi-Tenant

Todos os Services deverão considerar o Tenant ativo.

Nunca executar consultas sem contexto de Tenant.

O filtro deverá ser automático.

---

# 23. Logging

Registar apenas operações relevantes.

Exemplos:

* login;
* transferências;
* criação de competições;
* alterações de permissões.

Nunca registar dados sensíveis.

---

# 24. Testes

Cada módulo deverá possuir:

```text
tests/

test_models.py

test_services.py

test_selectors.py

test_permissions.py

test_api.py
```

Cobertura mínima recomendada:

80%.

---

# 25. Documentação

Todos os endpoints deverão possuir documentação OpenAPI.

Cada Service público deverá incluir uma descrição da sua responsabilidade.

---

# 26. Dependências

Antes de adicionar uma biblioteca:

* verificar manutenção;
* compatibilidade;
* licenciamento;
* impacto no projeto.

Preferir soluções simples.

---

# 27. Convenções

## Models

Singular.

```python
Player

Competition

Club
```

## Services

```python
PlayerService
```

## Selectors

```python
PlayerSelector
```

## Serializers

```python
PlayerCreateSerializer
```

## Permissions

```python
IsClubAdmin
```

---

# 28. Checklist para Novos Módulos

Antes de concluir um módulo confirmar:

* Models criados.
* Migrações aplicadas.
* Services implementados.
* Selectors implementados.
* Permissões implementadas.
* Serializers separados por responsabilidade.
* Views simples.
* Testes criados.
* Documentação atualizada.

---

# 29. Ferramentas Oficiais

Qualidade:

* Ruff
* MyPy
* Pytest

Documentação:

* drf-spectacular

Automação:

* Celery
* Redis

---

# 30. Fluxo Oficial de Desenvolvimento

```text
Issue

↓

Criar Branch

↓

Implementar Models

↓

Criar Services

↓

Criar Selectors

↓

Criar API

↓

Escrever Testes

↓

Executar Lint

↓

Executar Testes

↓

Pull Request

↓

Code Review

↓

Merge

↓

Deploy
```

---

# 31. Regras Obrigatórias

É obrigatório:

* utilizar tipagem (`type hints`);
* separar lógica por camadas;
* documentar APIs;
* escrever testes;
* reutilizar código existente;
* seguir a arquitetura DDD adotada pelo projeto.

É proibido:

* lógica de negócio nas Views;
* consultas complexas nos Serializers;
* acesso direto entre módulos sem Services ou Selectors;
* utilização de `print()` para depuração em produção;
* credenciais no código-fonte.

---

# 32. Checklist de Revisão

Antes de aprovar um Pull Request verificar:

* Arquitetura respeitada.
* Código legível.
* Serviços reutilizáveis.
* Queries eficientes.
* Cobertura de testes.
* Documentação atualizada.
* Segurança validada.
* Compatibilidade Multi-Tenant.

---

# 33. Architecture Decision Record

## ADR-012 — Guia Oficial de Desenvolvimento Backend

**Decisão**

Todo o desenvolvimento backend deverá seguir uma arquitetura em camadas composta por Models, Services, Selectors, Permissions, Serializers e Views.

**Justificação**

* Reduz acoplamento.
* Facilita testes.
* Aumenta reutilização.
* Simplifica manutenção.
* Garante consistência entre todos os módulos.

Este guia é obrigatório para qualquer nova funcionalidade implementada no backend do Bolayetu.
