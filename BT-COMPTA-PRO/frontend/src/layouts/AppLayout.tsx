import { ArrowLeft, ChevronDown, LogOut, UserRound, WifiOff } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Logo } from '../components/Logo';
import { cx } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import { SECTIONS, tabsFor, titleFor } from './nav';

function useOnline() {
  const [online, setOnline] = useState(typeof navigator === 'undefined' ? true : navigator.onLine);
  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => {
      window.removeEventListener('online', on);
      window.removeEventListener('offline', off);
    };
  }, []);
  return online;
}

export default function AppLayout() {
  const { user, logout, hasRole } = useAuth();
  const [menu, setMenu] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const online = useOnline();
  const path = location.pathname.replace(/\/$/, '');

  useEffect(() => {
    setMenu(false);
    window.scrollTo(0, 0);
  }, [location.pathname]);

  const initials = `${user?.first_name?.[0] ?? ''}${user?.last_name?.[0] ?? ''}`.toUpperCase() || user?.username?.[0]?.toUpperCase();
  const tabs = tabsFor(user);
  const isTabRoot = tabs.some((t) => t.to === path);
  const focused = path.endsWith('/passer'); // épreuve en cours : pas de distraction

  const sidebar = (
    <nav className="flex h-full flex-col border-r border-white/5 bg-navy-950 text-white" aria-label="Navigation principale">
      <div className="flex h-16 shrink-0 items-center border-b border-white/[0.06] px-5">
        <NavLink to="/app" aria-label="Accueil BT COMPTA PRO">
          <Logo light />
        </NavLink>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-5 [scrollbar-width:thin]">
        {SECTIONS.map((section) => {
          const items = section.items.filter((i) => !i.roles || hasRole(...i.roles));
          if (!items.length) return null;
          return (
            <div key={section.title || 'main'} className="mb-6 last:mb-0">
              {section.title && (
                <div className="mb-1.5 px-3 text-[10.5px] font-semibold uppercase tracking-[0.16em] text-white/35">{section.title}</div>
              )}
              <ul className="space-y-0.5">
                {items.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.end}
                      className={({ isActive }) =>
                        cx(
                          'group relative flex h-10 items-center gap-3 rounded-lg px-3 text-[13.5px] font-medium transition-colors [&_svg]:size-[18px] [&_svg]:shrink-0',
                          isActive
                            ? 'bg-white/[0.08] text-white [&_svg]:text-brand-600 before:absolute before:inset-y-2 before:-left-3 before:w-[3px] before:rounded-r-full before:bg-brand-600'
                            : 'text-white/60 hover:bg-white/[0.04] hover:text-white [&_svg]:text-white/45 hover:[&_svg]:text-white/80',
                        )
                      }
                    >
                      {item.icon}
                      <span className="flex-1 truncate">{item.label}</span>
                      {item.badge && (
                        <span className={cx('rounded-md px-1.5 py-0.5 text-[10px] font-bold tracking-wide',
                          item.badge === 'BT1' ? 'bg-brand-600/15 text-brand-600' : 'bg-money-600/15 text-money-600')}>
                          {item.badge}
                        </span>
                      )}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>

      <div className="shrink-0 border-t border-white/[0.06] p-3">
        <div className="flex items-center gap-3 rounded-lg px-2 py-2">
          <NavLink to="/app/profil" className="flex min-w-0 flex-1 items-center gap-3 rounded-lg hover:opacity-90" title="Mon profil">
            <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-brand-600 text-xs font-bold text-white">{initials}</span>
            <span className="min-w-0 leading-tight">
              <span className="block truncate text-[13px] font-semibold text-white">{user?.first_name ? `${user.first_name} ${user.last_name}` : user?.username}</span>
              <span className="block truncate text-[11.5px] text-white/45">{user?.role_label}</span>
            </span>
          </NavLink>
          <button onClick={() => logout()} className="grid size-8 shrink-0 place-items-center rounded-lg text-white/45 transition hover:bg-white/[0.06] hover:text-white" title="Se déconnecter" aria-label="Se déconnecter">
            <LogOut className="size-4" />
          </button>
        </div>
      </div>
    </nav>
  );

  return (
    <div className="min-h-dvh lg:pl-[272px]">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[272px] lg:block">{sidebar}</aside>

      {/* Barre d'application : téléphone et tablette */}
      <header className="no-print sticky top-0 z-30 bg-navy-900 pl-[env(safe-area-inset-left)] pr-[env(safe-area-inset-right)] pt-[env(safe-area-inset-top)] text-white lg:hidden">
        <div className="flex h-14 items-center gap-1 px-2">
          {isTabRoot ? (
            <Link to="/app" className="pl-2" aria-label="Accueil"><Logo light /></Link>
          ) : (
            <>
              <button onClick={() => (window.history.length > 1 ? navigate(-1) : navigate('/app'))} className="grid size-11 place-items-center rounded-xl active:bg-white/10" aria-label="Retour">
                <ArrowLeft className="size-5" />
              </button>
              <span className="min-w-0 truncate text-[17px] font-semibold">{titleFor(path)}</span>
            </>
          )}
          <div className="flex-1" />
          <Link to="/app/profil" className="mr-1 grid size-9 place-items-center rounded-full bg-brand-600 text-xs font-bold" aria-label="Mon profil">{initials}</Link>
        </div>
        {!online && (
          <div className="flex items-center justify-center gap-1.5 bg-amber-500 py-1 text-xs font-semibold text-navy-950">
            <WifiOff className="size-3.5" /> Hors connexion : seuls les cours déjà ouverts restent disponibles
          </div>
        )}
      </header>

      {/* En-tête ordinateur */}
      <header className="sticky top-0 z-30 hidden h-16 items-center gap-3 border-b border-slate-200/70 bg-paper/85 px-8 backdrop-blur-md lg:flex">
        <div className="flex-1" />
        {!online && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
            <WifiOff className="size-3.5" /> Hors connexion
          </span>
        )}
        <div className="relative">
          <button onClick={() => setMenu((m) => !m)} className="flex items-center gap-2.5 rounded-xl py-1.5 pl-1.5 pr-2.5 hover:bg-white">
            <span className="grid size-8 place-items-center rounded-lg bg-gradient-to-br from-brand-600 to-navy-800 text-xs font-bold text-white">{initials}</span>
            <span className="text-left leading-tight">
              <span className="block text-sm font-semibold text-navy-900">{user?.first_name || user?.username}</span>
              <span className="block text-[11px] text-slate-500">{user?.role_label}</span>
            </span>
            <ChevronDown className="size-4 text-slate-400" />
          </button>
          {menu && (
            <div className="absolute right-0 mt-2 w-56 overflow-hidden rounded-2xl border border-slate-200 bg-white py-1.5 shadow-xl">
              <div className="border-b border-slate-100 px-4 pb-2.5 pt-1.5">
                <div className="truncate text-sm font-semibold text-navy-900">{user?.first_name} {user?.last_name}</div>
                <div className="truncate text-xs text-slate-500">{user?.email}</div>
              </div>
              <NavLink to="/app/profil" className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50">
                <UserRound className="size-4" /> Mon profil
              </NavLink>
              <button onClick={() => logout()} className="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50">
                <LogOut className="size-4" /> Se déconnecter
              </button>
            </div>
          )}
        </div>
      </header>

      <main key={location.pathname} className={cx('app-page mx-auto max-w-[1400px] px-4 py-5 sm:px-6 lg:px-8 lg:py-8', focused ? 'pb-8' : 'pb-tabbar')}>
        <Outlet />
      </main>

      {/* Onglets : téléphone et tablette */}
      {!focused && (
        <nav className="no-print fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md lg:hidden" aria-label="Onglets">
          <ul className="mx-auto grid max-w-2xl grid-cols-5">
            {tabs.map((tab) => {
              const active = tab.match.length ? tab.match.some((m) => path.startsWith(m)) : path === tab.to;
              return (
                <li key={tab.label}>
                  <Link to={tab.to} aria-current={active ? 'page' : undefined}
                    className={cx('flex h-[58px] flex-col items-center justify-center gap-0.5 text-[11px] font-semibold transition-colors active:scale-95 [&_svg]:size-[22px]',
                      active ? 'text-brand-600' : 'text-slate-500')}>
                    <span className={cx('grid h-7 w-14 place-items-center rounded-full transition-colors', active && 'bg-brand-50')}>{tab.icon}</span>
                    {tab.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      )}
    </div>
  );
}
