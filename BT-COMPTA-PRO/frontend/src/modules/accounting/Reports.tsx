import { FileDown, FileSpreadsheet } from 'lucide-react';
import { useState } from 'react';
import { Alert, Badge, Button, Card, cx, EmptyState, formatDate, formatNumber, Spinner } from '../../components/ui';
import { useFetch } from '../../hooks/useFetch';
import { download, errorMessage } from '../../services/api';

const n = (v: string | number | null | undefined) => (v === null || v === undefined || Number(v) === 0 ? '' : formatNumber(v, 2));

export function ExportButtons({ path, name }: { path: string; name: string }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState('');
  async function go(fmt: 'pdf' | 'xlsx') {
    setBusy(fmt);
    setErr('');
    try {
      await download(`${path}${path.includes('?') ? '&' : '?'}export=${fmt}`, `${name}.${fmt}`);
    } catch (e) {
      setErr(errorMessage(e, 'Export impossible.'));
    } finally {
      setBusy(null);
    }
  }
  return (
    <div className="no-print flex flex-wrap items-center gap-2">
      <Button size="sm" variant="secondary" onClick={() => go('pdf')} loading={busy === 'pdf'} icon={<FileDown className="size-4" />}>PDF</Button>
      <Button size="sm" variant="secondary" onClick={() => go('xlsx')} loading={busy === 'xlsx'} icon={<FileSpreadsheet className="size-4" />}>Excel</Button>
      {err && <span className="text-xs text-red-600">{err}</span>}
    </div>
  );
}

interface TBRow { code: string; label: string; debit: string; credit: string; balance_debit: string; balance_credit: string }

