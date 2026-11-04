import { CheckCircle2, Plus, Trash2, XCircle } from 'lucide-react';
import { useMemo, useState, type FormEvent } from 'react';
import { Alert, Button, cx, Field, formatNumber } from '../../components/ui';
import { api, errorMessage } from '../../services/api';
import type { Account, FiscalYear, Journal, JournalEntry } from '../../types';

interface Line { code: string; label: string; debit: string; credit: string }

const toNumber = (v: string) => Number(v.replace(/\s/g, '').replace(',', '.')) || 0;
const empty = (): Line => ({ code: '', label: '', debit: '', credit: '' });

export default function EntryForm({ companyId, fiscalYear, journals, accounts, entry, onSaved }: {
  companyId: number;
  fiscalYear: FiscalYear;
  journals: Journal[];
  accounts: Account[];
  entry?: JournalEntry | null;
  onSaved: (validated: boolean) => void;
}) {
  const byCode = useMemo(() => new Map(accounts.map((a) => [a.code, a])), [accounts]);
  const byId = useMemo(() => new Map(accounts.map((a) => [a.id, a])), [accounts]);
  const [journal, setJournal] = useState<number>(entry?.journal ?? journals[0]?.id);
  const [date, setDate] = useState(entry?.date ?? (new Date().toISOString().slice(0, 10) > fiscalYear.end_date ? fiscalYear.end_date : new Date().toISOString().slice(0, 10) < fiscalYear.start_date ? fiscalYear.start_date : new Date().toISOString().slice(0, 10)));
  const [reference, setReference] = useState(entry?.reference ?? '');
  const [label, setLabel] = useState(entry?.label ?? '');
  const [lines, setLines] = useState<Line[]>(
    entry ? entry.lines.map((l) => ({ code: byId.get(l.account)?.code ?? l.account_code ?? '', label: l.label, debit: Number(l.debit) ? l.debit : '', credit: Number(l.credit) ? l.credit : '' })) : [empty(), empty()],
  );
  const [error, setError] = useState('');
  const [busy, setBusy] = useState<string | null>(null);

  const totalD = lines.reduce((s, l) => s + toNumber(l.debit), 0);
  const totalC = lines.reduce((s, l) => s + toNumber(l.credit), 0);
  const balanced = Math.abs(totalD - totalC) < 0.005 && totalD > 0;

  const update = (i: number, patch: Partial<Line>) => setLines((ls) => ls.map((l, j) => (j === i ? { ...l, ...patch } : l)));

  function autoBalance(i: number) {
    const diff = totalD - totalC;
    if (Math.abs(diff) < 0.005 || lines[i].debit || lines[i].credit) return;
    update(i, diff > 0 ? { credit: String(Math.round(diff * 100) / 100) } : { debit: String(Math.round(-diff * 100) / 100) });
  }

  async function save(e: FormEvent, validate: boolean) {
    e.preventDefault();
    setError('');
    const payloadLines = [];
    for (const [i, l] of lines.entries()) {
      if (!l.code && !l.debit && !l.credit) continue;
      const acc = byCode.get(l.code.trim());
      if (!acc) return setError(`Ligne ${i + 1} : compte « ${l.code} » inconnu. Choisissez un compte du plan.`);
      payloadLines.push({ account: acc.id, label: l.label, debit: toNumber(l.debit).toFixed(2), credit: toNumber(l.credit).toFixed(2) });
    }
    setBusy(validate ? 'validate' : 'save');
    try {
      const body = { company: companyId, fiscal_year: fiscalYear.id, journal, date, reference, label, lines: payloadLines };
      const { data } = entry ? await api.put<JournalEntry>(`/accounting/entries/${entry.id}/`, body) : await api.post<JournalEntry>('/accounting/entries/', body);
      if (validate) await api.post(`/accounting/entries/${data.id}/validate/`);
      onSaved(validate);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <form onSubmit={(e) => save(e, false)} className="space-y-4">
      <datalist id="accounts-list">
        {accounts.map((a) => <option key={a.id} value={a.code}>{a.label}</option>)}
      </datalist>
      <div className="grid gap-3 sm:grid-cols-4">
        <Field label="Journal">
          <select className="field" value={journal} onChange={(e) => setJournal(Number(e.target.value))}>
            {journals.map((j) => <option key={j.id} value={j.id}>{j.code} — {j.label}</option>)}
          </select>
        </Field>
        <Field label="Date"><input type="date" className="field" value={date} min={fiscalYear.start_date} max={fiscalYear.end_date} onChange={(e) => setDate(e.target.value)} required /></Field>
        <Field label="Pièce justificative"><input className="field" value={reference} onChange={(e) => setReference(e.target.value)} placeholder="FA-001" /></Field>
        <Field label="Libellé"><input className="field" value={label} onChange={(e) => setLabel(e.target.value)} required placeholder="Achat de marchandises" /></Field>
      </div>

      {/* Tableau sur grand écran, fiches empilées sur téléphone */}
      <div className="overflow-x-auto rounded-xl border-slate-200 sm:border">
        <table className="w-full text-sm max-sm:block sm:min-w-[640px]">
          <thead className="max-sm:hidden">
            <tr className="bg-slate-50 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              <th className="w-32 px-2 py-2">Compte</th><th className="px-2 py-2">Intitulé / libellé</th>
              <th className="w-36 px-2 py-2 text-right">Débit</th><th className="w-36 px-2 py-2 text-right">Crédit</th><th className="w-10" />
            </tr>
          </thead>
          <tbody className="max-sm:block max-sm:space-y-2.5">
            {lines.map((l, i) => {
              const acc = byCode.get(l.code.trim());
              return (
                <tr key={i} className="border-slate-100 align-top max-sm:relative max-sm:grid max-sm:grid-cols-2 max-sm:gap-2 max-sm:rounded-xl max-sm:border max-sm:border-slate-200 max-sm:bg-paper/60 max-sm:p-3 max-sm:pr-11 sm:border-t">
                  <td className="px-1.5 py-1.5 max-sm:col-span-2 max-sm:p-0">
                    <input list="accounts-list" className={cx('field-sm font-mono', l.code && !acc && 'border-red-400')} value={l.code} onChange={(e) => update(i, { code: e.target.value })} placeholder="601" />
                  </td>
                  <td className="px-1.5 py-1.5 max-sm:col-span-2 max-sm:p-0">
                    <input className="field-sm" value={l.label} onChange={(e) => update(i, { label: e.target.value })} placeholder={acc?.label ?? 'Libellé de la ligne'} />
                    {acc && <div className="mt-0.5 truncate px-1 text-[11px] text-slate-400">{acc.label}</div>}
                  </td>
                  <td className="px-1.5 py-1.5 max-sm:min-w-0 max-sm:p-0"><input inputMode="decimal" placeholder="Débit" className="field-sm num text-right" value={l.debit} onFocus={() => autoBalance(i)} onChange={(e) => update(i, { debit: e.target.value, credit: e.target.value ? '' : l.credit })} /></td>
                  <td className="px-1.5 py-1.5 max-sm:min-w-0 max-sm:p-0"><input inputMode="decimal" placeholder="Crédit" className="field-sm num text-right" value={l.credit} onChange={(e) => update(i, { credit: e.target.value, debit: e.target.value ? '' : l.debit })} /></td>
                  <td className="px-1 py-1.5 max-sm:absolute max-sm:right-1 max-sm:top-2 max-sm:p-0">
                    <button type="button" disabled={lines.length <= 2} onClick={() => setLines((ls) => ls.filter((_, j) => j !== i))} className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-30" aria-label="Supprimer">
                      <Trash2 className="size-4" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot className="max-sm:mt-2.5 max-sm:block">
            <tr className="border-t-2 border-slate-200 bg-slate-50 font-semibold max-sm:grid max-sm:grid-cols-2 max-sm:rounded-xl max-sm:border-t-0">
              <td className="px-2 py-2.5 max-sm:col-span-2 max-sm:pb-0" colSpan={2}>
                <span className={cx('inline-flex items-center gap-1.5 text-xs', balanced ? 'text-money-700' : 'text-red-600')}>
                  {balanced ? <CheckCircle2 className="size-4" /> : <XCircle className="size-4" />}
                  {balanced ? 'Écriture équilibrée' : `Écart : ${formatNumber(Math.abs(totalD - totalC), 2)}`}
                </span>
              </td>
              <td className="num px-3 py-2.5 text-right text-navy-900">{formatNumber(totalD, 2)}</td>
              <td className="num px-3 py-2.5 text-right text-navy-900">{formatNumber(totalC, 2)}</td>
              <td className="max-sm:hidden" />
            </tr>
          </tfoot>
        </table>
      </div>
      <Button type="button" variant="ghost" size="sm" onClick={() => setLines((ls) => [...ls, empty()])} icon={<Plus className="size-4" />}>Ajouter une ligne</Button>

      {error && <Alert tone="error">{error}</Alert>}
      <Alert tone="info">Une écriture validée reçoit un numéro définitif et devient non modifiable. Toute correction se fera par contre-passation.</Alert>
      <div className="flex flex-wrap justify-end gap-2">
        <Button type="submit" variant="secondary" loading={busy === 'save'}>Enregistrer en brouillard</Button>
        <Button type="button" variant="success" disabled={!balanced} loading={busy === 'validate'} onClick={(e) => save(e as unknown as FormEvent, true)} icon={<CheckCircle2 className="size-4" />}>
          Enregistrer et valider
        </Button>
      </div>
    </form>
  );
}
