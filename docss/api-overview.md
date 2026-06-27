# Documentação da API BolaYetu – Visão Geral e Hosts

Este documento descreve como consumir a API do BolaYetu em ambientes de desenvolvimento e produção, alinhado com as configurações e domínios actualmente definidos no projecto.

- Backend (API): `https://api-bolayetu-manager.ndeas.cloud`
- Frontend (SPA): `https://bolayetu.ndeas.cloud`

A especificação completa da API é gerada automaticamente via **drf-spectacular** e exposta em:

- Swagger UI: `/api/docs/`
- Redoc: `/api/redoc/`
- Esquema OpenAPI (JSON): `/api/schema/`

---

## 1. Hosts e Base URLs

### 1.1. Produção

- **Host da API**: `https://api-bolayetu-manager.ndeas.cloud`
- **Base path**: `/api/`

Exemplo de URLs em produção:

- Autenticação (login): `https://api-bolayetu-manager.ndeas.cloud/api/auth/login/`
- Perfis de utilizador: `https://api-bolayetu-manager.ndeas.cloud/api/auth/me/`
- Torneios: `https://api-bolayetu-manager.ndeas.cloud/api/tournaments/`
- Clubs: `https://api-bolayetu-manager.ndeas.cloud/api/clubs/`
- Jogadores: `https://api-bolayetu-manager.ndeas.cloud/api/players/`
- Match Engine: `https://api-bolayetu-manager.ndeas.cloud/api/matchengine/`

### 1.2. Desenvolvimento local

Quando o backend está a correr localmente (por exemplo, `python manage.py runserver 0.0.0.0:8000` ou Gunicorn em `127.0.0.1:8000`), a API fica disponível em:

- **Base URL dev**: `http://localhost:8000/api/`

O frontend Vite, por padrão, usa:

- `VITE_API_BASE_URL` (ver secção 4) ou, na ausência, `http://localhost:8000/api`.

---

## 2. Descoberta da API (Swagger / Redoc)

