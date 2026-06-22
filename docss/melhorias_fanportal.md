Boa ideia. O FanPortal já cresceu bastante, faz sentido estruturarmos um plano antes de mexer no código.

Segue um plano de refatoração em fases, com subcomponentes e hooks sugeridos.

---

**1. Quebrar a UI em subcomponentes visuais**

Primeiro extrair apenas partes “de apresentação”, sem mexer na lógica:

- **FanPortalLayout**  
  - Responsável pelo `div` root, fundo, AuthRequiredModal e estrutura geral.
  - Mantém apenas layout (min-h-screen, etc.), recebe children.

- **FanPortalHeader**  
  - Título da liga, logo, botão de subscrição (`Seguir / Deixar de seguir`), estado live, etc.
  - Props típicas:
    - `tournament`, `isSubscribed`, `isTogglingSubscription`, `onToggleSubscription`.

- **FanPortalTabs**  
  - Selector de tabs: “Jogos”, “Tabela”, “Stats”, “Perfil” (o que já existir).
  - Props:
    - `activeTab`, `onChange(tab)`.

- **FanPortalMatchesByRound**  
  - Lista de jogos por jornada (round) + selector de jornada.
  - Props:
    - `matchesByRound`, `rounds`, `selectedRound`, `onSelectRound(round)`, `onSelectMatch(match)`.

- **FanPortalMatchCard**  
  - Um único cartão de jogo na lista (score, estado, relógio, botão para abrir detalhes).
  - Props:
    - `match`, `participantsIndex`, `onClick`.

- **FanPortalMatchModal**  
  - O modal de detalhes do jogo (tabs resumo / estatísticas, marcadores, etc.).
  - Props:
    - `match`, `tournament`, `participantsIndex`, `open`, `onClose`.

- **FanPortalStatsSection**  
  - A tab de estatísticas: top marcadores, assistências, gráficos se existirem.
  - Props:
    - `tournament`, `topScorersData`, `topAssistsData`.

- **FanPortalProfileSection**  
  - A tab de perfil do adepto: subscrições, filtros, paginação.
  - Props:
    - `profile`, estados de loading/erro, handlers de filtros e unsubscribe.

- **LiveNotificationToast**  
  - O bloco do toast que já existe (ficar isolado).
  - Props:
    - `notification`, `onClose`.

---

**2. Extrair hooks para a lógica pesada**

Depois separar a lógica da UI, para o componente principal ficar só a compor:

- **useFanPortalAuthGuard**  
  - Lógica actual de:
    - Validar token JWT.
    - Redireccionar para /login se sessão inválida/expirada.
  - Retorna algo como `{ isAuthenticated, token }` (na prática a partir de `useAuth` mas com as validações extras).

- **useFanPortalOverview(tournamentId)**  
  - Carrega overview inicial via `fanportalService.getOverview`.
  - Gere:
    - `tournament`, `isSubscribed`, `isOverviewLoading`, `overviewError`.
  - Inicializa `lastEventsRef` (pode vir como parte do retorno ou separado).

- **useFanPortalProfile(filters)**  
  - Carrega subscrições do adepto com `fanportalService.getProfile`.
  - Gere:
    - `profile`, `isProfileLoading`, `profileError`, handlers para paginação/filtros.

- **useFanPortalLiveUpdates(tournament, tournamentId, isAuthenticated)**  
  - Contém:
    - Polling a cada 10s.
    - Detecção de novos eventos por jogo (com `lastEventsRef`).
    - Geração de notificações:
      - Golo.
      - Cartão vermelho.
      - Cartão amarelo.
      - Início de jogo (whistle_start).
      - Fim de jogo (whistle_end).
    - Actualização de `tournament` em live.
  - Recebe callbacks:
    - `onTournamentUpdate`, `onSubscriptionUpdate`, `onLocalToast`, `onGlobalNotification`.

Assim o componente `FanPortal` passa a orquestrar:

- Chamadas aos hooks.
- Composição dos subcomponentes.

---

**3. Separar helpers de domínio em funções reutilizáveis**

Hoje já existem helpers dentro do componente:

- `getScorersForMatch`
- `getTeamLogoUrl`
- `topScorersData`
- `topAssistsData`
- `getGoalType`
- `getMatchClock`

Plano:

- Mover estes helpers para um ficheiro utilitário, por exemplo:
  - `src/pages/fanportal/fanportal.utils.ts`
- Exportar funções puras, sem dependência de estado React:
  - `buildScorers(match)`
  - `buildTopScorers(tournament)`
  - `buildTopAssists(tournament)`
  - `buildMatchClock(match)`

Isto facilita testes unitários futuros e reutilização noutras páginas (ex.: FanProfile, outras visões públicas).

---

**4. Organizar pasta fanportal**

Estrutura sugerida:

- `src/pages/fanportal/FanPortal.tsx` (container principal, fino)
- `src/pages/fanportal/components/`
  - `FanPortalLayout.tsx`
  - `FanPortalHeader.tsx`
  - `FanPortalTabs.tsx`
  - `FanPortalMatchesByRound.tsx`
  - `FanPortalMatchCard.tsx`
  - `FanPortalMatchModal.tsx`
  - `FanPortalStatsSection.tsx`
  - `FanPortalProfileSection.tsx`
  - `LiveNotificationToast.tsx`
- `src/pages/fanportal/hooks/`
  - `useFanPortalAuthGuard.ts`
  - `useFanPortalOverview.ts`
  - `useFanPortalProfile.ts`
  - `useFanPortalLiveUpdates.ts`
- `src/pages/fanportal/fanportal.utils.ts`

---

**5. Ordem de implementação recomendada**

Para minimizar risco e conflitos:

1. **Fase 1 – Subcomponentes visuais simples**
   - Extrair `LiveNotificationToast`, `FanPortalTabs`, `FanPortalMatchCard`, `FanPortalMatchModal` sem mover lógica.
   - Conectar via props, mantendo todo o estado no FanPortal.

2. **Fase 2 – Hooks de dados**
   - Extrair `useFanPortalOverview` e `useFanPortalProfile`.
   - Confirmar que carregamentos e erros continuam a comportar-se igual.

3. **Fase 3 – Hook de live updates**
   - Mover a lógica de polling e notificações para `useFanPortalLiveUpdates`.
   - Ligar `setTournament`, `setIsSubscribed`, `setNotification`, `addNotification` via callbacks.

4. **Fase 4 – Utils de domínio**
   - Mover helpers (`getScorersForMatch`, `topScorersData`, etc.) para `fanportal.utils.ts`.
   - Substituir chamadas no código pelos helpers importados.

5. **Fase 5 – Limpeza e pequenos ajustes**
   - Verificar se há estados redundantes/duplicados.
   - Confirmar que cada subcomponente recebe apenas as props necessárias (evitar “props gigantes”).

6. **Fase 6 – Testes**
   - Roda sempre `npm test` após cada fase maior.
   - Opcionalmente, criar 1–2 testes de snapshot para subcomponentes principais (MatchCard, MatchModal) no futuro.

---

Se quiser, no próximo passo posso começar pela Fase 1 (extrair, por exemplo, `LiveNotificationToast` e `FanPortalTabs`) e já deixar o componente principal bem mais limpo antes de seguir para os hooks.