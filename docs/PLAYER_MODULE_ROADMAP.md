# Plano de Melhorias — Módulo PLAYER
**Bolayetu Backend · Roadmap MVP por Fases**
_Gerado com base no repositório atual + Arquitetura_do_Modulo_PLAYER.md_

---

## 1. Estado Atual vs. Arquitetura Pretendida

### O que já existe no repositório

| Ficheiro | O que faz |
|---|---|
| `players/models/player.py` | Modelo principal do Player |
| `players/models/registration.py` | Registo do jogador num clube |
| `players/models/player_document.py` | Documentos do jogador |
| `players/models/player_video.py` | Vídeos do jogador |
| `players/models/player_achievement.py` | Conquistas do jogador |
| `players/models/player_registration_request.py` | Pedido de registo num clube |
| `players/services/player_document_service.py` | Serviço de documentos |
| `players/services/player_video_service.py` | Serviço de vídeos |
| `players/services/player_achievement_service.py` | Serviço de conquistas |
| `players/services/player_registration_request_service.py` | Serviço de pedidos de registo |
| `players/services/stats_sync_service.py` | Sincronização de estatísticas |
| `players/serializers/` | Serializers para documentos, vídeos, conquistas, registo |
| `players/views/` | Views para media, documentos, vídeos, conquistas, registo |
| `players/selectors/` | Seletores (presente mas conteúdo desconhecido) |
| `players/permissions/` | Permissões (presente mas provavelmente incompleto) |
| `players/migrations/` | 6 migrações (0001–0006) |
| `players/tests/` | Testes para modelos, API, seletores, novos modelos, registo, upload |

### O que está em falta vs. Arquitetura

| Componente da Arquitetura | Estado |
|---|---|
| `global_id` permanente no Player | ❓ Provavelmente ausente ou incompleto |
| `PlayerIdentityDocument` (modelo internacional) | ❌ Não existe |
| `PlayerContact` + `EmergencyContact` | ❌ Não existe |
| `LegalGuardian` (menores) | ❌ Não existe |
| `PlayerMedicalProfile` + `MedicalDocument` | ❌ Não existe |
| `PlayerCareer` (historial de carreira estruturado) | ❌ Não existe |
| `PlayerContract` | ❌ Não existe (existe no módulo `transfers`) |
| `PlayerAgentRelationship` | ❌ Não existe |
| `PlayerTrainingHistory` (EPP/Solidarity) | ❌ Não existe |
| `PlayerSeasonStatistics` | ❌ Não existe (parcialmente em `stats_sync_service`) |
| `NationalTeamCallUp` / `NationalTeamAppearance` | ❌ Não existe |
| `PlayerPrivacySettings` | ❌ Não existe |
| `PlayerSocialProfile` | ❌ Não existe |
| `external_ids` (FIFA Connect, etc.) | ❌ Não existe |
| `Player.status` (ACTIVE/INACTIVE/RETIRED/DECEASED) | ❓ Provavelmente ausente |
| Onboarding wizard flow (Account→Identity→Football→Club) | ❌ Não existe como serviço |
| Domain events do Player (`PlayerCreated`, `PlayerVerified`, etc.) | ❌ Não existe |
| `players/events/` | ❌ Não existe |
| `players/tasks/` | ❌ Não existe |
| `players/validators/` | ❌ Não existe |
| `players/admin/` (admin dedicado) | Existe mas provavelmente básico |
| Permissões por papel (Coach, Medical Staff, Agent, Scout) | ❌ Não existe |

---

## 2. Problemas de Estrutura Detetados

### 2.1 Ausência de `global_id`
O Player provavelmente usa apenas o `id` Django padrão. A arquitetura exige um `global_id` permanente e imutável (ex: `BY-PLY-01HXYZ...`) que sobreviva a mudanças de clube, status e outros eventos.

### 2.2 Modelo de Identidade Civil Angolano vs. Internacional
O documento de arquitectura adverte explicitamente: _"Não utilizar BI angolano como campo universal."_ O modelo deve ser o `IdentityDocument` internacional (Passport, National ID, Birth Certificate, Residence Permit, Other).

### 2.3 Ausência de `PlayerCareer` dedicado
A carreira do jogador não pode depender apenas dos `PlayerRegistration`. Existe o `stats_sync_service.py` mas não há um modelo `PlayerCareer` que permita reconstruir o historial completo com estatísticas por clube/temporada/competição.

