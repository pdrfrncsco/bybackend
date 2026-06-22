# Módulo de Treinadores — Checklist e Testes

## Checklist de Integração (Backend)
- App `treinadores` presente em `INSTALLED_APPS`.
- Migrations aplicadas (`treinadores.0001_initial`).
- Rotas incluídas em `config/urls.py`:
  - `GET/POST /api/treinadores/`
  - `GET/PUT/PATCH /api/treinadores/{id}/`
  - `GET/POST /api/treinadores/{id}/historico/`
  - `POST /api/treinadores/{id}/historico/encerrar/`
  - `GET /api/treinadores/{id}/relatorio/`
- Regra de integridade: no máximo 1 histórico ativo por treinador (`data_fim = null`).
- Regra de negócio: histórico não é editado por endpoints genéricos (apenas criação e encerramento).
- Restrições multi-tenant: Treinador e Clube filtrados/validados pelo `request.user.tenant`.

## Checklist de Integração (Frontend)
- Types adicionados em `src/types.ts`:
  - `Treinador`, `HistoricoTreinador`, `LicencaTreinador`, `TreinadorRelatorioPayload`
- Service `src/services/treinador.service.ts` disponível para consumir a API.
- Componentes base criados:
  - `TreinadorList`
  - `TreinadorProfile`
  - `TreinadorHistoricoTimeline`
  - `TreinadorForm`
  - `TreinadorRelatorio`
- PWA sem cache fantasma: definir `VITE_BUILD_VERSION` no build/deploy para versionar `cacheId`/`cacheName`.

## Sugestões de Testes Unitários (API)
- **Permissões**
  - `GET /api/treinadores/` exige autenticação.
  - `POST/PUT/PATCH /api/treinadores/...` exige perfil Manager/Admin (ou RBAC equivalente).
- **Serialização**
  - `GET /api/treinadores/{id}/` retorna `historico` embutido (ordenado corretamente).
- **Histórico**
  - `POST /api/treinadores/{id}/historico/` rejeita criação quando já existe histórico ativo.
  - `POST /api/treinadores/{id}/historico/encerrar/` encerra apenas o histórico ativo.
  - Validação: `data_fim >= data_inicio` e `jogos >= vitorias+empates+derrotas`.
- **Tenant**
  - `POST historico` rejeita `clube` fora do tenant do utilizador.

## Sugestões de Testes Unitários (Relatórios)
- `GET /api/treinadores/{id}/relatorio/`:
  - total de jogos = soma dos históricos
  - % vitórias calculada corretamente (0..100)
  - tempo médio por clube coerente com intervalos (`data_inicio`..`data_fim` ou hoje)
  - histórico cronológico ordenado por `data_inicio`

