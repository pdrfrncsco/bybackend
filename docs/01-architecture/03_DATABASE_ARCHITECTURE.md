# DATABASE ARCHITECTURE

**Documento:** `03_DATABASE_ARCHITECTURE.md`

**Versão:** 2.0.0

**Estado:** Documento Oficial de Arquitetura da Base de Dados

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define a arquitetura da Base de Dados do Bolayetu.

O seu propósito é estabelecer os princípios de modelação, organização dos dados e relacionamento entre entidades, garantindo uma base sólida para o desenvolvimento da plataforma.

Este documento serve como referência para:

* Modelação de dados.
* Desenvolvimento Backend.
* Definição de APIs.
* Estratégias de migração.
* Performance.
* Escalabilidade.
* Auditoria.

---

# 2. Princípios da Arquitetura

A Base de Dados deverá obedecer aos seguintes princípios:

* Normalização até à 3ª Forma Normal (3NF), salvo exceções justificadas por desempenho.
* Separação clara entre domínios.
* Integridade referencial.
* Histórico preservado.
* Multi-Tenancy.
* Auditoria.
* Baixo acoplamento entre módulos.
* Preparação para crescimento internacional.

---

# 3. Tecnologia Oficial

O SGBD oficial da plataforma é:

**PostgreSQL**

Razões para a escolha:

* Robustez.
* Integridade transacional (ACID).
* Excelente suporte a índices.
* JSONB para dados semiestruturados.
* Full Text Search.
* Extensões GIS (PostGIS) para futuras funcionalidades geográficas.
* Escalabilidade.

SQLite apenas poderá ser utilizada para prototipagem local e nunca em ambientes de produção.

---

# 4. Organização por Domínios

A base de dados será organizada de acordo com os domínios do negócio.

```text id="3kdnpc"
Accounts

Organizations

Clubs

Players

Fans

Competitions

Matches

Standings

Statistics

Transfers

News

Notifications

Billing

Subscriptions

Media

Analytics
```

Cada domínio é responsável pelas suas próprias entidades.

---

# 5. Modelo Conceptual

```text id="ltybq5"
Tenant
   │
Organization
   │
Competition
   │
Season
   │
Club
   │
Squad
   │
Player
   │
Career
   │
Match
   │
Statistics
```

Este diagrama representa apenas as relações de alto nível.

---

# 6. Entidades Fundamentais

A plataforma possui um conjunto de entidades consideradas nucleares.

## Tenant

Representa uma Organização independente dentro do modelo SaaS.

Cada Tenant possui:

* Domínio.
* Configurações.
* Branding.
* Utilizadores.
* Dados isolados.

---

## User

Representa a identidade digital.

Contém apenas:

* autenticação;
* credenciais;
* segurança.

Nunca deverá conter dados de negócio.

---

## Organization

Representa uma federação, associação, liga ou organizador de competições.

É responsável pela gestão desportiva do seu Tenant.

---

## Club

Representa uma entidade desportiva.

Possui:

* identidade;
* branding;
* plantel;
* equipa técnica;
* participação em competições.

---

## Player

Representa um atleta.

Possui identidade permanente na plataforma.

O histórico nunca deverá ser eliminado.

---

## Competition

Representa um campeonato, taça ou torneio.

Sempre pertence a uma Organização.

---

## Match

Representa uma partida oficial.

Relaciona:

* competição;
* jornada;
* clubes;
* estatísticas.

---

## Standing

Representa a classificação atual de uma competição.

Deverá ser recalculável.

---

## Statistics

Representa métricas produzidas a partir dos eventos desportivos.

Nunca deverá armazenar dados redundantes sem justificação.

---

# 7. Relações de Negócio

As principais relações são:

```text id="wrvdl7"
Tenant

1:N

Organizations

1:N

Competitions

1:N

Matches

N:N

Clubs

1:N

Players
```

Além destas existirão relações específicas para:

* inscrições;
* contratos;
* transferências;
* equipa técnica;
* patrocinadores;
* notícias.

---

# 8. Estratégia Multi-Tenant

Todos os dados deverão pertencer a um Tenant.

Modelo adotado:

**Shared Database + Shared Schema + Tenant Identifier**

Cada entidade relevante possuirá referência ao Tenant.

