# SYSTEM ARCHITECTURE

**Documento:** `01_SYSTEM_ARCHITECTURE.md`

**Versão:** 2.0.0

**Estado:** Documento Oficial de Arquitetura

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Introdução

## 1.1 Objetivo

Este documento define a arquitetura de alto nível do Bolayetu.

O seu propósito é estabelecer uma visão comum sobre a organização técnica da plataforma, garantindo que todas as decisões de desenvolvimento sejam consistentes, escaláveis e alinhadas com os objetivos estratégicos do produto.

Este documento não descreve detalhes de implementação de código. Em vez disso, apresenta a estrutura arquitetural, os princípios de engenharia, a comunicação entre componentes e as responsabilidades de cada domínio da aplicação.

É considerado o documento central da arquitetura do sistema.

---

## 1.2 Público-Alvo

Este documento destina-se a:

* Arquitetos de Software
* Programadores Backend
* Programadores Frontend
* DevOps Engineers
* Product Managers
* UX/UI Designers
* QA Engineers
* Inteligência Artificial (LLMs)
* Novos membros da equipa

Todos os participantes do projeto deverão compreender este documento antes de iniciar qualquer desenvolvimento.

---

## 1.3 Escopo

Este documento cobre:

* Arquitetura lógica
* Arquitetura física
* Arquitetura funcional
* Organização dos módulos
* Comunicação entre componentes
* Multi-Tenancy
* Infraestrutura
* Segurança
* Escalabilidade
* Integrações
* Fluxos de alto nível

Não cobre:

* Implementação detalhada de APIs
* Estrutura da Base de Dados
* Design UI/UX
* Regras específicas de cada módulo

Esses assuntos serão tratados em documentos próprios.

---

# 2. Filosofia da Arquitetura

O Bolayetu foi concebido para ser uma plataforma digital de longo prazo.

As decisões arquiteturais devem privilegiar:

* Evolução contínua
* Modularidade
* Reutilização
* Manutenção simplificada
* Segurança
* Escalabilidade
* Independência tecnológica entre módulos

O sistema deverá conseguir crescer sem exigir reestruturações profundas.

---

# 3. Visão Geral da Plataforma

O Bolayetu é uma plataforma SaaS Multi-Tenant para gestão do ecossistema do futebol.

A plataforma conecta diferentes tipos de utilizadores e organizações através de um único sistema integrado.

O objetivo não é apenas gerir campeonatos, mas digitalizar toda a operação do futebol.

---

## 3.1 Ecossistema

```text
                           BOLAYETU
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
Organizações               Clubes                Adeptos
        │                      │
        │                      │
        └──────────────┐  ┌────┘
                       │  │
                  Jogadores
                       │
               Equipas Técnicas
                       │
                 Competições
                       │
                  Estatísticas
                       │
                   Marketplace
```

Todos os componentes da plataforma existem para fortalecer este ecossistema.

Cada novo módulo deverá acrescentar valor a pelo menos um destes participantes.

---

# 4. Objetivos Arquiteturais

A arquitetura do Bolayetu foi desenhada para atingir os seguintes objetivos.

## 4.1 Escalabilidade

A plataforma deverá suportar crescimento contínuo em:

* Organizações
* Clubes
* Jogadores
* Competições
* Utilizadores simultâneos
* Volume de dados

Sem necessidade de reescrever componentes centrais.

---

## 4.2 Modularidade

Cada domínio deverá ser implementado como um módulo independente.

Exemplos:

* Accounts
* Organizations
* Clubs
* Players
* Competitions
* Matches
* Transfers
* Analytics

Cada módulo deverá possuir responsabilidades claramente definidas.

---

## 4.3 Baixo Acoplamento

Os módulos não deverão depender diretamente da implementação interna uns dos outros.

A comunicação deverá ocorrer através de:

* Services
* Selectors
* APIs internas
* Eventos (quando aplicável)

---

## 4.4 Alta Coesão

Cada módulo deverá concentrar apenas funcionalidades relacionadas com o seu domínio.

Exemplo:

O módulo **Players** não deverá conter regras de negócio relativas às competições.

Da mesma forma, o módulo **Competitions** não deverá gerir contratos de jogadores.

