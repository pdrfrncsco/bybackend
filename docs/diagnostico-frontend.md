  Diagnóstico do Frontend — Módulo Organização

  Com base nas skills de design em backend/.ai/skills/design/ (Frontend Engineer, UI    
  Designer, Design System, Dashboard Designer e Frontend Reviewer), segue o estado      
  actual do frontend com foco no módulo Organização.

  ────────────────────────────────────────

  1. Resumo executivo

  O frontend está numa fase intermédia-avançada para o domínio Organização, mas
  ainda longe da maturidade enterprise prescrita pelas skills. A arquitectura por       
  features está bem encaminhada; o Design System formal ainda não existe; e há dados    
  mock que mascaram lacunas de produto.

  ┌───────────────────────┬────────────┬───────────────────────────────────────────┐    
  │ Dimensão              │ Estado     │ Nota                                      │    
  ├───────────────────────┼────────────┼───────────────────────────────────────────┤    
  │ Arquitectura          │ ✅ Boa     │ src/modules/organizations/ segue o padrão │    
  │ (feature-based)       │            │ correcto                                  │    
  ├───────────────────────┼────────────┼───────────────────────────────────────────┤    
  │ Integração API        │ ✅ Boa     │ Service layer + TanStack Query            │    
  ├───────────────────────┼────────────┼───────────────────────────────────────────┤    
  │ UX / páginas          │ ⚠️        │ 4 páginas funcionais, gaps de dashboard e │     
  │ Organização           │ Parcial    │ gestão                                    │    
  ├───────────────────────┼────────────┼───────────────────────────────────────────┤    
  │ Design System         │ ❌         │ Sem shadcn/ui, sem src/components/ui/     │    
  │                       │ Inexistent │                                           │    
  │                       │ e          │                                           │    
  ├───────────────────────┼────────────┼───────────────────────────────────────────┤    
  │ Testes                │ ❌ Zero    │ Nenhum ficheiro .test.tsx                 │    
  ├───────────────────────┼────────────┼───────────────────────────────────────────┤    
  │ Conformidade com      │ ⚠️ ~55%   │ Muitos desvios documentados abaixo        │     
  │ skills                │            │                                           │    
  └───────────────────────┴────────────┴───────────────────────────────────────────┘    

  O npm run type-check passa sem erros — base técnica estável para continuar a
  construção.

  ────────────────────────────────────────

  2. O que já está construído (Organização)

  Estrutura do módulo — sólida

  organizations/
  ├── components/   → Card, KPI, Skeleton, Empty/Error, HistoryTable, TransferItem      
  ├── hooks/        → useOrganizationMe, KPIs, clubs, tournaments, subscribe...
  ├── pages/        → List, Detail, Settings, Dashboard
  ├── services/     → organization.api.ts (camada API completa)
  ├── schemas/      → Zod para update
  └── types/        → Tipos alinhados com backend (snake_case)

  Páginas implementadas

  ┌──────────────┬────────────────────┬────────────────────────────────────────────┐    
  │ Página       │ Rota               │ Estado                                     │    
  ├──────────────┼────────────────────┼────────────────────────────────────────────┤    
  │ Listagem     │ /organizations     │ ✅ Com pesquisa, filtro por tipo,          │    
  │ pública      │                    │ empty/error/loading                        │    
  ├──────────────┼────────────────────┼────────────────────────────────────────────┤    
  │ Detalhe      │ /organizations/:sl │ ✅ Tabs (Resumo / Histórico), KPIs,        │    
  │ público      │ ug                 │ subscrição                                 │    
  ├──────────────┼────────────────────┼────────────────────────────────────────────┤    
  │ Definições   │ /organization/sett │ ✅ Form RHF+Zod, upload logo/banner, live  │    
  │              │ ings               │ preview                                    │    
  ├──────────────┼────────────────────┼────────────────────────────────────────────┤    
  │ Dashboard    │ /dashboard/organiz │ ⚠️ Parcial — KPIs reais, mas secções      │     
  │ admin        │ ation              │ incompletas                                │    
  └──────────────┴────────────────────┴────────────────────────────────────────────┘    

  Pontos fortes (alinhados com as skills)

  • Service layer — API nunca chamada directamente nos componentes
  • Estados UX — skeleton, empty e error nas páginas públicas
  • Formulários — React Hook Form + Zod com mensagens em PT
  • Identidade visual — tokens Material 3 no tailwind.config.ts + index.css
    (glass-card, glow-bg)
  • Referência visual — layout_design/2 organization_dashboard_bolayetu/ como mock      
    HTML de alta fidelidade
  • Multi-tenant — TenantProvider mapeia organização → contexto de tenant

  ────────────────────────────────────────

  3. Lacunas críticas no módulo Organização

  3.1 Dashboard administrativo incompleto

  O OrganizationDashboardPage liga KPIs e competições à API, mas viola o Dashboard      
  Designer Skill:

  ┌─────────────────────────────────┬─────────────────────────────────┐
  │ Widget esperado (skill)         │ Estado actual                   │
  ├─────────────────────────────────┼─────────────────────────────────┤
  │ KPIs com trend/comparação       │ ⚠️ Só valor + ícone, sem trend │
  ├─────────────────────────────────┼─────────────────────────────────┤
  │ Quick Actions                   │ ⚠️ Só "Criar Competição"       │
  ├─────────────────────────────────┼─────────────────────────────────┤
  │ Charts (evolução, distribuição) │ ❌ Ausentes                     │
  ├─────────────────────────────────┼─────────────────────────────────┤
  │ Activity Feed                   │ ❌ Ausente                      │
  ├─────────────────────────────────┼─────────────────────────────────┤
  │ Clubes associados (tabela)      │ ❌ Hook existe, UI não usa      │
  ├─────────────────────────────────┼─────────────────────────────────┤
  │ Notificações / eventos próximos │ ❌ Ausentes                     │
  ├─────────────────────────────────┼─────────────────────────────────┤
  │ Transferências                  │ ❌ Dados hardcoded (mock)       │
  └─────────────────────────────────┴─────────────────────────────────┘

   frontend/src/modules/organizations/pages/OrganizationDashboardPage.tsx lines         
  187-188

                  <TransferItem playerName="Manuel Neto" fromClub="Atlético de
  Luanda" toClub="1º de Agosto" timeAgo="2 horas atrás" />
                  <TransferItem playerName="Gelson Kiala" fromClub="Sagrada
  Esperança" toClub="Petro de Luanda" timeAgo="Ontem" />

  3.2 Navegação incorrecta

  Links de competições apontam para /onboarding/competition em vez de
  ROUTES.COMPETITIONS — UX confusa para utilizadores já onboarded.

  3.3 Funcionalidades de backend sem UI

  A API expõe endpoints que não têm interface:

  • Gestão de membros da organização
  • Pedidos de filiação de clubes (club_affiliation_requests no backend)
  • Launch portal — hook useLaunchOrganization() existe, mas só é usado no
    onboarding
  • Estado de subscrição no detalhe público — estado local isSubscribed não
    reflecte o backend

  3.4 Inconsistência de layout

  • Dashboard usa DashboardLayout (sidebar, topbar, notificações)
  • Settings usa layout standalone — quebra a consistência do UI Designer Skill
    (Topbar → Sidebar → Breadcrumb → Page Header)

  3.5 Tabelas estáticas

  A tabela de competições é HTML manual — sem sorting, filtering, paginação nem modo    
  responsivo, como exige o Design System Skill.

  ────────────────────────────────────────

  4. Diagnóstico global do frontend

  4.1 Design System — maior dívida técnica

  As skills prescrevem shadcn/ui + Radix + CVA + pasta shared/components/ui/. Na        
  realidade:

  ┌────────────────────────────────┬────────────────────────────┐
  │ Prescrito                      │ Actual                     │
  ├────────────────────────────────┼────────────────────────────┤
  │ shadcn/ui + Radix              │ ❌ Não instalado           │
  ├────────────────────────────────┼────────────────────────────┤
  │ src/components/ui/             │ ❌ Pasta vazia/inexistente │
  ├────────────────────────────────┼────────────────────────────┤
  │ Storybook                      │ ❌ Não configurado         │
  ├────────────────────────────────┼────────────────────────────┤
  │ Chart.js                       │ ❌ Não instalado           │
  ├────────────────────────────────┼────────────────────────────┤
  │ TanStack Table                 │ ❌ Não instalado           │
  ├────────────────────────────────┼────────────────────────────┤
  │ React 19                       │ ⚠️ React 18.2             │
  ├────────────────────────────────┼────────────────────────────┤
  │ CVA (class-variance-authority) │ ❌ Ausente                 │
  └────────────────────────────────┴────────────────────────────┘

  O visual actual é construído com classes utilitárias Tailwind + CSS custom
  (glass-card, btn-primary), o que funciona mas não escala para os restantes
  módulos.

  4.2 Módulos por estado de implementação

  ┌──────────────────────────────────────────┬─────────────────────────────────────┐    
  │ Módulo                                   │ Estado                              │    
  ├──────────────────────────────────────────┼─────────────────────────────────────┤    
  │ organizations                            │ ⚠️ ~70% — foco desta fase          │     
  ├──────────────────────────────────────────┼─────────────────────────────────────┤    
  │ auth / onboarding                        │ ✅ Funcional (wizard completo)      │    
  ├──────────────────────────────────────────┼─────────────────────────────────────┤    
  │ clubs                                    │ ⚠️ ~40% — listagem + detalhe, sem  │     
  │                                          │ gestão completa                     │    
  ├──────────────────────────────────────────┼─────────────────────────────────────┤    
  │ competitions                             │ ⚠️ ~50% — listagem, detalhe, match │     
  │                                          │ center parcial                      │    
  ├──────────────────────────────────────────┼─────────────────────────────────────┤    
  │ players                                  │ ⚠️ ~30% — listagem + detalhe       │     
  │                                          │ básicos                             │    
  ├──────────────────────────────────────────┼─────────────────────────────────────┤    
  │ notifications                            │ ⚠️ ~40% — bell + dropdown + página │     
  ├──────────────────────────────────────────┼─────────────────────────────────────┤    
  │ dashboards                               │ ⚠️ Mock — MOCK_DASHBOARD_DATA      │     
  │                                          │ quando API falha                    │    
  ├──────────────────────────────────────────┼─────────────────────────────────────┤    
  │ transfers, news, fans, rankings,         │ ❌ Scaffold vazio                   │    
  │ stadiums, subscriptions                  │                                     │    
  └──────────────────────────────────────────┴─────────────────────────────────────┘    

  4.3 Dados fictícios (risco de "demo enganosa")

   frontend/src/modules/dashboards/services/dashboard.api.ts lines 4-5

  // Realistas fallbacks de mock para garantir que os dashboards nunca apareçam
  vazios (WOW Aesthetics)
  export const MOCK_DASHBOARD_DATA: DashboardOverviewResponse = {

  Os dashboards executivos/federação/liga mostram números fictícios quando o
  endpoint /dashboard/overview/ não existe.

  4.4 Qualidade e conformidade

  ┌──────────────────────────────────┬─────────────────────────────────────────────┐    
  │ Critério (Frontend Reviewer      │ Estado                                      │    
  │ Skill)                           │                                             │    
  ├──────────────────────────────────┼─────────────────────────────────────────────┤    
  │ Arquitectura feature-based       │ ✅                                          │    
  ├──────────────────────────────────┼─────────────────────────────────────────────┤    
  │ TypeScript strict                │ ✅ (type-check OK)                          │    
  ├──────────────────────────────────┼─────────────────────────────────────────────┤    
  │ Testes (component/hook/service)  │ ❌ Zero                                     │    
  ├──────────────────────────────────┼─────────────────────────────────────────────┤    
  │ Acessibilidade WCAG 2.1          │ ⚠️ Parcial (focus rings, alguns            │     
  │                                  │ aria-label)                                 │    
  ├──────────────────────────────────┼─────────────────────────────────────────────┤    
  │ i18n (i18next instalado)         │ ⚠️ Strings hardcoded em PT                 │     
  ├──────────────────────────────────┼─────────────────────────────────────────────┤    
  │ Responsive mobile-first          │ ⚠️ Parcial                                 │     
  ├──────────────────────────────────┼─────────────────────────────────────────────┤    
  │ Permission denied states         │ ❌ Ausentes                                 │    
  ├──────────────────────────────────┼─────────────────────────────────────────────┤    
  │ Inline styles                    │ ⚠️ Presentes (cores de branding)           │     
  └──────────────────────────────────┴─────────────────────────────────────────────┘    

  4.5 Desvios face ao layout de referência

  O mock layout_design/2 organization_dashboard_bolayetu/code.html inclui widgets       
  que faltam na implementação React:

  • Gráfico de evolução de subscritores
  • Calendário de jogos próximos
  • Feed de actividade recente
  • Tabela de clubes com acções rápidas
  • Secção de aprovações pendentes

  ────────────────────────────────────────

  5. Mapa de prioridades para continuar o módulo Organização

  Seguindo a sequência Design System → Componentes reutilizáveis → Páginas → Estados    
  → Testes das skills:

  Fase A — Fundação (bloqueante para escalar)

  1. Inicializar Design System: Button, Card, Input, Select, Badge, Table,
     Skeleton, EmptyState, Tabs
  2. Migrar KpiCard, OrganizationCard e formulários para primitivos do DS
  3. Instalar TanStack Table para tabelas de competições e clubes

  Fase B — Completar Dashboard Organização

  4. Remover mock de TransferItem — ligar a API de transfers ou mostrar empty
     state honesto
  5. Adicionar widget de clubes associados (useOrganizationClubs)
  6. Adicionar Activity Feed e Quick Actions (criar clube, convidar membro,
     publicar competição)
  7. Corrigir navegação: competições → /competitions
  8. Alinhar Settings ao DashboardLayout

  Fase C — Gestão operacional

  9. UI de membros da organização
  10. UI de pedidos de filiação de clubes
  11. Corrigir estado de subscrição no detalhe público (ler do backend)
  12. Secção lançar portal fora do onboarding (para orgs em estado pending)

  Fase D — Qualidade

  13. Testes para hooks e componentes críticos
  14. Estados 403/404/422 consistentes
  15. Remover ou isolar mocks dos dashboards executivos

  ────────────────────────────────────────

  6. Diagrama do estado actual vs. alvo

  ┌────────────────────────┐ ┌───────────────────────────────────────────┐
  │     Estado Actual      │ │               Alvo (Skills)               │
  │                        │ │                                           │
  │                        │ │                                           │
  │ ┌────────────────────┐ │ ├─────────────────────┐   ┌───────────────┐ │
  │ │                    │ │ │                     │   │               │ │
  │ │ Listagem Pública ✅ ├─┼►│  Páginas completas  ├──►│ Testes + A11y │ │
  │ │                    │ │ │                     │   │               │ │
  │ └────────────────────┘ │ ├─────────────────────┘   └───────────────┘ │
  │            ┌───────────┤ │                                 ▲         │
  │ ┌────────────────────┐ │ ├─────────────────────┐           │         │
  │ │          ┴         │ │ │                     │           │         │
  │ │ Detalhe Público ⚠️ │ ├►│   DS reutilizável   ├───────────┤         │
  │ │                    │ │ │                     │           │         │
  │ └────────────────────┘ │ ├─────────────────────┘           │         │
  │            ┌───────────┤ │                                 │         │
  │ ┌────────────────────┐ │ ├─────────────────────┐           │         │
  │ │          ┴         │ │ │                     │           │         │
  │ │     Settings ✅     │ ├►│ Dashboard acionável ├───────────┤         │
  │ │                    │ │ │                     │           │         │
  │ └────────────────────┘ │ ├─────────────────────┘           │         │
  │            ┌───────────┤ │                                 │         │
  │ ┌────────────────────┐ │ ├─────────────────────┐           │         │
  │ │          ┴         │ │ │                     │           │         │
  │ │    Dashboard ⚠️    │ │ │  Gestão operacional ├───────────┘         │
  │ │                    │ │ │                     │                     │
  │ └────────────────────┘ │ ├─────────────────────┘                     │
  │                        │ │          ▲                                │
  │ ┌────────────────────┐ │ └──────────┼────────────────────────────────┘
  │ │                    │ │            │
  │ │     Membros ❌      ├─┼────────────┤
  │ │                    │ │            │
  │ └────────────────────┘ │            │
  │                        │            │
  │ ┌────────────────────┐ │            │
  │ │                    │ │            │
  │ │    Filiações ❌     ├─┼────────────┘
  │ │                    │ │
  │ └────────────────────┘ │
  │            ┌───────────┤
  │ ┌────────────────────┐ │
  │ │          ┴         │ │
  │ │  Design System ❌   │ │
  │ │                    │ │
  │ └────────────────────┘ │
  │                        │
  └────────────────────────┘
  ctrl+o to show source

  ────────────────────────────────────────

  7. Recomendação imediata

  Para continuar a construção pelo componente Organização, a ordem mais eficiente é:    

  1. Primeiro — criar os primitivos do Design System (as skills proíbem
     componentes one-off fora do DS)
  2. Depois — refactor do OrganizationDashboardPage para alinhar com o mock HTML e      
     remover dados fictícios
  3. Em seguida — unificar Settings no DashboardLayout e corrigir rotas de
     competições
  4. Por último — membros e filiações (dependem de UI de gestão que ainda não
     existe)

  ────────────────────────────────────────

  Quer que avance com a Fase A (Design System + refactor dos componentes de
  Organização) ou prefere ir directamente ao dashboard completo (Fase B) usando as      
  classes Tailwind actuais e migrar para o DS depois?