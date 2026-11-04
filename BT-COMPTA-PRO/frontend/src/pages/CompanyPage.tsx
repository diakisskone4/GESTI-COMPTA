import { ArrowLeft, BookOpen, CheckCircle2, FileText, Lock, Pencil, PieChart, Plus, Rows3, Scale, Settings2, Trash2, Undo2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useConfirm } from '../components/ConfirmDialog';
import { Alert, Badge, Button, Card, EmptyState, Field, formatDate, formatNumber, Modal, PageHeader, Spinner, Tabs } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import EntryForm from '../modules/accounting/EntryForm';
import { ExportButtons, Ledger, Statements, TrialBalance } from '../modules/accounting/Reports';
import { api, errorMessage } from '../services/api';
import type { Account, Company, FiscalYear, Journal, JournalEntry } from '../types';

type Tab = 'entries' | 'ledger' | 'balance' | 'statements' | 'settings';

export default function CompanyPage() {
  const { id } = useParams();
  const company = useFetch<Company>(`/accounting/companies/${id}/`);
  const years = useFetch<FiscalYear[]>(`/accounting/fiscal-years/?company=${id}`);
  const journals = useFetch<Journal[]>(`/accounting/journals/?company=${id}`);
  const accounts = useFetch<Account[]>(`/accounting/accounts/?company=${id}`);
  const [fyId, setFyId] = useState<number | null>(null);
  const [tab, setTab] = useState<Tab>('entries');

  useEffect(() => {
    if (years.data?.length && !fyId) setFyId(years.data[0].id);
  }, [years.data, fyId]);

  if (company.loading || years.loading) return <Spinner />;
  if (company.error || !company.data) return <Alert tone="error">{company.error ?? 'Entreprise introuvable.'}</Alert>;

  const fy = years.data?.find((y) => y.id === fyId) ?? null;
  const base = `/accounting/companies/${id}`;

  return (
    <div>
      <Link to="/app/comptabilite" className="no-print mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-brand-600">
        <ArrowLeft className="size-4" /> Mes entreprises
      </Link>
      <PageHeader
        eyebrow={[company.data.legal_form, company.data.city, company.data.tax_id && `NIF ${company.data.tax_id}`].filter(Boolean).join(' · ')}
        title={company.data.name}
        actions={
          years.data && years.data.length > 0 ? (
            <select className="field w-auto" value={fyId ?? ''} onChange={(e) => setFyId(Number(e.target.value))}>
              {years.data.map((y) => <option key={y.id} value={y.id}>{y.label}{y.is_closed ? ' (clôturé)' : ''}</option>)}
            </select>
          ) : undefined
        }
      />
      <Tabs<Tab>
        value={tab}
        onChange={setTab}
        items={[
          { value: 'entries', label: 'Écritures', icon: <Rows3 className="size-4" /> },
          { value: 'ledger', label: 'Grand livre', icon: <BookOpen className="size-4" /> },
          { value: 'balance', label: 'Balance', icon: <Scale className="size-4" /> },
          { value: 'statements', label: 'États financiers', icon: <PieChart className="size-4" /> },
          { value: 'settings', label: 'Exercices & journaux', icon: <Settings2 className="size-4" /> },
        ]}
      />
      {!fy && tab !== 'settings' ? (
        <Card><EmptyState icon={<FileText className="size-6" />} title="Aucun exercice" text="Créez un exercice comptable pour commencer." action={<Button onClick={() => setTab('settings')}>Créer un exercice</Button>} /></Card>
      ) : (
        <>
          {tab === 'entries' && fy && journals.data && accounts.data && (
            <EntriesTab companyId={Number(id)} fy={fy} journals={journals.data} accounts={accounts.data} base={base} />
          )}
          {tab === 'ledger' && fy && <Ledger key={fy.id} base={base} fy={fy.id} />}
          {tab === 'balance' && fy && <TrialBalance key={fy.id} base={base} fy={fy.id} />}
          {tab === 'statements' && fy && <Statements key={fy.id} base={base} fy={fy.id} />}
          {tab === 'settings' && <SettingsTab companyId={Number(id)} years={years.data ?? []} journals={journals.data ?? []} onChange={() => { years.reload(); journals.reload(); }} />}
        </>
      )}
    </div>
  );
}

