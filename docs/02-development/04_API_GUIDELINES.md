# API GUIDELINES

**Documento:** `04_API_GUIDELINES.md`

**Versão:** 2.0.0

**Estado:** Guia Oficial de APIs

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define os padrões oficiais para o desenvolvimento e consumo das APIs do Bolayetu.

Todas as APIs deverão seguir estas regras.

Objetivos:

* Consistência
* Escalabilidade
* Segurança
* Documentação
* Versionamento
* Compatibilidade futura

---

# 2. Filosofia

O Bolayetu adota uma arquitetura **API First**.

Todo recurso da plataforma deverá ser disponibilizado através de APIs.

Interfaces Web, Mobile, PWA e integrações externas utilizarão exatamente os mesmos endpoints.

---

# 3. Base URL

Produção

```text
https://api.bolayetu.com/api/v1/
```

Staging

```text
https://staging-api.bolayetu.com/api/v1/
```

Desenvolvimento

```text
http://localhost:8000/api/v1/
```

---

# 4. Versionamento

Toda API deverá possuir versão.

Formato:

```text
/api/v1/
```

Exemplo:

```text
/api/v1/players

/api/v1/clubs

/api/v1/competitions
```

Nunca remover endpoints existentes sem política de depreciação.

---

# 5. Convenção REST

Utilizar apenas substantivos.

Bom exemplo:

```text
GET /players

POST /players

PATCH /players/{id}

DELETE /players/{id}
```

Evitar:

```text
/createPlayer

/deleteCompetition

/getPlayer
```

---

# 6. Métodos HTTP

GET

Consultar recursos.

POST

Criar recursos.

PUT

Substituir recurso completo.

PATCH

Atualizar parcialmente.

DELETE

Remover recurso.

---

# 7. Estrutura das URLs

Formato:

```text
/api/v1/{resource}
```

Exemplos:

```text
/api/v1/players

/api/v1/clubs

/api/v1/matches

/api/v1/statistics
```

Sub-recursos:

```text
/api/v1/clubs/{id}/players

/api/v1/competitions/{id}/matches

/api/v1/players/{id}/career
```

---

# 8. Formato das Respostas

Sucesso:

```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {}
}
```

Erro:

```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {}
}
```

---

# 9. Paginação

Formato padrão:

```json
{
  "count": 120,
  "next": "...",
  "previous": "...",
  "results": []
}
```

Parâmetros:

```text
?page=1

?page_size=20
```

---

# 10. Ordenação

Parâmetro:

```text
?ordering=name

?ordering=-created_at
```

---

# 11. Pesquisa

Parâmetro:

```text
?search=petro
```

---

# 12. Filtros

Formato:

```text
?status=active

?season=2027

?club=uuid

?organization=uuid
```

Filtros deverão utilizar `django-filter`.

---

# 13. Campos Selecionados

Suporte opcional para reduzir payload.

```text
?fields=id,name,photo
```

---

# 14. Inclusão de Relacionamentos

Formato:

```text
?include=club,statistics
```

Evita múltiplas chamadas quando apropriado.

---

# 15. Códigos HTTP

200 OK

201 Created

202 Accepted

204 No Content

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Unprocessable Entity

429 Too Many Requests

500 Internal Server Error

---

# 16. Identificadores

Todos os recursos públicos utilizarão UUID.

Exemplo:

```text
/api/v1/players/5f80f6cb-9d95-4f98-9fd5-39b23e80ab18
```

Nunca expor IDs incrementais.

---

# 17. Autenticação

Modelo oficial:

JWT

Cabeçalho:

```text
Authorization:

Bearer ACCESS_TOKEN
```

Refresh Token deverá possuir endpoint próprio.

---

# 18. Multi-Tenant

Toda API deverá executar dentro do contexto do Tenant.

Fluxo:

```text
Subdomain

↓

Tenant Resolver

↓

Authentication

↓

Permissions

↓

Endpoint
```

Nenhuma resposta poderá incluir dados de outro Tenant.

---

# 19. Permissões

As permissões deverão considerar:

* Tenant
* Role
* Ownership
* Estado da subscrição

Toda validação pertence ao backend.

---

# 20. Rate Limiting

Aplicar limites por:

* IP
* Utilizador
* Tenant
* Endpoint

Exemplos:

Login

Uploads

Recuperação de senha

APIs públicas

---

# 21. Erros

