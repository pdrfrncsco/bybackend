# FRONTEND ARCHITECTURE

**Documento:** `05_FRONTEND_ARCHITECTURE.md`

**Versão:** 2.0.0

**Estado:** Documento Oficial de Arquitetura Frontend

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define a arquitetura oficial do frontend do Bolayetu.

O objetivo é estabelecer padrões para:

* organização do código;
* estrutura dos módulos;
* gestão de estado;
* comunicação com APIs;
* reutilização de componentes;
* design system;
* escalabilidade.

Todo o desenvolvimento frontend deverá seguir este documento.

---

# 2. Stack Tecnológica

## Linguagem

* TypeScript

## Framework

* React 19+

## Build Tool

* Vite

## Styling

* TailwindCSS

## Component Library

* shadcn/ui

## Gestão de Estado Global

* Zustand

## Gestão de Estado do Servidor

* TanStack Query

## Formulários

* React Hook Form

## Validação

* Zod

## Navegação

* React Router

## Gráficos

* Chart.js

## PDFs

* PDF.js

## PWA

* vite-plugin-pwa

---

# 3. Princípios Arquiteturais

O frontend deverá seguir os seguintes princípios:

* Feature-Based Architecture
* Component-Driven Development
* Atomic Design (adaptado)
* Mobile First
* Responsive Design
* API First
* Reutilização máxima
* Separação entre UI e lógica

---

# 4. Estrutura Geral

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
```

Cada diretório possui uma responsabilidade única.

---

# 5. Organização por Funcionalidades

Todo o desenvolvimento deverá ser organizado por domínio de negócio.

```text
features/

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
news/
notifications/
subscriptions/
billing/
analytics/
media/
settings/
```

Cada domínio é completamente independente.

---

# 6. Estrutura Interna de um Módulo

Exemplo para `players`.

```text
players/

components/
pages/
hooks/
services/
schemas/
types/
constants/
store/
utils/
routes.ts
index.ts
```

Cada módulo deverá seguir exatamente esta organização.

---

# 7. Responsabilidades

## Pages

Representam páginas completas.

Exemplos:

* Dashboard
* Lista
* Detalhes
* Criar
* Editar

Nunca deverão conter componentes reutilizáveis.

---

## Components

Componentes reutilizáveis do domínio.

Exemplos:

* PlayerCard
* PlayerAvatar
* PlayerTable
* PlayerStatistics

---

## Hooks

Centralizam lógica reutilizável.

Exemplos:

```typescript
usePlayers()

usePlayer()

usePlayerStats()

useTransferHistory()
```

Nunca deverão renderizar UI.

---

## Services

Responsáveis pela comunicação com a API.

Exemplo:

```typescript
PlayerService

getPlayers()

createPlayer()

updatePlayer()

deletePlayer()
```

Nunca deverão conter componentes React.

---

## Schemas

Validação com Zod.

Exemplo:

```typescript
PlayerSchema

ClubSchema

CompetitionSchema
```

---

## Types

Interfaces TypeScript.

Exemplo:

```typescript
Player

Club

Competition
```

---

## Store

Estado global do módulo utilizando Zustand.

Exemplo:

```typescript
usePlayerStore()
```

---

## Utils

Funções utilitárias específicas do domínio.

---

# 8. Componentes Globais

Todos os componentes reutilizáveis deverão ficar em:

```text
components/
```

Exemplos:

```text
Button

Input

Table

Modal

Dialog

Avatar

Badge

Toast

Card

Tabs

Dropdown

Breadcrumb

Loader

Pagination
```

Nenhum módulo deverá duplicar estes componentes.

---

# 9. Layouts

Os layouts representam diferentes áreas da aplicação.

```text
layouts/

PublicLayout

DashboardLayout

OrganizationLayout

ClubLayout

PlayerLayout

FanLayout

AuthLayout
```

Cada perfil possui um layout próprio.

---

# 10. Rotas

As rotas deverão ser organizadas por domínio.

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

Cada rota deverá utilizar proteção baseada em permissões.

---

# 11. Gestão de Estado

## Estado do Servidor

Utilizar TanStack Query.

Responsável por:

* cache;
* sincronização;
* invalidação;
* paginação.

---

## Estado Global

Utilizar Zustand.

Responsável por:

* utilizador autenticado;
* tenant;
* tema;
* notificações;
* preferências.

---

## Estado Local

Utilizar apenas React State.

Sempre que possível manter o estado próximo do componente.

---

# 12. Comunicação com Backend

Fluxo oficial.

```text
Component