function EntriesTab({ companyId, fy, journals, accounts, base }: { companyId: number; fy: FiscalYear; journals: Journal[]; accounts: Account[]; base: string }) {
  const [status, setStatus] = useState('');
  const [journal, setJournal] = useState('');
  const url = `/accounting/entries/?company=${companyId}&fiscal_year=${fy.id}${status ? `&status=${status}` : ''}${journal ? `&journal=${journal}` : ''}`;
  const { data, loading, error, reload } = useFetch<JournalEntry[]>(url);
  const [editing, setEditing] = useState<JournalEntry | null | undefined>(undefined);
  const [reversing, setReversing] = useState<JournalEntry | null>(null);
  const [reason, setReason] = useState('');
  const [msg, setMsg] = useState<{ tone: 'success' | 'error'; text: string } | null>(null);
  const confirm = useConfirm();

  async function act(fn: () => Promise<unknown>, ok: string) {
    setMsg(null);
    try {
      await fn();
      setMsg({ tone: 'success', text: ok });
      reload();
    } catch (err) {
      setMsg({ tone: 'error', text: errorMessage(err) });
    }
  }

  return (
    <div className="space-y-4">
      <Card className="flex flex-wrap items-center gap-3 p-4">
        <select className="field-sm w-auto" value={journal} onChange={(e) => setJournal(e.target.value)}>
          <option value="">Tous les journaux</option>
          {journals.map((j) => <option key={j.id} value={j.id}>{j.code} — {j.label}</option>)}
        </select>
        <select className="field-sm w-auto" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Tous les statuts</option>
          <option value="draft">Brouillard</option>
          <option value="validated">Validées</option>
        </select>
        <div className="flex-1" />
        <ExportButtons path={`${base}/journal/?fiscal_year=${fy.id}`} name="journal" />
        {!fy.is_closed && <Button size="sm" onClick={() => setEditing(null)} icon={<Plus className="size-4" />}>Nouvelle écriture</Button>}
      </Card>
      {msg && <Alert tone={msg.tone} onClose={() => setMsg(null)}>{msg.text}</Alert>}
      {fy.is_closed && <Alert tone="warning">Exercice clôturé : consultation uniquement.</Alert>}
      {loading && <Spinner />}
      {error && <Alert tone="error">{error}</Alert>}
      {data?.length === 0 && <Card><EmptyState icon={<Rows3 className="size-6" />} title="Aucune écriture" text="Saisissez votre première écriture en partie double." /></Card>}

      <div className="space-y-3">
        {data?.map((e) => (
          <Card key={e.id} className="overflow-hidden">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-slate-100 px-4 py-3">
              <Badge tone="navy">{e.journal_code}</Badge>
              <span className="num text-sm font-semibold text-navy-900">{e.number ? `N° ${e.number}` : 'Brouillard'}</span>
              <span className="text-sm text-slate-500">{formatDate(e.date)}</span>
              {e.reference && <span className="font-mono text-xs text-slate-500">{e.reference}</span>}
              <span className="min-w-0 flex-1 truncate text-sm font-medium text-slate-700">{e.label}</span>
              {e.status === 'validated' ? <Badge tone="green"><Lock className="size-3" /> Validée</Badge> : <Badge tone="amber">Brouillard</Badge>}
              {e.reversed_by_id && <Badge tone="red">Contre-passée</Badge>}
              {e.reversal_of && <Badge tone="slate">Contre-passation</Badge>}
              <div className="flex gap-1">
                {e.status === 'draft' && !fy.is_closed && (
                  <>
                    <Button size="sm" variant="success" onClick={() => act(() => api.post(`/accounting/entries/${e.id}/validate/`), 'Écriture validée.')} icon={<CheckCircle2 className="size-3.5" />}>Valider</Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditing(e)} aria-label="Modifier"><Pencil className="size-3.5" /></Button>
                    <Button size="sm" variant="ghost" onClick={async () => (await confirm({ title: 'Supprimer ce brouillard ?', message: `« ${e.label} » sera définitivement supprimé.`, confirmLabel: 'Supprimer', danger: true })) && act(() => api.delete(`/accounting/entries/${e.id}/`), 'Brouillard supprimé.')} aria-label="Supprimer"><Trash2 className="size-3.5 text-red-500" /></Button>
                  </>
                )}
                {e.status === 'validated' && !e.reversed_by_id && !e.reversal_of && !fy.is_closed && (
                  <Button size="sm" variant="secondary" onClick={() => { setReversing(e); setReason(''); }} icon={<Undo2 className="size-3.5" />}>Contre-passer</Button>
                )}
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="table-base">
                <tbody>
                  {e.lines.map((l) => (
                    <tr key={l.id}>
                      <td className="w-24 font-mono font-semibold text-navy-900">{l.account_code}</td>
                      <td className={Number(l.credit) ? 'pl-10' : ''}>{l.label || l.account_label}</td>
                      <td className="num w-36 text-right">{Number(l.debit) ? formatNumber(l.debit, 2) : ''}</td>
                      <td className="num w-36 text-right">{Number(l.credit) ? formatNumber(l.credit, 2) : ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        ))}
      </div>

      <Modal open={editing !== undefined} onClose={() => setEditing(undefined)} title={editing ? 'Modifier le brouillard' : 'Nouvelle écriture'} wide>
        {editing !== undefined && (
          <EntryForm companyId={companyId} fiscalYear={fy} journals={journals} accounts={accounts} entry={editing}
            onSaved={(validated) => { setEditing(undefined); setMsg({ tone: 'success', text: validated ? 'Écriture enregistrée et validée.' : 'Brouillard enregistré.' }); reload(); }} />
        )}
      </Modal>
      <Modal open={!!reversing} onClose={() => setReversing(null)} title={`Contre-passer l'écriture n° ${reversing?.number}`}>
        <div className="space-y-4">
          <Alert tone="info">Une écriture inverse (débits et crédits permutés) sera créée et validée. L'opération est tracée dans le journal d'audit.</Alert>
          <Field label="Motif de la correction"><input className="field" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Erreur d'imputation…" /></Field>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setReversing(null)}>Annuler</Button>
            <Button onClick={() => { const r = reversing!; setReversing(null); act(() => api.post(`/accounting/entries/${r.id}/reverse/`, { reason }), 'Contre-passation enregistrée.'); }}>Confirmer</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

function SettingsTab({ companyId, years, journals, onChange }: { companyId: number; years: FiscalYear[]; journals: Journal[]; onChange: () => void }) {
  const next = years.length ? Number(years[0].end_date.slice(0, 4)) + 1 : new Date().getFullYear();
  const [fy, setFy] = useState({ label: `Exercice ${next}`, start_date: `${next}-01-01`, end_date: `${next}-12-31` });
  const [jr, setJr] = useState({ code: '', label: '', kind: 'misc' });
  const [msg, setMsg] = useState<{ tone: 'success' | 'error'; text: string } | null>(null);
  const confirm = useConfirm();

  async function act(fn: () => Promise<unknown>, ok: string) {
    setMsg(null);
    try {
      await fn();
      setMsg({ tone: 'success', text: ok });
      onChange();
    } catch (err) {
      setMsg({ tone: 'error', text: errorMessage(err) });
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {msg && <div className="lg:col-span-2"><Alert tone={msg.tone} onClose={() => setMsg(null)}>{msg.text}</Alert></div>}
      <Card className="p-5">
        <h3 className="font-semibold text-navy-900">Exercices comptables</h3>
        <ul className="mt-3 divide-y divide-slate-100">
          {years.map((y) => (
            <li key={y.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
              <div><div className="font-medium text-slate-700">{y.label}</div><div className="text-xs text-slate-500">{formatDate(y.start_date)} → {formatDate(y.end_date)}</div></div>
              {y.is_closed ? <Badge tone="slate"><Lock className="size-3" /> Clôturé</Badge> : (
                <Button size="sm" variant="secondary" onClick={async () => (await confirm({ title: `Clôturer « ${y.label} » ?`, message: 'Cette opération est définitive : plus aucune écriture ne pourra être passée sur cet exercice.', confirmLabel: 'Clôturer', danger: true })) && act(() => api.post(`/accounting/fiscal-years/${y.id}/close/`), 'Exercice clôturé.')}>Clôturer</Button>
              )}
            </li>
          ))}
        </ul>
        <form className="mt-4 grid gap-3 rounded-xl bg-paper p-4 sm:grid-cols-3" onSubmit={(e) => { e.preventDefault(); act(() => api.post('/accounting/fiscal-years/', { company: companyId, ...fy }), 'Exercice créé.'); }}>
          <Field label="Libellé"><input className="field" value={fy.label} onChange={(e) => setFy({ ...fy, label: e.target.value })} required /></Field>
          <Field label="Ouverture"><input type="date" className="field" value={fy.start_date} onChange={(e) => setFy({ ...fy, start_date: e.target.value })} required /></Field>
          <Field label="Clôture"><input type="date" className="field" value={fy.end_date} onChange={(e) => setFy({ ...fy, end_date: e.target.value })} required /></Field>
          <div className="sm:col-span-3"><Button type="submit" size="sm" icon={<Plus className="size-4" />}>Ajouter l'exercice</Button></div>
        </form>
      </Card>
      <Card className="p-5">
        <h3 className="font-semibold text-navy-900">Journaux</h3>
        <ul className="mt-3 divide-y divide-slate-100">
          {journals.map((j) => <li key={j.id} className="flex items-center gap-3 py-2.5 text-sm"><Badge tone="navy">{j.code}</Badge><span className="text-slate-700">{j.label}</span></li>)}
        </ul>
        <form className="mt-4 grid gap-3 rounded-xl bg-paper p-4 sm:grid-cols-[100px_1fr]" onSubmit={(e) => { e.preventDefault(); act(() => api.post('/accounting/journals/', { company: companyId, ...jr }), 'Journal créé.'); setJr({ code: '', label: '', kind: 'misc' }); }}>
          <Field label="Code"><input className="field uppercase" maxLength={10} value={jr.code} onChange={(e) => setJr({ ...jr, code: e.target.value.toUpperCase() })} required /></Field>
          <Field label="Libellé"><input className="field" value={jr.label} onChange={(e) => setJr({ ...jr, label: e.target.value })} required /></Field>
          <div className="sm:col-span-2"><Button type="submit" size="sm" icon={<Plus className="size-4" />}>Ajouter le journal</Button></div>
        </form>
      </Card>
    </div>
  );
}
