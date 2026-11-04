import { ArrowRight, Building2, Plus } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Alert, Badge, Button, Card, EmptyState, Field, Modal, PageHeader, Spinner } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { api, errorMessage } from '../services/api';
import type { Company } from '../types';

export default function CompaniesPage() {
  const { data, loading, error } = useFetch<Company[]>('/accounting/companies/');
  const [open, setOpen] = useState(false);
  const year = new Date().getFullYear();
  const [form, setForm] = useState({ name: '', legal_form: 'SARL', tax_id: '', rccm: '', city: 'Bamako', address: '', is_training: true,
    fy_label: `Exercice ${year}`, start_date: `${year}-01-01`, end_date: `${year}-12-31` });
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function create(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr('');
    try {
      const { data: company } = await api.post<Company>('/accounting/companies/', form);
      await api.post('/accounting/fiscal-years/', { company: company.id, label: form.fy_label, start_date: form.start_date, end_date: form.end_date });
      navigate(`/app/comptabilite/${company.id}`);
    } catch (error) {
      setErr(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Comptabilité générale"
        title="Mes entreprises"
        subtitle="Chaque dossier dispose de ses exercices, de ses journaux (AC, VT, BQ, CA, OD) et du plan SYSCOHADA."
        actions={<Button onClick={() => setOpen(true)} icon={<Plus className="size-4" />}>Nouvelle entreprise</Button>}
      />
      {loading && <Spinner />}
      {error && <Alert tone="error">{error}</Alert>}
      {data && data.length === 0 && (
        <Card>
          <EmptyState icon={<Building2 className="size-6" />} title="Aucune entreprise" text="Créez un dossier (réel ou d'entraînement) pour commencer la saisie comptable."
            action={<Button onClick={() => setOpen(true)} icon={<Plus className="size-4" />}>Créer un dossier</Button>} />
        </Card>
      )}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data?.map((c) => (
          <Link key={c.id} to={`/app/comptabilite/${c.id}`} className="group">
            <Card className="h-full p-5 transition group-hover:-translate-y-0.5 group-hover:shadow-lg">
              <div className="flex items-start justify-between">
                <span className="grid size-11 place-items-center rounded-xl bg-navy-900 text-white"><Building2 className="size-5" /></span>
                {c.is_training ? <Badge tone="amber">Entraînement</Badge> : <Badge tone="green">Dossier réel</Badge>}
              </div>
              <h3 className="mt-4 font-semibold text-navy-900">{c.name}</h3>
              <p className="text-sm text-slate-500">{[c.legal_form, c.city].filter(Boolean).join(' · ')}</p>
              <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-500">
                <span>{c.fiscal_years_count} exercice(s) · {c.entries_count} écriture(s)</span>
                <ArrowRight className="size-4 text-slate-300 group-hover:text-brand-600" />
              </div>
            </Card>
          </Link>
        ))}
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title="Nouvelle entreprise">
        <form onSubmit={create} className="space-y-4">
          {err && <Alert tone="error">{err}</Alert>}
          <Field label="Raison sociale"><input className="field" value={form.name} onChange={set('name')} required /></Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Forme juridique">
              <select className="field" value={form.legal_form} onChange={set('legal_form')}>
                {['SARL', 'SA', 'SAS', 'SNC', 'GIE', 'Entreprise individuelle', 'Association'].map((f) => <option key={f}>{f}</option>)}
              </select>
            </Field>
            <Field label="Ville"><input className="field" value={form.city} onChange={set('city')} /></Field>
            <Field label="NIF"><input className="field" value={form.tax_id} onChange={set('tax_id')} /></Field>
            <Field label="RCCM"><input className="field" value={form.rccm} onChange={set('rccm')} /></Field>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={form.is_training} onChange={(e) => setForm((f) => ({ ...f, is_training: e.target.checked }))} className="size-4 accent-brand-600" />
            Dossier d'entraînement (exercices pédagogiques)
          </label>
          <div className="rounded-xl bg-paper p-4">
            <div className="mb-3 text-sm font-semibold text-navy-900">Premier exercice comptable</div>
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="Libellé"><input className="field" value={form.fy_label} onChange={set('fy_label')} required /></Field>
              <Field label="Ouverture"><input type="date" className="field" value={form.start_date} onChange={set('start_date')} required /></Field>
              <Field label="Clôture"><input type="date" className="field" value={form.end_date} onChange={set('end_date')} required /></Field>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>Annuler</Button>
            <Button type="submit" loading={busy}>Créer le dossier</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