Exemplo conceptual:

```text id="fs9vkf"
Tenant

↓

Organization

↓

Competition

↓

Club

↓

Player
```

Nenhuma consulta deverá devolver dados de outro Tenant.

---

# 9. Estratégia de Chaves

Todas as entidades utilizarão:

* Primary Key.
* Foreign Keys.
* Constraints.

Recomenda-se o uso de UUID como identificador público.

As relações deverão utilizar Foreign Keys para garantir integridade.

---

# 10. Integridade Referencial

As seguintes regras são obrigatórias:

* Não eliminar entidades com histórico relevante.
* Utilizar exclusão lógica (soft delete) quando apropriado.
* Preservar o histórico de carreira dos jogadores.
* Preservar o histórico de transferências.
* Preservar o histórico de competições.

---

# 11. Histórico

Algumas entidades são históricas por natureza.

Exemplos:

* Career History.
* Club Affiliation.
* Transfers.
* Seasons.
* Match Results.

Esses dados nunca deverão ser substituídos ou sobrescritos.

Sempre deverão gerar novos registos.

---

# 12. Auditoria

Todas as entidades críticas deverão suportar auditoria.

Campos recomendados:

* created_at
* updated_at
* created_by
* updated_by
* deleted_at (quando aplicável)

No futuro poderá existir uma tabela específica de auditoria para alterações sensíveis.

---

# 13. Estratégia de Índices

Índices deverão ser utilizados para:

* Foreign Keys.
* Pesquisas frequentes.
* Campos únicos.
* Consultas por Tenant.
* Datas.
* Slugs.

Índices compostos deverão ser utilizados apenas quando suportados por análises de desempenho.

---

# 14. Performance

A arquitetura deverá privilegiar:

* consultas eficientes;
* paginação;
* agregações otimizadas;
* cache;
* pré-processamento de estatísticas.

Evitar consultas N+1.

Utilizar `select_related` e `prefetch_related` quando apropriado.

---

# 15. Versionamento dos Dados

As alterações relevantes deverão preservar versões históricas.

Exemplos:

* Regulamentos.
* Configurações.
* Planos de subscrição.
* Estatísticas consolidadas.

Nunca substituir informação histórica sem necessidade.

---

# 16. Armazenamento de Ficheiros

A Base de Dados nunca armazenará ficheiros binários.

Serão armazenados apenas:

* URL pública.
* Metadados.
* Tipo.
* Tamanho.
* Hash.
* Data de upload.

Os ficheiros serão mantidos no Cloudflare R2.

---

# 17. Escalabilidade

A arquitetura deverá suportar:

* milhares de organizações;
* centenas de milhares de jogadores;
* milhões de partidas;
* milhões de estatísticas.

O crescimento deverá ocorrer sem alterações estruturais significativas.

---

# 18. Convenções

Todas as entidades deverão seguir convenções uniformes.

## Nomenclatura

* Singular para modelos.
* Snake_case para campos.
* UUID para identificadores públicos.
* Slug para URLs amigáveis.

## Datas

Utilizar sempre UTC na persistência.

A conversão para o fuso horário do utilizador será responsabilidade da camada de apresentação.

---

# 19. Segurança

A Base de Dados deverá garantir:

* isolamento entre Tenants;
* integridade referencial;
* validação de permissões na camada de aplicação;
* proteção contra exclusões acidentais;
* backups automáticos.

---

# 20. Evolução

A arquitetura foi concebida para incorporar novos domínios sem comprometer os existentes.

Domínios previstos:

* Scouts
* Árbitros
* Empresários
* Academias
* Patrocinadores
* Formação
* Marketplace
* APIs Públicas

Todos os novos domínios deverão respeitar os princípios definidos neste documento.

---

# 21. Regras Fundamentais

1. Todo o dado pertence a um domínio de negócio.
2. Todo o dado relevante pertence a um Tenant.
3. O histórico nunca deverá ser perdido.
4. A integridade referencial é obrigatória.
5. A Base de Dados não deverá conter lógica de negócio.
6. As estatísticas deverão ser derivadas dos eventos sempre que possível.
7. Os ficheiros deverão permanecer fora da Base de Dados.
8. A arquitetura deverá privilegiar evolução e escalabilidade em detrimento de otimizações prematuras.