---

## 4.5 Segurança

A segurança faz parte da arquitetura desde o primeiro dia.

Não deverá existir funcionalidade implementada sem considerar:

* autenticação;
* autorização;
* isolamento de tenants;
* validação de permissões;
* auditoria.

---

## 4.6 Performance

Toda a arquitetura deverá privilegiar:

* consultas eficientes;
* cache;
* processamento assíncrono;
* distribuição por CDN;
* utilização eficiente dos recursos.

---

# 5. Princípios Arquiteturais

O Bolayetu adota os seguintes princípios.

## Domain Driven Design (DDD)

O software será organizado segundo domínios de negócio.

Os módulos representarão áreas funcionais da plataforma e não apenas agrupamentos técnicos.

---

## Clean Architecture

A lógica de negócio deverá permanecer independente da infraestrutura.

As regras do domínio não deverão depender de:

* Django
* React
* PostgreSQL
* Cloudflare
* Docker

Estas tecnologias poderão evoluir sem alterar a lógica principal do sistema.

---

## SOLID

Todos os componentes deverão respeitar os princípios SOLID.

Especial atenção deverá ser dada à separação de responsabilidades e à inversão de dependências.

---

## API First

Toda a comunicação entre frontend e backend ocorrerá através de APIs.

As APIs constituem o contrato oficial entre as diferentes aplicações da plataforma.

---

## Cloud Native

O sistema será concebido para ambientes cloud.

Nenhum componente deverá assumir dependências específicas de infraestrutura local.

---

## Docker First

Todo o ambiente de desenvolvimento, testes e produção deverá executar através de containers.

O comportamento da aplicação deverá ser consistente entre todos os ambientes.

---

## Mobile First

Embora o frontend principal seja uma aplicação web, toda a arquitetura deverá permitir futuras aplicações móveis sem alterações estruturais.

---

# 6. Princípios de Evolução

A arquitetura deverá permitir evolução contínua.

Ao adicionar um novo módulo deverão ser preservados os seguintes critérios:

* Compatibilidade com a arquitetura existente.
* Reutilização dos componentes comuns.
* Independência entre domínios.
* Documentação atualizada.
* Cobertura por testes.

Nenhuma funcionalidade deverá comprometer estes princípios.

---

# 7. Decisões Arquiteturais Fundamentais

As seguintes decisões são consideradas permanentes para a versão 2.x do Bolayetu.

| ID      | Decisão                                       |
| ------- | --------------------------------------------- |
| ADR-001 | Arquitetura orientada ao domínio (DDD)        |
| ADR-002 | Backend em Django + Django REST Framework     |
| ADR-003 | Frontend em React + TypeScript                |
| ADR-004 | PostgreSQL como base de dados oficial         |
| ADR-005 | Multi-Tenant por Organização                  |
| ADR-006 | Docker como ambiente oficial                  |
| ADR-007 | Cloudflare R2 para armazenamento de media     |
| ADR-008 | Cloudflare CDN para distribuição de ficheiros |
| ADR-009 | JWT para autenticação                         |
| ADR-010 | RBAC para controlo de permissões              |

Estas decisões apenas poderão ser alteradas através de um novo Architecture Decision Record (ADR), devidamente documentado e aprovado.

---

# 8. Estrutura da Documentação

Este documento serve como ponto de entrada para toda a documentação técnica.

Os detalhes serão desenvolvidos nos documentos seguintes:

* 02_BUSINESS_ARCHITECTURE.md
* 03_DATABASE_ARCHITECTURE.md
* 04_BACKEND_ARCHITECTURE.md
* 05_FRONTEND_ARCHITECTURE.md
* 06_MULTITENANT_ARCHITECTURE.md
* 06A_GLOBAL_AND_TENANT_DOMAIN.md
* 07_SECURITY_ARCHITECTURE.md
* 08_MEDIA_STORAGE_ARCHITECTURE.md
* 08A_DIGITAL_ASSET_MANAGEMENT.md
* 09_DEVOPS_ARCHITECTURE.md
* 10_EVENTS_AND_WORKFLOWS.md

Todos estes documentos complementam esta arquitetura e devem ser considerados parte integrante da especificação oficial do Bolayetu.

