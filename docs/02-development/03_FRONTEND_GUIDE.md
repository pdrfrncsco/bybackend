# FRONTEND DEVELOPMENT GUIDE

**Documento:** `03_FRONTEND_GUIDE.md`

**Versão:** 2.0.0

**Estado:** Guia Oficial de Desenvolvimento Frontend

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define os padrões oficiais para o desenvolvimento frontend do Bolayetu.

Os objetivos são:

* garantir consistência visual;
* promover reutilização;
* melhorar a experiência do utilizador;
* facilitar manutenção;
* permitir evolução da plataforma.

Todo o desenvolvimento frontend deverá seguir este documento.

---

# 2. Stack Oficial

## Linguagem

* TypeScript 5+

## Framework

* React 19+

## Build Tool

* Vite

## UI

* TailwindCSS
* shadcn/ui

## Estado Global

* Zustand

## Estado do Servidor

* TanStack Query

## Formulários

* React Hook Form

## Validação

* Zod

## Navegação

* React Router

## Ícones

* Lucide React

## Gráficos

* Chart.js

## Progressive Web App

* vite-plugin-pwa

---

# 3. Arquitetura do Projeto

```text
src/

app/
assets/
components/
features/
hooks/
layouts/
lib/
providers/
routes/
services/
store/
styles/
types/
utils/

main.tsx
```

Nenhum ficheiro deverá ser colocado fora desta estrutura sem justificação.

---

# 4. Desenvolvimento por Feature

Todo o frontend será organizado por funcionalidades.

Exemplo:

```text
features/

players/

clubs/

competitions/

matches/

statistics/

organizations/

news/

notifications/
```

Cada módulo deverá ser independente.

---

# 5. Estrutura Interna

Exemplo:

```text
players/

components/

pages/

hooks/

services/

schemas/

store/

types/

constants/

utils/

routes.ts

index.ts
```

Todos os módulos deverão seguir esta organização.

---

# 6. Fluxo Oficial

```text
User Action

↓

Component

↓

Hook

↓

Service

↓

API

↓

Backend

↓

TanStack Query

↓

Component
```

Nenhum componente deverá comunicar diretamente com a API.

---

# 7. Pages

As páginas representam funcionalidades completas.

Exemplos:

* PlayerListPage
* PlayerDetailsPage
* CreatePlayerPage
* EditPlayerPage

As páginas apenas compõem componentes.

---

# 8. Components

Os componentes deverão ser pequenos.

Responsabilidade única.

Exemplos:

```text
PlayerCard

PlayerAvatar

PlayerStatistics

PlayerTable
```

Máximo recomendado:

300 linhas.

---

# 9. Shared Components

Componentes reutilizáveis ficam em:

```text
components/

ui/

forms/

tables/

charts/

layout/

feedback/
```

Exemplos:

* Button
* Card
* Table
* Badge
* Avatar
* Dialog
* Drawer
* Pagination
* EmptyState
* Skeleton

Nunca duplicar estes componentes.

---

# 10. Hooks

Toda lógica reutilizável deverá estar em Hooks.

Exemplo:

```typescript
usePlayers()

usePlayer()

usePlayerStatistics()

useNotifications()
```

Nunca renderizar UI dentro de Hooks.

---

# 11. Services

Os Services comunicam exclusivamente com a API.

Exemplo:

```typescript
PlayerService

getPlayers()

getPlayer()

createPlayer()

updatePlayer()

deletePlayer()
```

Nunca utilizar `fetch()` ou `axios` diretamente dentro dos componentes.

---

# 12. TanStack Query

Toda comunicação remota deverá utilizar TanStack Query.

Responsabilidades:

* cache;
* sincronização;
* retries;
* paginação;
* invalidação.

---

# 13. Zustand

Responsável por:

* utilizador autenticado;
* Tenant;
* preferências;
* tema;
* notificações globais.

Nunca armazenar dados remotos persistentes.

---

# 14. Formulários

Todos os formulários utilizarão:

* React Hook Form
* Zod

Fluxo:

```text
Form

↓

Validation

↓

Submit

↓

Service

↓

API
```

---

# 15. Validação

Toda validação deverá ser centralizada.

```text
schemas/

player.schema.ts

club.schema.ts

competition.schema.ts
```

Nunca repetir regras de validação.

---

# 16. Tipos

Todo o projeto utilizará TypeScript.

Evitar:

```typescript
any
```

Utilizar:

```typescript
interface Player

interface Competition

interface Club
```

---