### 2.4 Contrato e Agente não estão no módulo correto
O módulo `transfers/` contém modelos de transferência, mas `PlayerContract` e `PlayerAgentRelationship` devem viver no módulo `players/` — são entidades de lifecycle do jogador, não de transferência.

### 2.5 `Player` provavelmente é um God Model
Com campos de posição, documentos e registo todos no mesmo modelo, o risco de um God Model com demasiados campos é elevado. A arquitectura prevê um modelo principal pequeno com entidades especializadas.

### 2.6 Sem sistema de privacidade
Não existe `PlayerPrivacySettings`. Dados médicos, contratos e contactos são provavelmente visíveis para qualquer role autenticado.

### 2.7 Sem eventos de domínio
O módulo `core/events/` existe e está em uso (ex: `clubs/tests/test_events.py`), mas `players/events/` não existe — o módulo Player não emite eventos como `PlayerRegistrationCreated` ou `PlayerTransferred`.

### 2.8 Sem suporte a menores
`LegalGuardian` não existe. Para o mercado africano e para compliance com as regras FIFA de transferências de menores (guia publicado fev. 2026), este é um requisito de MVP.

---

## 3. Plano de Fases — MVP

---

### FASE 1 — Player Identity (Fundação)
**Objetivo:** Construir a entidade `Player` correctamente, com identidade global permanente, documentos internacionais, contactos e suporte a menores.

**Estimativa:** 2–3 sprints

#### 1.1 Refatorar `Player` (model principal)
```python
# players/models/player.py — tornar o modelo pequeno e focado

class Player(TenantModel):
    global_id = models.CharField(max_length=32, unique=True, editable=False)
    account = models.OneToOneField('accounts.User', null=True, blank=True)
    status = models.CharField(choices=PlayerStatus.choices)  # ACTIVE/INACTIVE/RETIRED/DECEASED
    
    # Identity (mínimo)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    preferred_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField()
    country_of_birth = models.CharField(max_length=3)  # ISO 3166
    nationality = models.CharField(max_length=3)
    secondary_nationality = models.CharField(max_length=3, blank=True)
    gender = models.CharField(choices=Gender.choices)
    
    # Football (mínimo)
    primary_position = models.CharField(choices=Position.choices)
    dominant_foot = models.CharField(choices=Foot.choices)
    
    # Media
    profile_photo = models.ForeignKey('media_assets.MediaAsset', null=True, blank=True)
    
    is_minor = property  # calculado: age < 18
    is_public = models.BooleanField(default=False)
    
    created_at / updated_at
```

**Acções:**
- [ ] Gerar `global_id` no `save()` com prefixo `BY-PLY-` + ULID
- [ ] Adicionar `PlayerStatus` enum: ACTIVE, INACTIVE, RETIRED, DECEASED
- [ ] Mover campos não-essenciais para modelos especializados
- [ ] Migração para adicionar `global_id` e `status` sem quebrar dados existentes

#### 1.2 Criar `PlayerIdentityDocument`
```python
# players/models/identity.py (novo)
class PlayerIdentityDocument(TenantModel):
    player = FK(Player)
    document_type = CharField(choices=[NATIONAL_ID, PASSPORT, BIRTH_CERT, RESIDENCE_PERMIT, OTHER])
    document_number = CharField()
    issuing_country = CharField(max_length=3)  # ISO 3166
    issuing_authority = CharField(blank=True)
    issue_date = DateField(null=True)
    expiry_date = DateField(null=True)
    document_front = FK(MediaAsset, null=True)
    document_back = FK(MediaAsset, null=True)
    verification_status = CharField(choices=[PENDING, VERIFIED, REJECTED])
    verified_by = FK(User, null=True)
    verified_at = DateTimeField(null=True)
```

**Acções:**
- [ ] Criar `players/models/identity.py`
- [ ] Serializer, service, views, URLs para CRUD de documentos de identidade
- [ ] Testes unitários e de integração

#### 1.3 Criar `PlayerContact`
```python
# players/models/contact.py (novo)
class PlayerContact(TenantModel):
    player = OneToOneField(Player)
    primary_email = EmailField()
    secondary_email = EmailField(blank=True)
    mobile_phone = CharField()
    secondary_phone = CharField(blank=True)
    country_code = CharField()
    address = TextField(blank=True)
    city = CharField(blank=True)
    province = CharField(blank=True)
    postal_code = CharField(blank=True)
    country = CharField(max_length=3)

class EmergencyContact(TenantModel):
    player = FK(Player)
    name = CharField()
    relationship = CharField()
    phone = CharField()
    email = EmailField(blank=True)
    country = CharField(max_length=3, blank=True)
```