# 9. Arquitetura em Camadas

## 9.1 Visão Geral

O Bolayetu adota uma arquitetura em camadas (Layered Architecture), inspirada nos princípios da Clean Architecture e do Domain Driven Design (DDD).

Cada camada possui responsabilidades bem definidas e comunica apenas com as camadas adjacentes, reduzindo o acoplamento e facilitando a evolução da plataforma.

```text
                        Presentation Layer
        (React, PWA, Mobile Apps, Public Website)
                               │
                               ▼
                        Application Layer
            (REST API, Authentication, Permissions)
                               │
                               ▼
                           Domain Layer
      (Business Rules, Services, Selectors, Domain Logic)
                               │
                               ▼
                      Infrastructure Layer
     (Storage, Redis, Celery, Cloudflare, Email, Payments)
                               │
                               ▼
                           Data Layer
                  (PostgreSQL, Backups, Indexes)
```

Cada camada deve possuir responsabilidades exclusivas.

---

## 9.2 Presentation Layer

A Presentation Layer representa todas as interfaces utilizadas pelos utilizadores.

### Componentes

* Website Institucional
* Aplicação Web (React)
* Progressive Web App (PWA)
* Futuras Aplicações Mobile
* APIs Públicas (consumo externo)

Esta camada é responsável apenas por:

* apresentar informação;
* recolher dados do utilizador;
* chamar APIs;
* apresentar mensagens;
* gerir estado da interface.

### Não é permitido

A camada de apresentação **não deverá**:

* implementar regras de negócio;
* executar consultas diretas à base de dados;
* tomar decisões de domínio.

---

## 9.3 Application Layer

A Application Layer funciona como ponto de entrada do sistema.

É responsável por orquestrar os pedidos recebidos.

### Componentes

* Django REST Framework
* ViewSets
* API Views
* Serializers
* Authentication
* Permissions
* Rate Limiting

Responsabilidades:

* receber pedidos HTTP;
* validar autenticação;
* validar permissões;
* validar dados de entrada;
* encaminhar para os Services;
* devolver respostas normalizadas.

### Regra Fundamental

A Application Layer **não deverá conter regras de negócio**.

Toda a lógica pertence à Domain Layer.

---

## 9.4 Domain Layer

A Domain Layer representa o coração da plataforma.

É aqui que reside todo o conhecimento do negócio.

Esta camada deverá permanecer independente de frameworks e tecnologias específicas.

### Componentes

* Services
* Selectors
* Domain Models
* Validators
* Domain Events (futuro)

Responsabilidades:

* regras de negócio;
* validações de domínio;
* cálculos;
* fluxos operacionais;
* políticas do sistema.

Exemplos:

* Aprovar um Clube.
* Validar transferência de um Jogador.
* Encerrar uma Competição.
* Gerar Classificações.

Toda a inteligência da plataforma pertence a esta camada.

---

## 9.5 Infrastructure Layer

A Infrastructure Layer fornece serviços técnicos utilizados pelo domínio.

Exemplos:

* Cloudflare R2
* Redis
* Celery
* Email
* SMS
* Push Notifications
* PDF Generator
* Storage
* Logging

Esta camada nunca deverá conter regras de negócio.

Ela apenas disponibiliza recursos para as restantes camadas.

---

## 9.6 Data Layer

A Data Layer representa a persistência dos dados.

Tecnologia oficial:

* PostgreSQL

Responsabilidades:

* armazenamento;
* índices;
* integridade referencial;
* otimização de consultas;
* backups.

Nenhuma outra camada deverá executar SQL diretamente.

Todo o acesso deverá ocorrer através dos modelos, repositórios (quando existirem) ou Selectors.

---

# 10. Fluxo Geral da Aplicação

A comunicação deverá seguir sempre o seguinte fluxo:

```text
Utilizador
      │
      ▼
React Application
      │
      ▼
REST API
      │
      ▼
Authentication
      │
      ▼
Permissions
      │
      ▼
Service
      │
      ▼
Selector
      │
      ▼
Database
```

O fluxo inverso devolve os dados ao frontend.

Nenhum componente deverá ignorar este fluxo.

---

