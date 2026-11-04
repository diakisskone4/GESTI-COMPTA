import { Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Alert, Badge, Card, cx, PageHeader, Spinner } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import type { Account } from '../types';

const CLASSES: Record<string, string> = {
  '1': 'Ressources durables', '2': 'Actif immobilisé', '3': 'Stocks', '4': 'Tiers', '5': 'Trésorerie',
  '6': 'Charges des activités ordinaires', '7': 'Produits des activités ordinaires', '8': 'Autres charges et produits',
};

export default function AccountPlanPage() {
  const { data, loading, error } = useFetch<Account[]>('/accounting/accounts/');
  const [cls, setCls] = useState('');
  const [q, setQ] = useState('');
  const list = useMemo(
    () => (data ?? []).filter((a) => (!cls || a.account_class === cls) && (!q || a.code.startsWith(q) || a.label.toLowerCase().includes(q.toLowerCase()))),
    [data, cls, q],
  );

  return (
    <div>
      <PageHeader eyebrow="Référentiel" title="Plan comptable SYSCOHADA révisé" subtitle="Extrait de travail des comptes principaux et divisionnaires utilisés dans l'application." />
      <div className="my-5 flex flex-col gap-3 lg:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
          <input className="field pl-10" placeholder="Numéro ou intitulé…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <div className="flex gap-1 overflow-x-auto rounded-xl bg-white p-1 ring-1 ring-slate-200">
          {['', ...Object.keys(CLASSES)].map((c) => (
            <button key={c} onClick={() => setCls(c)} title={CLASSES[c]} className={cx('shrink-0 rounded-lg px-3 py-1.5 text-sm font-medium', cls === c ? 'bg-navy-900 text-white' : 'text-slate-600 hover:bg-slate-50')}>
              {c ? `Classe ${c}` : 'Toutes'}
            </button>
          ))}
        </div>
      </div>
      {loading && <Spinner />}
      {error && <Alert tone="error">{error}</Alert>}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="table-base">
            <thead><tr><th className="w-28">Compte</th><th>Intitulé</th><th className="hidden sm:table-cell">Classe</th><th className="w-28">Statut</th></tr></thead>
            <tbody>
              {list.map((a) => (
                <tr key={a.id} className="hover:bg-slate-50/60">
                  <td className={cx('font-mono text-navy-900', a.code.length <= 2 ? 'font-bold' : a.code.length === 3 ? 'pl-5 font-semibold' : 'pl-8')}>{a.code}</td>
                  <td className={cx(a.code.length <= 2 ? 'font-semibold text-navy-900' : 'text-slate-700')}>{a.label}</td>
                  <td className="hidden text-slate-500 sm:table-cell">{CLASSES[a.account_class]}</td>
                  <td>{a.verified ? <Badge tone="green">Vérifié</Badge> : <Badge tone="amber">À vérifier</Badge>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