#### 1.4 Criar `LegalGuardian` (menores)
```python
# players/models/guardian.py (novo)
class LegalGuardian(TenantModel):
    player = FK(Player)
    name = CharField()
    relationship = CharField()
    document_number = CharField(blank=True)
    phone = CharField()
    email = EmailField(blank=True)
    address = TextField(blank=True)
    consent_status = CharField(choices=[PENDING, GIVEN, REVOKED])
    consent_document = FK(MediaAsset, null=True)
    consent_given_at = DateTimeField(null=True)
```

**Acções:**
- [ ] Auto-criar `LegalGuardian` quando `player.is_minor` é True
- [ ] Validação: menores não podem ter registo activo sem guardian com consent

#### 1.5 Criar `PlayerExternalId`
```python
# players/models/external_id.py (novo)
class PlayerExternalId(TenantModel):
    player = FK(Player)
    system = CharField(choices=[FIFA_CONNECT, FIFA_ID, NATIONAL_ASSOC, LEAGUE, CLUB_REG, OTHER])
    external_id = CharField()
    issued_at = DateField(null=True)
    notes = TextField(blank=True)
```

#### 1.6 Criar `PlayerPrivacySettings`
```python
# players/models/privacy.py (novo)
class PlayerPrivacySettings(TenantModel):
    player = OneToOneField(Player)
    # Visibilidade por categoria (PUBLIC / CLUB / ORGANIZATION / AGENT / PRIVATE)
    profile_visibility = CharField(default='PUBLIC')
    contact_visibility = CharField(default='CLUB')
    contract_visibility = CharField(default='CLUB')
    salary_visibility = CharField(default='PRIVATE')
    medical_visibility = CharField(default='PRIVATE')
    documents_visibility = CharField(default='CLUB')
    statistics_visibility = CharField(default='PUBLIC')
```

#### 1.7 Criar `players/events/` — Domain Events Fase 1
```python
# players/events/types.py (novo)
PlayerCreated
PlayerOnboardingCompleted
PlayerVerified
PlayerDocumentUploaded
PlayerDocumentVerified
PlayerStatusChanged
```

**Acções:**
- [ ] Criar `players/events/__init__.py` e `players/events/types.py`
- [ ] Integrar dispatcher do `core/events/dispatcher.py`
- [ ] Emitir eventos nos services relevantes

#### 1.8 Completar `PlayerDocument` (melhorar o existente)
O modelo actual provavelmente precisa de:
- [ ] Adicionar categoria `IDENTITY` (já existe: Registration, Medical, etc.)
- [ ] Adicionar `visibility` field
- [ ] Adicionar `verification_status`, `verified_by`, `verified_at`
- [ ] Integrar com `PlayerPrivacySettings`

#### 1.9 Completar `PlayerPrivacySettings` com middleware de permissões
- [ ] Criar `players/permissions/player_permissions.py` com classes por role
- [ ] `CanViewPlayerMedical`, `CanViewPlayerContract`, `CanViewPlayerContact`, etc.

---

### FASE 2 — Football Identity (Registo + Carreira)
**Objetivo:** Implementar correctamente o ciclo de registo do jogador num clube, historial de carreira e estatísticas por temporada.

**Estimativa:** 2–3 sprints

#### 2.1 Melhorar `PlayerRegistration` (modelo existente)
O modelo atual (`players/models/registration.py`) provavelmente precisa de:
```python
# Campos a adicionar/verificar:
organization_id = FK(Organization)
competition_id = FK(Competition, null=True)
season_id = FK(Season, null=True)  # se Season existir
registration_type = CharField(choices=[AMATEUR, PROFESSIONAL, YOUTH, ACADEMY, LOAN, TRIAL, GUEST])
status = CharField(choices=[PENDING, ACTIVE, SUSPENDED, LOANED, RELEASED, TRANSFERRED, RETIRED])
registration_number = CharField(unique_together=['tenant', 'registration_number'])
effective_from = DateField()
effective_until = DateField(null=True)
shirt_number = IntegerField(null=True)
squad_number = IntegerField(null=True)
eligibility_status = CharField()
registration_document = FK(MediaAsset, null=True)
approved_by = FK(User, null=True)
approved_at = DateTimeField(null=True)
```

