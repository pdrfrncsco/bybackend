# DEVOPS ARCHITECTURE

**Documento:** `09_DEVOPS_ARCHITECTURE.md`

**Versão:** 2.0.0

**Estado:** Documento Oficial de Arquitetura DevOps

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define a arquitetura DevOps oficial do Bolayetu.

O objetivo é garantir:

* ambientes consistentes;
* deploy automatizado;
* elevada disponibilidade;
* escalabilidade;
* observabilidade;
* recuperação rápida;
* segurança operacional.

Toda a infraestrutura deverá seguir este documento.

---

# 2. Princípios

A estratégia DevOps do Bolayetu baseia-se em:

* Infrastructure as Code (IaC)
* Docker First
* GitOps
* CI/CD
* Immutable Infrastructure
* Cloud Native
* Zero Downtime Deployments
* Observabilidade

---

# 3. Arquitetura Geral

```text
                    Developers
                         │
                         ▼
                    GitHub Repository
                         │
                         ▼
                  GitHub Actions (CI)
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         Backend Image         Frontend Build
              │                     │
              └──────────┬──────────┘
                         ▼
                   Deploy Pipeline
                         │
                         ▼
                    Ubuntu Server
                         │
      ┌──────────────────┼──────────────────┐
      ▼                  ▼                  ▼
    Nginx             Docker             Cloudflare
      │                  │                  │
      ▼                  ▼                  ▼
 React SPA      Django + Celery + Redis    CDN/WAF
                         │
                         ▼
                    PostgreSQL
                         │
                         ▼
                  Cloudflare R2
```

---

# 4. Ambientes

A plataforma deverá possuir ambientes independentes.

```text
Development

↓

Testing

↓

Staging

↓

Production
```

Cada ambiente utiliza configurações próprias.

---

# 5. Estrutura dos Servidores

```text
/opt/bolayetu/

backend/

frontend/

docker/

nginx/

logs/

backups/

scripts/

.env
```

Toda a infraestrutura deverá seguir uma estrutura previsível.

---

# 6. Docker

Todos os serviços deverão executar em containers.

Containers previstos:

```text
nginx

frontend

backend

postgres

redis

celery

celery-beat

flower (opcional)

watchtower (opcional)
```

Cada serviço possui uma responsabilidade única.

---

# 7. Docker Compose

A orquestração local será feita através do Docker Compose.

Separar os ficheiros por ambiente:

```text
docker-compose.dev.yml

docker-compose.test.yml

docker-compose.prod.yml
```

---

# 8. Git Workflow

Estratégia oficial:

```text
main

develop

feature/*

release/*

hotfix/*
```

Branches temporárias deverão ser eliminadas após merge.

---

# 9. CI (Continuous Integration)

A cada Pull Request deverão ser executados:

* instalação de dependências;
* lint;
* testes unitários;
* testes de integração;
* verificação de tipos TypeScript;
* build frontend;
* migrações (dry run).

Falhas bloqueiam o merge.

---

# 10. CD (Continuous Delivery)

Após aprovação:

1. Build da imagem Docker.
2. Publicação da imagem.
3. Atualização do ambiente.
4. Migrações.
5. Health Check.
6. Limpeza de versões antigas.

---

# 11. Deploy

Fluxo oficial:

```text
Git Push

↓

GitHub Actions

↓

Docker Build

↓

Servidor

↓

Docker Pull

↓

Restart

↓

Health Check
```

Deploys deverão ser automatizados.

---

# 12. Configuração

Toda configuração deverá utilizar variáveis de ambiente.

Exemplos:

* SECRET_KEY
* DATABASE_URL
* REDIS_URL
* R2_BUCKET
* CLOUDFLARE_ACCOUNT_ID
* EMAIL_HOST
* JWT_SECRET

Nunca armazenar segredos no código.

---

# 13. Nginx

Responsabilidades:

* Reverse Proxy
* SSL
* Compressão
* Cache
* Headers
* HTTP/2
* HTTP/3 (quando disponível)

---

# 14. Cloudflare

Utilizar:

* DNS
* CDN
* SSL
* WAF
* Rate Limiting
* DDoS Protection
* Cache Rules

Todo o tráfego externo deverá passar pelo Cloudflare.

---

# 15. PostgreSQL

Políticas:

