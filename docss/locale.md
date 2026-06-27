Implementei o sistema de multidiomas com Context, dicionários e integração nos pontos que pediste. Vou resumir a arquitetura e onde usar.

---

**1. Dicionários de Tradução (locales.ts)**

No ficheiro [locale/i18n/locales.ts](file:///c:/Project/bolayetu/frontend/locale/i18n/locales.ts) tens:

- Tipo base:

```ts
export type Language = 'pt' | 'en' | 'fr';
```

- Objeto `translations` com PT, EN e FR, separados em namespaces:

```ts
export const translations = {
  pt: {
    nav: { dashboard: 'Dashboard', clubs: 'Clubs', players: 'Jogadores', tournaments: 'Torneios', venues: 'Estádios', reports: 'Relatórios', news: 'Notícias', ads: 'Publicidade', subscription: 'Assinatura', settings: 'Definições', sign_out: 'Sair' },
    public: { home: 'Início', news: 'Notícias', orgs: 'Organizações', tournaments: 'Campeonatos', features: 'Funcionalidades', pricing: 'Preços', support: 'Suporte', login: 'Entrar', create_league: 'Criar Liga', dashboard: 'Dashboard' },
    settings: { title: 'Definições', subtitle: 'Gerencie as suas preferências e segurança da conta.', profile: 'Perfil', organization: 'Organização', security: 'Segurança', notifications: 'Notificações', users: 'Utilizadores', language: 'Idioma', save: 'Guardar Alterações', saving: 'A guardar...' }
  },
  en: {
    nav: { dashboard: 'Dashboard', clubs: 'Clubs', players: 'Players', tournaments: 'Tournaments', venues: 'Venues', reports: 'Reports', news: 'News', ads: 'Advertising', subscription: 'Subscription', settings: 'Settings', sign_out: 'Sign Out' },
    public: { home: 'Home', news: 'News', orgs: 'Organizations', tournaments: 'Championships', features: 'Features', pricing: 'Pricing', support: 'Support', login: 'Login', create_league: 'Create League', dashboard: 'Dashboard' },
    settings: { title: 'Settings', subtitle: 'Manage your preferences and account security.', profile: 'Profile', organization: 'Organization', security: 'Security', notifications: 'Notifications', users: 'Users', language: 'Language', save: 'Save Changes', saving: 'Saving...' }
  },
  fr: {
    nav: { dashboard: 'Tableau de bord', clubs: 'Clubs', players: 'Joueurs', tournaments: 'Tournois', venues: 'Stades', reports: 'Rapports', news: 'Actualités', ads: 'Publicité', subscription: 'Abonnement', settings: 'Paramètres', sign_out: 'Déconnexion' },
    public: { home: 'Accueil', news: 'Actualités', orgs: 'Organisations', tournaments: 'Championnats', features: 'Fonctionnalités', pricing: 'Tarifs', support: 'Support', login: 'Connexion', create_league: 'Créer Ligue', dashboard: 'Tableau de bord' },
    settings: { title: 'Paramètres', subtitle: 'Gérez vos préférences et la sécurité de votre compte.', profile: 'Profil', organization: 'Organisation', security: 'Sécurité', notifications: 'Notifications', users: 'Utilisateurs', language: 'Langue', save: 'Enregistrer', saving: 'Enregistrement...' }
  }
};
```

Chave de tradução é sempre um path do tipo `"nav.dashboard"`, `"public.home"`, `"settings.language"`.

---

**2. LanguageContext com `t(key)` e localStorage**

No ficheiro [locale/context/LanguageContext.tsx](file:///c:/Project/bolayetu/frontend/locale/context/LanguageContext.tsx):

- Interface do contexto:

```ts
interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}
```

- Hook e Provider:

```tsx
const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>('pt');

  useEffect(() => {
    const savedLang = localStorage.getItem('bolayetu_lang') as Language;
    if (savedLang && ['pt', 'en', 'fr'].includes(savedLang)) {
      setLanguageState(savedLang);
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('bolayetu_lang', lang);
  };

  const t = (key: string): string => {
    const keys = key.split('.');
    let current: any = translations[language];
    
    for (const k of keys) {
      if (current[k] === undefined) {
        console.warn(`Translation missing for key: ${key} in language: ${language}`);
        return key;
      }
      current = current[k];
    }
    
    return current as string;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};
```

Comportamento:

- Carrega idioma de `localStorage` (`bolayetu_lang`).
- Salva sempre que `setLanguage` é chamado.
- `t('namespace.chave')` percorre o objeto de traduções; se faltar, devolve a própria chave.

---

**3. Integração global no App**

No [App.tsx](file:///c:/Project/bolayetu/frontend/App.tsx#L105-L199) envolvi toda a app com o `LanguageProvider`:

```tsx
import { LanguageProvider } from './locale/context/LanguageContext';

const App: React.FC = () => {
  return (
    <LanguageProvider>
      <AuthProvider>
        <NotificationProvider>
          <HashRouter>
            <Routes>
              ...
            </Routes>
          </HashRouter>
        </NotificationProvider>
      </AuthProvider>
    </LanguageProvider>
  );
};
```

Assim, `useLanguage()` funciona em qualquer página/layout.

---

**4. Sidebar traduzida dinamicamente**

No [Sidebar.tsx](file:///c:/Project/bolayetu/frontend/components/bars/Sidebar.tsx):

- Importa o contexto:

```tsx
import { useLanguage } from '../../locale/context/LanguageContext';
```

- Usa `t`:

```tsx
const { user } = useAuth();
const { can } = usePermissions();
const { t } = useLanguage();

const navItems = [
  { name: 'nav.dashboard', path: '/dashboard', icon: 'fa-chart-line', show: true, end: true },
  { name: 'nav.clubs', path: '/dashboard/clubs', icon: 'fa-shield-halved', show: true },
  { name: 'nav.players', path: '/dashboard/players', icon: 'fa-users', show: true },
  { name: 'nav.tournaments', path: '/dashboard/tournaments', icon: 'fa-trophy', show: true },
  { name: 'nav.venues', path: '/dashboard/venues', icon: 'fa-location-dot', show: true },
  { name: 'nav.reports', path: '/dashboard/reports', icon: 'fa-file-pdf', show: true },
  { name: 'nav.news', path: '/dashboard/news', icon: 'fa-newspaper', show: can(PERMISSIONS.MANAGE_SETTINGS) },
  { name: 'nav.subscription', path: '/dashboard/subscription', icon: 'fa-credit-card', show: can(PERMISSIONS.VIEW_FINANCIALS) },
  { name: 'nav.settings', path: '/dashboard/settings', icon: 'fa-cog', show: true },
];
```

- Render:

```tsx
<i className={`fa-solid ${item.icon} w-6`}></i>
{t(item.name)}
```

Trocar de idioma reflete imediatamente na Sidebar.

---

**5. Layout público com nav traduzida + switcher de idioma**

No [PublicLayout.tsx](file:///c:/Project/bolayetu/frontend/components/layouts/PublicLayout.tsx):

- Importa contexto e tipo:

```tsx
import { useLanguage } from '../../locale/context/LanguageContext';
import type { Language } from '../../locale/i18n/locales';

const { isAuthenticated } = useAuth();
const { language, setLanguage, t } = useLanguage();
```

- Nav links usam chaves:

```tsx
const navLinks = [
  { key: 'public.home', path: '/' },
  { key: 'public.tournaments', path: '/tournaments' },
  { key: 'public.orgs', path: '/organizations' },
  { key: 'public.news', path: '/news' },
  { key: 'public.features', path: '/features' },
  { key: 'public.pricing', path: '/pricing' },
  { key: 'public.support', path: '/support' },
];
```

- Render das entradas:

```tsx
{navLinks.map((link) => (
  <Link
    key={link.path}
    to={link.path}
    className={...}
  >
    {t(link.key)}
  </Link>
))}
```

- Switcher de idioma na nav pública:

```tsx
<div className="flex items-center space-x-4">
  <div className="hidden sm:flex items-center space-x-1 mr-2">
    {(['pt', 'en', 'fr'] as Language[]).map((lang) => (
      <button
        key={lang}
        type="button"
        onClick={() => setLanguage(lang)}
        className={`text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded-full border ${
          language === lang
            ? 'bg-white text-secondary-900 border-white'
            : isScrolled || (location.pathname !== '/' && location.pathname !== '')
              ? 'text-gray-500 border-gray-200 hover:bg-gray-100'
              : 'text-white/80 border-white/40 hover:bg-white/10'
        }`}
      >
        {lang}
      </button>
    ))}
  </div>
  {isAuthenticated ? (
    <Link to="/dashboard" className="bg-brand-600 ...">
      {t('public.dashboard')}
    </Link>
  ) : (
    <>
      <Link to="/login" className="text-sm font-bold ...">
        {t('public.login')}
      </Link>
      <Link to="/onboarding" className="bg-brand-600 ...">
        {t('public.create_league')}
      </Link>
    </>
  )}
</div>
```

Efeito:

- Botões “pt / en / fr” alteram o contexto global.
- Nav pública e botões de login/dashboard mudam de idioma instantaneamente.

---

**6. Settings: seletor de idioma funcional e textos chave traduzidos**

No [Settings.tsx](file:///c:/Project/bolayetu/frontend/pages/Settings.tsx):

- Importa e usa contexto:

```tsx
import { useLanguage } from '../locale/context/LanguageContext';
import type { Language } from '../locale/i18n/locales';

const { user } = useAuth();
const { can } = usePermissions();
const { language, setLanguage, t } = useLanguage();
```

- Estado inicial de `profile` já respeita o idioma atual:

```tsx
const [profile, setProfile] = useState({
  name: user?.name || '',
  email: user?.email || '',
  phone: '+244 923 000 000',
  language: language,
  timezone: 'Africa/Luanda'
});
```

- Título e subtítulo:

```tsx
<h1 className="text-2xl font-bold text-gray-800">{t('settings.title')}</h1>
<p className="text-sm text-gray-500">{t('settings.subtitle')}</p>
```

- Tabs usam traduções:

```tsx
<i className="fa-solid fa-user mr-2"></i> {t('settings.profile')}
...
<i className="fa-solid fa-building mr-2"></i> {t('settings.organization')}
...
<i className="fa-solid fa-lock mr-2"></i> {t('settings.security')}
...
<i className="fa-solid fa-bell mr-2"></i> {t('settings.notifications')}
...
<i className="fa-solid fa-users-gear mr-2"></i> {t('settings.users')}
```

- Seletor de idioma sincronizado com o Context:

```tsx
<label className="block text-sm font-medium text-gray-700 mb-1">{t('settings.language')}</label>
<select 
  value={language}
  onChange={(e) => {
    const newLang = e.target.value as Language;
    setLanguage(newLang);
    setProfile({...profile, language: newLang});
  }}
  className="w-full border-gray-300 rounded-md shadow-sm border p-2 focus:border-brand-500 focus:ring-brand-500 bg-white"
>
  <option value="pt">Português</option>
  <option value="en">English</option>
  <option value="fr">Français</option>
</select>
```

- Botão “Guardar Alterações” também usando traduções:

```tsx
{isLoading ? (
  <>
    <i className="fa-solid fa-circle-notch fa-spin mr-2"></i> {t('settings.saving')}
  </>
) : (
  <>
    <i className="fa-solid fa-save mr-2"></i> {t('settings.save')}
  </>
)}
```

Assim, quando o utilizador mudar o idioma nas definições:

- O `LanguageContext` é atualizado (global).
- O `profile.language` fica em sincronia.
- Sidebar, layout público, textos-chave de Settings são atualizados.

---

**7. Verificação técnica**

- Corri `npm run build` no frontend: build ok (apenas o aviso conhecido de bundle > 500kB).
- Diagnostics do TypeScript para os ficheiros alterados (`locales.ts`, `LanguageContext.tsx`, `Sidebar.tsx`, `PublicLayout.tsx`, `App.tsx`, `Settings.tsx`) não apontam erros.

---

**Como usar a partir de agora**

- Para traduzir novo texto em qualquer componente:

  1. Adicionar a tradução à estrutura em `translations` (namespace apropriado).
  2. No componente, importar `useLanguage`:
     ```tsx
     import { useLanguage } from '../locale/context/LanguageContext';
     const { t } = useLanguage();
     ```
  3. Renderizar com `t('namespace.chave')`.

Se quiseres, no próximo passo posso:

- Internacionalizar mais partes do Dashboard (títulos de cards, labels de tabelas).
- Adicionar persistência do idioma também no backend (por exemplo, campo de preferência no utilizador) para sincronizar entre dispositivos.