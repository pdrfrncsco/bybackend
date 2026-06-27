# Plano de Migração da Arquitetura do Backend do Bolayetu (V2)

**Versão:** 2.0
**Estado:** Planeamento
**Objetivo:** Refatoração incremental da arquitetura do Bolayetu para suportar um ecossistema desportivo SaaS escalável, multi-tenant e preparado para expansão em África.

---

# 1. Objetivos da Migração

A nova arquitetura deverá permitir:

* Escalabilidade horizontal.
* Arquitetura orientada ao domínio (DDD).
* Backend e Frontend organizados pelos mesmos contextos de negócio.
* Multi-Tenant SaaS.
* Cloudflare R2/CDN para gestão de ficheiros.
* Docker como ambiente oficial.
* APIs desacopladas.
* Clean Architecture.
* Facilidade de manutenção.
* Baixo acoplamento entre módulos.
* Preparação para marketplace, scouting, transferências e analytics.

---

# 2. Princípios da Migração

## Nunca interromper o desenvolvimento.

A migração será incremental.

## Nunca apagar funcionalidades existentes antes da validação.

O fluxo deverá ser:

```text
Sistema Atual
      ↓
Novo Módulo
      ↓
Migração de Código
      ↓
Testes
      ↓
Substituição
      ↓
Remoção do Legado
```

## Cada fase deve permitir rollback.

---

# 3. Objetivos Técnicos

Ao final da migração o projeto deverá possuir:

* Domain Driven Design
* Clean Architecture
* Feature-Based Modules
* Multi-Tenant
* Docker
* Cloudflare R2
* Cloudflare CDN
* Redis
* Celery
* PostgreSQL
* APIs REST organizadas
* Frontend modular

---

# 4. Arquitetura Final Esperada

```text
backend/

apps/

accounts/
organizations/
clubs/
players/
fans/

competitions/
matches/
standings/
statistics/
transfers/

stadiums/
referees/
coaches/

news/

notifications/

analytics/

reports/

subscriptions/

billing/

media/

onboarding/

common/

core/

config/
```

---

# 5. Roadmap da Migração

## Sprint -1 — Preparação

### Objetivos

Criar uma base segura para a migração.

### Atividades

* Auditoria da arquitetura atual.
* Inventário das apps.
* Inventário dos endpoints.
* Inventário das permissões.
* Inventário dos modelos.
* Documentação da arquitetura atual.
* Configuração do ambiente Docker de homologação.
* Configuração do CI.
* Definição dos padrões de código.

### Entregáveis

```text
docs/

architecture-audit.md

api-map.md

dependency-map.md

coding-standards.md
```

---

# Sprint 0 — Fundação

## Objetivos

Criar a nova estrutura do projeto.

### Criar

```text
config/
core/
common/
```

### Reorganizar

Settings

```text
settings/

base.py

development.py

production.py

testing.py
```

### Criar Core

```text
authentication/
permissions/
middleware/
validators/
storage/
exceptions/
```

Resultado esperado:

Nova fundação sem alterar funcionalidades.

---

# Sprint 1 — Accounts

## Objetivos

Refatorar autenticação.

Criar:

```text
accounts/
```

Responsabilidades

* User
* Roles
* JWT
* RBAC
* Perfis

Perfis

```text
OrganizacaoProfile

ClubeProfile

JogadorProfile

AdeptoProfile
```

Resultado esperado:

Separação entre identidade e perfil.

---

# Sprint 2 — Multi-Tenant

Criar

```text
tenants/
```

Implementar

* Tenant
* Domain
* TenantMiddleware
* TenantResolver

Exemplo

```text
faf.bolayetu.com

girabola.bolayetu.com
```

Resultado esperado

Todas as APIs passam a ser tenant-aware.

---

# Sprint 3 — Organizações

Criar

```text
organizations/
```

Responsabilidades

* Federações
* Associações
* Ligas
* Campeonatos

