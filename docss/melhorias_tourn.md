Vou primeiro dar uma olhada rápida nos ficheiros TournamentDetails.tsx e MatchEvents.tsx para entender a estrutura atual e então montar um plano de implementação em fases bem alinhado com o teu código.
        
            
toolName: search_codebase
            
status: success
          
query: MatchEvents component and live match handling logic
          

        
            
toolName: todo_write
            
status: success
          
Todos updated: 1 items
          
Agora que já vi a estrutura básica dos componentes de torneio e do motor de jogo, vou montar um plano em fases cobrindo cada um dos 9 pontos, indicando onde no código atuar e como organizar a implementação.
        
            
toolName: todo_write
            
status: success
          
Todos updated: 1 items
          
Vou organizar o plano em fases lógicas, de forma que cada fase possa ser desenvolvida, testada e entregue de maneira independente, mas sempre integrando tudo no fluxo TournamentDetails.tsx ↔ MatchEvents.tsx.

---

**Fase 1 – Regras básicas de início de jogo**

Foco: garantir que um jogo só começa quando é permitido (data/hora e escalação).

- **1.1. Bloqueio por data/hora (Directo só no dia/hora certa)**
  - Backend:
    - Adicionar validação no endpoint de controlo do jogo (ex.: `/matchengine/matches/{id}/control_match/`) para:
      - Recusar `start_match` se `now` < `match.scheduled_kickoff` (ou um “limite” configurado, ex.: 15 minutos antes) ou muito depois (por ex. mais de X horas/dias).
      - Devolver erro claro (ex.: `422` com mensagem “Jogo só pode ser iniciado na data e hora marcada.”).
  - Frontend (MatchEvents.tsx):
    - Ler do `match` a data/hora do jogo (já vem do backend).
    - Antes de chamar `handleGameControl('start_match')`, verificar:
      - Se `now` está fora da janela permitida, mostrar mensagem e não chamar o serviço.
    - Desabilitar o botão “Iniciar Jogo” quando `match.status === 'scheduled'` mas `now` estiver fora da janela permitida (feedback visual imediato).

- **1.2. Obrigatoriedade de escalação completa (11 vs 11) antes de iniciar**
  - Backend:
    - No mesmo endpoint `start_match`, validar:
      - `homeLineup` tem exatamente 11 `isStarter === true`.
      - `awayLineup` tem exatamente 11 `isStarter === true`.
      - Caso contrário, recusar com mensagem (“Cada equipa deve ter 11 titulares definidos.”).
  - Frontend (MatchEvents.tsx):
    - Usar `homePlayers` e `awayPlayers` (já existem) e filtrar por `isStarter === true`.
    - Antes de chamar `handleGameControl('start_match')`:
      - Se algum lado tiver menos de 11, mostrar alerta e não enviar o pedido.
    - Opcional: mostrar um contador na tab de escalação (ex.: “10/11” para cada equipa) para o utilizador ver que ainda falta alguém.

Resultado da fase: não é possível iniciar o jogo antes/fora do horário e não é possível iniciar sem as duas equipas com 11 titulares.

---

**Fase 2 – Escalação, substituições e bloqueio de alterações**

Foco: garantir consistência entre escalação inicial, banco e controlo live.

- **2.1. Ajustar modal de Substituição (jogador que sai / entra)**
  - Atualmente, o `EventModal` em MatchEvents.tsx recebe um único array `players`.
  - Alterações propostas:
    - No momento de abrir o modal para `type: 'substitution'`, preparar dois arrays:
      - `starters` = jogadores com `isStarter === true` (escalação inicial + quem estiver em campo).
      - `bench` = jogadores com `isStarter === false` (banco de suplentes).
    - Criar um `SubstitutionModal` específico OU adaptar o `EventModal` para aceitar:
      - `playersOut` (para “jogador que sai”).
      - `playersIn` (para “jogador que entra”).
    - No JSX:
      - Dropdown “Jogador que sai” lista apenas `playersOut`.
      - Dropdown “Jogador que entra” lista apenas `playersIn`.
  - Backend:
    - Garantir que as substituições recebidas atualizam a lineup (quem sai deixa de estar em campo, quem entra passa a `isStarter` ou a um estado equivalente de “em campo”).

