# EVENTS AND WORKFLOWS

**Documento:** `10_EVENTS_AND_WORKFLOWS.md`

**Versão:** 2.0.0

**Estado:** Documento Oficial de Eventos e Fluxos de Trabalho

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define a arquitetura de eventos e workflows do Bolayetu.

O objetivo é estabelecer como os diferentes módulos da plataforma interagem entre si, distinguindo operações síncronas de operações assíncronas e definindo eventos de domínio reutilizáveis.

Este documento complementa:

* 02_BUSINESS_ARCHITECTURE.md
* 04_BACKEND_ARCHITECTURE.md
* 06_MULTITENANT_ARCHITECTURE.md

---

# 2. Conceitos

## Workflow

Um workflow representa uma sequência de passos necessários para concluir um processo de negócio.

Exemplos:

* Registo de Organização
* Inscrição de Clube
* Transferência de Jogador
* Encerramento de Competição

---

## Evento

Um evento representa algo que aconteceu no domínio.

Exemplos:

* PlayerRegistered
* CompetitionCreated
* MatchFinished

Eventos nunca executam lógica de negócio.

Eles notificam outros módulos.

---

# 3. Princípios

Toda a comunicação deverá seguir:

* Baixo acoplamento
* Alta coesão
* Idempotência
* Rastreabilidade
* Reutilização
* Processamento assíncrono quando apropriado

---

# 4. Arquitetura

```text id="9jxj4n"
Frontend

↓

API

↓

Service

↓

Business Event

↓

Event Dispatcher

↓

Subscribers

↓

Celery Tasks

↓

Notifications
```

O Service executa a regra de negócio.

O Evento apenas comunica o resultado.

---

# 5. Categorias de Eventos

## Domain Events

Representam alterações de negócio.

Exemplos:

* ClubApproved
* PlayerTransferred
* MatchStarted

---

## System Events

Relacionados com infraestrutura.

Exemplos:

* BackupCompleted
* CacheCleared
* HealthCheckFailed

---

## Integration Events

Utilizados para integração com serviços externos.

Exemplos:

* PaymentConfirmed
* EmailDelivered
* WebhookReceived

---

# 6. Estrutura Recomendada

```text id="lgkpy8"
core/

events/

dispatcher.py

base.py

handlers/

subscribers/

publishers/
```

Cada módulo poderá possuir eventos próprios.

---

# 7. Convenção de Nomes

Utilizar verbos no passado.

Exemplos:

```text id="3zjlwm"
PlayerCreated

PlayerUpdated

PlayerTransferred

ClubApproved

CompetitionPublished

MatchFinished
```

---

# 8. Fluxo Geral

```text id="8u0m7j"
Request

↓

Service

↓

Database Commit

↓

Publish Event

↓

Subscribers

↓

Tasks

↓

Notifications
```

Os eventos apenas são publicados após a confirmação da transação.

---

# 9. Workflow de Onboarding da Organização

```text id="b2q91p"
Criar Conta

↓

Validar Email

↓

Criar Tenant

↓

Criar Organização

↓

Criar Administrador

↓

Configurar Branding

↓

Selecionar Plano

↓

Dashboard
```

Eventos:

* UserRegistered
* TenantCreated
* OrganizationCreated
* SubscriptionActivated

---

# 10. Workflow do Clube

```text id="jlwm7a"
Criar Clube

↓

Submeter Documentos

↓

Solicitar Afiliação

↓

Avaliação

↓

Aprovação

↓

Participação em Competições
```

Eventos:

* ClubCreated
* ClubSubmitted
* ClubApproved
* ClubRejected

---

# 11. Workflow do Jogador

```text id="91v1el"
Criar Perfil

↓

Completar Dados

↓

Enviar Documentos

↓

Solicitar Vínculo

↓

Aprovação

↓

Registo na Competição
```

Eventos:

* PlayerCreated
* PlayerProfileCompleted
* PlayerRegistrationRequested
* PlayerRegistered

---

# 12. Workflow da Competição

```text id="qvbd1q"
Criar Competição

↓

Publicar Regulamento

↓

Abrir Inscrições

↓

Receber Clubes

↓

Gerar Calendário

↓

Iniciar Época

↓

Encerrar Competição
```

Eventos:

* CompetitionCreated
* RegistrationOpened
* FixtureGenerated
* CompetitionStarted
* CompetitionFinished

---

# 13. Workflow da Partida

```text id="lq6d1j"
Criar Partida

↓

Escalações

↓

Início

↓

Eventos

↓

Fim

↓

Atualizar Estatísticas

↓

Atualizar Classificação

↓

Notificações
```

