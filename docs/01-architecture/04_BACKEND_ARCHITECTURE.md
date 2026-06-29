# BACKEND ARCHITECTURE

**Documento:** `04_BACKEND_ARCHITECTURE.md`

**Versão:** 2.0.0

**Estado:** Documento Oficial de Arquitetura Backend

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define a arquitetura oficial do backend do Bolayetu.

O objetivo é estabelecer padrões para:

* organização do código;
* separação de responsabilidades;
* desenvolvimento de novos módulos;
* APIs;
* segurança;
* testes;
* escalabilidade.

Todas as implementações deverão seguir este documento.

---

# 2. Stack Tecnológica

## Linguagem

* Python 3.12+

## Framework

* Django
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
* Cloudflare CDN

## Autenticação

* JWT

## Containers

* Docker

---

# 3. Arquitetura Geral

O backend segue uma arquitetura modular baseada em Domain Driven Design (DDD).

```text
apps/
│
├── accounts/
├── organizations/
├── clubs/
├── players/
├── fans/
├── competitions/
├── matches/
├── standings/
├── statistics/
├── transfers/
├── news/
├── notifications/
├── subscriptions/
├── billing/
├── media/
├── analytics/
│
├── common/
├── core/
└── config/
```

Cada aplicação representa um domínio de negócio.

---

# 4. Estrutura de um Módulo

Todos os módulos deverão possuir a mesma organização.

```text
players/

models/
serializers/
selectors/
services/
permissions/
validators/
views/
urls/
tasks/
signals/
admin/
filters/
schemas/
constants/
exceptions/
tests/

apps.py
```

Esta estrutura é obrigatória.

---

# 5. Responsabilidades

## Models

Responsáveis apenas pela persistência dos dados.

Devem conter:

* campos;
* relacionamentos;
* propriedades simples.

Não devem conter regras complexas de negócio.

---

## Serializers

Responsáveis por:

* validação de entrada;
* transformação de dados;
* serialização.

Nunca devem executar regras de negócio.

---

## Views

As Views apenas orquestram o fluxo.

Responsabilidades:

* autenticação;
* permissões;
* validação inicial;
* chamada aos Services;
* resposta HTTP.

Nunca devem conter lógica de negócio.

---

## Services

O coração da aplicação.

Toda a lógica de negócio pertence aos Services.

Exemplos:

* aprovar clube;
* criar competição;
* gerar classificação;
* transferir jogador.

Nenhuma regra de negócio deverá estar fora desta camada.

---

## Selectors

Responsáveis pelas consultas.

Exemplos:

* listar jogadores ativos;
* classificação da competição;
* estatísticas do clube.

Toda consulta complexa deverá existir num Selector.

---

## Permissions

Responsáveis por validar:

* papéis;
* ownership;
* tenant;
* autorização.

Nunca deverão existir verificações de permissões espalhadas pelos Services.

---

## Validators

Centralizam validações reutilizáveis.

Exemplo:

* validar idade mínima;
* validar número da camisola;
* validar regulamentos.

---

## Tasks

Executadas pelo Celery.

Exemplos:

* emails;
* PDFs;
* notificações;
* importações;
* geração de relatórios.

---

## Signals

Utilização restrita.

Apenas para:

* auditoria;
* logging;
* sincronizações simples.

Nunca implementar regras críticas através de Signals.

---

# 6. Fluxo Oficial

Toda operação deverá seguir o seguinte fluxo.

```text
Request

↓

View

↓

Serializer

↓

Permission

↓

Service

↓

Selector (quando necessário)

↓

Model

↓

Database

↓

Response
```

Qualquer implementação fora deste fluxo deverá ser justificada.

---

# 7. Organização dos Services

Os Services deverão ser pequenos.

Exemplo:

```text
PlayerService

create_player()

update_player()

approve_transfer()

request_affiliation()

retire_player()
```

Evitar Services gigantes.

---

# 8. Organização dos Selectors

