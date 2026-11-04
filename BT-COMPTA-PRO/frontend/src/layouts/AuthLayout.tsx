import { CheckCircle2 } from 'lucide-react';
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { Logo } from '../components/Logo';

export default function AuthLayout({ title, subtitle, children }: { title: string; subtitle: ReactNode; children: ReactNode }) {
  return (
    <div className="grid min-h-screen bg-paper lg:grid-cols-[1fr_1.1fr]">
      <div className="relative hidden overflow-hidden bg-navy-900 p-12 text-white lg:flex lg:flex-col">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(70%_50%_at_100%_0%,rgba(22,131,216,0.35),transparent_60%),radial-gradient(60%_50%_at_0%_100%,rgba(22,163,106,0.25),transparent_60%)]" />
        <Link to="/" className="relative">
          <Logo light />
        </Link>
        <div className="relative mt-auto max-w-md">
          <h2 className="text-3xl font-bold leading-tight">La comptabilité du BT, de la théorie à l'écriture validée.</h2>
          <ul className="mt-8 space-y-3 text-sm text-white/75">
            {['Cours BT1 et BT2 structurés par module', 'Calculatrices avec étapes et écritures', 'Journal, grand livre, balance et états financiers', 'Examens blancs notés sur 20'].map((t) => (
              <li key={t} className="flex items-center gap-3">
                <CheckCircle2 className="size-4 text-money-600" /> {t}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="flex flex-col px-4 py-8 sm:px-8">
        <Link to="/" className="mb-10 lg:hidden">
          <Logo />
        </Link>
        <div className="m-auto w-full max-w-md">
          <h1 className="text-2xl font-bold tracking-tight text-navy-900 sm:text-3xl">{title}</h1>
          <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </div>
    </div>
  );
}