Formato único.

```json
{
  "success": false,
  "code": "PLAYER_ALREADY_REGISTERED",
  "message": "The player is already registered in this competition.",
  "errors": {
    "competition": [
      "Player already registered."
    ]
  }
}
```

Cada erro deverá possuir um código estável.

---

# 22. Uploads

Uploads utilizarão multipart/form-data.

Fluxo:

```text
Frontend

↓

API

↓

Media Service

↓

Cloudflare R2

↓

MediaAsset
```

Nunca armazenar ficheiros localmente em produção.

---

# 23. Downloads

Conteúdo público:

Cloudflare CDN.

Conteúdo privado:

Signed URLs temporárias.

---

# 24. Documentação

Toda API deverá ser documentada automaticamente.

Ferramenta oficial:

drf-spectacular

Documentação:

```text
/api/schema/

/api/docs/
```

Cada endpoint deverá conter:

* descrição;
* parâmetros;
* exemplos;
* códigos HTTP;
* permissões.

---

# 25. Idempotência

Operações críticas deverão suportar Idempotency Key.

Exemplos:

* pagamentos;
* inscrições;
* transferências;
* uploads.

Cabeçalho:

```text
Idempotency-Key:
```

---

# 26. Webhooks

Integrações externas deverão utilizar Webhooks.

Eventos previstos:

* PaymentConfirmed
* SubscriptionActivated
* PlayerTransferred
* MatchFinished

Todos deverão possuir assinatura HMAC.

---

# 27. APIs Públicas

No futuro existirão APIs públicas.

Exemplos:

* classificações;
* resultados;
* estatísticas;
* calendário;
* clubes;
* jogadores.

Estas APIs utilizarão API Keys.

---

# 28. Versionamento Futuro

Quando necessário:

```text
/api/v2/
```

A versão anterior deverá permanecer disponível durante o período de transição definido pela plataforma.

---

# 29. Segurança

Obrigatório:

* HTTPS
* JWT
* Rate Limiting
* Tenant Isolation
* RBAC
* Object Ownership
* Audit Logging

Nunca confiar no cliente.

---

# 30. Observabilidade

Cada chamada deverá registar:

* Request ID
* Tenant
* Utilizador
* Endpoint
* Método
* Tempo de resposta
* Código HTTP

Facilita monitorização e auditoria.

---

# 31. Convenções

Recursos:

Plural.

```text
players

clubs

competitions

matches
```

Campos:

snake_case

```json
{
  "first_name": "Pedro"
}
```

Datas:

ISO-8601 UTC.

```text
2026-07-12T15:30:00Z
```

Booleanos:

```json
true

false
```

---

# 32. Checklist para Novos Endpoints

Antes de publicar um endpoint verificar:

* URL padronizada.
* Método HTTP correto.
* Serializer adequado.
* Permissions implementadas.
* Tenant validado.
* Paginação quando necessário.
* Documentação OpenAPI.
* Testes automatizados.
* Tratamento de erros.
* Logging.

---

# 33. Regras Obrigatórias

É obrigatório:

* utilizar REST.
* utilizar UUID.
* documentar todos os endpoints.
* validar permissões.
* utilizar respostas padronizadas.
* implementar paginação em listagens.
* utilizar filtros oficiais.
* manter compatibilidade entre versões.

É proibido:

* expor IDs internos.
* criar endpoints sem documentação.
* alterar contratos sem versionamento.
* devolver dados de outros Tenants.
* utilizar verbos nas URLs.

---

# 34. Evolução da Plataforma

A arquitetura foi concebida para suportar:

* aplicações móveis nativas;
* parceiros externos;
* marketplace;
* APIs públicas;
* SDKs oficiais;
* integrações com federações, ligas e serviços terceiros.

Todas as novas APIs deverão manter compatibilidade com estas diretrizes.

---

# 35. Architecture Decision Record

## ADR-014 — Estratégia de APIs

**Decisão**

Adotar uma arquitetura **REST API First**, versionada, documentada automaticamente, segura e preparada para múltiplos clientes.

**Justificação**

* Permite reutilização da lógica de negócio.
* Facilita integrações.
* Suporta Web, Mobile, PWA e parceiros.
* Simplifica manutenção e evolução.
* Garante consistência entre todos os consumidores da plataforma.

Este documento é a referência oficial para qualquer endpoint desenvolvido no Bolayetu.
