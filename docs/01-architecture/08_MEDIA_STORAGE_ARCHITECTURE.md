# MEDIA STORAGE ARCHITECTURE

**Documento:** `08_MEDIA_STORAGE_ARCHITECTURE.md`

**Versão:** 2.0.0

**Estado:** Documento Oficial de Arquitetura de Armazenamento de Media

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define a arquitetura oficial para armazenamento, gestão e distribuição de ficheiros no Bolayetu.

O objetivo é garantir:

* escalabilidade;
* alta disponibilidade;
* baixo custo;
* segurança;
* desempenho;
* integração com Cloudflare.

O backend não deverá utilizar armazenamento local em ambientes de produção.

---

# 2. Princípios

A arquitetura de media deverá seguir os seguintes princípios:

* Cloud Native
* Object Storage
* CDN First
* Stateless Backend
* Versionamento
* Alta Disponibilidade
* Segurança
* Escalabilidade Horizontal

---

# 3. Arquitetura Geral

```text
               Utilizador
                    │
                    ▼
            React Frontend
                    │
                    ▼
           Django REST API
                    │
                    ▼
            Media Service Layer
                    │
                    ▼
            Cloudflare R2 Bucket
                    │
                    ▼
            Cloudflare CDN
                    │
                    ▼
              Browser / Mobile
```

O backend atua apenas como orquestrador.

Nunca deverá armazenar ficheiros permanentemente.

---

# 4. Componentes

## Frontend

Responsável por:

* selecionar ficheiros;
* validar formatos básicos;
* apresentar progresso do upload;
* visualizar conteúdos.

---

## Backend

Responsável por:

* autenticação;
* autorização;
* validação;
* geração de nomes únicos;
* metadados;
* integração com o Storage Provider.

---

## Cloudflare R2

Responsável pelo armazenamento permanente.

---

## Cloudflare CDN

Responsável pela distribuição dos ficheiros.

---

# 5. Tipos de Conteúdo

A plataforma deverá suportar:

## Imagens

* Fotografias
* Logótipos
* Banners
* Escudos
* Avatares

---

## Documentos

* PDF
* DOCX
* XLSX

---

## Vídeos

* Highlights
* Treinos
* Apresentações
* Entrevistas

---

## Áudio

* Podcasts
* Entrevistas

---

## Relatórios

* Estatísticas
* PDFs
* Exportações

---

# 6. Organização dos Buckets

Utilizar um único bucket principal.

Exemplo:

```text
bolayetu-storage/
```

A organização lógica será feita por prefixos.

---

# 7. Estrutura de Diretórios

```text
tenant/

organization/

clubs/

players/

competitions/

matches/

documents/

reports/

avatars/

logos/

banners/

videos/

exports/

temp/
```

Exemplo:

```text
tenant/faf/

clubs/

petro/

logo.png
```

---

# 8. Organização por Tenant

Todos os ficheiros pertencem a um Tenant.

Exemplo:

```text
tenant/faf/

tenant/girabola/

tenant/apf-luanda/
```

Esta estrutura facilita:

* auditoria;
* backups;
* migração;
* isolamento.

---

# 9. Organização por Domínio

Dentro de cada Tenant:

```text
clubs/

players/

competitions/

matches/

media/

reports/
```

---

# 10. Convenção de Nomes

Nunca utilizar o nome original do ficheiro.

Formato recomendado:

```text
UUID.ext
```

Exemplo:

```text
7d9a3e5f-33f4-4f6a-b221-acde98765432.jpg
```

Isto evita colisões e exposição de informação sensível.

---

# 11. Metadados

A base de dados deverá armazenar apenas metadados.

Campos recomendados:

* id
* uuid
* tenant
* owner_type
* owner_id
* original_name
* filename
* mime_type
* extension
* size
* checksum
* bucket
* object_key
* cdn_url
* uploaded_by
* uploaded_at

Nunca armazenar o conteúdo binário na base de dados.

---

# 12. Fluxo de Upload

```text
Utilizador

↓

Frontend

↓

Validação

↓

API

↓

Media Service

↓

Cloudflare R2

↓

Guardar Metadados

↓

Resposta com URL CDN
```

---

# 13. Fluxo de Download

```text
Browser

↓

Cloudflare CDN

↓

Cloudflare R2
```

O backend não participa no download de ficheiros públicos.

---

# 14. Fluxo para Conteúdo Privado

```text
Utilizador

↓

API

↓

Autorização

↓

Signed URL

↓

Cloudflare R2

↓

Download
```

Conteúdos privados deverão utilizar URLs temporárias.