Eventos:

* MatchCreated
* MatchStarted
* GoalScored
* CardIssued
* PlayerSubstituted
* MatchFinished

---

# 14. Workflow de Transferência

```text id="3h7mrl"
Pedido

↓

Clube Atual

↓

Novo Clube

↓

Aprovação

↓

Atualizar Registo

↓

Atualizar Carreira
```

Eventos:

* TransferRequested
* TransferApproved
* PlayerTransferred

---

# 15. Workflow de Subscrição

```text id="wyjlwm"
Selecionar Plano

↓

Pagamento

↓

Confirmação

↓

Ativação

↓

Limites Atualizados
```

Eventos:

* SubscriptionCreated
* PaymentConfirmed
* SubscriptionActivated
* SubscriptionExpired

---

# 16. Workflow de Upload

```text id="utl7np"
Selecionar Ficheiro

↓

Upload

↓

Validação

↓

Cloudflare R2

↓

Gerar Variantes

↓

Atualizar MediaAsset
```

Eventos:

* AssetUploaded
* ThumbnailGenerated
* AssetReady

---

# 17. Eventos Assíncronos

Processos executados pelo Celery:

* envio de emails;
* notificações push;
* geração de PDFs;
* thumbnails;
* compressão de imagens;
* exportações;
* estatísticas;
* backups.

Estes processos nunca deverão bloquear o utilizador.

---

# 18. Eventos Globais

Exemplos:

```text id="x8d4gk"
UserRegistered

TenantCreated

RoleAssigned

PermissionGranted

AssetUploaded

NotificationSent
```

Disponíveis para qualquer módulo.

---

# 19. Eventos por Domínio

Accounts

* UserCreated
* PasswordChanged

Organizations

* OrganizationCreated
* OrganizationUpdated

Clubs

* ClubApproved
* ClubSuspended

Players

* PlayerTransferred
* PlayerRetired

Competitions

* CompetitionStarted
* CompetitionFinished

Matches

* MatchFinished
* MatchCancelled

Billing

* InvoiceGenerated
* PaymentReceived

Media

* AssetReady
* AssetDeleted

---

# 20. Event Dispatcher

Responsabilidades:

* publicar eventos;
* encaminhar subscritores;
* evitar duplicação;
* garantir ordem de execução.

Implementar um dispatcher central em `core/events`.

---

# 21. Subscribers

Cada módulo pode reagir a eventos.

Exemplo:

```text id="sj3gn2"
MatchFinished

↓

Statistics

↓

Standings

↓

Notifications

↓

Analytics
```

Nenhum módulo chama diretamente outro módulo.

---

# 22. Idempotência

Todos os eventos deverão ser idempotentes.

Executar o mesmo evento duas vezes não deverá produzir resultados inconsistentes.

---

# 23. Observabilidade

Cada evento deverá registar:

* UUID
* Tipo
* Origem
* Tenant
* Utilizador
* Data/Hora
* Estado
* Duração

Facilita auditoria e depuração.

---

# 24. Tratamento de Falhas

Quando um consumidor falhar:

1. Registar erro.
2. Repetir conforme política de retry.
3. Enviar para Dead Letter Queue (futuro), quando aplicável.
4. Alertar equipa técnica se exceder o limite.

---

# 25. Escalabilidade

A arquitetura deverá permitir:

* múltiplos consumidores;
* filas independentes;
* processamento distribuído;
* integração com sistemas externos.

No futuro poderá evoluir para brokers como RabbitMQ ou Kafka sem alterar os eventos de domínio.

---

# 26. Regras Obrigatórias

É obrigatório:

* publicar eventos apenas após confirmação da transação;
* utilizar nomes consistentes;
* manter eventos imutáveis;
* documentar novos eventos.

É proibido:

* colocar lógica de negócio em eventos;
* utilizar eventos para substituir Services;
* criar dependências circulares entre módulos.

---

# 27. Architecture Decision Record

## ADR-010 — Arquitetura de Eventos

**Decisão**

Adotar uma arquitetura orientada por eventos de domínio, com processamento síncrono para regras críticas e processamento assíncrono para tarefas demoradas.

**Justificação**

* Reduz acoplamento entre módulos.
* Facilita escalabilidade.
* Melhora desempenho.
* Permite reutilização de processos.
* Simplifica futuras integrações externas e evolução para arquiteturas distribuídas.

Todos os novos workflows deverão utilizar este modelo sempre que houver comunicação entre domínios da plataforma.

---

# 28. Estado de Implementação (2026-07-04)

Esta secção regista o estado real da implementação e a política aplicada de persistência/retry, mantendo o restante documento como referência de arquitetura-alvo.