O ficheiro [config/urls.py](file:///c:/Project/bolayetu/backend/config/urls.py) expõe os endpoints de documentação:

- `GET /api/schema/` – esquema OpenAPI em JSON.
- `GET /api/docs/` – Swagger UI para explorar e testar endpoints.
- `GET /api/redoc/` – documentação gerada em Redoc.

Internamente, estes endpoints são configurados por:

```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'BolaYetu API',
    'DESCRIPTION': 'Documentação da API do BolaYetu',
    'VERSION': '1.0.0',
    # ...
}
```

---

## 3. Autenticação e Autorização

A API usa **JWT (JSON Web Tokens)** via `djangorestframework-simplejwt`. As definições relevantes encontram-se em [config/settings.py](file:///c:/Project/bolayetu/backend/config/settings.py#L184-L189):

- Tempo de vida do access token: 1 dia.
- Tempo de vida do refresh token: 7 dias.

### 3.1. Endpoints de autenticação

Definidos em [usuarios/urls.py](file:///c:/Project/bolayetu/backend/usuarios/urls.py):

- `POST /api/auth/login/` – obtém o par (`access`, `refresh`).
- `POST /api/auth/token/refresh/` – renova o `access` com base no `refresh`.
- `GET /api/auth/me/` – devolve dados do utilizador autenticado.
- `POST /api/auth/register/` – registo (quando exposto conforme as regras de negócio).

### 3.2. Exemplo de login via cURL

```bash
curl -X POST \
  https://api-bolayetu-manager.ndeas.cloud/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "sua_senha_aqui"
  }'
```

Resposta esperada (resumida):

```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>"
}
```

### 3.3. Chamadas autenticadas

Depois de obter o `access`, inclua-o no cabeçalho `Authorization`:

```bash
curl -X GET \
  https://api-bolayetu-manager.ndeas.cloud/api/tournaments/ \
  -H "Authorization: Bearer <jwt_access_token>"
```

---

## 4. Integração com o Frontend (Vite)

No frontend, a base URL da API é configurada via variável de ambiente Vite:

Ficheiro: [frontend/.env.example](file:///c:/Project/bolayetu/frontend/.env.example)

```env
VITE_API_BASE_URL=https://api-bolayetu-manager.ndeas.cloud/api
```

O cliente Axios central está em [frontend/services/api.ts](file:///c:/Project/bolayetu/frontend/services/api.ts):

```ts
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});
```

- Em produção, configure `VITE_API_BASE_URL` para apontar para `https://api-bolayetu-manager.ndeas.cloud/api`.
- Em desenvolvimento, se não definir `VITE_API_BASE_URL`, o frontend usará `http://localhost:8000/api`.

---

## 5. Principais grupos de endpoints

Os grupos principais de endpoints são definidos em [config/urls.py](file:///c:/Project/bolayetu/backend/config/urls.py#L7-L31):

- `/api/auth/` – autenticação e gestão de utilizadores (`usuarios`).
- `/api/clubs/` – gestão de clubs (`clubs`).
- `/api/players/` – gestão de jogadores (`jogadores`).
- `/api/matches/` – agendamento e dados de jogos (`partidas`).
- `/api/onboarding/` – fluxo de onboarding e configuração inicial (`onboarding`).
- `/api/tournaments/` – torneios e formatos (`torneios`).
- `/api/classificacoes/` – classificações e standings de competições (`classificacoes`).
- `/api/matchengine/` – eventos em tempo real e motor de jogo (`matchengine`).
- `/api/stadiums/` – gestão de estádios (`estadios`).
- `/api/dashboard/` – KPIs e dados de painel (`dashboard`).
- `/api/notifications/` – notificações e canais (`notifications`).
- `/api/organizations/` – organizações/tenants (`organizacoes`).
- `/api/fanportal/` – endpoints do portal do adepto (`fanportal`).
- `/api/news/` – notícias (`news`).
- `/api/ads/` – gestão de publicidade (`ads`).
- `/api/subscriptions/` – assinaturas e planos (`assinaturas`).
- `/api/reports/` – relatórios e documentos (`relatorios`).
- `/api/definicoes/` – definições e configurações globais (`definicoes`).

Cada um destes módulos expõe os seus endpoints detalhados no esquema OpenAPI em `/api/schema/` e nas UIs `/api/docs/` e `/api/redoc/`.

---

## 6. CORS e consumo por domínios externos

Actualmente, em [config/settings.py](file:///c:/Project/bolayetu/backend/config/settings.py#L147-L148), o CORS está configurado como:

```python
CORS_ALLOW_ALL_ORIGINS = True
```

Isto permite que o frontend em `https://bolayetu.ndeas.cloud` consuma a API em `https://api-bolayetu-manager.ndeas.cloud` sem restrições adicionais.

Para ambientes mais restritos, recomenda‑se futuramente trocar para:

```python
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://bolayetu.ndeas.cloud",
]
```

---

## 7. Notas para evolução da documentação

- A documentação gerada automaticamente (Swagger/Redoc) acompanha alterações nos serializers e viewsets.
- Para endpoints mais complexos (por exemplo, fluxo de match engine ou relatórios), recomenda-se manter documentos específicos em `backend/docs/` ou em `.trae/documents/` detalhando:
  - Fluxos de negócio (ex.: criação de torneio, geração de calendário, actualização de eventos de jogo).
  - Exemplos de requests/responses de alto nível.

---

## 8. Papéis de utilizador e permissões (RBAC)

O backend utiliza um modelo de controlo de acesso baseado em papéis e permissões (RBAC), definido em [usuarios/models.py](file:///c:/Project/bolayetu/backend/usuarios/models.py#L7-L51) e [core/permissions.py](file:///c:/Project/bolayetu/backend/core/permissions.py#L4-L50).

### 8.1. Papéis principais (`User.role`)

Os valores possíveis para o campo `role` de utilizador são:

- `superadmin` – acesso de plataforma. Tem acesso total a todas as permissões.
- `ads_manager` – vocacionado para gestão de campanhas de publicidade.
- `admin` – administrador do tenant (organização).
- `manager` – gestor operacional do tenant (clubs, jogadores, torneios, etc.).
- `viewer` – utilizador de leitura, com acesso limitado.

Estes papéis são usados pelas permission classes:

- `IsAdmin` – permite acesso se `role` for `admin` ou `superadmin`, ou se o utilizador tiver permissões de gestão de tenant/plataforma.
- `IsManager` – permite acesso se `role` for `manager`, `admin`, `superadmin` ou `ads_manager`, ou se tiver permissões específicas (por exemplo, `manage_team`, `manage_players`, `manage_ads`).
- `HasPermission` – verifica permissões mais finas com base em códigos de permissão e roles atribuídos.

### 8.2. Roles e permissões dinâmicos

Para além do `role` principal, o utilizador pode ter múltiplos roles dinâmicos associados a um tenant ou à plataforma:

- Modelo `Role` – define um conjunto de permissões (`permissions`) com `code` (ex.: `manage_team`, `manage_tournaments`, `manage_reports`).
- Modelo `Permission` – representa um código de permissão reutilizável por vários roles.
- Modelo `UserRoleAssignment` – liga um `User` a um `Role`, opcionalmente por `tenant`.

O método `User.has_permission(code, tenant=None)`:

- Retorna `True` se o utilizador for `superuser` ou tiver `role = 'superadmin'`.
- Caso contrário, verifica se algum dos roles associados ao utilizador (para o tenant actual ou global) possui a permissão com o `code` indicado.

Alguns endpoints usam apenas `IsManager`/`IsAdmin`; outros combinam `IsManager` com `HasPermission` para exigir permissões adicionais associadas ao tenant (por exemplo, gestão de jogadores, clubs, relatórios ou anúncios).

### 8.3. Exemplos de códigos de permissão

Alguns códigos de permissão típicos (campo `Permission.code`) usados em roles:

| Código                    | Módulo         | Descrição resumida                                      |
|---------------------------|----------------|---------------------------------------------------------|
| `manage_platform`         | Plataforma     | Gestão global da plataforma (superadmin).              |
| `manage_tenant_settings`  | Definições     | Gestão de definições e configurações de tenant.        |
| `manage_team`             | Clubs         | Gestão de plantel e equipas do tenant.                 |
| `manage_players`          | Jogadores      | Gestão de jogadores (criar/editar/remover).            |
| `manage_tournaments`      | Torneios       | Gestão de torneios, calendário e classificações.       |
| `manage_reports`          | Relatórios     | Geração e acesso a relatórios administrativos.         |
| `manage_ads`              | Publicidade    | Gestão de campanhas de anúncios do tenant.             |

Estes códigos são atribuídos a roles (`Role.permissions`) e avaliados em runtime por `HasPermission` e `User.has_permission(code, tenant=...)`.

### 8.4. Como isto aparece no Swagger/Redoc

Nos endpoints protegidos, o Swagger/Redoc indicará:

- Tags como `"Admin/Manager Only"`, `"Users", "Admin Only"`, `"Relatórios", "Admin/Manager Only"`, etc.
- Descrições que mencionam explicitamente:
  - papéis necessários (`MANAGER`, `ADMIN`, `SUPERADMIN`);
  - quando se trata de endpoints públicos (`Public`, `Public News`);
  - quando basta estar autenticado (`Requer utilizador autenticado`).

Para a lista completa de endpoints e requisitos de acesso:

- Use `/api/schema/` para o JSON OpenAPI.
- Consulte `/api/docs/` (Swagger UI) ou `/api/redoc/` para descrições detalhadas actualizadas automaticamente com base nas annotations das views.