export function TrialBalance({ base, fy }: { base: string; fy: number }) {
  const { data, loading, error } = useFetch<{ rows: TBRow[]; totals: Record<string, string> & { balanced: boolean } }>(`${base}/trial-balance/?fiscal_year=${fy}`);
  if (loading) return <Spinner />;
  if (error || !data) return <Alert tone="error">{error}</Alert>;
  return (
    <Card className="overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-3.5">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-navy-900">Balance générale</h3>
          <Badge tone={data.totals.balanced ? 'green' : 'red'}>{data.totals.balanced ? 'Équilibrée' : 'Déséquilibrée'}</Badge>
        </div>
        <ExportButtons path={`${base}/trial-balance/?fiscal_year=${fy}`} name="balance" />
      </div>
      {data.rows.length === 0 ? <EmptyState icon={<FileDown />} title="Aucune écriture validée" /> : (
        <div className="overflow-x-auto">
          <table className="table-base">
            <thead><tr><th>Compte</th><th>Intitulé</th><th className="text-right">Débit</th><th className="text-right">Crédit</th><th className="text-right">Solde débiteur</th><th className="text-right">Solde créditeur</th></tr></thead>
            <tbody>
              {data.rows.map((r) => (
                <tr key={r.code} className="hover:bg-slate-50/60">
                  <td className="font-mono font-semibold text-navy-900">{r.code}</td><td>{r.label}</td>
                  <td className="num text-right">{n(r.debit)}</td><td className="num text-right">{n(r.credit)}</td>
                  <td className="num text-right">{n(r.balance_debit)}</td><td className="num text-right">{n(r.balance_credit)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot><tr><td colSpan={2}>Totaux</td><td className="num text-right">{n(data.totals.debit)}</td><td className="num text-right">{n(data.totals.credit)}</td><td className="num text-right">{n(data.totals.balance_debit)}</td><td className="num text-right">{n(data.totals.balance_credit)}</td></tr></tfoot>
          </table>
        </div>
      )}
    </Card>
  );
}

interface LedgerAccount { code: string; label: string; debit: string; credit: string; balance: string; lines: { date: string; journal: string; number: number | null; reference: string; label: string; debit: string; credit: string; balance: string }[] }

export function Ledger({ base, fy }: { base: string; fy: number }) {
  const [filter, setFilter] = useState('');
  const [applied, setApplied] = useState('');
  const { data, loading, error } = useFetch<LedgerAccount[]>(`${base}/ledger/?fiscal_year=${fy}${applied ? `&account=${applied}` : ''}`);
  const solde = (v: string) => (Number(v) === 0 ? '0' : `${formatNumber(Math.abs(Number(v)), 2)} ${Number(v) > 0 ? 'D' : 'C'}`);
  return (
    <div className="space-y-4">
      <Card className="flex flex-wrap items-center justify-between gap-3 p-4">
        <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); setApplied(filter.trim()); }}>
          <input className="field-sm w-48 font-mono" placeholder="Filtrer : 401, 6…" value={filter} onChange={(e) => setFilter(e.target.value)} />
          <Button size="sm" type="submit">Filtrer</Button>
        </form>
        <ExportButtons path={`${base}/ledger/?fiscal_year=${fy}${applied ? `&account=${applied}` : ''}`} name="grand-livre" />
      </Card>
      {loading && <Spinner />}
      {error && <Alert tone="error">{error}</Alert>}
      {data?.length === 0 && <Card><EmptyState icon={<FileDown />} title="Aucun mouvement" text="Validez des écritures pour alimenter le grand livre." /></Card>}
      {data?.map((acc) => (
        <Card key={acc.code} className="overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/50 px-5 py-3">
            <div><span className="font-mono font-bold text-navy-900">{acc.code}</span> <span className="text-sm text-slate-600">{acc.label}</span></div>
            <Badge tone={Number(acc.balance) >= 0 ? 'blue' : 'green'}>Solde {solde(acc.balance)}</Badge>
          </div>
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead><tr><th>Date</th><th>Jnl</th><th>N°</th><th>Libellé</th><th className="text-right">Débit</th><th className="text-right">Crédit</th><th className="text-right">Solde</th></tr></thead>
              <tbody>
                {acc.lines.map((l, i) => (
                  <tr key={i}><td className="whitespace-nowrap">{formatDate(l.date)}</td><td>{l.journal}</td><td className="num">{l.number}</td><td>{l.label}</td>
                    <td className="num text-right">{n(l.debit)}</td><td className="num text-right">{n(l.credit)}</td><td className="num whitespace-nowrap text-right">{solde(l.balance)}</td></tr>
                ))}
              </tbody>
              <tfoot><tr><td colSpan={4}>Totaux</td><td className="num text-right">{n(acc.debit)}</td><td className="num text-right">{n(acc.credit)}</td><td className="num text-right">{solde(acc.balance)}</td></tr></tfoot>
            </table>
          </div>
        </Card>
      ))}
    </div>
  );
}

interface Income { charges: { code: string; label: string; amount: string }[]; produits: { code: string; label: string; amount: string }[]; total_charges: string; total_produits: string; result: string }
interface BalanceSheet { actif: { label: string; amount: string }[]; passif: { label: string; amount: string }[]; result: string; total_actif: string; total_passif: string; balanced: boolean; note: string }

export function Statements({ base, fy }: { base: string; fy: number }) {
  const income = useFetch<Income>(`${base}/income-statement/?fiscal_year=${fy}`);
  const bs = useFetch<BalanceSheet>(`${base}/balance-sheet/?fiscal_year=${fy}`);
  if (income.loading || bs.loading) return <Spinner />;
  if (!income.data || !bs.data) return <Alert tone="error">{income.error || bs.error}</Alert>;
  const res = Number(income.data.result);
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="p-5"><div className="text-xs text-slate-500">Total produits</div><div className="num mt-1 text-xl font-bold text-navy-900">{formatNumber(income.data.total_produits, 2)}</div></Card>
        <Card className="p-5"><div className="text-xs text-slate-500">Total charges</div><div className="num mt-1 text-xl font-bold text-navy-900">{formatNumber(income.data.total_charges, 2)}</div></Card>
        <div className={cx('rounded-2xl p-5 text-white shadow-lg', res >= 0 ? 'bg-money-600' : 'bg-red-600')}>
          <div className="text-xs text-white/75">{res >= 0 ? 'Bénéfice de l\'exercice' : 'Perte de l\'exercice'}</div>
          <div className="num mt-1 text-xl font-bold">{formatNumber(Math.abs(res), 2)} FCFA</div>
        </div>
      </div>

      <Card className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-3.5">
          <div className="flex items-center gap-3"><h3 className="font-semibold text-navy-900">Bilan (grandes masses)</h3><Badge tone={bs.data.balanced ? 'green' : 'red'}>{bs.data.balanced ? 'Équilibré' : 'Déséquilibré'}</Badge></div>
          <ExportButtons path={`${base}/balance-sheet/?fiscal_year=${fy}`} name="bilan" />
        </div>
        <div className="grid divide-y divide-slate-100 md:grid-cols-2 md:divide-x md:divide-y-0">
          {([['Actif', bs.data.actif, bs.data.total_actif], ['Passif', bs.data.passif, bs.data.total_passif]] as const).map(([title, rows, total]) => (
            <div key={title}>
              <div className="bg-slate-50 px-5 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</div>
              {rows.map((r) => <div key={r.label} className="flex justify-between px-5 py-2.5 text-sm"><span className="text-slate-600">{r.label}</span><span className="num font-medium text-navy-900">{formatNumber(r.amount, 2)}</span></div>)}
              <div className="flex justify-between border-t-2 border-slate-200 px-5 py-3 text-sm font-bold text-navy-900"><span>Total {title.toLowerCase()}</span><span className="num">{formatNumber(total, 2)}</span></div>
            </div>
          ))}
        </div>
        <p className="border-t border-slate-100 px-5 py-3 text-xs text-slate-500">{bs.data.note}</p>
      </Card>

      <Card className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-3.5">
          <h3 className="font-semibold text-navy-900">Compte de résultat</h3>
          <ExportButtons path={`${base}/income-statement/?fiscal_year=${fy}`} name="compte-de-resultat" />
        </div>
        <div className="grid divide-y divide-slate-100 md:grid-cols-2 md:divide-x md:divide-y-0">
          {([['Charges', income.data.charges, income.data.total_charges], ['Produits', income.data.produits, income.data.total_produits]] as const).map(([title, rows, total]) => (
            <div key={title}>
              <div className="bg-slate-50 px-5 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</div>
              {rows.length === 0 && <div className="px-5 py-3 text-sm text-slate-400">—</div>}
              {rows.map((r) => <div key={r.code} className="flex justify-between gap-3 px-5 py-2.5 text-sm"><span className="text-slate-600"><span className="font-mono font-semibold text-navy-900">{r.code}</span> {r.label}</span><span className="num font-medium text-navy-900">{formatNumber(r.amount, 2)}</span></div>)}
              <div className="flex justify-between border-t-2 border-slate-200 px-5 py-3 text-sm font-bold text-navy-900"><span>Total</span><span className="num">{formatNumber(total, 2)}</span></div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
