# MULTITENANT ARCHITECTURE

**Documento:** `06_MULTITENANT_ARCHITECTURE.md`

**Versão:** 2.0.0

**Estado:** Documento Oficial de Arquitetura Multi-Tenant

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define a arquitetura Multi-Tenant do Bolayetu.

O objetivo é garantir que múltiplas organizações utilizem a mesma plataforma, mantendo isolamento total dos dados, identidade própria e configurações independentes.

Toda a arquitetura SaaS da plataforma deverá seguir este documento.

---

# 2. Conceito de Tenant

Um Tenant representa uma organização independente dentro da plataforma.

Pode representar:

* Federação Nacional
* Associação Provincial
* Liga
* Organizador de Campeonato
* Academia (versões futuras)

Cada Tenant funciona como um ambiente lógico isolado.

---

# 3. Objetivos

A arquitetura deverá permitir:

* isolamento de dados;
* branding independente;
* utilizadores independentes;
* configurações próprias;
* subscrição própria;
* domínio próprio;
* crescimento horizontal.

---

# 4. Modelo Arquitetural

O Bolayetu utilizará:

## Shared Database

Uma única base de dados PostgreSQL.

---

## Shared Schema

Um único schema PostgreSQL.

---

## Tenant Context

Cada registo pertence a um Tenant.

```text id="l3m9yk"
Database

↓

Tenant

↓

Organization

↓

Business Data
```

---

# 5. Organização Geral

```text id="a1hs2v"
Bolayetu

│

├── Tenant A (FAF)

│      ├── Competitions

│      ├── Clubs

│      ├── Players

│      └── Users

│

├── Tenant B (APF Luanda)

│      ├── Competitions

│      ├── Clubs

│      ├── Players

│      └── Users

│

└── Tenant C (Girabola)

       ├── Competitions

       ├── Clubs

       ├── Players

       └── Users
```

Todos utilizam a mesma infraestrutura.

---

# 6. Identificação do Tenant

O Tenant será identificado através do subdomínio.

Exemplos:

```text id="7wj1pq"
faf.bolayetu.com

girabola.bolayetu.com

apf-luanda.bolayetu.com

academy.bolayetu.com
```

O domínio principal:

```text id="yc6n4z"
bolayetu.com
```

será utilizado para:

* Landing Page
* Marketing
* Login Global
* Registo

---

# 7. Resolução do Tenant

Fluxo:

```text id="u2mjlwm"
Request

↓

Host Header

↓

Tenant Resolver

↓

Tenant Context

↓

Authentication

↓

Permissions

↓

Business Logic
```

Todo o pedido deverá possuir um Tenant ativo antes da execução de qualquer regra de negócio.

---

# 8. Tenant Resolver

Responsabilidades:

* identificar subdomínio;
* localizar Tenant;
* validar estado;
* carregar configurações;
* disponibilizar Tenant ao contexto da requisição.

Exemplo:

```text id="u6lg5k"
Host:

faf.bolayetu.com

↓

Tenant

↓

FAF
```

---

# 9. Estrutura do Tenant

Cada Tenant deverá possuir:

* Nome
* Slug
* Subdomínio
* Logótipo
* Tema
* Idioma
* Fuso Horário
* País
* Estado
* Plano
* Configurações

---

# 10. Branding

Cada Tenant poderá personalizar:

* logótipo;
* favicon;
* cores;
* banner;
* nome público;
* contactos.

A personalização nunca deverá afetar outros Tenants.

---

# 11. Isolamento

Todo o isolamento deverá ocorrer automaticamente.

Nenhuma consulta deverá devolver dados pertencentes a outro Tenant.

Fluxo:

```text id="hij2m6"
Request

↓

Tenant

↓

Query Filter

↓

Database
```

O programador não deverá precisar adicionar filtros manualmente em todas as consultas.

---

# 12. Tenant Middleware

O middleware deverá:

* resolver Tenant;
* validar domínio;
* validar estado;
* anexar Tenant ao request;
* disponibilizar Tenant aos Services.

---

# 13. Tenant Context

Durante todo o ciclo da requisição existirá um contexto.

```text id="jnbr7v"
Request

↓

Tenant Context

↓

Services

↓

Selectors

↓

Models
```

Todo módulo poderá consultar o Tenant ativo.

---

# 14. Autenticação

Fluxo:

```text id="olz8y6"
Login

↓

JWT

↓

Tenant

↓

Role

↓

Permissions
```

Um utilizador nunca poderá autenticar-se num Tenant ao qual não pertence.

