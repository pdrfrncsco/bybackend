# SECURITY ARCHITECTURE

**Documento:** `07_SECURITY_ARCHITECTURE.md`

**Versão:** 2.0.0

**Estado:** Documento Oficial de Arquitetura de Segurança

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define a arquitetura de segurança do Bolayetu.

O objetivo é proteger:

* utilizadores;
* organizações;
* clubes;
* jogadores;
* dados;
* APIs;
* infraestrutura.

A segurança é um requisito arquitetural e deverá estar presente em todas as fases do desenvolvimento.

---

# 2. Princípios de Segurança

Toda a plataforma deverá seguir os seguintes princípios:

* Security by Design
* Least Privilege
* Zero Trust
* Defense in Depth
* Secure by Default
* Auditability
* Data Isolation
* Privacy by Design

Nenhuma funcionalidade deverá comprometer estes princípios.

---

# 3. Arquitetura de Segurança

```text
                Browser / Mobile
                       │
                       ▼
             Cloudflare WAF + DDoS
                       │
                       ▼
                   Nginx HTTPS
                       │
                       ▼
                Django REST API
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
 Authentication   Authorization   Rate Limit
          │            │            │
          └────────────┼────────────┘
                       ▼
                 Business Services
                       ▼
                  PostgreSQL
```

Cada camada acrescenta um nível adicional de proteção.

---

# 4. Identidade

A identidade digital pertence exclusivamente ao módulo **Accounts**.

Cada utilizador possui:

* UUID
* Email
* Password Hash
* Estado da conta
* MFA (futuro)
* Último acesso
* Sessões ativas

Nunca armazenar palavras-passe em texto simples.

---

# 5. Autenticação

Modelo oficial:

**JWT + Refresh Token**

Fluxo:

```text
Login

↓

Access Token

↓

Refresh Token

↓

Protected APIs
```

Características:

* Access Token de curta duração.
* Refresh Token rotativo.
* Revogação suportada.
* Logout global.

---

# 6. Autorização

O sistema utilizará **RBAC (Role-Based Access Control)**.

Papéis base:

* Platform Admin
* Organization Admin
* Organization Manager
* Club Admin
* Club Manager
* Coach
* Player
* Fan

Cada papel possui permissões explícitas.

---

# 7. Permissões

As permissões seguem o princípio do menor privilégio.

Exemplos:

```text
competition.create

competition.update

competition.delete

club.manage

player.transfer

player.approve

news.publish
```

As permissões são avaliadas sempre no backend.

---

# 8. Segurança Multi-Tenant

Toda a segurança considera o contexto do Tenant.

Fluxo:

```text
Request

↓

Tenant Resolver

↓

Authentication

↓

Authorization

↓

Ownership

↓

Business Logic
```

Nenhum pedido será executado sem um Tenant válido.

---

# 9. Isolamento de Dados

É proibido:

* consultas sem contexto de Tenant;
* acesso cruzado entre organizações;
* reutilização de cache entre Tenants.

Todas as consultas deverão aplicar isolamento automaticamente.

---

# 10. Object Ownership

Além do RBAC, deverá existir validação de propriedade.

Exemplo:

Um Clube apenas poderá editar:

* os seus jogadores;
* as suas equipas;
* os seus documentos.

Nunca recursos de outro Clube.

---

# 11. Segurança das APIs

Todas as APIs deverão:

* utilizar HTTPS;
* exigir autenticação quando necessário;
* validar permissões;
* validar Tenant;
* validar ownership;
* devolver erros padronizados.

Versionamento obrigatório:

```text
/api/v1/
```

---

# 12. Rate Limiting

O Rate Limiting será aplicado por:

* IP
* Utilizador
* Tenant
* Endpoint

Exemplos:

* Login
* Recuperação de senha
* Uploads
* APIs públicas

Redis será utilizado para controlo das quotas.

---

# 13. Proteção contra Ataques

A plataforma deverá mitigar:

* SQL Injection
* XSS
* CSRF (quando aplicável)
* SSRF
* Clickjacking
* Brute Force
* Credential Stuffing
* Session Fixation
* Replay Attacks

Utilizar as proteções nativas do Django e complementar com configurações do Nginx e Cloudflare.

---

# 14. Gestão de Sessões

Sessões deverão permitir:

* revogação;
* encerramento remoto;
* expiração automática;
* histórico de dispositivos.

Cada utilizador poderá visualizar as sessões ativas.

---

# 15. Gestão de Palavras-passe

Regras mínimas:

* comprimento mínimo configurável;
* armazenamento com algoritmo seguro;
* histórico opcional;
* redefinição por email;
* bloqueio temporário após tentativas falhadas.