---

# 15. Categorias de Visibilidade

## Pública

Exemplos:

* escudos;
* fotografias públicas;
* banners.

---

## Restrita

Exemplos:

* documentos internos;
* contratos;
* certificados.

---

## Privada

Exemplos:

* documentos médicos;
* ficheiros financeiros;
* documentação legal.

---

# 16. Segurança

Todo upload deverá validar:

* tipo MIME;
* extensão;
* tamanho;
* utilizador;
* Tenant.

Nunca confiar apenas na extensão do ficheiro.

---

# 17. Limites

Cada plano poderá definir:

* armazenamento máximo;
* tamanho máximo por ficheiro;
* número máximo de uploads.

---

# 18. Processamento

Após upload poderão ser executadas tarefas assíncronas:

* geração de thumbnails;
* otimização de imagens;
* conversão de formatos;
* extração de metadados;
* geração de previews.

Estas tarefas serão executadas pelo Celery.

---

# 19. Imagens

As imagens deverão possuir variantes.

Exemplo:

```text
original/

thumbnail/

small/

medium/

large/
```

O frontend deverá utilizar sempre a variante mais adequada.

---

# 20. Vídeos

Os vídeos poderão possuir:

* thumbnail;
* duração;
* resolução;
* formato;
* tamanho.

No futuro poderá ser integrado um serviço de transcodificação.

---

# 21. Cache

O Cloudflare deverá gerir:

* cache HTTP;
* compressão;
* otimização;
* expiração.

Os URLs deverão permitir invalidação quando necessário.

---

# 22. Versionamento

Quando um ficheiro for substituído:

* gerar novo objeto;
* atualizar metadados;
* invalidar cache.

Evitar reutilizar o mesmo objeto.

---

# 23. Eliminação

A eliminação deverá seguir o fluxo:

1. Remover referência lógica.
2. Agendar remoção física.
3. Executar tarefa assíncrona.
4. Registar auditoria.

---

# 24. Backups

Os ficheiros deverão possuir estratégia de recuperação compatível com as políticas do Cloudflare R2.

Os metadados deverão ser incluídos nos backups da base de dados.

---

# 25. API de Media

Endpoints previstos:

```text
POST   /api/v1/media/upload
GET    /api/v1/media/{id}
DELETE /api/v1/media/{id}
GET    /api/v1/media/{id}/signed-url
```

Todas as operações deverão respeitar Tenant, permissões e ownership.

---

# 26. Estrutura Django

```text
apps/

media/

models/

services/

storage/

validators/

serializers/

views/

tasks/

permissions/

selectors/

tests/
```

O módulo `storage/` encapsula qualquer integração com fornecedores de armazenamento.

---

# 27. Interface de Storage

A aplicação deverá depender de uma abstração.

```python
StorageProvider

upload()

download()

delete()

generate_signed_url()

exists()

copy()

move()
```

Esta abordagem permite substituir o fornecedor de armazenamento sem alterar a lógica de negócio.

---

# 28. Observabilidade

Monitorizar:

* uploads;
* downloads;
* falhas;
* tempo de resposta;
* utilização de armazenamento;
* consumo por Tenant.

---

# 29. Escalabilidade

A arquitetura deverá suportar:

* milhões de ficheiros;
* milhares de uploads simultâneos;
* distribuição global;
* crescimento sem alterações estruturais.

---

# 30. Regras Obrigatórias

É obrigatório:

* utilizar Cloudflare R2 em produção;
* distribuir conteúdos através da Cloudflare CDN;
* armazenar apenas metadados na base de dados;
* organizar ficheiros por Tenant;
* utilizar UUID como nome físico;
* validar todos os uploads;
* utilizar URLs temporárias para conteúdos privados.

É proibido:

* utilizar `MEDIA_ROOT` em produção;
* armazenar ficheiros binários na base de dados;
* expor buckets diretamente;
* reutilizar nomes de ficheiros enviados pelos utilizadores.

---

# 31. Architecture Decision Record

## ADR-007 — Arquitetura de Armazenamento

**Decisão**

Adotar **Cloudflare R2** como armazenamento oficial e **Cloudflare CDN** como camada de distribuição.

**Justificação**

* Elevada escalabilidade.
* Excelente integração com a infraestrutura Cloudflare.
* Custos reduzidos.
* Distribuição global de baixa latência.
* Backend completamente stateless.
* Facilidade de migração entre ambientes.
* Compatibilidade com futuras aplicações móveis e APIs públicas.

Esta decisão é estrutural e deverá ser seguida por todos os módulos da plataforma.