**Acções:**
- [ ] Auditar campos actuais vs. arquitectura
- [ ] Migração para adicionar campos em falta
- [ ] Garantir que `Player` nunca tem `club_id` directo — sempre via `PlayerRegistration`
- [ ] `get_current_registration()` selector no Player

#### 2.2 Criar `PlayerCareer`
```python
# players/models/career.py (novo)
class PlayerCareer(TenantModel):
    player = FK(Player)
    club = FK(Club)
    season = CharField(max_length=20)  # ex: "2024/25"
    competition = FK(Competition, null=True)
    position = CharField(choices=Position.choices)
    appearances = IntegerField(default=0)
    starts = IntegerField(default=0)
    minutes_played = IntegerField(default=0)
    goals = IntegerField(default=0)
    assists = IntegerField(default=0)
    yellow_cards = IntegerField(default=0)
    red_cards = IntegerField(default=0)
    
    class Meta:
        unique_together = ['player', 'club', 'season', 'competition']
```

**Acções:**
- [ ] Criar `players/models/career.py`
- [ ] Criar `PlayerCareerService` com método `rebuild_from_match_events(player)`
- [ ] Selector `get_career_timeline(player)` que devolve lista cronológica de clubes
- [ ] Endpoint `GET /players/{id}/career/`

#### 2.3 Criar `PlayerSeasonStatistics`
```python
# players/models/statistics.py (novo)
class PlayerSeasonStatistics(TenantModel):
    player = FK(Player)
    season = CharField()
    competition = FK(Competition, null=True)
    club = FK(Club)
    
    # Agregados
    appearances = IntegerField(default=0)
    starts = IntegerField(default=0)
    minutes = IntegerField(default=0)
    goals = IntegerField(default=0)
    assists = IntegerField(default=0)
    shots = IntegerField(default=0)
    shots_on_target = IntegerField(default=0)
    passes = IntegerField(default=0)
    pass_accuracy = DecimalField(null=True)
    key_passes = IntegerField(default=0)
    tackles = IntegerField(default=0)
    interceptions = IntegerField(default=0)
    yellow_cards = IntegerField(default=0)
    red_cards = IntegerField(default=0)
```

**Acções:**
- [ ] Refatorar `stats_sync_service.py` para popular este modelo
- [ ] Criar Celery task `recalculate_player_season_stats`
- [ ] Endpoint `GET /players/{id}/statistics/`

#### 2.4 Melhorar `PlayerFootballProfile` (campos de futebol separados do Player)
```python
# players/models/football_profile.py (novo)
class PlayerFootballProfile(TenantModel):
    player = OneToOneField(Player)
    primary_position = CharField(choices=Position.choices)
    secondary_positions = ArrayField(CharField(), blank=True, default=list)
    dominant_foot = CharField(choices=[LEFT, RIGHT, BOTH])
    height_cm = DecimalField(null=True)
    weight_kg = DecimalField(null=True)
    sporting_status = CharField(choices=[AMATEUR, PROFESSIONAL, SEMI_PROFESSIONAL, YOUTH])
    biography = TextField(blank=True)
    cover_photo = FK(MediaAsset, null=True)
    social_instagram = URLField(blank=True)
    social_x = URLField(blank=True)
    social_youtube = URLField(blank=True)
    social_tiktok = URLField(blank=True)
    social_website = URLField(blank=True)
```

**Nota:** Se `primary_position` já está no modelo `Player`, movê-lo para aqui e manter apenas o mínimo no Player principal.

#### 2.5 Implementar Onboarding Service
```python
# players/services/onboarding.py (novo)
class PlayerOnboardingService:
    STEPS = ['account', 'identity', 'personal', 'football', 'contact', 'guardian', 'documents', 'club', 'review']
    
    def get_onboarding_status(player) -> dict  # step actual + % completado
    def complete_step(player, step, data) -> Player
    def is_onboarding_complete(player) -> bool
    def send_onboarding_invitation(email, club) -> InvitationToken
```

**Acções:**
- [ ] Criar `players/services/onboarding.py`
- [ ] `PlayerOnboardingStatus` model ou usar flags no `Player`
- [ ] Endpoint `GET/PATCH /players/me/onboarding/`
- [ ] Endpoint `POST /players/invite/` (clube convida jogador)

