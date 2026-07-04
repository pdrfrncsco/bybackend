# Auditoria de Conformidade do Backend

Data: 2026-07-04  
Escopo: `bybackend` comparado com `bybackend/docs` e `byfrontend/Diagnostico_BolaYetu_e_Proximas_Fases.md`.

## Resumo Executivo

O backend atual está mais avançado do que o diagnóstico do frontend indica. Já existem apps e APIs para DAM (`media_assets`), Players, Transfers, Notifications, Match Center e eventos, além de 121 testes automatizados a passar.

Ainda assim, a conformidade com a arquitetura oficial não está completa. Os maiores riscos são: configuração de ambiente inconsistente com Docker/PostgreSQL/R2, isolamento multi-tenant incompleto em endpoints públicos e de media, DAM parcialmente contornado por `ImageField` legado, e eventos/notificações dependentes de Celery/Redis sem modo de teste/dev isolado.

Resultado de testes:

```text
python manage.py test
Ran 121 tests in 231.992s
OK (skipped=1)
```

Observação: durante os testes houve tentativas de ligação ao Redis/Celery até `Retry limit exceeded`, mas a suíte terminou com sucesso. Isto indica que o comportamento assíncrono não está bem isolado no ambiente de testes.

## Diferenças Contra o Diagnóstico do Frontend

O ficheiro `byfrontend/Diagnostico_BolaYetu_e_Proximas_Fases.md` está desatualizado em pontos importantes:

- Diz que Players não existe, mas há app `players`, modelos `Player`/`PlayerRegistration`, API e testes.
- Diz que DAM não está implementado, mas há app `media_assets`, `MediaAsset`, `MediaUsage`, storage local/R2 e API `/api/v1/media/`.
- Diz que eventos não existem, mas há `core/events/dispatcher.py` e subscribers em `notifications`.
- Diz que Transferências não foram iniciadas, mas há app `transfers`, modelo, API, services/selectors e testes.
- Diz que testes existem só em `accounts`, mas há testes em `organizations`, `clubs`, `competitions`, `players`, `transfers`, `notifications` e `core`.

O diagnóstico continua correto nestes pontos:

- Analytics real ainda não existe.
- Marketplace/Billing ainda não existe.
- O tenant por subdomínio continua parcialmente aplicado.
- O storage oficial R2 ainda depende de configuração e há campos legados que gravam ficheiros diretamente.

## Estado por Roadmap

| Área | Documento | Estado real | Conformidade |
|---|---|---:|---|
| Foundation/Auth/Multi-tenant | Roadmap v2.0 | Implementado com JWT, Tenant, memberships e middleware | Parcial |
| Organizations | Roadmap v2.1 | Implementado com onboarding, branding, membros, público | Parcial |
| Clubs | Roadmap v2.2 | Implementado com CRUD, membros, público, logo | Parcial |
| Players | Roadmap v2.3 / 06A | Implementado como entidade global + registrations | Bom |
| Competitions | Roadmap v2.4 | CRUD, inscrições, standings, calendário | Parcial |
| Match Center | Roadmap v2.5 | Matches, MatchEvent, stats | Parcial |
| Transfers | Roadmap v2.6 | Implementado | Parcial |
| Analytics | Roadmap v2.7 | Não implementado | Pendente |
| Marketplace/Billing | Roadmap v2.8 | Não implementado | Pendente |
| DAM | 08A | Implementado, mas com legados | Parcial |
| Eventos/Workflows | 10 | Dispatcher in-process + subscribers | Parcial |
| DevOps | 09 | Dockerfile e compose existem | Parcial |

## Achados Prioritários

### P0 - Configuração Docker usa SQLite apesar de subir PostgreSQL

`docker-compose.dev.yml` define `DB_ENGINE: "django.db.backends.postgresql"`, mas `settings.py` só ativa PostgreSQL quando `DB_ENGINE == "postgresql"` ou quando `DEBUG=False`. Como o compose usa `DJANGO_DEBUG=True`, o backend continua em SQLite.

Evidência:

- `docker-compose.dev.yml:37`
- `bybackend/config/settings.py:128`

Impacto: ambiente dev não valida constraints, comportamento e performance em PostgreSQL, contrariando a fundação DevOps/Database.

Correção recomendada: aceitar ambos os valores (`postgresql` e `django.db.backends.postgresql`) ou simplificar o compose para `DB_ENGINE=postgresql`.

### P0 - `.env.example` contém valores sensíveis e nomes incompatíveis com settings

O `.env.example` inclui valores reais ou realistas de Cloudflare R2 e usa nomes que o backend não lê:

- `.env.example` usa `CLOUDFLARE_R2_ACCESS_KEY`, `CLOUDFLARE_R2_SECRET_KEY`, `CLOUDFLARE_CDN_DOMAIN`.
- `settings.py` espera `CLOUDFLARE_R2_ACCESS_KEY_ID`, `CLOUDFLARE_R2_SECRET_ACCESS_KEY`, `CLOUDFLARE_R2_CDN_URL`.

Evidência:

- `bybackend/.env.example:24`
- `bybackend/.env.example:25`
- `bybackend/.env.example:29`
- `bybackend/config/settings.py:289`
- `bybackend/config/settings.py:290`
- `bybackend/config/settings.py:293`

Impacto: risco de exposição de credenciais e falha silenciosa ao ativar R2.

Correção recomendada: revogar/rotacionar quaisquer credenciais reais, substituir por placeholders, alinhar nomes e adicionar validação explícita quando `USE_CLOUDFLARE_R2=True`.

### P1 - Multi-tenant por subdomínio existe, mas não é fonte de verdade em todas as APIs

A documentação exige identificação do tenant por subdomínio e Tenant Resolver. O middleware existe e popula `request.tenant`, mas várias APIs públicas continuam globais ou resolvidas por slug/ID.

Evidência documental:

- `bybackend/docs/01-architecture/06_MULTITENANT_ARCHITECTURE.md:139`
- `bybackend/docs/01-architecture/06_MULTITENANT_ARCHITECTURE.md:181`
- `bybackend/docs/01-architecture/06_MULTITENANT_ARCHITECTURE.md:204`

Evidência em código:

- `bybackend/core/middleware.py:6`
- `bybackend/core/middleware.py:23`
- `bybackend/organizations/views/organization_views.py:381`
- `bybackend/competitions/views/competition_views.py:36`
- `bybackend/competitions/views/competition_views.py:85`

Impacto: risco de respostas globais onde a arquitetura espera contexto de tenant, principalmente em competições e páginas públicas por subdomínio.

Correção recomendada: definir política única:

- Rotas públicas globais explícitas continuam globais.
- Rotas tenant-scoped devem usar `request.tenant` obrigatoriamente quando houver subdomínio.
- Selectors públicos de competitions devem aceitar tenant opcional e filtrar quando presente.

### P1 - Media assets podem ser lidos/apagados por ID sem tenant/ownership guard

`MediaAssetListView` filtra por membership do utilizador, mas `MediaAssetDetailView`, `delete` e `signed-url` fazem lookup direto por `asset_id`.

Evidência:

- `bybackend/media_assets/views.py:139`
- `bybackend/media_assets/views.py:169`
- `bybackend/media_assets/views.py:180`
- `bybackend/media_assets/views.py:203`
- `bybackend/media_assets/selectors.py:18`

Impacto: um utilizador autenticado pode tentar aceder a metadata, signed URL ou apagar assets de outro tenant se souber o UUID.

Correção recomendada: resolver tenant/membership do utilizador e exigir `asset.tenant_id == membership.tenant_id`, exceto assets `system` com regras próprias.

### P1 - DAM está implementado, mas ainda há gravação duplicada em ImageField legado

A documentação 08A manda todos os módulos usarem `MediaAsset` e `MediaUsage`, sem armazenar ficheiros nos módulos. O código usa DAM, mas depois grava novamente em `Tenant.logo`, `Tenant.banner` e `Club.logo`.

Evidência documental:

- `bybackend/docs/01-architecture/08A_DIGITAL_ASSET_MANAGEMENT.md:605`
- `bybackend/docs/01-architecture/08A_DIGITAL_ASSET_MANAGEMENT.md:607`
- `bybackend/docs/01-architecture/08A_DIGITAL_ASSET_MANAGEMENT.md:615`

Evidência em código:

- `bybackend/organizations/services/organization_service.py:94`
- `bybackend/organizations/services/organization_service.py:141`
- `bybackend/clubs/services/club_service.py:114`
- `bybackend/clubs/services/club_service.py:149`

Impacto: duplicação de ficheiros, caminhos legados, custo de migração e risco de divergência entre DAM e campos antigos.

Correção recomendada: migrar serializers/frontend para URL via `MediaUsage`, tornar campos legados read-only/deprecated e depois remover `ImageField` em migração controlada.

### P1 - Eventos são in-process e notifications acionam Celery/Redis durante testes

A arquitetura prevê Event Dispatcher e Celery para assíncronos. O dispatcher existe, mas é síncrono em memória após commit. Notifications chamam `.delay()` e durante testes tentam Redis.

Evidência documental:

- `bybackend/docs/01-architecture/10_EVENTS_AND_WORKFLOWS.md:90`
- `bybackend/docs/01-architecture/10_EVENTS_AND_WORKFLOWS.md:98`
- `bybackend/docs/01-architecture/10_EVENTS_AND_WORKFLOWS.md:524`
- `bybackend/docs/01-architecture/10_EVENTS_AND_WORKFLOWS.md:607`