---

# 15. Utilizadores

Os utilizadores pertencem a um Tenant.

Um utilizador poderá, futuramente, possuir acesso a múltiplos Tenants, mediante permissões explícitas.

Exemplo:

```text id="zt5quz"
Administrador FAF

↓

FAF

Administrador APF

↓

APF Luanda
```

---

# 16. Perfis

Dentro de cada Tenant existirão perfis.

Exemplos:

* Organização
* Clube
* Jogador
* Adepto

Os perfis são independentes entre Tenants.

---

# 17. Organização

Cada Tenant possui apenas uma Organização principal.

```text id="r6z6jr"
Tenant

↓

Organization

↓

Competitions

↓

Clubs
```

---

# 18. Clubes

Cada Clube pertence a uma Organização.

Consequentemente pertence ao mesmo Tenant.

Nunca poderá existir um Clube associado simultaneamente a dois Tenants.

---

# 19. Jogadores

O Jogador possui identidade global na plataforma.

Os vínculos desportivos são específicos de cada Tenant.

Exemplo:

```text id="2q1z5l"
Player

↓

Career

↓

Club

↓

Tenant
```

O histórico da carreira é preservado mesmo após mudanças de clube.

---

# 20. APIs

Todas as APIs deverão funcionar dentro do contexto do Tenant.

```text id="h57tnm"
/api/v1/clubs

↓

Tenant

↓

Response
```

Nunca devolver recursos externos ao Tenant.

---

# 21. Permissões

As permissões deverão considerar:

* Tenant;
* Role;
* Ownership;
* Estado da subscrição.

---

# 22. Subscrições

Cada Tenant possui:

* plano;
* faturação;
* limite de utilizadores;
* limite de armazenamento;
* funcionalidades disponíveis.

Exemplo:

```text id="fbcm4v"
Starter

Professional

Enterprise
```

---

# 23. Armazenamento

Todos os ficheiros deverão ser organizados por Tenant.

Exemplo:

```text id="rg5h2u"
r2/

faf/

clubs/

players/

documents/

logos/
```

---

# 24. Cache

As chaves de cache deverão incluir o identificador do Tenant.

Exemplo:

```text id="uiz4ic"
tenant:12:clubs

tenant:12:standings

tenant:12:statistics
```

Evita colisões entre organizações.

---

# 25. Logging

Todos os logs deverão identificar:

* Tenant;
* utilizador;
* módulo;
* ação;
* data.

---

# 26. Escalabilidade

A arquitetura deverá suportar:

* milhares de Tenants;
* centenas de milhares de Clubes;
* milhões de Jogadores;
* milhões de partidas.

Sem necessidade de alterar a estratégia Multi-Tenant.

---

# 27. Segurança

É obrigatório garantir:

* isolamento completo entre Tenants;
* validação automática do Tenant;
* autenticação contextual;
* proteção contra acesso cruzado;
* auditoria das operações.

---

# 28. Recuperação

Cada Tenant poderá possuir:

* backup lógico;
* exportação de dados;
* recuperação independente (quando suportado pela estratégia operacional).

---

# 29. Futuras Evoluções

A arquitetura foi concebida para suportar:

* Domínios personalizados (`faf.ao`);
* White Label;
* Multi-país;
* Multi-idioma;
* Multi-moeda;
* APIs públicas por Tenant;
* Aplicações móveis específicas por Organização.

---

# 30. Regras Obrigatórias

É obrigatório:

* resolver o Tenant antes da autenticação;
* anexar o Tenant ao contexto da requisição;
* filtrar automaticamente todas as consultas por Tenant;
* isolar ficheiros, cache e configurações;
* impedir qualquer acesso entre Tenants.

É proibido:

* consultas sem contexto de Tenant;
* partilha de dados entre organizações sem autorização explícita;
* armazenamento de configurações específicas do Tenant em código-fonte.

---

# 31. Architecture Decision Record (ADR)

## ADR-002 — Estratégia Multi-Tenant

**Decisão**

Adotar o modelo **Shared Database + Shared Schema + Tenant Context**.

**Justificação**

* Menor custo operacional.
* Escalabilidade adequada para milhares de organizações.
* Facilidade de manutenção.
* Simplicidade de backups.
* Compatibilidade com PostgreSQL, Django e Docker.
* Evolução futura para arquiteturas mais distribuídas, se necessário.

Esta decisão é considerada estruturante para toda a plataforma e apenas poderá ser alterada mediante um novo ADR aprovado.
