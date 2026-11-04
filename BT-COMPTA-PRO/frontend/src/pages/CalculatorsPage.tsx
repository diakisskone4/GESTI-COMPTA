import { ArrowRight, Calculator, Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Badge, Card, cx, PageHeader, Spinner } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import type { CalculatorMeta } from '../types';

export default function CalculatorsPage() {
  const { data, loading, error } = useFetch<CalculatorMeta[]>('/calculations/');
  const [level, setLevel] = useState<'all' | 'BT1' | 'BT2'>('all');
  const [q, setQ] = useState('');

  const groups = useMemo(() => {
    const list = (data ?? []).filter(
      (c) => (level === 'all' || c.level === level) && (`${c.title} ${c.description} ${c.category}`.toLowerCase().includes(q.toLowerCase())),
    );
    return list.reduce<Record<string, CalculatorMeta[]>>((acc, c) => {
      (acc[`${c.level} · ${c.category}`] ||= []).push(c);
      return acc;
    }, {});
  }, [data, level, q]);

  return (
    <div>
      <PageHeader eyebrow="Module de calcul automatique" title="Calculatrices comptables" subtitle="Chaque calcul affiche la formule, les étapes, le résultat, son interprétation et les écritures, avec export PDF et Excel." />
      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
          <input className="field pl-10" placeholder="Rechercher : TVA, amortissement, seuil…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <div className="flex gap-1 rounded-xl bg-white p-1 ring-1 ring-slate-200">
          {(['all', 'BT1', 'BT2'] as const).map((l) => (
            <button key={l} onClick={() => setLevel(l)} className={cx('rounded-lg px-4 py-1.5 text-sm font-medium', level === l ? 'bg-navy-900 text-white' : 'text-slate-600 hover:bg-slate-50')}>
              {l === 'all' ? 'Toutes' : l}
            </button>
          ))}
        </div>
      </div>
      {loading && <Spinner />}
      {error && <Alert tone="error">{error}</Alert>}
      <div className="space-y-8">
        {Object.entries(groups).map(([group, items]) => (
          <section key={group}>
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{group}</h2>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {items.map((c) => (
                <Link key={c.slug} to={`/app/calculatrices/${c.slug}`} className="group">
                  <Card className="flex h-full gap-4 p-4 transition group-hover:-translate-y-0.5 group-hover:border-brand-600/30 group-hover:shadow-lg">
                    <span className={cx('grid size-10 shrink-0 place-items-center rounded-xl', c.level === 'BT1' ? 'bg-brand-50 text-brand-600' : 'bg-money-50 text-money-600')}>
                      <Calculator className="size-5" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="font-semibold leading-snug text-navy-900">{c.title}</h3>
                        <ArrowRight className="mt-0.5 size-4 shrink-0 text-slate-300 transition group-hover:text-brand-600" />
                      </div>
                      <p className="mt-1 line-clamp-2 text-[13px] text-slate-500">{c.description}</p>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        ))}
        {data && Object.keys(groups).length === 0 && <p className="text-sm text-slate-500">Aucune calculatrice ne correspond à « {q} ».</p>}
      </div>
      {data && <div className="mt-8 flex gap-2 text-xs text-slate-500"><Badge>{data.length} calculatrices</Badge> Calculs en arithmétique décimale exacte (Decimal) côté serveur.</div>}
    </div>
  );
}
