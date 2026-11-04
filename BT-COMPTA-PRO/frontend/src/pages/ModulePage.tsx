import { ArrowLeft, Calculator, CheckCircle2, Circle, ClipboardCheck, Sigma } from 'lucide-react';
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Alert, Badge, Button, Card, cx, PageHeader, Progress, Spinner } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { api, errorMessage } from '../services/api';
import type { Module, Quiz } from '../types';

export default function ModulePage() {
  const { id } = useParams();
  const { data, loading, error, setData } = useFetch<Module>(`/pedagogy/modules/${id}/`);
  const quizzes = useFetch<Quiz[]>(`/exams/quizzes/?module=${id}`);
  const [active, setActive] = useState(0);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  if (loading) return <Spinner />;
  if (error || !data?.chapters) return <Alert tone="error">{error ?? 'Module introuvable.'}</Alert>;

  const chapters = data.chapters;
  const chapter = chapters[active];
  const done = chapters.filter((c) => c.completed).length;

  async function toggle() {
    setBusy(true);
    setMsg('');
    try {
      if (chapter.completed) await api.delete(`/pedagogy/chapters/${chapter.id}/complete/`);
      else await api.post(`/pedagogy/chapters/${chapter.id}/complete/`);
      setData((m) => m && { ...m, chapters: m.chapters!.map((c) => (c.id === chapter.id ? { ...c, completed: !c.completed } : c)) });
      if (!chapter.completed && active < chapters.length - 1) setActive(active + 1);
    } catch (err) {
      setMsg(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <Link to={`/app/formation/${data.level_code}`} className="mb-4 hidden lg:inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-brand-600">
        <ArrowLeft className="size-4" /> Programme {data.level_code}
      </Link>
      <PageHeader eyebrow={`${data.level_code} · Module ${data.code}`} title={data.title} subtitle={data.objectives} />

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <Card className="h-fit p-3 lg:sticky lg:top-24">
          <div className="px-2 pb-3 pt-1">
            <div className="flex justify-between text-xs text-slate-500">
              <span>{done}/{chapters.length} chapitres</span>
              <span className="num font-semibold">{Math.round((done / chapters.length) * 100)} %</span>
            </div>
            <Progress value={(done / chapters.length) * 100} className="mt-2" />
          </div>
          <ol className="max-h-[60vh] space-y-0.5 overflow-y-auto">
            {chapters.map((c, i) => (
              <li key={c.id}>
                <button
                  onClick={() => setActive(i)}
                  className={cx('flex w-full items-start gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm transition', i === active ? 'bg-navy-900 text-white' : 'text-slate-600 hover:bg-slate-50')}
                >
                  {c.completed ? <CheckCircle2 className={cx('mt-0.5 size-4 shrink-0', i === active ? 'text-money-600' : 'text-money-600')} /> : <Circle className="mt-0.5 size-4 shrink-0 opacity-40" />}
                  <span>{c.title}</span>
                </button>
              </li>
            ))}
          </ol>
        </Card>

        <div className="space-y-4">
          <Card className="p-6 sm:p-8">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="blue">Chapitre {active + 1}</Badge>
              {chapter.completed && <Badge tone="green">Terminé</Badge>}
            </div>
            <h2 className="mt-3 text-xl font-bold text-navy-900">{chapter.title}</h2>
            <p className="mt-4 leading-relaxed text-slate-700">{chapter.summary}</p>

            {chapter.lessons.map((l) => (
              <div key={l.id} className="mt-6 space-y-4">
                {l.content && l.content !== chapter.summary && <p className="whitespace-pre-line leading-relaxed text-slate-700">{l.content}</p>}
                {l.definitions && <div className="rounded-xl bg-paper p-4 text-sm text-slate-700"><strong className="text-navy-900">Définitions. </strong>{l.definitions}</div>}
                {l.example && <div className="rounded-xl border border-brand-100 bg-brand-50/60 p-4 text-sm text-slate-700"><strong className="text-navy-900">Exemple. </strong>{l.example}</div>}
              </div>
            ))}

            {chapter.formulas && (
              <div className="mt-6 rounded-2xl border border-navy-900/10 bg-navy-900 p-5 text-white">
                <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-white/60"><Sigma className="size-4" /> Formule</div>
                <div className="font-mono text-[15px] leading-relaxed">{chapter.formulas}</div>
              </div>
            )}

            {msg && <div className="mt-4"><Alert tone="error">{msg}</Alert></div>}
            <div className="mt-8 flex flex-wrap gap-2 border-t border-slate-100 pt-5">
              <Button onClick={toggle} loading={busy} variant={chapter.completed ? 'secondary' : 'success'} icon={<CheckCircle2 className="size-4" />}>
                {chapter.completed ? 'Marquer comme non terminé' : 'J\'ai compris ce chapitre'}
              </Button>
              {chapter.calculator_slug && (
                <Link to={`/app/calculatrices/${chapter.calculator_slug}`} className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                  <Calculator className="size-4" /> S'exercer avec la calculatrice
                </Link>
              )}
            </div>
          </Card>

          {quizzes.data && quizzes.data.length > 0 && (
            <Card className="p-5">
              <h3 className="font-semibold text-navy-900">Évaluer ce module</h3>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {quizzes.data.map((q) => (
                  <Link key={q.id} to={`/app/examens/${q.id}/passer`} className="flex items-center gap-3 rounded-xl border border-slate-200 p-3 hover:border-brand-600/40 hover:bg-brand-50/50">
                    <ClipboardCheck className="size-5 text-brand-600" />
                    <span className="flex-1 text-sm font-medium text-slate-700">{q.title}</span>
                    <span className="text-xs text-slate-400">{q.duration_minutes} min</span>
                  </Link>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
