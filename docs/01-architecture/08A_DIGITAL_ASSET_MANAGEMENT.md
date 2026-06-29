# 08A_DIGITAL_ASSET_MANAGEMENT.md

**Documento:** `08A_DIGITAL_ASSET_MANAGEMENT.md`

**Versão:** 2.0.0

**Estado:** Documento Oficial

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define a arquitetura oficial de gestão de ativos digitais (Digital Asset Management - DAM) do Bolayetu.

Todos os ficheiros da plataforma serão tratados como ativos digitais reutilizáveis.

O objetivo é eliminar duplicação, aumentar a reutilização e centralizar toda a gestão de conteúdos multimédia.

---

# 2. O que é um Asset?

Um Asset representa qualquer recurso digital utilizado pela plataforma.

Exemplos:

* Fotografia
* Logótipo
* Escudo
* Documento
* Vídeo
* Áudio
* Banner
* Relatório
* Thumbnail

O Asset é uma entidade de negócio.

O ficheiro físico é apenas uma representação desse Asset.

---

# 3. Arquitetura

```text
                Frontend

                    │

                    ▼

            Asset Service

                    │

          Asset Manager (DAM)

                    │

        ┌───────────┼────────────┐

        ▼           ▼            ▼

 Metadata     Cloudflare R2     CDN

        │

        ▼

 PostgreSQL
```

---

# 4. Entidade Principal

MediaAsset

Esta será uma entidade Global.

Nunca pertence exclusivamente a um módulo.

---

# 5. Estrutura Conceptual

MediaAsset

↓

Storage Object

↓

Variants

↓

Usage

↓

Permissions

↓

Audit

---

# 6. Campos

MediaAsset

* UUID
* Nome
* Slug
* Tipo
* Categoria
* MIME
* Extensão
* Tamanho
* Hash SHA256
* Bucket
* Object Key
* CDN URL
* Private URL
* Thumbnail URL
* Owner
* Tenant
* Visibility
* Status
* Uploaded By
* Uploaded At
* Updated At

---

# 7. Owner

Todo Asset pertence a alguém.

Pode ser:

Player

Club

Competition

Organization

Match

News

System

---

# 8. Asset Categories

Avatar

Logo

Banner

Cover

Gallery

Video

Document

Certificate

Report

Export

News Image

Sponsor Logo

---

# 9. Asset Types

IMAGE

VIDEO

DOCUMENT

AUDIO

PDF

ARCHIVE

---

# 10. Asset Visibility

PUBLIC

INTERNAL

PRIVATE

SIGNED

---

# 11. Asset Status

UPLOADING

PROCESSING

READY

ARCHIVED

DELETED

---

# 12. Variants

Um Asset pode possuir várias versões.

```text
Original

↓

Thumbnail

↓

Small

↓

Medium

↓

Large

↓

WebP

↓

AVIF
```

---

# 13. Relação entre Objetos

```text
Player

↓

MediaAsset

↓

Usage

↓

Competition

↓

News
```

O mesmo ficheiro pode ser utilizado por vários módulos.

---

# 14. Asset Usage

Em vez de duplicar ficheiros...

Criamos ligações.

```text
MediaAsset

↓

MediaUsage

↓

Player

↓

MediaUsage

↓

News

↓

MediaUsage

↓

Competition
```

---

# 15. Benefícios

Um único upload.

Múltiplas utilizações.

Sem duplicação.

---

# 16. Tags

Os Assets poderão possuir Tags.

Exemplo:

Angola

Girabola

Petro

Goalkeeper

Sponsor

Training

Final

---

# 17. Pesquisa

A pesquisa poderá utilizar:

Nome

Tags

Tipo

Categoria

Tenant

Owner

Data

---

# 18. Versionamento

Cada alteração gera nova versão.

```text
Asset

↓

Version 1

↓

Version 2

↓

Version 3
```

Nunca substituir diretamente o ficheiro.

---

# 19. Thumbnail Service

Após upload:

Celery

↓

Thumbnail

↓

WebP

↓

AVIF

↓

Metadata

---

# 20. Metadata

Será possível extrair automaticamente:

Imagens

* largura
* altura
* orientação

Vídeos

* duração
* resolução
* codec

PDF

* páginas

---

# 21. Auditoria

Todo Asset deverá possuir histórico.

Upload

Visualização

Download

Partilha

Eliminação

---

# 22. Asset Permissions

Exemplo:

Organization Admin

↓

Pode eliminar

Club Manager

↓

Pode editar

Player

↓

Pode gerir apenas os próprios Assets

---

# 23. APIs

```text
POST

/api/v1/assets

GET

/api/v1/assets

GET

/api/v1/assets/{id}

PATCH

/api/v1/assets/{id}

DELETE

/api/v1/assets/{id}

POST

/api/v1/assets/{id}/variants

GET

/api/v1/assets/search
```

---

# 24. Django

Novo módulo:

```text
apps/

media/

models/

MediaAsset

MediaVariant

MediaUsage

MediaTag

MediaFolder

MediaCollection

services/

selectors/

tasks/

storage/

permissions/
```

---

# 25. Media Collections

Será possível criar coleções.

Exemplo:

Petro 2027

Girabola 2028

Final da Taça

Treinos

Sponsors

---

# 26. Futuro

Este módulo permitirá:

Biblioteca de imagens.

Galerias.

Vídeos.

Marketplace.

Conteúdo patrocinado.

IA para reconhecimento de imagens.

OCR de documentos.

Compressão automática.

CDN inteligente.

---

# 27. Regras

Nunca armazenar ficheiros em módulos.

Todos os módulos utilizam MediaAsset.

Nunca duplicar Assets.

Nunca guardar caminhos físicos.

Sempre utilizar UUID.

Sempre utilizar MediaUsage para relacionamentos.

---

# 28. ADR

## ADR-008

O Bolayetu adotará uma arquitetura Digital Asset Management (DAM).

Todos os ficheiros da plataforma serão tratados como Assets reutilizáveis.

Esta decisão reduz duplicação, melhora escalabilidade e aproxima a plataforma de soluções empresariais modernas.
