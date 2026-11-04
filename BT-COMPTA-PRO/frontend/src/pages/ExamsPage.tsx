import { ArrowRight, Clock, FileQuestion, Trophy } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Badge, Card, cx, formatNumber, PageHeader, Spinner } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import type { Quiz } from '../types';

export default function ExamsPage() {
  const [level, setLevel] = useState<'BT1' | 'BT2'>('BT1');
  const { data, loading, error } = useFetch<Quiz[]>(`/exams/quizzes/?level=${level}`);
  const mocks = data?.filter((q) => q.kind === 'mock') ?? [];
  const others = data?.filter((q) => q.kind !== 'mock') ?? [];

  return (
    <div>
      <PageHeader eyebrow="Gestion des examens" title="Quiz et examens blancs" subtitle="Questions à choix multiples, calculs et saisies d'écritures corrigés automatiquement, avec note sur 20 et correction détaillée." />
      <div className="mb-6 inline-flex gap-1 rounded-xl bg-white p-1 ring-1 ring-slate-200">
        {(['BT1', 'BT2'] as const).map((l) => (
          <button key={l} onClick={() => setLevel(l)} className={cx('rounded-lg px-5 py-1.5 text-sm font-semibold', level === l ? 'bg-navy-900 text-white' : 'text-slate-600 hover:bg-slate-50')}>{l}</button>
        ))}
      </div>
      {loading && <Spinner />}
      {error && <Alert tone="error">{error}</Alert>}

      {mocks.length > 0 && (
        <div className="mb-8 grid gap-4 lg:grid-cols-2">
          {mocks.map((q) => (
            <Link key={q.id} to={`/app/examens/${q.id}/passer`} className="group relative overflow-hidden rounded-3xl bg-navy-900 p-6 text-white shadow-xl shadow-navy-900/20">
              <div className="pointer-events-none absolute -right-16 -top-16 size-56 rounded-full bg-brand-600/40 blur-3xl" />
              <div className="relative">
                <Badge tone="green" className="bg-money-600 text-white">Examen blanc</Badge>
                <h3 className="mt-4 text-xl font-bold">{q.title}</h3>
                <p className="mt-2 text-sm text-white/65">{q.description}</p>
                <div className="mt-6 flex flex-wrap items-center gap-4 text-sm text-white/80">
                  <span className="inline-flex items-center gap-1.5"><Clock className="size-4" /> {q.duration_minutes} min</span>
                  <span className="inline-flex items-center gap-1.5"><FileQuestion className="size-4" /> {q.questions_count} questions</span>
                  {q.best_grade && <span className="inline-flex items-center gap-1.5"><Trophy className="size-4" /> Meilleure note {formatNumber(q.best_grade, 2)}/20</span>}
                  <span className="ml-auto inline-flex items-center gap-1 font-semibold text-white">Commencer <ArrowRight className="size-4 transition group-hover:translate-x-0.5" /></span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {others.map((q) => (
          <Link key={q.id} to={`/app/examens/${q.id}/passer`} className="group">
            <Card className="flex h-full flex-col p-5 transition group-hover:-translate-y-0.5 group-hover:shadow-lg">
              <div className="flex items-center justify-between">
                <Badge tone="blue">{q.kind_label}</Badge>
                {q.best_grade !== null && <Badge tone={Number(q.best_grade) >= 10 ? 'green' : 'red'}>{formatNumber(q.best_grade, 2)}/20</Badge>}
              </div>
              <h3 className="mt-3 font-semibold text-navy-900">{q.title}</h3>
              <p className="mt-1 flex-1 text-sm text-slate-500">{q.module_title}</p>
              <div className="mt-4 flex items-center gap-4 border-t border-slate-100 pt-3 text-xs text-slate-500">
                <span className="inline-flex items-center gap-1"><Clock className="size-3.5" /> {q.duration_minutes} min</span>
                <span className="inline-flex items-center gap-1"><FileQuestion className="size-3.5" /> {q.questions_count} questions</span>
                {q.attempts_count > 0 && <span>{q.attempts_count} tentative(s)</span>}
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