#### 2.6 Domain Events Fase 2
```python
PlayerRegistrationCreated
PlayerRegistrationApproved
PlayerRegistrationClosed
PlayerCareerUpdated
```

#### 2.7 Selectors a criar/melhorar
```python
# players/selectors/
get_active_registration(player)     → PlayerRegistration | None
get_current_club(player)            → Club | None
get_career_timeline(player)         → List[PlayerCareer]
get_season_statistics(player, season) → PlayerSeasonStatistics
get_players_for_club(club)          → QuerySet[Player]
get_free_agents(tenant)             → QuerySet[Player]
search_players(tenant, filters)     → QuerySet[Player]
```

---

### FASE 3 — Professional (Contratos + Agentes + Transferências)
**Objetivo:** Implementar contratos, agentes, e integrar o workflow de transferências com o módulo `players/`.

**Estimativa:** 2–3 sprints

#### 3.1 Criar `PlayerContract`
```python
# players/models/contract.py (novo)
class PlayerContract(TenantModel):
    player = FK(Player)
    club = FK(Club)
    contract_type = CharField(choices=[PROFESSIONAL, YOUTH, AMATEUR, SHORT_TERM, TRIAL, LOAN, EXTENSION])
    status = CharField(choices=[DRAFT, ACTIVE, EXPIRED, TERMINATED, SUSPENDED])
    start_date = DateField()
    end_date = DateField()
    signed_date = DateField(null=True)
    salary = DecimalField(null=True)
    currency = CharField(max_length=3, default='USD')
    bonuses = JSONField(default=dict)
    release_clause = DecimalField(null=True)
    has_image_rights = BooleanField(default=False)
    option_year = BooleanField(default=False)
    termination_clause = TextField(blank=True)
    contract_document = FK(MediaAsset, null=True)
    signed_by_player = BooleanField(default=False)
    signed_by_club = BooleanField(default=False)
    verified_at = DateTimeField(null=True)
```

**Acções:**
- [ ] Criar `players/models/contract.py`
- [ ] Criar `PlayerContractService` com `create_contract()`, `terminate()`, `renew()`
- [ ] Validação: apenas um contrato ACTIVE por jogador por clube em simultâneo
- [ ] Endpoint `GET/POST /players/{id}/contracts/`
- [ ] Integrar com `PlayerPrivacySettings.contract_visibility`

#### 3.2 Criar `PlayerAgentRelationship`
```python
# players/models/agent.py (novo)
class Agent(TenantModel):  # entidade de negócio, não User
    name = CharField()
    license_number = CharField(blank=True)
    agency = CharField(blank=True)
    country = CharField(max_length=3)
    email = EmailField()
    phone = CharField()
    fifa_agent_id = CharField(blank=True)
    
class PlayerAgentRelationship(TenantModel):
    player = FK(Player)
    agent = FK(Agent)
    representation_agreement = FK(MediaAsset, null=True)
    start_date = DateField()
    end_date = DateField(null=True)
    status = CharField(choices=[ACTIVE, EXPIRED, TERMINATED])
    commission_rate = DecimalField(null=True)  # %
```

#### 3.3 Criar `PlayerTrainingHistory` (EPP/Solidarity Contribution)
```python
# players/models/training.py (novo)
class PlayerTrainingHistory(TenantModel):
    player = FK(Player)
    club = FK(Club, null=True)
    academy_name = CharField(blank=True)
    start_date = DateField()
    end_date = DateField(null=True)
    country = CharField(max_length=3)
    training_category = CharField(choices=[AMATEUR, YOUTH, ACADEMY, PROFESSIONAL])
    verified = BooleanField(default=False)
    verified_by = FK(User, null=True)
    notes = TextField(blank=True)
```

**Nota:** Este modelo é crítico para o cálculo futuro de Training Compensation e Solidarity Contribution em transferências internacionais.

#### 3.4 Integrar módulo `transfers/` com `players/`
O módulo `transfers/` já existe. É necessário:
- [ ] Garantir que `Transfer` referencia `PlayerRegistration` (não apenas Player)
- [ ] Criar `PlayerTransferService` em `players/services/transfer.py` que orquestra:
  - Fechar `PlayerRegistration` actual
  - Criar nova `PlayerRegistration` no novo clube
  - Actualizar `PlayerCareer`
  - Emitir `PlayerTransferred` event
