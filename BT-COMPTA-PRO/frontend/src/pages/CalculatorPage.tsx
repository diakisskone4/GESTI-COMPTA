import { ArrowLeft, FileDown, FileSpreadsheet, Play, Printer, RotateCcw, Save } from 'lucide-react';
import { useEffect, useState, type FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Alert, Badge, Button, Card, PageHeader, Spinner } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import DynamicForm, { initialValues, type FormValues } from '../modules/calculator/DynamicForm';
import ResultView from '../modules/calculator/ResultView';
import { api, download, errorMessage } from '../services/api';
import type { CalcOutput, CalculatorMeta } from '../types';

export default function CalculatorPage() {
  const { slug } = useParams();
  const { data: meta, loading, error } = useFetch<CalculatorMeta>(`/calculations/${slug}/`);
  const [values, setValues] = useState<FormValues>({});
  const [output, setOutput] = useState<CalcOutput | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<{ msg: string; field?: string | null } | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (meta) {
      setValues(initialValues(meta.fields));
      setOutput(null);
      setErr(null);
    }
  }, [meta]);

  async function run(e?: FormEvent, save = false) {
    e?.preventDefault();
    setBusy(save ? 'save' : 'run');
    setErr(null);
    setSaved(false);
    try {
      const { data } = await api.post(`/calculations/${slug}/run/`, { inputs: values, save });
      setOutput(data.output);
      if (save) setSaved(true);
      if (!save && window.innerWidth < 1280) setTimeout(() => document.getElementById('resultats')?.scrollIntoView({ behavior: 'smooth' }), 50);
    } catch (error) {
      const field = (error as { response?: { data?: { field?: string } } }).response?.data?.field;
      setErr({ msg: errorMessage(error), field });
    } finally {
      setBusy(null);
    }
  }

  async function exportFile(fmt: 'pdf' | 'xlsx') {
    setBusy(fmt);
    setErr(null);
    try {
      await download(`/calculations/${slug}/export/${fmt}/`, `${slug}.${fmt}`, 'post', { inputs: values });
    } catch (error) {
      setErr({ msg: errorMessage(error, 'Export impossible : vérifiez les données saisies.') });
    } finally {
      setBusy(null);
    }
  }

  if (loading) return <Spinner />;
  if (error || !meta) return <Alert tone="error">{error ?? 'Calculatrice introuvable.'}</Alert>;
  // Les calculatrices à tableaux de saisie (factures, stocks, journal…) utilisent toute la largeur.
  const wide = meta.fields.some((f) => f.type === 'table');

  return (
    <div>
      <Link to="/app/calculatrices" className="no-print mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-brand-600">
        <ArrowLeft className="size-4" /> Toutes les calculatrices
      </Link>
      <PageHeader
        eyebrow={<span className="flex items-center gap-2"><Badge tone={meta.level === 'BT1' ? 'blue' : 'green'}>{meta.level}</Badge> {meta.category}</span>}
        title={meta.title}
        subtitle={meta.description}
        actions={
          <div className="no-print flex flex-wrap gap-2">
            <Button variant="secondary" size="sm" onClick={() => exportFile('pdf')} loading={busy === 'pdf'} icon={<FileDown className="size-4" />}>PDF</Button>
            <Button variant="secondary" size="sm" onClick={() => exportFile('xlsx')} loading={busy === 'xlsx'} icon={<FileSpreadsheet className="size-4" />}>Excel</Button>
            <Button variant="secondary" size="sm" onClick={() => window.print()} disabled={!output} icon={<Printer className="size-4" />}>Imprimer</Button>
          </div>
        }
      />

      <div className={`grid items-start gap-6 ${wide ? '' : 'xl:grid-cols-[minmax(380px,460px)_1fr]'}`}>
        <Card className={`no-print p-5 ${wide ? '' : 'xl:sticky xl:top-24'}`}>
          <form onSubmit={run} className="space-y-5">
            <DynamicForm fields={meta.fields} values={values} onChange={setValues} errorField={err?.field} />
            {err && <Alert tone="error">{err.msg}</Alert>}
            {saved && <Alert tone="success">Calcul enregistré dans votre historique.</Alert>}
            <div className="flex flex-wrap gap-2 border-t border-slate-100 pt-4">
              <Button type="submit" loading={busy === 'run'} icon={<Play className="size-4" />} className="flex-1">Calculer</Button>
              <Button type="button" variant="secondary" onClick={() => run(undefined, true)} loading={busy === 'save'} icon={<Save className="size-4" />}>Enregistrer</Button>
              <Button type="button" variant="ghost" onClick={() => { setValues(initialValues(meta.fields)); setOutput(null); }} icon={<RotateCcw className="size-4" />}>Exemple</Button>
            </div>
            {meta.reference && <p className="text-xs text-slate-500">Référence : {meta.reference}</p>}
          </form>
        </Card>

        <div id="resultats" className="min-w-0">
          {output ? (
            <ResultView output={output} />
          ) : (
            <Card className="ledger-rule grid min-h-72 place-items-center p-10 text-center">
              <div>
                <div className="mx-auto grid size-14 place-items-center rounded-2xl bg-navy-900 text-white"><Play className="size-6" /></div>
                <p className="mt-4 font-semibold text-navy-900">Les champs sont pré-remplis avec un exemple.</p>
                <p className="mt-1 text-sm text-slate-500">Modifiez les données puis cliquez sur « Calculer » pour obtenir formules, étapes et écritures.</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
