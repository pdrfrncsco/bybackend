# IMPLEMENTATION GUIDE FOR LLMS

**Documento:** `01_IMPLEMENTATION_GUIDE_FOR_LLMS.md`

**Versão:** 1.0.0

**Projeto:** Bolayetu

---

# Objetivo

Este documento define as regras obrigatórias que qualquer Large Language Model (LLM), agente de IA ou assistente de programação deve seguir durante o desenvolvimento do Bolayetu.

Nenhuma implementação deverá ignorar este documento.

---

# O Bolayetu é um produto de longo prazo

O Bolayetu não é um projeto de demonstração.

É uma plataforma SaaS de gestão do ecossistema do futebol, preparada para utilização por:

* Federações
* Associações
* Ligas
* Clubes
* Jogadores
* Adeptos
* Parceiros

Toda implementação deverá privilegiar escalabilidade, manutenção e reutilização.

---

# Ordem obrigatória de leitura

Antes de implementar qualquer funcionalidade, a LLM deverá estudar os seguintes documentos.

```text
00_PLATFORM_GUIDE.md

01_SYSTEM_ARCHITECTURE.md

02_BUSINESS_ARCHITECTURE.md

03_DATABASE_ARCHITECTURE.md

04_BACKEND_ARCHITECTURE.md

05_FRONTEND_ARCHITECTURE.md

06_MULTITENANT_ARCHITECTURE.md

06A_GLOBAL_AND_TENANT_DOMAIN.md

07_SECURITY_ARCHITECTURE.md

08_MEDIA_STORAGE_ARCHITECTURE.md

08A_DIGITAL_ASSET_MANAGEMENT.md

09_DEVOPS_ARCHITECTURE.md

10_EVENTS_AND_WORKFLOWS.md

01_CODING_STANDARDS.md

02_BACKEND_GUIDE.md

03_FRONTEND_GUIDE.md

04_API_GUIDELINES.md
```

Nenhuma implementação deverá contradizer estes documentos.

---

# Nunca inventar arquitetura

A IA nunca deverá:

* inventar novos padrões;
* alterar estrutura dos módulos;
* alterar responsabilidades;
* criar novas convenções.

Caso exista conflito entre documentos, deverá parar e solicitar decisão humana.

---

# Implementação incremental

Cada tarefa deverá implementar apenas um pequeno conjunto de funcionalidades.

Exemplo:

✔ Criar Models.

✔ Criar Migrations.

✔ Criar Services.

✔ Criar Selectors.

✔ Criar API.

✔ Criar Frontend.

Nunca implementar vários domínios ao mesmo tempo.

---

# Não alterar documentação

A documentação representa a verdade oficial.

O código deve adaptar-se à documentação.

Nunca o contrário.

---

# Nunca simplificar arquitetura

Mesmo que uma solução simples pareça funcionar...

A IA deverá seguir rigorosamente:

* DDD
* Services
* Selectors
* Multi-Tenant
* RBAC
* MediaAsset
* Event Driven

---

# Ordem oficial de desenvolvimento

Sempre seguir:

```text
Database

↓

Backend

↓

API

↓

Frontend

↓

Tests

↓

Documentation
```

Nunca começar pelo frontend.

---

# Estrutura dos Commits

Cada implementação deverá corresponder a uma única responsabilidade.

Exemplos:

feat(players): create player models

feat(players): implement player services

feat(players): create player api

feat(players): implement frontend pages

---

# Nunca criar código morto

Não criar:

* código não utilizado;
* funcionalidades incompletas;
* TODO permanentes;
* comentários desnecessários.

---

# Obrigatório

Toda implementação deverá possuir:

* tipagem;
* testes;
* documentação;
* tratamento de erros;
* validação;
* permissões.

---

# Não utilizar atalhos

Nunca colocar:

* lógica nas Views;
* lógica nos Serializers;
* chamadas HTTP em componentes React;
* SQL manual quando o ORM resolve o problema.

---

# Antes de escrever código

A IA deverá responder mentalmente:

1. Que domínio estou a implementar?

2. Que documentos regulam este domínio?

3. Existe implementação semelhante?

4. Esta solução respeita DDD?

5. Respeita Multi-Tenant?

6. Respeita RBAC?

7. Respeita MediaAsset?

8. Respeita Event Driven?

Se alguma resposta for negativa...

A implementação deverá ser revista antes de continuar.

---

# Critérios de aceitação

Uma tarefa apenas estará concluída quando possuir:

✔ Código

✔ Testes

✔ Documentação

✔ APIs

✔ Tipagem

✔ Validação

✔ Permissões

✔ Logs

✔ Eventos

✔ Cobertura mínima definida pelo projeto

---

# Objetivo Final

Todas as implementações deverão aproximar o Bolayetu de uma plataforma Football Operating System (Football OS), modular, escalável, segura e preparada para expansão internacional.