- [ ] Garantir que o Player nunca é deletado — apenas os vínculos terminam

#### 3.5 Domain Events Fase 3
```python
PlayerContractSigned
PlayerContractRenewed
PlayerContractTerminated
PlayerTransferRequested
PlayerReleased
PlayerTransferred
PlayerLoanStarted
PlayerLoanEnded
```

---

### FASE 4 — Ecosystem (Performance + Medical + National Team + Compliance)
**Objetivo:** Completar o ecossistema com dados médicos, seleção nacional, performance metrics e compliance com regras FIFA.

**Estimativa:** 3+ sprints (pós-MVP inicial)

#### 4.1 Criar `PlayerMedicalProfile`
```python
# players/models/medical.py (novo)
class PlayerMedicalProfile(TenantModel):
    player = OneToOneField(Player)
    blood_type = CharField(blank=True)
    medical_status = CharField(choices=[FIT, INJURED, RECOVERING, SUSPENDED_MEDICAL])
    injury_status = TextField(blank=True)
    medical_clearance = BooleanField(default=False)
    fitness_status = CharField(blank=True)
    medical_notes = TextField(blank=True)
    last_medical_exam = DateField(null=True)
    next_medical_exam = DateField(null=True)

class MedicalDocument(TenantModel):
    player = FK(Player)
    doc_type = CharField()
    file = FK(MediaAsset)
    issued_at = DateField()
    expires_at = DateField(null=True)
    verified_by = FK(User, null=True)
    verification_status = CharField()
```

**Nota de privacidade:** Acesso restrito a `Player`, `Club Medical Staff` e `Authorized Organization` apenas.

#### 4.2 Criar `NationalTeamCallUp` e `NationalTeamAppearance`
```python
# players/models/national_team.py (novo)
class NationalTeamCallUp(TenantModel):
    player = FK(Player)
    national_team = CharField(max_length=3)  # ISO país
    category = CharField(choices=[SENIOR, U23, U20, U17, U15])
    competition = FK(Competition, null=True)
    call_up_date = DateField()
    release_date = DateField(null=True)
    status = CharField(choices=[CALLED, RELEASED, DECLINED, INJURED])
    caps = IntegerField(default=0)
```

#### 4.3 `PlayerPerformanceMetric` (GPS/Biometric)
```python
# players/models/performance.py (novo)
class PlayerPerformanceMetric(TenantModel):
    player = FK(Player)
    match = FK(Match, null=True)
    recorded_at = DateTimeField()
    metric_type = CharField()  # SPEED, DISTANCE, SPRINTS, HEART_RATE, etc.
    value = DecimalField()
    unit = CharField()
    source = CharField()  # GPS, WEARABLE, MANUAL
```

#### 4.4 Compliance e regras configuráveis (RSTP 2027)
```python
# players/models/compliance.py (novo)
class PlayerComplianceRecord(TenantModel):
    player = FK(Player)
    rule_type = CharField()  # MINOR_TRANSFER, WORK_PERMIT, etc.
    status = CharField(choices=[COMPLIANT, NON_COMPLIANT, PENDING_REVIEW])
    notes = TextField()
    reviewed_at = DateTimeField(null=True)
```

**Nota:** O novo RSTP entra em vigor a 1 de janeiro de 2027. As regras de transferência, contratos e compliance **devem ser configuráveis** por regulamento, não hardcoded.

---

## 4. Refatorações Transversais (Todas as Fases)