Migrar funcionalidades existentes.

---

# Sprint 4 — Clubs

Criar

```text
clubs/
```

Responsabilidades

* Clubs
* Staff Técnico
* Patrocinadores

Implementar pedidos de afiliação.

---

# Sprint 5 — Jogadores

Criar

```text
players/
```

Responsabilidades

* Perfil Profissional
* Histórico
* Carreira
* Estatísticas

Implementar pedidos de vínculo.

---

# Sprint 6 — Competições

Migrar

```text
competitions/

matches/

standings/

statistics/
```

Separar:

* Campeonato
* Jogos
* Classificações
* Estatísticas

---

# Sprint 7 — Transferências

Criar

```text
transfers/
```

Preparar

* Transferências
* Contratos
* Empréstimos

---

# Sprint 8 — Cloudflare

Eliminar MEDIA_ROOT como armazenamento principal.

Implementar

Cloudflare R2

Cloudflare CDN

django-storages

boto3

Migrar

* Fotos
* Logos
* Vídeos
* PDFs
* Relatórios

Resultado

```text
https://cdn.bolayetu.com/
```

---

# Sprint 9 — Docker

Criar

```text
docker/

backend/

frontend/

postgres/

redis/

nginx/
```

Implementar

* Dockerfile
* docker-compose.yml
* docker-compose.prod.yml

Containers

* Backend
* Frontend
* PostgreSQL
* Redis
* Celery
* Nginx

---

# Sprint 10 — Novo Frontend

Implementar arquitetura modular.

```text
modules/

organizations/

clubs/

players/

fans/

competitions/

matches/

transfers/

news/

notifications/

subscriptions/
```

Cada módulo deverá conter:

```text
components/

pages/

services/

hooks/

types/

schemas/

constants/
```

---

# Sprint 11 — Analytics

Criar

```text
analytics/
```

Dashboards

* Organização
* Clube
* Jogador
* Plataforma

---

# Sprint 12 — Marketplace

Preparar:

* Empresários
* Scouts
* Academias
* Patrocinadores
* Marketplace de jogadores

---

# 6. Estratégia Git

Criar uma branch dedicada:

```text
refactor/architecture-v2
```

Fluxo recomendado

```text
main

↓

develop

↓

refactor/architecture-v2

↓

feature/*
```

Nenhuma funcionalidade nova deverá ser desenvolvida diretamente na branch principal durante a refatoração.

---

# 7. Critérios de Qualidade

Cada Sprint só poderá ser considerada concluída quando:

* Todos os testes passarem.
* APIs permanecerem compatíveis (ou devidamente versionadas).
* Documentação atualizada.
* Deploy validado.
* Rollback possível.

---

# 8. Critérios de Sucesso

Ao final da migração o Bolayetu deverá suportar:

* Milhares de Organizações.
* Milhares de Clubs.
* Centenas de milhares de Jogadores.
* Milhões de Adeptos.
* Multi-Tenant SaaS.
* White Label.
* Docker.
* Cloudflare.
* Marketplace.
* Mobile App.
* APIs públicas.
* Escalabilidade internacional.

---

# 9. Próximos Passos

1. Concluir a Sprint -1 (Auditoria).
2. Criar a estrutura base da arquitetura.
3. Refatorar autenticação.
4. Implementar Multi-Tenant.
5. Migrar os domínios de negócio.
6. Migrar para Cloudflare R2.
7. Dockerizar a plataforma.
8. Implementar o novo frontend modular.
9. Evoluir para Analytics e Marketplace.

---

# Visão de Longo Prazo

O Bolayetu deixará de ser apenas uma aplicação de gestão de campeonatos para tornar-se uma plataforma digital de referência para o futebol africano, permitindo a gestão integrada de organizações, clubs, jogadores e adeptos, preparada para crescimento contínuo, internacionalização e novos modelos de negócio.