- **2.2. Bloquear escalação após início do jogo**
  - Frontend (MatchEvents.tsx):
    - O botão que abre o `LineupModal` deve ser:
      - Desabilitado (`disabled`) quando `match.status === 'live'` ou `match.status === 'finished'`.
    - Dentro do `LineupModal`:
      - Funções `onToggle` (titular/reserva) e `onToggleCaptain` não devem ser chamadas quando o jogo já começou:
        - Ou nem renderizar os controlos (checkboxes, botões) quando `match.status !== 'scheduled'`.
  - Backend:
    - No serviço `updateLineup` e `setCaptain` em `matchengine.service.ts` (equivalente do lado servidor):
      - Recusar alterações se `match.status` não for `scheduled`.

Resultado da fase: escalação e capitão são definidos antes do jogo, substituições usam corretamente titulares e banco, e depois de começar já não é possível mexer na escalação inicial.

---

**Fase 3 – Sincronização em tempo real com o calendário (TournamentDetails.tsx)**

Foco: minutos e golos refletirem no calendário, e edição estar desabilitada enquanto o jogo decorre.

- **3.1. Garantir a propagação dos dados live**
  - Backend:
    - Quando o MatchEngine atualiza o jogo (minutos, eventos, estatísticas), assegurar que:
      - O endpoint de torneio (`/tournaments/{id}`) devolve `matches` com:
        - `status` (`scheduled`, `live`, `finished`…).
        - `homeScore`, `awayScore` atualizados.
        - Opcionalmente, `timer` e `currentPeriod` (para mostrar tempo de jogo no calendário).
  - Frontend (TournamentDetails.tsx):
    - Já existe um `useEffect` a fazer polling de 10s quando há jogos `live` (trecho que encontrámos).
    - Ajustar o cartão do jogo no “calendário” para:
      - Mostrar marcador atual `homeScore - awayScore`.
      - Se `status === 'live'`, exibir:
        - Badge “Em directo” + minuto (`timer`) e/ou período (`currentPeriod`), se disponíveis no objeto do match.
    - Garantir que a fonte de verdade é o backend (não calcular nada manualmente aqui, só renderizar).

- **3.2. Desabilitar edição de calendário enquanto o jogo está em DIRECTO**
  - Em TournamentDetails.tsx (ou no componente responsável pelo card de jogo/calendário):
    - Onde há ações de edição (editar data, alterar equipas, apagar jogo, etc.):
      - Desabilitar botões / esconder ações quando `match.status === 'live'`.
      - Opcional: tooltip tipo “Edição indisponível enquanto o jogo decorre.”
  - Opcional de reforço:
    - Se houver rota específica de edição de jogo, adicionar guarda:
      - Ao carregar os dados, se `status === 'live'`, redirecionar de volta e mostrar mensagem.

Resultado da fase: qualquer alteração no MatchEvents.tsx se reflete em TournamentDetails.tsx via polling; jogos live mostram minutos e marcador, e não podem ser editados no calendário.

---

**Fase 4 – Pós-jogo (HT/FT) e classificação**

Foco: experiência após o jogo e destaque na tabela de classificação.

- **4.1. Expandir card de jogo terminado para mostrar marcadores**
  - Backend:
    - Garantir que os eventos de golo (incluindo auto-golos) estão disponíveis em:
      - MatchEvents.tsx (já estão).
      - TournamentDetails.tsx: `tournament.matches[n].events` ou algum resumo de golos (ex.: `scorers`).
  - Frontend (TournamentDetails.tsx):
    - No card de jogo com `status === 'finished'`:
      - Adicionar um ícone (por ex. “i”, seta, ou ícone de lista) ou usar hover.
      - Ao passar o mouse ou clicar:
        - Expandir o card ou abrir um pequeno painel/dropdown.
        - Listar marcadores por equipa:
          - Agrupação: filtrar `events` por `type === 'goal'`.
          - Dividir entre `teamId === homeTeamId` e `teamId === awayTeamId`.
          - Mostrar algo como:
            - “12' – João Silva”
            - “78' – Carlos (pênalti)” (se tiver informação).
        - Tratar auto-golo:
          - Se `isOwnGoal === true`, mostrar claramente e creditar no marcador correto (já é calculado no motor, mas a descrição pode indicar “(auto-golo)”).

