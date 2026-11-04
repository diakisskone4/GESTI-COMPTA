import { ChevronRight, Download, LogOut, UserRound } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { SECTIONS } from '../layouts/nav';
import { useInstall } from '../modules/mobile/Install';

const row = 'flex h-14 items-center gap-3.5 px-4 text-[15px] font-medium text-navy-900 active:bg-slate-50 [&>svg:first-child]:size-5 [&>svg:first-child]:text-slate-500';

/** Menu complet de l'application sur téléphone et tablette. */
export default function MorePage() {
  const { user, logout, hasRole } = useAuth();
  const { installed, start, guideNode } = useInstall();
  const initials = `${user?.first_name?.[0] ?? ''}${user?.last_name?.[0] ?? ''}`.toUpperCase() || user?.username?.[0]?.toUpperCase();

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <Link to="/app/profil" className="card flex items-center gap-3.5 p-4 active:scale-[0.99]">
        <span className="grid size-14 shrink-0 place-items-center rounded-full bg-brand-600 text-lg font-bold text-white">{initials}</span>
        <span className="min-w-0 flex-1">
          <span className="block truncate font-bold text-navy-900">{user?.first_name} {user?.last_name}</span>
          <span className="block truncate text-sm text-slate-500">{user?.role_label}{user?.level ? ` · ${user.level}` : ''}</span>
        </span>
        <ChevronRight className="size-5 text-slate-300" />
      </Link>

      {SECTIONS.slice(1).map((section) => {
        const items = section.items.filter((i) => !i.roles || hasRole(...i.roles));
        if (!items.length) return null;
        return (
          <section key={section.title}>
            <h2 className="mb-2 px-1 text-xs font-bold uppercase tracking-wider text-slate-500">{section.title}</h2>
            <ul className="card divide-y divide-slate-100 overflow-hidden">
              {items.map((item) => (
                <li key={item.to}>
                  <Link to={item.to} className={`${row} [&_svg]:size-5 [&_svg]:text-slate-500`}>
                    {item.icon}
                    <span className="min-w-0 flex-1 truncate">{item.label}</span>
                    {item.badge && <span className="text-xs font-bold text-slate-400">{item.badge}</span>}
                    <ChevronRight className="!size-4 !text-slate-300" />
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        );
      })}

      <section>
        <h2 className="mb-2 px-1 text-xs font-bold uppercase tracking-wider text-slate-500">Compte</h2>
        <ul className="card divide-y divide-slate-100 overflow-hidden">
          <li><Link to="/app/profil" className={row}><UserRound /><span className="flex-1">Mon profil</span><ChevronRight className="size-4 text-slate-300" /></Link></li>
          {!installed && (
            <li><button onClick={start} className={`${row} w-full text-left`}><Download /><span className="flex-1">Installer l'application</span><ChevronRight className="size-4 text-slate-300" /></button></li>
          )}
          <li><button onClick={() => logout()} className={`${row} w-full text-left !text-red-600 [&>svg:first-child]:!text-red-500`}><LogOut /><span className="flex-1">Se déconnecter</span></button></li>
        </ul>
      </section>
      <p className="text-center text-xs text-slate-400">BT COMPTA PRO · SYSCOHADA · Mali</p>
      {guideNode}
    </div>
  );
}