---

# 16. MFA (Planeado)

A arquitetura deverá permitir autenticação multifator.

Métodos previstos:

* TOTP
* Email OTP
* SMS OTP
* Aplicações autenticadoras

O desenho da autenticação não deverá impedir esta evolução.

---

# 17. Auditoria

Toda a atividade crítica deverá ser registada.

Exemplos:

* Login
* Logout
* Criação de competição
* Alteração de resultados
* Transferência de jogador
* Alteração de permissões
* Mudança de plano

Cada registo deverá incluir:

* utilizador;
* Tenant;
* ação;
* recurso;
* data/hora;
* endereço IP.

---

# 18. Proteção de Dados

Os dados serão classificados em níveis.

## Público

Informação acessível sem autenticação.

Exemplos:

* resultados;
* classificações;
* notícias públicas.

---

## Interno

Dados disponíveis apenas para utilizadores autenticados.

---

## Confidencial

Exemplos:

* documentos;
* contratos;
* dados financeiros.

---

## Restrito

Exemplos:

* palavras-passe;
* tokens;
* chaves de API;
* segredos da aplicação.

---

# 19. Uploads

Todos os uploads deverão passar por validações.

Verificar:

* tipo MIME;
* extensão;
* tamanho;
* conteúdo permitido.

Armazenamento:

Cloudflare R2

Nunca executar ficheiros enviados pelos utilizadores.

---

# 20. Segredos da Aplicação

Nunca armazenar segredos no código.

Utilizar variáveis de ambiente para:

* SECRET_KEY
* JWT_SECRET
* PostgreSQL
* Redis
* Cloudflare
* Email
* APIs externas

---

# 21. Logging

Os logs deverão ser estruturados.

Categorias:

* Segurança
* Sistema
* API
* Base de Dados
* Celery
* Infraestrutura

Informação sensível nunca deverá ser registada.

---

# 22. Monitorização

Monitorizar:

* tentativas de login;
* erros 401;
* erros 403;
* picos de tráfego;
* uploads suspeitos;
* falhas de autenticação;
* utilização anormal de APIs.

---

# 23. Backups

Backups deverão ser:

* automáticos;
* cifrados;
* testados regularmente;
* armazenados em local distinto da infraestrutura principal.

Definir políticas de retenção e recuperação.

---

# 24. Segurança DevOps

Obrigatório:

* HTTPS em todos os ambientes públicos.
* Docker atualizado.
* Dependências auditadas.
* Imagens base oficiais.
* Princípio do menor privilégio nos containers.
* Utilizadores não-root sempre que possível.

---

# 25. Segurança Frontend

O frontend deverá:

* armazenar tokens de forma segura;
* proteger rotas;
* limpar dados sensíveis ao terminar sessão;
* validar permissões de interface.

A segurança efetiva permanece sempre no backend.

---

# 26. Segurança da Base de Dados

Obrigatório:

* ligações autenticadas;
* privilégios mínimos para utilizadores da BD;
* backups;
* índices adequados;
* auditoria de operações críticas.

Nunca expor a base de dados diretamente à Internet.

---

# 27. Segurança Cloudflare

Utilizar:

* WAF
* SSL/TLS
* Rate Limiting
* Bot Protection
* DDoS Protection
* CDN
* DNS Security

Cloudflare constitui a primeira linha de defesa da plataforma.

---

# 28. Resposta a Incidentes

A plataforma deverá possuir procedimentos para:

* deteção;
* contenção;
* erradicação;
* recuperação;
* análise pós-incidente.

Todos os incidentes relevantes deverão ser registados.

---

# 29. Regras Obrigatórias

É obrigatório:

* autenticação em todas as APIs privadas;
* autorização baseada em RBAC;
* validação de ownership;
* isolamento entre Tenants;
* auditoria das operações críticas;
* utilização exclusiva de HTTPS.

É proibido:

* credenciais no código-fonte;
* permissões implícitas;
* acesso direto entre Tenants;
* armazenamento de dados sensíveis em texto simples.

---

# 30. Architecture Decision Records

## ADR-006 — Modelo de Segurança

**Decisão**

Adotar uma arquitetura baseada em:

* JWT Authentication
* RBAC
* Tenant Isolation
* Object Ownership
* Audit Logging
* Defense in Depth

**Justificação**

Este modelo oferece elevada escalabilidade, compatibilidade com aplicações web e móveis, forte isolamento entre organizações e uma base sólida para evolução futura com MFA, APIs públicas e integrações externas.

Esta decisão aplica-se a toda a plataforma Bolayetu e deverá orientar qualquer desenvolvimento relacionado com autenticação, autorização e proteção de dados.