- **4.2. Destacar top 3 e bottom 3 na classificação**
  - Identificar onde a tabela de classificação é renderizada em TournamentDetails.tsx (provavelmente há um map sobre `standings` ou algo similar).
  - Lógica:
    - Ordenar a classificação como já é feito hoje (por pontos, etc.).
    - Na renderização de cada linha:
      - Para índice `0,1,2` (top 3): aplicar classe CSS de fundo verde suave (ex.: `bg-green-50` ou equivalente na tua tailwind/custom design).
      - Para os últimos 3 índices (length-3, length-2, length-1): aplicar cor de fundo vermelha suave (ex.: `bg-red-50`).
    - Se o torneio tiver grupos:
      - Fazer essa lógica por grupo (os 2 top dentro de cada grupo).

Resultado da fase: cards de jogos terminados ficam “ricos” com a lista de marcadores, e a tabela de classificação ganha um destaque visual imediato para os 3 primeiros e 3 últimos.

---

**Fase 5 – Estatísticas do torneio (tab extra em TournamentDetails.tsx)**

Foco: nova aba de estatísticas com subtabs.

- **5.1. Adicionar tab “Estatísticas” em TournamentDetails.tsx**
  - Ver o sistema de tabs já existente no componente (provavelmente há um `activeTab` / `setActiveTab`).
  - Adicionar uma nova tab, ex.: “Estatísticas”.
  - Quando `activeTab === 'stats'` (nome a escolher), renderizar um painel de estatísticas do torneio.

- **5.2. Subtabs de estatísticas dentro da tab principal**
  - Dentro da aba “Estatísticas”, criar subtabs:
    - “Melhores Marcadores”
    - “Golos por Jornadas”
    - “Clubes com Mais Golos”
    - “Clubes com Menos Golos”
  - Implementação front:
    - Subestado local, ex.: `statsSubtab` com valores `'scorers' | 'goalsByRound' | 'clubsMostGoals' | 'clubsLeastGoals'`.

- **5.3. Fonte de dados para as estatísticas**
  - Opção A (mais simples, se a API já retorna eventos por jogo no torneio):
    - Usar `tournament.matches` e os `events` de cada match.
    - Construir:
      - Melhores marcadores:
        - Mapear todos os eventos de golo → agrupar por `playerId` / `playerName` → contar golos → ordenar desc.
      - Golos por jornadas:
        - Agrupar golos por `match.round` ou campo equivalente (ex.: “jornada”).
        - Somar golos por jornada.
      - Clubes com mais/menos golos:
        - Para cada jogo, somar golos marcados por `homeTeamId` e `awayTeamId` (usando scoreboard final ou eventos).
        - Produzir ranking de clubes.
  - Opção B (mais robusta, se a API expõe estatísticas prontas):
    - Criar/usar endpoints dedicados de estatísticas do torneio.
    - TournamentDetails.tsx apenas consome e renderiza dados já agregados, o que simplifica o frontend.

Resultado da fase: o utilizador consegue ver uma visão agregada do torneio, complementando o calendário e a classificação.

---

**Resumo das dependências entre fases**

- Fase 1 e 2 são a base das regras do jogo (começo e escalação).
- Fase 3 aproveita o polling de live que TournamentDetails.tsx já tem para refletir o que acontece no MatchEvents.tsx.
- Fase 4 melhora a experiência pós-jogo e a leitura da classificação.
- Fase 5 adiciona uma camada analítica sobre o torneio inteiro.

Se quiseres, na próxima etapa posso começar pela Fase 1 e 2 diretamente no código (MatchEvents.tsx + serviços), garantindo primeiro as regras de negócio críticas (horário e escalação) e depois seguir para o resto.




3. Recap rápido dos dados usados

- golos vem do somatório de eventos type === 'goal' por jogador em todos os jogos finalizados.
- matches conta em quantos desses jogos o jogador marcou pelo menos uma vez.
- A columa “Jogos” mostra esse matches .
- A média “Média G/J” é golos / matches , com duas casas decimais.