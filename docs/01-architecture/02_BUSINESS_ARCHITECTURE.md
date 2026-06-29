# BUSINESS ARCHITECTURE

**Documento:** `02_BUSINESS_ARCHITECTURE.md`

**Versão:** 2.0.0

**Estado:** Documento Oficial de Arquitetura de Negócio

**Projeto:** Bolayetu – Football Ecosystem Platform

---

# 1. Objetivo

Este documento define a arquitetura de negócio do Bolayetu.

A Arquitetura de Negócio descreve:

* os participantes do ecossistema;
* as suas responsabilidades;
* os relacionamentos;
* os fluxos operacionais;
* as regras de interação.

Este documento é a principal referência para:

* Modelagem da Base de Dados;
* Desenvolvimento Backend;
* Desenvolvimento Frontend;
* Definição das APIs;
* Definição de Permissões (RBAC);
* Onboarding dos utilizadores.

---

# 2. Princípios da Arquitetura

Toda a arquitetura do Bolayetu baseia-se em quatro princípios.

## Especialização

Cada participante possui responsabilidades próprias.

Exemplo:

A Organização gere competições.

O Clube gere atletas.

O Jogador gere a própria carreira.

---

## Colaboração

Nenhuma entidade funciona isoladamente.

O ecossistema cria valor através da interação entre todos os participantes.

---

## Autonomia

Cada entidade controla os seus próprios recursos.

Exemplos:

Um Clube controla o seu plantel.

Um Jogador controla o seu perfil profissional.

Uma Organização controla as suas competições.

---

## Governança

As Organizações exercem funções de supervisão sobre as competições que administram.

---

# 3. Ecossistema

```text
                         BOLAYETU

                              │

     ┌────────────────────────┼────────────────────────┐

     │                        │                        │

Organizações              Clubes                  Adeptos

     │                        │

     │                        │

     └──────────────┐    ┌────┘

                    │    │

                Jogadores

                    │

             Equipa Técnica

                    │

               Competições

                    │

               Estatísticas
```

Todos os módulos da plataforma deverão fortalecer este ecossistema.

---

# 4. Participantes

O Bolayetu possui quatro participantes principais.

## Organização

Representa a entidade gestora do futebol.

Exemplos:

* Federação Nacional
* Associação Provincial
* Liga
* Organizador de Torneios

A Organização é o Tenant principal da plataforma.

---

## Clube

Representa uma entidade desportiva.

O Clube participa em competições e gere os seus recursos humanos e desportivos.

---

## Jogador

Representa um atleta.

O Jogador possui identidade própria dentro da plataforma.

Pode existir sem vínculo ativo a um clube.

---

## Adepto

Representa um utilizador interessado em acompanhar o futebol.

O Adepto não gere informação institucional.

O seu foco é consumo de conteúdos e interação.

---

# 5. Hierarquia do Ecossistema

A hierarquia lógica é a seguinte.

```text
Plataforma

↓

Organização

↓

Competição

↓

Clube

↓

Jogador

↓

Adepto
```

Esta hierarquia não representa dependência técnica.

Representa apenas organização do negócio.

---

# 6. Responsabilidades

## Organização

É responsável por:

* criar competições;
* definir épocas;
* publicar regulamentos;
* aprovar clubes;
* gerir classificações;
* validar resultados;
* gerir árbitros;
* publicar notícias institucionais;
* gerar relatórios.

Nunca deverá gerir diretamente jogadores individuais.

---

## Clube

É responsável por:

* gerir plantel;
* gerir equipa técnica;
* gerir documentos;
* gerir patrocinadores;
* inscrever-se em competições;
* aprovar pedidos de jogadores;
* publicar notícias do clube.

Nunca deverá alterar informações institucionais da Organização.

---

## Jogador

É responsável por:

* gerir o perfil profissional;
* atualizar informações pessoais;
* gerir currículo;
* publicar vídeos;
* gerir documentos;
* solicitar vínculo a clubes.

Nunca deverá alterar informação institucional do clube.

---

## Adepto

É responsável por:

* seguir clubes;
* seguir jogadores;
* seguir competições;
* personalizar notificações;
* consumir conteúdos.