Os Selectors deverão conter apenas consultas.

Exemplo:

```text
PlayerSelector

active_players()

club_players()

free_agents()

top_scorers()
```

Nunca modificar dados dentro de um Selector.

---

# 9. APIs

Todas as APIs deverão seguir REST.

Padrão:

```text
/api/v1/
```

Exemplo:

```text
/api/v1/players/

/api/v1/clubs/

/api/v1/competitions/

/api/v1/matches/
```

Versionamento é obrigatório.

---

# 10. Respostas

Formato oficial.

```json
{
    "success": true,
    "message": "Player created successfully.",
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

# 11. Multi-Tenant

Todos os módulos deverão ser Tenant Aware.

Toda consulta deverá considerar:

* Tenant;
* Organização;
* Permissões.

Nunca devolver dados pertencentes a outro Tenant.

---

# 12. Segurança

Obrigatório utilizar:

* JWT
* RBAC
* Object Ownership
* Tenant Isolation
* Rate Limiting

Permissões nunca deverão depender apenas do frontend.

---

# 13. Media

Todo upload deverá seguir o fluxo:

```text
Frontend

↓

API

↓

Media Service

↓

Cloudflare R2

↓

Cloudflare CDN

↓

URL Pública
```

Nunca utilizar `MEDIA_ROOT` em produção.

---

# 14. Background Jobs

Todo processamento pesado deverá utilizar Celery.

Exemplos:

* gerar PDF;
* gerar estatísticas;
* envio de emails;
* exportações;
* notificações.

---

# 15. Logging

Toda operação crítica deverá gerar logs.

Exemplos:

* login;
* alteração de permissões;
* transferências;
* criação de competições;
* alterações de resultados.

---

# 16. Testes

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

**80%**

---

# 17. Convenções

## Modelos

Singular.

Exemplo:

```python
Player
Competition
Club
```

---

## Services

Sufixo:

```text
PlayerService
CompetitionService
```

---

## Selectors

```text
PlayerSelector
CompetitionSelector
```

---

## Serializers

```text
PlayerSerializer
PlayerCreateSerializer
PlayerUpdateSerializer
```

---

## Permissions

```text
IsOrganization

IsClub

IsPlayer

IsAdmin
```

---

# 18. Dependências entre Módulos

Um módulo nunca deverá importar diretamente Models de outro módulo para executar lógica de negócio.

Comunicação preferencial:

```text
Service

↓

Selector

↓

API Interna (quando necessário)
```

---

# 19. Common

O módulo `common/` conterá componentes reutilizáveis.

Exemplos:

* BaseModel
* UUIDModel
* TimeStampedModel
* SoftDeleteModel
* Paginação
* Mixins
* Utilitários

---

# 20. Core

O módulo `core/` conterá infraestrutura da plataforma.

Exemplos:

* autenticação;
* permissões base;
* middleware;
* storage;
* logging;
* configuração do Celery;
* configuração do Redis;
* configuração do Cloudflare;
* tratamento global de exceções.

---

# 21. Regras Obrigatórias

É proibido:

* lógica de negócio em Views;
* lógica de negócio em Serializers;
* consultas complexas nas Views;
* acesso direto entre domínios sem Services ou Selectors;
* dependências circulares entre módulos;
* utilização de sinais (`signals`) para processos críticos.

É obrigatório:

* manter baixo acoplamento;
* documentar APIs;
* escrever testes;
* reutilizar componentes comuns;
* respeitar o isolamento entre Tenants.

---

# 22. Evolução da Arquitetura

A arquitetura foi concebida para suportar:

* microsserviços, caso necessário no futuro;
* filas distribuídas;
* múltiplas aplicações cliente (Web, Mobile, APIs públicas);
* integração com serviços externos;
* crescimento do número de módulos sem perda de organização.

Qualquer alteração estrutural deverá ser registada através de um **Architecture Decision Record (ADR)** e aprovada antes da implementação.