Evidência em código:

- `bybackend/core/events/dispatcher.py:89`
- `bybackend/notifications/subscribers.py:34`
- `bybackend/notifications/subscribers.py:35`
- `bybackend/media_assets/services/media_service.py:224`

Impacto: testes lentos/flaky e sem garantias de entrega assíncrona persistente.

Correção recomendada: configurar `CELERY_TASK_ALWAYS_EAGER=True` em testes/dev local ou mockar tasks nos testes; evoluir o dispatcher para fila persistente quando a plataforma precisar de garantias.

### P2 - Paginação não é uniforme em endpoints de lista

A guideline de API exige paginação em GET de lista. Há paginação em organizations public, players e transfers, mas clubs public, competitions list e alguns endpoints internos retornam listas completas.

Evidência:

- `bybackend/organizations/views/organization_views.py:376`
- `bybackend/players/views/__init__.py:64`
- `bybackend/transfers/views/__init__.py:85`
- `bybackend/clubs/views/club_views.py:317`
- `bybackend/competitions/views/competition_views.py:36`

Impacto: inconsistência contratual para o frontend e risco de performance conforme dados crescem.

Correção recomendada: aplicar `StandardPagination` em todas as listagens públicas e administrativas com potencial de crescimento.

### P2 - OpenAPI/documentação não cobre todos os detalhes de contrato

As tags principais já foram atualizadas em `SPECTACULAR_SETTINGS`, mas há endpoints com `request={"multipart/form-data": None}` ou `request={"application/json": None}`, o que empobrece a especificação.

Evidência:

- `bybackend/config/settings.py:262`
- `bybackend/organizations/views/organization_views.py:117`
- `bybackend/organizations/views/organization_views.py:189`
- `bybackend/clubs/views/club_views.py:115`

Impacto: SDKs/clients e frontend ficam sem contrato forte para multipart e payloads administrativos.

Correção recomendada: criar serializers explícitos para uploads, membros e ações administrativas.

## Conformidade Positiva

- Estrutura services/selectors/serializers/views está presente na maioria dos módulos.
- `INSTALLED_APPS` inclui os domínios atuais (`players`, `organizations`, `clubs`, `competitions`, `transfers`, `media_assets`, `notifications`).
- `SPECTACULAR_SETTINGS` já inclui tags para clubs, competitions, media, players e transfers.
- O DAM central existe com `MediaAssetService`, `MediaAsset`, `MediaUsage` e providers local/R2.
- Players seguem a arquitetura global: `Player` não pertence diretamente a Tenant; `PlayerRegistration` faz o vínculo.
- Transfers já dependem de Player global e Clubs tenant-scoped.
- O projeto tem `Dockerfile` e `docker-compose.dev.yml`.
- A suíte de testes atual passa.

## Plano Recomendado

### Fase 0 - Correções de fundação

1. Corrigir `DB_ENGINE` no compose/settings para usar PostgreSQL no ambiente Docker.
2. Limpar `.env.example`, alinhar variáveis R2 e validar configuração quando R2 estiver ativo.
3. Adicionar `CELERY_TASK_ALWAYS_EAGER=True` em settings de teste ou fixture de testes.
4. Adicionar guards tenant/ownership em MediaAsset detail/delete/signed-url.
5. Definir política de `request.tenant` para APIs públicas e aplicar em competitions/clubs/organizations.

### Fase 1 - Fechar DAM

1. Migrar consumidores para `MediaUsage`.
2. Remover gravação duplicada em `Tenant.logo`, `Tenant.banner`, `Club.logo`.
3. Adicionar testes de isolamento de media entre tenants.

### Fase 2 - Uniformizar API

1. Aplicar paginação a clubs/competitions e listagens administrativas.
2. Trocar schemas genéricos por serializers explícitos.
3. Rever respostas `204` vs envelope padrão, se o frontend exigir envelope em todas as operações.

### Fase 3 - Evoluir eventos

1. Separar evento de domínio, handler e tarefa assíncrona.
2. Adicionar testes sem Redis real.
3. Definir quais eventos exigem persistência/retry e quais podem continuar in-process.

### Fase 4 - Produto pendente

1. Implementar Analytics real para substituir dashboards mock.
2. Implementar Marketplace/Billing quando players/competitions/match center estiverem estáveis.

## Conclusão

O estado atual do `bybackend` já superou várias lacunas apontadas pelo diagnóstico do frontend, especialmente DAM, Players, Transfers, Events e testes. A prioridade agora não deve ser abrir novos módulos, mas fechar os desvios de fundação: ambiente, secrets, R2, isolamento tenant/media e consistência das APIs. Isso reduz risco antes de Analytics, Marketplace e evolução comercial.