## 28.1 Componentes implementados

* `core/events/base.py` — `Event` (dataclass imutável: id, type, payload, origin, tenant_id, user_id, created_at).
* `core/events/dispatcher.py` — dispatcher em memória, com deduplicação por `event.id`, métricas (`events_published_total`, `events_dispatched_total`, `events_handlers_failed_total`) e publicação após `transaction.on_commit`.
* `core/events/types.py` — `EventType`, registo central dos nomes de eventos (evita strings mágicas espalhadas pelos módulos).
* Subscribers por módulo (`media_assets/subscribers.py`, `notifications/subscribers.py`), registados via `AppConfig.ready()`/import no `__init__.py` do módulo.
* Tarefas assíncronas (Celery) chamadas pelos subscribers, nunca pelo Service diretamente.

## 28.2 Eventos publicados atualmente

| Evento | Publicador | Subscriber(s) | Tarefa assíncrona |
|---|---|---|---|
| `AssetUploaded` | `media_assets.services.MediaAssetService.upload_for_owner` | `media_assets.subscribers.handle_asset_uploaded` | `media_assets.tasks.generate_thumbnails` |
| `ClubApproved` | `clubs.services.ClubService.activate` | `notifications.subscribers.handle_club_approved` | `notifications.tasks.send_notification_email` / `send_notification_push` |
| `ClubSuspended` | `clubs.services.ClubService.suspend` | `notifications.subscribers.handle_club_suspended` | `notifications.tasks.send_notification_email` / `send_notification_push` |

Outros eventos descritos nas secções 9 a 19 (ex.: `PlayerTransferred`, `CompetitionStarted`, `MatchFinished`) ainda não têm publicador real — ficam registados como trabalho futuro (Fase 4+), a implementar apenas quando o módulo correspondente precisar de reagir a eles, evitando eventos "mortos" sem subscriber nem publicador.

## 28.3 Política de persistência/retry por categoria

Decisão aplicada (ADR-010, complementar):

* **Entrega de notificações ao utilizador** (`notifications.tasks.send_notification_email`, `send_notification_push`): **persistência + retry**.
  * Persistência: o resultado é sempre gravado em `Notification.status` (`pending` → `sent`/`failed`), independentemente do resultado do Celery.
  * Retry: falhas transitórias (`NotificationDeliveryError` — timeout, exceção de rede, resposta não-2xx) são repetidas até 3 vezes com backoff (`max_retries=3, default_retry_delay=30`).
  * Sem retry: condições permanentes (sem destinatário, sem endpoint de push configurado) marcam o estado final imediatamente — repetir não resolveria.
* **Geração de variantes de imagem** (`media_assets.tasks.generate_thumbnails`, `delete_asset_from_storage`): **persistência + retry**.
  * Persistência: variantes gravadas em `MediaVariant`; o `MediaAsset` original nunca é bloqueado pela falha de geração de thumbnails.
  * Retry: até 3 tentativas (`max_retries=3`) para falhas de leitura/gravação em storage.
* **Dispatcher de eventos em memória** (`core/events/dispatcher.py`): **in-process, sem persistência do próprio evento**.
  * O evento em si não é gravado em base de dados nem em fila persistente — existe apenas durante o ciclo de vida do processo, entre o `transaction.on_commit` e a execução síncrona dos subscribers.
  * Falha de um handler é isolada (capturada e contabilizada em `events_handlers_failed_total`) e não interrompe os restantes subscribers nem a operação de negócio já confirmada em BD.
  * Aceitável para o volume atual da plataforma; se um evento crítico precisar de garantia de entrega mesmo em caso de crash do processo entre commit e dispatch, deve migrar para uma fila persistente (Celery/broker) em vez do dispatcher em memória — ver secção 25.

## 28.4 Testes sem broker real

Os testes automatizados nunca dependem de Redis ou de um broker real:

* `config/settings.py` força, de forma incondicional quando `TESTING=True` (não sobreponível por variável de ambiente), `CELERY_BROKER_URL="memory://"`, `CELERY_RESULT_BACKEND="cache+memory://"` e `CELERY_TASK_ALWAYS_EAGER=True`.
* `notifications/tests/test_tasks_retry.py` valida a política de retry/persistência acima (falha transitória repete e recupera, falha permanente não repete) sem qualquer chamada de rede real (SMTP/HTTP são mockados).
* `clubs/tests/test_events.py` e `notifications/tests/test_integration_events.py` validam o fluxo evento → subscriber → notificação de ponta a ponta, usando `TransactionTestCase` (necessário para que `transaction.on_commit` seja executado).
