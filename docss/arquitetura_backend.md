# BOLAYETU PLATFORM GUIDE

**Versão:** 2.0
**Estado:** Documento Orientador Oficial
**Projeto:** Bolayetu — Football Ecosystem Platform

---

# 1. Visão do Produto

O Bolayetu é uma plataforma digital de gestão e desenvolvimento do ecossistema do futebol.

Não é apenas um sistema de gestão de campeonatos.

É uma infraestrutura digital que liga:

* Organizações Desportivas
* Clubes
* Jogadores
* Adeptos
* Equipas Técnicas
* Árbitros
* Scouts
* Empresários
* Patrocinadores

O objetivo é tornar-se a principal plataforma digital do futebol em Angola e, posteriormente, em África.

---

# 2. Missão

Digitalizar o ecossistema do futebol através de uma plataforma SaaS moderna, segura, escalável e centrada nos seus intervenientes.

---

# 3. Visão Tecnológica

O projeto será desenvolvido desde a raiz com foco em:

* Escalabilidade
* Modularidade
* Segurança
* Performance
* Multi-Tenancy
* Cloud Native
* APIs First

---

# 4. Arquitetura Geral

A plataforma será composta por quatro grandes pilares.

```text
Organizações

↓

Clubes

↓

Jogadores

↓

Adeptos
```

Todos interagem através do Bolayetu.

---

# 5. Princípios Fundamentais

Todo o desenvolvimento deverá seguir estes princípios:

* Domain Driven Design (DDD)
* Clean Architecture
* SOLID
* Feature-Based Architecture
* API First
* Mobile First
* Cloud Native
* Docker First
* Multi-Tenant by Design

Nenhum módulo deverá ser desenvolvido ignorando estes princípios.

---

# 6. Stack Tecnológica

## Backend

* Python
* Django
* Django REST Framework
* PostgreSQL
* JWT Authentication
* Redis
* Celery

---

## Frontend

* React
* TypeScript
* Vite
* TailwindCSS
* Shadcn UI
* TanStack Query
* Zustand
* React Hook Form
* Zod
* Framer Motion

---

## Infraestrutura

* Docker
* Docker Compose
* Nginx
* Ubuntu Server

---

## Cloud

* Cloudflare DNS
* Cloudflare CDN
* Cloudflare R2
* SSL
* WAF

---

# 7. Modelo SaaS

O Bolayetu será um SaaS Multi-Tenant.

Cada Organização será um Tenant.

Exemplos:

```text
faf.bolayetu.com

girabola.bolayetu.com

apf-luanda.bolayetu.com
```

Cada Tenant possui:

* Branding próprio
* Clubes próprios
* Competições próprias
* Utilizadores próprios
* Configurações próprias

Nenhum Tenant poderá aceder aos dados de outro.

---

# 8. Modelo de Utilizadores

O sistema possuirá dois níveis.

## Identidade

Representada pelo User.

Responsável apenas por:

* Login
* Password
* Segurança
* Autorização

---

## Perfil de Negócio

Cada utilizador poderá possuir um perfil.

Perfis disponíveis:

* Organização
* Clube
* Jogador
* Adepto

Os dados de negócio nunca deverão ficar diretamente no User.

---

# 9. Ecossistema

## Organização

Responsável por:

* Competições
* Clubes
* Regulamentos
* Calendários
* Rankings

---

## Clube

Responsável por:

* Plantel
* Equipa Técnica
* Transferências
* Documentos
* Estatísticas

---

## Jogador

Responsável por:

* Perfil
* Carreira
* Histórico
* Estatísticas
* Conquistas

---

## Adepto

Responsável por:

* Favoritos
* Clubes Seguidos
* Jogadores Seguidos
* Notificações

---

# 10. Estrutura dos Módulos

Cada domínio deverá existir como módulo independente.

Exemplo:

```text
accounts

organizations

clubs

players

fans

competitions

matches

statistics

standings

transfers

news

notifications

analytics

subscriptions

billing

media

reports

onboarding
```

Nenhum módulo deverá depender diretamente da implementação interna de outro.

Toda comunicação deverá ocorrer através de Services ou APIs internas.

---

# 11. Gestão de Ficheiros

Nenhum ficheiro deverá permanecer armazenado localmente.

Todos os uploads utilizarão:

Cloudflare R2

Distribuição através de:

Cloudflare CDN

Exemplos:

* Fotos
* Logos
* Vídeos
* PDFs
* Relatórios

---

# 12. Docker

Todo o ambiente deverá executar em containers.

Serviços previstos:

* Backend
* Frontend
* PostgreSQL
* Redis
* Celery Worker
* Celery Beat
* Nginx

O ambiente local deverá reproduzir o ambiente de produção e funcionar com Sqlite localmente.

---

# 13. Segurança

O sistema deverá implementar desde o início:

* JWT Authentication
* RBAC (Role-Based Access Control)
* Tenant Isolation
* Object Ownership Validation
* Auditoria
* Rate Limiting
* Logs

Segurança nunca será tratada como funcionalidade futura.

---

# 14. Frontend

A aplicação React será organizada por módulos.

Cada módulo deverá conter:

* Pages
* Components
* Hooks
* Services
* Schemas
* Types
* Constants

Nenhum componente deverá conter lógica de negócio.

---

# 15. Backend

Cada módulo Django deverá conter:

* Models
* Services
* Selectors
* Serializers
* Permissions
* Views
* URLs
* Tests

Regras de negócio pertencem aos Services.

Consultas complexas pertencem aos Selectors.

Views apenas orquestram.

---

# 16. Qualidade de Código

Todo código deverá ser:

* Modular
* Testável
* Documentado
* Reutilizável
* Legível

Evitar:

* Classes gigantes
* Componentes gigantes
* Views gigantes
* Duplicação de código

---

# 17. Fluxo de Desenvolvimento

Antes de qualquer implementação:

1. Analisar o domínio.
2. Identificar impacto arquitetural.
3. Definir modelo de dados.
4. Definir APIs.
5. Implementar backend.
6. Implementar frontend.
7. Testar.
8. Documentar.

---

# 18. Roadmap Inicial

Fase 1

* Arquitetura
* Autenticação
* Multi-Tenant

Fase 2

* Organizações

Fase 3

* Clubes

Fase 4

* Jogadores

Fase 5

* Competições

Fase 6

* Jogos

Fase 7

* Estatísticas

Fase 8

* Transferências

Fase 9

* Notificações

Fase 10

* Marketplace

---

# 19. Objetivo Final

Construir uma plataforma preparada para servir:

* Federações
* Associações
* Ligas
* Clubes
* Academias
* Jogadores
* Adeptos

em qualquer país africano, mantendo uma arquitetura moderna, escalável e preparada para evolução contínua.

---

# 20. Regra de Ouro

Antes de implementar qualquer funcionalidade, responder às seguintes perguntas:

1. Este módulo respeita o domínio de negócio?
2. É reutilizável?
3. Está preparado para múltiplos Tenants?
4. É compatível com Docker?
5. Utiliza Cloudflare para media?
6. Respeita a separação entre identidade e perfil?
7. Está alinhado com a visão do Bolayetu?

Se alguma resposta for "não", a implementação deve ser revista antes de avançar.