* Backups automáticos.
* Índices monitorizados.
* Vacuum periódico.
* Atualizações planeadas.

Nunca expor a base de dados diretamente à Internet.

---

# 16. Redis

Utilização:

* cache;
* broker do Celery;
* rate limiting;
* armazenamento temporário.

Nunca utilizar Redis para persistência permanente.

---

# 17. Celery

Responsável por tarefas assíncronas.

Exemplos:

* emails;
* notificações;
* thumbnails;
* exportações;
* relatórios;
* processamento de vídeos.

---

# 18. Cloudflare R2

Responsável pelo armazenamento permanente de ficheiros.

O backend nunca deverá utilizar armazenamento local em produção.

---

# 19. Observabilidade

Monitorizar:

* CPU
* RAM
* Disco
* Containers
* PostgreSQL
* Redis
* Celery
* APIs
* Uploads
* Tempo de resposta

---

# 20. Logging

Todos os serviços deverão gerar logs estruturados.

Categorias:

* Application
* API
* Database
* Celery
* Nginx
* Security
* System

Os logs deverão possuir rotação automática.

---

# 21. Alertas

Alertas para:

* utilização elevada de CPU;
* utilização elevada de memória;
* falhas de deploy;
* falhas de backup;
* indisponibilidade da API;
* erros 5xx;
* fila Celery acumulada.

---

# 22. Health Checks

Cada serviço deverá possuir endpoint de verificação.

Exemplo:

```text
/api/v1/health

/api/v1/readiness

/api/v1/liveness
```

---

# 23. Backup

Backups automáticos para:

* PostgreSQL
* Configurações
* Assets críticos (metadados)

Definir políticas de retenção:

* diário;
* semanal;
* mensal.

Testar regularmente a recuperação.

---

# 24. Escalabilidade

A arquitetura deverá permitir:

* múltiplos workers Django;
* múltiplos workers Celery;
* múltiplas instâncias frontend;
* balanceamento de carga;
* cache distribuída.

Sem alterações na lógica de negócio.

---

# 25. Segurança Operacional

Obrigatório:

* SSH por chave pública;
* firewall configurada;
* atualizações de segurança;
* utilizadores sem privilégios excessivos;
* acesso administrativo auditado.

---

# 26. Gestão de Dependências

Backend:

* `uv` ou `pip-tools` (recomendado) para gestão de dependências.
* Atualizações periódicas.
* Auditoria de vulnerabilidades.

Frontend:

* `npm` ou `pnpm` (preferencial para projetos grandes).
* Atualizações controladas.
* Auditoria automática.

---

# 27. Versionamento

Cada release deverá possuir:

* número de versão;
* changelog;
* tag Git;
* imagem Docker correspondente.

---

# 28. Disaster Recovery

Plano mínimo:

* recuperação da base de dados;
* recuperação de configurações;
* reconstrução dos containers;
* restauro dos metadados;
* validação pós-recuperação.

Definir RPO e RTO conforme os requisitos do negócio.

---

# 29. Infraestrutura como Código

A infraestrutura deverá evoluir para IaC.

Ferramentas recomendadas:

* Docker Compose (atual)
* Terraform (futuro)
* Ansible (provisionamento)
* GitHub Actions (automação)

---

# 30. Regras Obrigatórias

É obrigatório:

* utilizar Docker em todos os ambientes;
* automatizar deploys;
* executar testes antes de publicar;
* monitorizar todos os serviços;
* utilizar HTTPS;
* manter backups automáticos;
* documentar alterações de infraestrutura.

É proibido:

* deploy manual em produção;
* alterações diretas em produção sem registo;
* armazenamento de segredos no repositório;
* containers executados como utilizador root quando evitável.

---

# 31. Architecture Decision Records

## ADR-009 — Estratégia DevOps

**Decisão**

Adotar uma arquitetura baseada em:

* Docker
* GitHub Actions
* Nginx
* Cloudflare
* PostgreSQL
* Redis
* Celery
* Cloudflare R2

**Justificação**

Esta arquitetura proporciona:

* consistência entre ambientes;
* deploy automatizado;
* elevada disponibilidade;
* escalabilidade horizontal;
* facilidade de manutenção;
* redução do risco operacional.

Todas as futuras decisões de infraestrutura deverão manter compatibilidade com esta arquitetura ou ser formalizadas através de um novo ADR.