Nunca deverá alterar informação desportiva.

---

# 7. Relacionamentos

## Organização → Clube

Uma Organização administra vários Clubes.

Um Clube pode estar afiliado a uma Organização.

A afiliação deverá ser explícita e registada.

---

## Clube → Jogador

Um Clube pode possuir muitos Jogadores.

Um Jogador pode ter vários vínculos ao longo da carreira.

Nunca deverá existir perda do histórico.

---

## Organização → Competição

Uma Organização pode criar várias Competições.

Cada Competição pertence apenas a uma Organização.

---

## Competição → Clube

Uma Competição possui vários Clubes participantes.

A participação depende de inscrição e aprovação.

---

## Clube → Equipa Técnica

Um Clube pode possuir vários membros da equipa técnica.

Cada membro desempenha um papel específico.

---

## Adepto → Clube

Relação de seguimento.

Não existe gestão administrativa.

---

## Adepto → Jogador

Relação de seguimento.

Não existe qualquer vínculo contratual.

---

# 8. Fluxos de Negócio

## Fluxo de Organização

```text
Criar Conta

↓

Criar Organização

↓

Configurar Tenant

↓

Criar Competição

↓

Receber Clubes

↓

Gerir Campeonato

↓

Publicar Resultados
```

---

## Fluxo do Clube

```text
Criar Conta

↓

Criar Clube

↓

Solicitar Afiliação

↓

Aprovação

↓

Criar Plantel

↓

Inscrever-se

↓

Participar
```

---

## Fluxo do Jogador

```text
Criar Conta

↓

Criar Perfil

↓

Completar Currículo

↓

Solicitar Vínculo

↓

Aprovação

↓

Competir

↓

Atualizar Estatísticas
```

---

## Fluxo do Adepto

```text
Criar Conta

↓

Selecionar Clubes

↓

Selecionar Jogadores

↓

Receber Notícias

↓

Interagir
```

---

# 9. Ciclo de Vida

## Organização

```text
Registo

↓

Configuração

↓

Ativa

↓

Suspensa

↓

Encerrada
```

---

## Clube

```text
Registo

↓

Afiliação

↓

Ativo

↓

Suspenso

↓

Inativo
```

---

## Jogador

```text
Registo

↓

Perfil

↓

Sem Clube

↓

Vinculado

↓

Transferido

↓

Reformado
```

---

# 10. Interdependência

Cada participante gera valor para os restantes.

| Entidade    | Depende de               | Gera valor para |
| ----------- | ------------------------ | --------------- |
| Organização | Plataforma               | Clubes          |
| Clube       | Organização              | Jogadores       |
| Jogador     | Clube (quando vinculado) | Competições     |
| Adepto      | Conteúdo do ecossistema  | Plataforma      |

---

# 11. Regras Fundamentais

* Um Utilizador pode possuir apenas um Perfil principal por conta.
* A identidade (User) é independente do Perfil de negócio.
* Todas as ações devem respeitar o RBAC.
* Nenhuma entidade pode alterar recursos pertencentes a outra sem autorização.
* Todos os vínculos e afiliações devem manter histórico.
* Os dados pertencem ao Tenant correspondente.

---

# 12. Evolução do Ecossistema

A arquitetura foi concebida para incorporar novos participantes sem alterar os domínios existentes.

Participantes previstos para versões futuras:

* Árbitro
* Scout
* Empresário
* Academia
* Patrocinador
* Agente
* Observador Técnico
* Parceiro Comercial

Cada novo participante deverá possuir:

* perfil próprio;
* responsabilidades definidas;
* permissões específicas;
* integração com os restantes domínios.

---

# 13. Princípios de Evolução

Qualquer novo módulo deverá responder às seguintes questões:

1. Qual o participante principal beneficiado?
2. Que responsabilidade acrescenta ao ecossistema?
3. Como interage com os restantes participantes?
4. Qual o impacto na arquitetura existente?
5. Requer novas permissões?
6. Requer novos fluxos de negócio?
7. Mantém os princípios de especialização, colaboração, autonomia e governança?

Se alguma destas questões não estiver claramente respondida, a funcionalidade não deverá ser implementada antes da respetiva revisão arquitetural.
