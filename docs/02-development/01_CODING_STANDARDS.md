# CODING STANDARDS

**Documento:** `01_CODING_STANDARDS.md`

**Versão:** 2.0.0

**Estado:** Documento Oficial de Normas de Desenvolvimento

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define os padrões oficiais de desenvolvimento do Bolayetu.

O objetivo é garantir:

* consistência do código;
* elevada legibilidade;
* facilidade de manutenção;
* escalabilidade;
* qualidade técnica.

Estas normas aplicam-se a todo o código do projeto.

---

# 2. Princípios

Todo o desenvolvimento deverá seguir os seguintes princípios:

* Clean Code
* SOLID
* DRY (Don't Repeat Yourself)
* KISS (Keep It Simple)
* YAGNI (You Aren't Gonna Need It)
* Domain Driven Design (DDD)
* Convention over Configuration

---

# 3. Idioma

## Código

Todo o código deverá ser escrito em **inglês**.

Exemplos:

```python
Player
Competition
Registration
Transfer
```

---

## Comentários

Comentários técnicos deverão ser escritos em inglês.

Documentação do projeto poderá ser escrita em português.

---

## Interface

A aplicação suportará internacionalização (i18n).

Nenhum texto deverá ser escrito diretamente nos componentes.

---

# 4. Convenções Gerais

## Nomes

Utilizar nomes claros.

Bom exemplo:

```python
player_registration
```

Mau exemplo:

```python
pr
```

---

## Funções

Utilizar verbos.

```python
create_player()

approve_registration()

calculate_standings()
```

---

## Classes

Sempre em PascalCase.

```python
PlayerService

CompetitionSerializer

TransferPolicy
```

---

## Variáveis

snake_case (Python)

camelCase (TypeScript)

---

## Constantes

UPPER_CASE

```python
MAX_PLAYERS
DEFAULT_LANGUAGE
```

---

# 5. Python

Seguir integralmente a PEP 8.

Utilizar:

* type hints;
* docstrings quando necessário;
* imports organizados.

Exemplo:

```python
def create_player(
    *,
    club: Club,
    data: PlayerCreateDTO,
) -> Player:
    ...
```

---

# 6. Django

Cada módulo deverá seguir:

```text
models/
serializers/
selectors/
services/
permissions/
validators/
tasks/
signals/
tests/
```

Nunca colocar lógica de negócio nas Views.

---

# 7. Models

Os Models representam apenas persistência.

Permitido:

* campos;
* propriedades simples;
* métodos utilitários.

Proibido:

* chamadas HTTP;
* emails;
* regras complexas;
* notificações.

---

# 8. Services

Toda regra de negócio pertence aos Services.

Exemplo:

```python
PlayerService.register()

TransferService.approve()

CompetitionService.publish()
```

---

# 9. Selectors

Todos os Selectors deverão ser apenas leitura.

Nunca modificar dados.

---

# 10. Serializers

Responsáveis apenas por:

* validação;
* transformação;
* serialização.

Nunca executar lógica de negócio.

---

# 11. Views

As Views deverão:

* autenticar;
* autorizar;
* chamar Services;
* devolver respostas.

Máximo recomendado:

**50 linhas por método.**

---

# 12. Frontend

Utilizar:

* React
* TypeScript
* Functional Components

Nunca utilizar componentes de classe.

---

# 13. Componentes

Cada componente deverá possuir apenas uma responsabilidade.

Máximo recomendado:

300 linhas.

Se exceder esse limite, dividir.

---

# 14. Hooks

Todo Hook deverá iniciar com:

```text
use
```

Exemplo:

```typescript
usePlayers()

useCompetition()

useNotifications()
```

---

# 15. APIs

Nunca utilizar fetch diretamente.

Sempre utilizar:

```typescript
PlayerService

CompetitionService

ClubService
```

---

# 16. Gestão de Estado

Servidor:

TanStack Query.

Global:

Zustand.

Local:

useState.

Evitar duplicação de estado.

---

# 17. Estilos

Utilizar exclusivamente:

TailwindCSS.

Nunca utilizar:

* CSS inline;
* Bootstrap;
* jQuery.

Componentes reutilizáveis deverão utilizar o Design System oficial.

---

# 18. TypeScript

Evitar:

```typescript
any
```

Sempre utilizar interfaces ou tipos explícitos.

Exemplo:

```typescript
interface Player {
    id: string;
    name: string;
}
```

---

# 19. Tratamento de Erros

Nunca ignorar exceções.

Backend:

Utilizar exceções específicas.

Frontend:

Apresentar mensagens amigáveis ao utilizador.

---

# 20. Logging

Registar apenas eventos relevantes.

Nunca registar:

* palavras-passe;
* tokens;
* dados sensíveis.

---

# 21. Testes

Cada nova funcionalidade deverá incluir testes.

Backend:

* Models
* Services
* APIs
* Permissions

Frontend:

* Components
* Hooks
* Services

Cobertura mínima recomendada:

80%.

---

# 22. Git

Commits pequenos.

Mensagem no formato:

```text
feat(players): add player registration

fix(auth): refresh token validation

refactor(clubs): simplify approval flow
```

---

# 23. Pull Requests

Cada PR deverá:

* resolver um problema específico;
* possuir descrição;
* referenciar Issue (quando existir);
* passar todos os testes.

---

# 24. Documentação

Todo módulo deverá possuir:

* descrição;
* responsabilidades;
* dependências;
* exemplos de utilização.

---

# 25. Performance

Evitar:

* consultas N+1;
* componentes demasiado grandes;
* renderizações desnecessárias;
* duplicação de chamadas à API.

---

# 26. Segurança

Nunca confiar no frontend.

Toda validação crítica deverá existir no backend.

Nunca expor:

* segredos;
* credenciais;
* tokens;
* chaves privadas.

---

# 27. Refatoração

Antes de adicionar código novo, verificar se existe implementação reutilizável.

Preferir reutilização à duplicação.

---

# 28. Dependências

Antes de adicionar uma biblioteca:

1. Resolve um problema real?
2. É amplamente mantida?
3. É compatível com a stack?
4. Aumenta significativamente o tamanho do projeto?
5. Existe alternativa mais simples?

Toda nova dependência deverá ser justificada.

---

# 29. Estrutura dos Ficheiros

Backend:

```text
apps/
core/
common/
config/
```

Frontend:

```text
features/
components/
layouts/
hooks/
services/
store/
```

A estrutura deverá permanecer consistente.

---

# 30. Revisão de Código

Antes de aprovar um Pull Request, verificar:

* Legibilidade
* Performance
* Segurança
* Testes
* Convenções
* Documentação
* Reutilização

---

# 31. Regras Obrigatórias

É obrigatório:

* utilizar TypeScript em todo o frontend;
* utilizar tipagem em Python;
* escrever testes;
* reutilizar componentes;
* documentar decisões importantes;
* seguir a arquitetura oficial.

É proibido:

* lógica de negócio nas Views;
* chamadas HTTP dentro de componentes React;
* duplicação de código;
* utilização de `any` sem justificação;
* código comentado permanentemente;
* credenciais no repositório.

---

# 32. Ferramentas Oficiais

## Backend

* Ruff (lint e formatação)
* Black (caso Ruff não cubra todos os cenários)
* MyPy
* Pytest

## Frontend

* ESLint
* Prettier
* TypeScript
* Vitest
* React Testing Library

## Qualidade

* Husky
* lint-staged
* Commitlint

Todos estes processos deverão ser executados automaticamente antes do commit ou durante a integração contínua.

---

# 33. Architecture Decision Record

## ADR-011 — Normas de Desenvolvimento

**Decisão**

Adotar um padrão único de desenvolvimento baseado em Clean Code, SOLID, DDD e ferramentas automáticas de validação.

**Justificação**

* Melhora a qualidade do código.
* Reduz dívida técnica.
* Facilita onboarding de novos programadores.
* Aumenta a consistência entre backend e frontend.
* Simplifica revisões de código e manutenção.

Estas normas são obrigatórias para todo o código produzido no Bolayetu e deverão ser revistas apenas através de um novo ADR aprovado.
