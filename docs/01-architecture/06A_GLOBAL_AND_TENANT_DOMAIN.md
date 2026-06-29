# GLOBAL DOMAIN vs TENANT DOMAIN

**Documento:** `06A_GLOBAL_AND_TENANT_DOMAIN.md`

**Versão:** 2.0.0

**Estado:** Documento Oficial

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define a separação entre os domínios globais e os domínios pertencentes aos Tenants.

Esta arquitetura elimina duplicação de informação e permite que o Bolayetu evolua para uma plataforma continental.

---

# 2. Princípio Fundamental

Nem todos os dados pertencem a uma Organização.

Existem dois tipos de entidades:

* Entidades Globais
* Entidades do Tenant

---

# 3. Domínio Global

O Domínio Global representa toda a informação que existe independentemente de qualquer Organização.

Estas entidades pertencem à plataforma.

Nunca pertencem a um Tenant.

---

## Características

* únicas;
* permanentes;
* reutilizáveis;
* independentes.

---

# 4. Entidades Globais

## User

Representa a identidade digital.

Nunca pertence a um Tenant.

Pode possuir acesso a vários Tenants.

---

## Player

O jogador pertence ao Bolayetu.

Não pertence a uma Organização.

Não pertence a um Clube.

Os Clubes apenas registam vínculos temporários.

---

## Country

Lista oficial de países.

Global.

---

## Province

Divisão administrativa.

Global.

---

## City

Global.

---

## Language

Global.

---

## Currency

Global.

---

## Sport

Futebol

Futsal

Futebol Feminino

etc.

---

## MediaFile

Representa qualquer ficheiro enviado.

O ficheiro existe apenas uma vez.

Pode ser utilizado por vários módulos.

---

## NotificationTemplate

Modelos de notificações.

---

## Permission

Lista global de permissões.

---

## Role

Lista global de papéis.

---

# 5. Domínio Tenant

O Domínio Tenant representa tudo o que pertence a uma Organização.

Cada Tenant possui dados completamente isolados.

---

# 6. Entidades Tenant

Organization

Competition

Season

Club

Team Staff

Standing

Match

Registration

Subscription

Branding

Billing

News

Reports

Configurations

---

# 7. Relação entre os Domínios

```text
                    GLOBAL DOMAIN

      User

      Player

      Country

      Media

      Roles

            │

            │

            ▼

================ TENANT ==================

            Organization

                  │

                  ▼

            Competition

                  │

                  ▼

                Club

                  │

                  ▼

           Player Registration

                  │

                  ▼

             Match Statistics
```

---

# 8. Porque o Jogador é Global?

O jogador possui uma carreira.

A carreira não pertence a uma Federação.

Nem pertence a um Clube.

Exemplo:

```text
Pedro

↓

Petro

↓

1º Agosto

↓

TP Mazembe

↓

Al Ahly
```

Todos estes clubes pertencem a organizações diferentes.

Mesmo assim o jogador continua a ser o mesmo.

---

# 9. Player Registration

Em vez do Clube "possuir" o Jogador...

O Clube cria um registo.

```text
Player

↓

Registration

↓

Club

↓

Competition

↓

Season
```

Assim:

O histórico nunca é perdido.

---

# 10. Career

O histórico passa a ser construído automaticamente.

```text
Player

↓

Registration

↓

Transfer

↓

Registration

↓

Transfer

↓

Registration
```

A carreira deixa de depender do Clube.

---

# 11. Club

O Clube pertence sempre a uma Organização.

Não existe Clube global.

Exemplo:

```text
Girabola

↓

Petro de Luanda
```

Outro campeonato poderá possuir outro clube com nome semelhante.

O contexto pertence sempre ao Tenant.

---

# 12. Competition

Sempre Tenant.

Nunca Global.

---

# 13. Standing

Sempre Tenant.

---

# 14. Match

Sempre Tenant.

---

# 15. Statistics

Existem dois níveis.

## Estatísticas Globais

Carreira.

Jogos.

Golos.

Assistências.

---

## Estatísticas Tenant

Competição.

Época.

Clube.

Campeonato.

---

# 16. Benefícios

Esta arquitetura permite:

* carreira única do jogador;
* histórico permanente;
* menos duplicação;
* melhor SEO;
* APIs públicas;
* scouting internacional;
* marketplace.

---

# 17. Marketplace

Como o jogador é Global...

O Marketplace torna-se simples.

```text
Scout

↓

Player

↓

Career

↓

Videos

↓

Statistics

↓

Transfer
```

---

# 18. APIs

Exemplo:

Global

```text
/api/v1/players
```

Tenant

```text
/api/v1/competitions

/api/v1/clubs

/api/v1/matches
```

---

# 19. Estrutura Django

```text
apps/

global/

accounts/

players/

countries/

media/

permissions/

roles/

tenant/

organizations/

competitions/

clubs/

matches/

standings/

subscriptions/

billing/
```

---

# 20. Regra de Ouro

Antes de criar qualquer modelo perguntar:

"Esta entidade existe sem uma Organização?"

Se SIM

↓

Global

Se NÃO

↓

Tenant

---

# 21. Resumo

## Global

* User
* Player
* Country
* Language
* Currency
* Media
* Roles
* Permissions

## Tenant

* Organization
* Club
* Competition
* Season
* Match
* Standing
* Registration
* Billing
* Subscription
* Branding
* Reports

Esta separação constitui um dos princípios fundamentais da arquitetura do Bolayetu e deverá ser respeitada em toda a evolução da plataforma.