# 11. Arquitetura Física

A arquitetura física descreve como os componentes são distribuídos na infraestrutura.

## Visão Geral

```text
                    Internet
                        │
                        ▼
              Cloudflare DNS
                        │
                        ▼
             Cloudflare CDN / WAF
                        │
                        ▼
                    Nginx
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
 React Frontend                    Django API
                                        │
               ┌────────────────────────┼────────────────────────┐
               ▼                        ▼                        ▼
           PostgreSQL                Redis                  Celery
               │                        │                        │
               └───────────────┬────────┴───────────────┐
                               ▼                        ▼
                     Cloudflare R2             External Services
```

Cada componente possui responsabilidades específicas.

---

# 12. Componentes da Infraestrutura

## Cloudflare

Responsável por:

* DNS
* SSL
* CDN
* Cache
* WAF
* Proteção DDoS

Toda a comunicação externa deverá passar pelo Cloudflare.

---

## Nginx

Responsável por:

* Reverse Proxy
* Compressão
* Cache HTTP
* Headers de Segurança
* Servir ficheiros estáticos
* Encaminhamento de pedidos

O Nginx nunca deverá executar lógica de negócio.

---

## Frontend

Aplicação desenvolvida em:

* React
* TypeScript
* Vite

Responsabilidades:

* Interface
* Navegação
* Gestão de Estado
* Consumo da API

---

## Backend

Aplicação desenvolvida em:

* Django
* Django REST Framework

Responsabilidades:

* APIs
* Regras de Negócio
* Segurança
* Gestão de Dados

---

## PostgreSQL

Base de dados oficial.

Armazena:

* Organizações
* Clubes
* Jogadores
* Competições
* Estatísticas
* Utilizadores

---

## Redis

Responsável por:

* Cache
* Filas
* Sessões (quando aplicável)
* Rate Limiting
* Celery Broker

---

## Celery

Executa tarefas assíncronas.

Exemplos:

* envio de emails;
* geração de PDFs;
* notificações;
* processamento de imagens;
* importações e exportações.

---

## Cloudflare R2

Responsável pelo armazenamento de:

* fotografias;
* logótipos;
* banners;
* documentos;
* vídeos;
* relatórios.

O backend nunca deverá depender de armazenamento local em produção.

---

# 13. Fluxo de Comunicação

## Fluxo de Leitura

```text
Browser

↓

React

↓

API

↓

Service

↓

Selector

↓

PostgreSQL

↓

Service

↓

Serializer

↓

React
```

---

## Fluxo de Escrita

```text
Utilizador

↓

React

↓

API

↓

Serializer

↓

Service

↓

Models

↓

PostgreSQL

↓

Response
```

---

## Fluxo de Upload

```text
Utilizador

↓

React

↓

API

↓

Storage Service

↓

Cloudflare R2

↓

CDN URL

↓

Frontend
```

---

# 14. Regras Arquiteturais

Para preservar a consistência da plataforma, deverão ser respeitadas as seguintes regras:

1. A Presentation Layer nunca comunica diretamente com a Base de Dados.
2. A Domain Layer não depende do React, Django ou PostgreSQL.
3. Toda a lógica de negócio pertence aos Services.
4. Todas as consultas complexas pertencem aos Selectors.
5. Os ViewSets apenas orquestram pedidos e respostas.
6. Nenhum módulo deverá aceder diretamente aos modelos internos de outro módulo.
7. Toda a comunicação entre domínios deverá ocorrer através de contratos bem definidos.
8. Todos os serviços externos (Cloudflare, Email, Pagamentos, SMS) deverão estar encapsulados na Infrastructure Layer.

---

# 15. Benefícios da Arquitetura

A arquitetura adotada proporciona:

* Elevada modularidade.
* Facilidade de manutenção.
* Evolução incremental.
* Testabilidade.
* Escalabilidade horizontal.
* Baixo acoplamento.
* Alta coesão.
* Preparação para microsserviços no futuro.
* Facilidade de integração com aplicações móveis.
* Base sólida para crescimento internacional.

Esta arquitetura constitui a fundação técnica do Bolayetu e deverá orientar todas as decisões de implementação ao longo do ciclo de vida do produto.