# 17. Rotas

Organização:

```text
routes/

public.tsx

auth.tsx

organization.tsx

club.tsx

player.tsx

fan.tsx

admin.tsx
```

Cada rota deverá possuir proteção baseada em permissões.

---

# 18. Layouts

Layouts oficiais:

```text
PublicLayout

AuthLayout

DashboardLayout

OrganizationLayout

ClubLayout

PlayerLayout

FanLayout
```

Cada perfil possui navegação própria.

---

# 19. Gestão de Estado

Estado Local

React State.

Estado Global

Zustand.

Estado Remoto

TanStack Query.

Nunca duplicar estados.

---

# 20. Tratamento de Erros

Todas as chamadas deverão tratar:

* timeout;
* autenticação;
* autorização;
* validação;
* falha de rede;
* erro interno.

Apresentar mensagens compreensíveis.

---

# 21. Feedback Visual

Toda operação deverá apresentar feedback.

Exemplos:

* loading;
* skeleton;
* success toast;
* error toast;
* empty state;
* confirmação.

Nunca deixar o utilizador sem resposta.

---

# 22. Design System

Todos os componentes deverão seguir o Design System.

Inclui:

* tipografia;
* espaçamento;
* cores;
* ícones;
* animações.

Nunca criar estilos inconsistentes.

---

# 23. Responsividade

Todos os layouts deverão ser Mobile First.

Breakpoints:

* Mobile
* Tablet
* Laptop
* Desktop
* Large Desktop

---

# 24. Performance

Boas práticas:

* Lazy Loading
* Suspense
* Memoização quando necessária
* Virtualização
* Code Splitting
* Prefetch
* Imagens otimizadas

---

# 25. Acessibilidade

Obrigatório:

* HTML semântico;
* labels em formulários;
* navegação por teclado;
* foco visível;
* contraste adequado;
* atributos ARIA quando necessários.

---

# 26. Internacionalização

Todo texto deverá ser preparado para i18n.

Nunca escrever textos diretamente nos componentes.

---

# 27. Assets

Toda media será obtida através do módulo MediaAsset.

Nunca utilizar caminhos fixos.

Utilizar sempre URLs fornecidas pela API.

---

# 28. Testes

Cada Feature deverá possuir:

```text
tests/

components/

hooks/

pages/

services/
```

Ferramentas:

* Vitest
* React Testing Library

---

# 29. Checklist para Nova Feature

Antes de concluir uma funcionalidade verificar:

* Página criada.
* Componentes reutilizáveis.
* Hook implementado.
* Service criado.
* Schemas criados.
* Tipos definidos.
* Rotas registadas.
* Testes escritos.
* Estados de loading, erro e vazio implementados.

---

# 30. Fluxo Oficial de Desenvolvimento

```text
Issue

↓

Criar Branch

↓

Criar Tipos

↓

Criar Schemas

↓

Criar Service

↓

Criar Hook

↓

Criar Componentes

↓

Criar Página

↓

Adicionar Rotas

↓

Testar

↓

Pull Request

↓

Code Review

↓

Merge
```

---

# 31. Regras Obrigatórias

É obrigatório:

* utilizar TypeScript;
* utilizar TanStack Query para dados remotos;
* utilizar Zustand apenas para estado global;
* utilizar React Hook Form + Zod;
* reutilizar componentes do Design System;
* implementar loading, erro e empty state;
* documentar componentes públicos.

É proibido:

* chamadas HTTP dentro de componentes;
* utilização de `any` sem justificação;
* duplicação de componentes;
* lógica de negócio nas páginas;
* estilos inline;
* utilização de bibliotecas UI fora do Design System sem aprovação.

---

# 32. Ferramentas Oficiais

Qualidade:

* ESLint
* Prettier
* TypeScript

Testes:

* Vitest
* React Testing Library

Documentação:

* Storybook (para componentes reutilizáveis)

Automação:

* Husky
* lint-staged
* Commitlint

---

# 33. Architecture Decision Record

## ADR-013 — Guia Oficial de Desenvolvimento Frontend

**Decisão**

Adotar uma arquitetura frontend baseada em Features, Componentes Reutilizáveis, TanStack Query, Zustand e Design System único.

**Justificação**

* Facilita escalabilidade.
* Melhora reutilização.
* Reduz inconsistências.
* Simplifica manutenção.
* Proporciona uma experiência uniforme em toda a plataforma.

Este guia deverá ser seguido por qualquer desenvolvimento frontend realizado no Bolayetu.