### 4.1 Estrutura de ficheiros final (target)
```
players/
│
├── models/
│   ├── __init__.py        ← exportar todos os modelos
│   ├── player.py          ← modelo principal (pequeno)
│   ├── identity.py        ← PlayerIdentityDocument (NOVO)
│   ├── contact.py         ← PlayerContact + EmergencyContact (NOVO)
│   ├── guardian.py        ← LegalGuardian (NOVO)
│   ├── football_profile.py ← PlayerFootballProfile (NOVO)
│   ├── registration.py    ← PlayerRegistration (MELHORAR)
│   ├── career.py          ← PlayerCareer (NOVO)
│   ├── contract.py        ← PlayerContract (NOVO)
│   ├── agent.py           ← Agent + PlayerAgentRelationship (NOVO)
│   ├── training.py        ← PlayerTrainingHistory (NOVO)
│   ├── statistics.py      ← PlayerSeasonStatistics (NOVO)
│   ├── achievement.py     ← PlayerAchievement (MELHORAR)
│   ├── national_team.py   ← NationalTeamCallUp (NOVO)
│   ├── medical.py         ← PlayerMedicalProfile (NOVO, Fase 4)
│   ├── performance.py     ← PlayerPerformanceMetric (NOVO, Fase 4)
│   ├── privacy.py         ← PlayerPrivacySettings (NOVO)
│   ├── external_id.py     ← PlayerExternalId (NOVO)
│   ├── player_document.py ← melhorar existente
│   ├── player_video.py    ← manter existente
│   └── player_registration_request.py ← manter/melhorar
│
├── services/
│   ├── __init__.py
│   ├── onboarding.py      ← NOVO: wizard de onboarding
│   ├── registration.py    ← NOVO: registo num clube
│   ├── career.py          ← NOVO: historial de carreira
│   ├── contract.py        ← NOVO: contratos
│   ├── transfer.py        ← NOVO: orquestrador de transferências
│   ├── release.py         ← NOVO: saída do clube
│   ├── verification.py    ← NOVO: verificação de identidade
│   ├── player_document_service.py   ← existente
│   ├── player_video_service.py      ← existente
│   ├── player_achievement_service.py ← existente
│   ├── player_registration_request_service.py ← existente
│   └── stats_sync_service.py        ← refatorar
│
├── selectors/
│   ├── __init__.py
│   ├── player_selectors.py   ← NOVO: get_active_registration, get_current_club, etc.
│   └── career_selectors.py   ← NOVO: get_career_timeline
│
├── serializers/
│   ├── player.py              ← NOVO: serializer principal
│   ├── player_document.py     ← existente
│   ├── player_video.py        ← existente
│   ├── player_achievement.py  ← existente
│   ├── player_registration_request.py ← existente
│   ├── identity.py            ← NOVO
│   ├── contact.py             ← NOVO
│   ├── guardian.py            ← NOVO
│   ├── career.py              ← NOVO
│   └── contract.py            ← NOVO
│
├── views/
│   ├── player_views.py              ← NOVO: CRUD principal
│   ├── player_me_views.py           ← existente (melhorar)
│   ├── player_document_views.py     ← existente
│   ├── player_video_views.py        ← existente
│   ├── player_achievement_views.py  ← existente
│   ├── player_registration_request_views.py ← existente
│   ├── player_career_views.py       ← NOVO
│   └── player_onboarding_views.py   ← NOVO
│
├── permissions/
│   ├── __init__.py
│   └── player_permissions.py  ← NOVO: CanViewPlayer, CanViewMedical, etc.
│
├── validators/
│   ├── __init__.py
│   └── player_validators.py   ← NOVO: validate_minor, validate_position, etc.
│
├── events/
│   ├── __init__.py
│   └── types.py               ← NOVO: todos os domain events
│
├── tasks/
│   ├── __init__.py
│   └── player_tasks.py        ← NOVO: recalculate_stats, send_notifications
│
├── admin/
│   └── (melhorar admin existente)
│
├── tests/
│   ├── __init__.py
│   ├── test_models.py         ← existente
│   ├── test_api.py            ← existente
│   ├── test_selectors.py      ← existente
│   ├── test_new_models.py     ← existente
│   ├── test_new_api.py        ← existente
│   ├── test_registration_requests.py ← existente
│   ├── test_player_media_upload.py   ← existente
│   ├── test_player_achievement_media_upload.py ← existente
│   ├── test_identity.py       ← NOVO
│   ├── test_career.py         ← NOVO
│   ├── test_contract.py       ← NOVO
│   └── test_onboarding.py     ← NOVO
│
└── urls.py                    ← expandir
```

### 4.2 `global_id` — Implementação
```python
# players/models/player.py
import ulid

def generate_player_global_id():
    return f"BY-PLY-{ulid.new().str}"

class Player(TenantModel):
    global_id = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
        db_index=True
    )
    
    def save(self, *args, **kwargs):
        if not self.global_id:
            self.global_id = generate_player_global_id()
        super().save(*args, **kwargs)
```

### 4.3 Soft delete — Nunca apagar o Player
```python
# Regra de negócio crítica
# Adicionar ao PlayerService:
def delete_player(player):
    raise NotImplementedError(
        "Players cannot be deleted. Use player.status = PlayerStatus.INACTIVE instead."
    )
```

