# GLOSSARY

**Documento:** `03_GLOSSARY.md`
**Versão:** 2.0.0
**Estado:** Documento Oficial de Terminologia
**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este glossário define a terminologia oficial utilizada no Bolayetu.

Todos os documentos, APIs, modelos de dados, interfaces, código-fonte e comunicações deverão utilizar estas definições.

Quando existir conflito entre terminologias, prevalece a definição deste documento.

---

# 2. Princípios

* Um conceito deve possuir apenas uma definição oficial.
* Evitar sinónimos para o mesmo conceito técnico.
* Utilizar linguagem consistente entre negócio e desenvolvimento.
* Sempre que possível, utilizar termos independentes do contexto de um país, permitindo a expansão internacional.

---

# 3. Conceitos Gerais

## Plataforma

O Bolayetu é a plataforma digital que integra todos os participantes do ecossistema do futebol.

---

## Ecossistema

Conjunto de organizações, clubes, jogadores, adeptos, competições e parceiros que interagem através do Bolayetu.

---

## Tenant

Unidade lógica independente dentro da plataforma.

Cada Tenant possui:

* utilizadores próprios;
* branding próprio;
* configurações próprias;
* dados isolados.

Normalmente representa uma Organização.

Exemplo:

```text id="n8x1k7"
faf.bolayetu.com
```

---

## Organização

Entidade responsável pela gestão de competições.

Exemplos:

* Federação
* Associação Provincial
* Liga
* Organizador de Torneios

Responsabilidades:

* gerir competições;
* aprovar clubes;
* gerir regulamentos;
* publicar classificações.

---

## Clube

Entidade desportiva participante em competições.

Pode possuir:

* plantel;
* equipa técnica;
* estádio;
* patrocinadores;
* histórico.

O clube gere apenas os seus próprios recursos.

---

## Jogador

Atleta registado na plataforma.

Pode possuir:

* perfil profissional;
* histórico de carreira;
* estatísticas;
* documentos;
* vídeos;
* conquistas.

O jogador pode existir sem estar associado a um clube.

---

## Adepto

Utilizador cujo principal objetivo é acompanhar clubes, jogadores e competições.

Pode:

* seguir clubes;
* seguir jogadores;
* receber notificações;
* personalizar conteúdos.

---

## Equipa Técnica

Conjunto de profissionais associados a um clube.

Exemplos:

* treinador principal;
* treinador adjunto;
* preparador físico;
* fisioterapeuta;
* médico;
* analista de desempenho.

---

## Árbitro

Profissional responsável pela arbitragem das partidas.

Poderá futuramente possuir perfil próprio.

---

# 4. Competições

## Competição

Evento desportivo organizado por uma Organização.

Exemplos:

* campeonato;
* taça;
* supertaça;
* torneio amistoso.

---

## Época

Período oficial durante o qual decorre uma competição.

Exemplo:

```text id="vbskji"
2026/2027
```

---

## Jornada

Conjunto de partidas disputadas numa determinada fase da competição.

---

## Partida

Evento desportivo entre dois clubes.

Uma partida possui:

* local;
* data;
* árbitros;
* escalações;
* eventos;
* estatísticas.

---

## Fase

Etapa de uma competição.

Exemplos:

* fase de grupos;
* oitavos;
* quartos;
* meias-finais;
* final.

---

## Grupo

Subdivisão de uma competição.

Exemplo:

Grupo A

Grupo B

---

# 5. Jogadores

## Plantel

Conjunto de jogadores registados por um clube.

---

## Vínculo

Relação ativa entre jogador e clube.

Um vínculo pode:

* iniciar;
* terminar;
* ser suspenso.

---

## Transferência

Mudança de vínculo entre clubes.

Pode ser:

* definitiva;
* empréstimo;
* gratuita.

---

## Histórico de Carreira

Registo cronológico dos clubes pelos quais um jogador passou.

Nunca deverá ser apagado.

---

## Estatística

Indicador de desempenho.

Exemplos:

* jogos;
* golos;
* assistências;
* cartões;
* minutos.

---

# 6. Organizações

## Afiliação

Processo através do qual um clube passa a integrar oficialmente uma organização.

---

## Licenciamento

Processo de validação para permitir a participação de um clube numa competição.

---

## Regulamento

Documento que define as regras de uma competição.

---

# 7. Plataforma

## Perfil

Representação de negócio associada a um utilizador.

Exemplos:

* Perfil de Organização
* Perfil de Clube
* Perfil de Jogador
* Perfil de Adepto

---

## Utilizador

Entidade responsável pela autenticação.

Contém apenas:

* identidade;
* autenticação;
* autorização.

Nunca deverá conter dados de negócio.

---

## Papel (Role)

Nível de autorização atribuído ao utilizador.

Exemplos:

ADMIN

ORGANIZACAO

CLUBE

JOGADOR

ADEPTO

---

## Permissão

Autorização para executar determinada operação.

Exemplos:

* criar competição;
* editar clube;
* aprovar jogador.

---

# 8. Infraestrutura

## Multi-Tenant

Arquitetura onde múltiplas organizações utilizam a mesma plataforma, mantendo isolamento completo dos seus dados.

---

## Docker

Tecnologia utilizada para executar todos os serviços da plataforma em ambientes consistentes.

---

## Cloudflare R2

Serviço oficial de armazenamento de ficheiros.

---

## CDN

Rede responsável pela distribuição global dos ficheiros.

---

## API

Interface utilizada para comunicação entre frontend e backend.

Todas as APIs deverão ser RESTful e documentadas.

---

## JWT

Mecanismo oficial de autenticação da plataforma.

---

## RBAC

Modelo de controlo de acesso baseado em papéis.

---

# 9. Produto

## MVP

Primeira versão funcional do Bolayetu destinada à validação do produto no mercado.

---

## Dashboard

Página inicial personalizada para cada perfil.

Cada tipo de utilizador possui o seu próprio dashboard.

---

## Onboarding

Processo inicial de configuração do utilizador após o registo.

---

## Marketplace

Módulo destinado à ligação entre clubes, jogadores, scouts, empresários, patrocinadores e parceiros.

---

## Analytics

Conjunto de dashboards e indicadores utilizados para apoiar decisões.

---

# 10. Convenções de Terminologia

Sempre utilizar:

* Organização (não Federação, exceto quando se referir a uma entidade específica).
* Clube (não Equipa).
* Jogador (não Atleta, salvo em textos editoriais).
* Competição (termo genérico).
* Partida (evento individual).
* Época (temporada desportiva).
* Tenant (conceito técnico).
* Perfil (conceito de negócio).
* Utilizador (conceito de autenticação).

---

# 11. Evolução do Glossário

Este documento deverá ser atualizado sempre que novos conceitos estruturantes forem introduzidos na plataforma.

A criação de novos módulos deverá ser acompanhada pela inclusão da respetiva terminologia neste glossário.

Nenhum novo conceito de negócio deverá ser utilizado sem possuir uma definição oficial neste documento.