↓

Hook

↓

Service

↓

API

↓

Backend
```

Nunca chamar `fetch()` diretamente dentro dos componentes.

---

# 13. Formulários

Todos os formulários deverão utilizar:

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

# 14. Gestão de Erros

Todos os erros deverão ser tratados.

Categorias:

* validação;
* autenticação;
* autorização;
* servidor;
* rede.

O utilizador deverá receber mensagens claras.

---

# 15. Design System

Todo o frontend deverá utilizar um único Design System.

Inclui:

* cores;
* tipografia;
* espaçamentos;
* ícones;
* componentes;
* animações.

Nenhum componente deverá utilizar estilos arbitrários que contrariem o Design System.

---

# 16. Tema

A aplicação suportará:

* Light Mode
* Dark Mode

O tema deverá ser persistido nas preferências do utilizador.

---

# 17. Dashboards

Cada perfil possuirá um dashboard próprio.

```text
Organization Dashboard

Club Dashboard

Player Dashboard

Fan Dashboard

Administrator Dashboard
```

Cada dashboard apresentará apenas informação relevante para o respetivo perfil.

---

# 18. PWA

O frontend deverá funcionar como Progressive Web App.

Funcionalidades previstas:

* instalação;
* cache offline;
* atualização automática;
* notificações push (quando suportado).

---

# 19. Performance

Boas práticas obrigatórias:

* Lazy Loading
* Code Splitting
* Suspense
* Memoização quando necessária
* Virtualização de listas grandes
* Otimização de imagens
* Prefetch de rotas

---

# 20. Segurança

O frontend nunca deverá confiar na interface para aplicar regras de segurança.

Responsabilidades:

* armazenar JWT de forma segura;
* renovar tokens;
* ocultar funcionalidades não autorizadas;
* proteger rotas.

A validação definitiva pertence sempre ao backend.

---

# 21. Testes

Cada módulo deverá possuir:

```text
tests/

components/

hooks/

services/

pages/
```

Tipos de testes:

* Unitários
* Integração
* End-to-End (quando aplicável)

---

# 22. Convenções

## Componentes

PascalCase.

```text
PlayerCard

CompetitionTable

TransferTimeline
```

---

## Hooks

Sempre iniciar por:

```text
use
```

Exemplo:

```text
useCompetition()

useClubPlayers()

useNotifications()
```

---

## Stores

```text
usePlayerStore()

useAuthStore()
```

---

## Services

```text
PlayerService

ClubService

CompetitionService
```

---

## Tipos

Interfaces sempre em PascalCase.

```typescript
Player

Club

Competition
```

---

# 23. Estrutura Recomendada

```text
src/

app/

assets/

components/

features/

hooks/

layouts/

providers/

routes/

services/

store/

styles/

types/

utils/

main.tsx
```

Esta estrutura deverá permanecer estável ao longo da evolução do projeto.

---

# 24. Regras Obrigatórias

É proibido:

* chamadas diretas à API dentro dos componentes;
* duplicação de componentes;
* lógica de negócio nas páginas;
* estilos inline sem justificação;
* utilização de estado global para dados exclusivamente locais.

É obrigatório:

* reutilizar componentes;
* utilizar TypeScript em todo o projeto;
* utilizar TanStack Query para dados remotos;
* utilizar Zustand para estado global;
* validar formulários com Zod;
* documentar componentes públicos.

---

# 25. Evolução da Arquitetura

A arquitetura foi concebida para suportar:

* novas aplicações móveis;
* micro-frontends (se necessário);
* internacionalização (i18n);
* múltiplos temas;
* white-label por Tenant;
* dashboards altamente personalizáveis.

Qualquer alteração estrutural deverá ser documentada através de um **Architecture Decision Record (ADR)** e manter compatibilidade com os princípios definidos nos documentos de arquitetura do Bolayetu.