### 4.4 URLs — Estrutura RESTful target
```python
# players/urls.py
/players/                              GET (list), POST (create)
/players/{global_id}/                  GET, PATCH
/players/{global_id}/identity/         GET, POST, PATCH
/players/{global_id}/contact/          GET, PATCH
/players/{global_id}/guardian/         GET, POST, PATCH
/players/{global_id}/documents/        GET, POST
/players/{global_id}/documents/{id}/   GET, DELETE
/players/{global_id}/registrations/    GET
/players/{global_id}/career/           GET
/players/{global_id}/statistics/       GET
/players/{global_id}/contracts/        GET (restricted)
/players/{global_id}/achievements/     GET, POST
/players/{global_id}/videos/           GET, POST
/players/me/                           GET, PATCH (próprio jogador)
/players/me/onboarding/                GET, PATCH
/players/invite/                       POST (clube convida jogador)
```

---

## 5. Prioridade de Implementação (Resumo Executivo)

### Sprint 1 (Fundação Crítica)
1. **Adicionar `global_id` ao Player** — sem isto, o sistema não tem identidade global
2. **Adicionar `PlayerStatus`** — ACTIVE/INACTIVE/RETIRED/DECEASED
3. **Criar `PlayerIdentityDocument`** — substituir qualquer campo de BI angolano
4. **Criar `PlayerPrivacySettings`** — sem isto, dados sensíveis ficam expostos

### Sprint 2 (Identidade Completa)
5. **Criar `PlayerContact` + `EmergencyContact`**
6. **Criar `LegalGuardian`** com validação de menores
7. **Criar `PlayerExternalId`** (preparação FIFA Connect)
8. **Domain Events Fase 1**

### Sprint 3 (Football Identity)
9. **Melhorar `PlayerRegistration`** — campos em falta
10. **Criar `PlayerCareer`** — historial cronológico
11. **Criar `PlayerFootballProfile`** — separar campos de futebol
12. **Criar `PlayerSeasonStatistics`** + refatorar `stats_sync_service`

### Sprint 4 (Onboarding + Selectors)
13. **`PlayerOnboardingService`** — wizard de onboarding
14. **Selectors completos** — `get_current_club`, `get_career_timeline`, etc.
15. **Permissões por role** — `PlayerPermission` classes

### Sprint 5+ (Professional)
16. **`PlayerContract`**
17. **`Agent` + `PlayerAgentRelationship`**
18. **`PlayerTrainingHistory`** (Solidarity Contribution)
19. **Integração Transfer workflow**

---

## 6. Riscos e Decisões Pendentes

| Risco | Impacto | Mitigação |
|---|---|---|
| Migração de `global_id` em dados existentes | ALTO | Gerar `global_id` retroativamente em migração de dados |
| God Model no Player atual | MÉDIO | Auditar e mover campos para modelos especializados gradualmente |
| `PlayerContract` vs. `transfers/` — duplicação | MÉDIO | Definir claramente: `transfers/` gere o processo, `players/` gere o contrato |
| Suporte a menores (LegalGuardian) | ALTO legal | Implementar no Sprint 2, antes de qualquer onboarding de menores |
| Privacidade de dados médicos | ALTO | `PlayerMedicalProfile` com ACL restrito desde o início |
| Regras RSTP 2027 hardcoded | MÉDIO | Modelar regras como configurações por regulamento, não como código |
| `PlayerPosition` — ArrayField para posições secundárias | BAIXO | Verificar se PostgreSQL ArrayField está configurado no projeto |

---

## 7. Convenções do Projeto a Manter

Com base na estrutura existente do repositório:

- **Padrão Service/Selector/Serializer** — já adotado, manter consistente
- **TenantModel como base** — todos os modelos herdam do modelo base multi-tenant
- **`core/events/dispatcher.py`** — usar o dispatcher existente para eventos
- **`media_assets/`** — usar o sistema de media existente para todos os uploads
- **Celery** — tasks assíncronas via `config/celery.py`
- **Testes** — manter a prática de `test_models.py`, `test_api.py`, `test_services.py`
- **Migrações** — numeração sequencial `000X_descricao.py`

---

_Documento gerado em 2026-08-08. Rever após leitura do código-fonte completo dos modelos para validar campos actuais vs. previstos._
