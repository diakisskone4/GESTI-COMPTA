import { ArrowLeft, CheckCircle2, RotateCcw, XCircle } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { Alert, Badge, ButtonLink, Card, cx, formatDate, formatNumber, Spinner } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import type { Attempt } from '../types';

function renderAnswer(a: unknown): string {
  if (a === null || a === undefined || a === '') return 'Sans réponse';
  if (Array.isArray(a)) {
    if (a.length && typeof a[0] === 'object') {
      return (a as { account: string; debit?: string; credit?: string }[])
        .filter((l) => l.account)
        .map((l) => `${l.account} ${Number(l.debit) ? `D ${l.debit}` : `C ${l.credit ?? ''}`}`)
        .join(' ; ') || 'Sans réponse';
    }
    return a.length ? 'Choix effectué' : 'Sans réponse';
  }
  return String(a);
}

export default function AttemptPage() {
  const { id } = useParams();
  const { data, loading, error } = useFetch<Attempt>(`/exams/attempts/${id}/`);
  if (loading) return <Spinner />;
  if (error || !data) return <Alert tone="error">{error ?? 'Résultat introuvable.'}</Alert>;
  const grade = Number(data.grade ?? 0);
  const good = data.details.filter((d) => d.correct).length;

  return (
    <div className="mx-auto max-w-3xl">
      <Link to="/app/examens" className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-brand-600"><ArrowLeft className="size-4" /> Examens</Link>
      <div className={cx('relative overflow-hidden rounded-3xl p-6 text-white shadow-xl sm:p-8', grade >= 10 ? 'bg-money-600 shadow-money-600/25' : 'bg-navy-900 shadow-navy-900/25')}>
        <div className="pointer-events-none absolute -right-12 -top-12 size-48 rounded-full bg-white/10" />
        <div className="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="text-sm text-white/70">{data.quiz_level} · {formatDate(data.finished_at)}</div>
            <h1 className="mt-1 text-2xl font-bold">{data.quiz_title}</h1>
            <p className="mt-2 text-sm text-white/80">{good} bonne(s) réponse(s) sur {data.details.length} · {formatNumber(data.score, 2)} / {formatNumber(data.max_score, 2)} points{data.timed_out ? ' · remis après le temps imparti' : ''}</p>
          </div>
          <div className="text-right">
            <div className="num text-5xl font-extrabold leading-none">{formatNumber(grade, 2)}</div>
            <div className="text-sm text-white/70">sur 20</div>
          </div>
        </div>
      </div>

      <h2 className="mb-3 mt-8 font-semibold text-navy-900">Correction détaillée</h2>
      <div className="space-y-3">
        {data.details.map((d, i) => (
          <Card key={d.question} className={cx('border-l-4 p-5', d.correct ? 'border-l-money-600' : 'border-l-red-500')}>
            <div className="flex items-start gap-3">
              {d.correct ? <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-money-600" /> : <XCircle className="mt-0.5 size-5 shrink-0 text-red-500" />}
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-slate-400">Question {i + 1}</span>
                  <Badge tone={d.correct ? 'green' : 'red'}>{formatNumber(d.points, 2)} / {formatNumber(d.max_points, 2)}</Badge>
                </div>
                <p className="mt-1 font-medium text-slate-800">{d.text}</p>
                {d.kind !== 'mcq' && <p className="mt-2 text-sm text-slate-500">Votre réponse : <span className="font-mono">{renderAnswer(d.answer)}</span></p>}
                {!d.correct && <p className="mt-1 text-sm text-slate-600">Réponse attendue : <strong className="font-mono text-navy-900">{d.expected}</strong></p>}
                {d.explanation && <div className="mt-3 rounded-xl bg-paper px-4 py-3 text-sm text-slate-700">{d.explanation}</div>}
              </div>
            </div>
          </Card>
        ))}
      </div>
      <div className="mt-6 flex justify-end">
        <ButtonLink to={`/app/examens/${data.quiz}/passer`} icon={<RotateCcw className="size-4" />}>Repasser l'épreuve</ButtonLink>
      </div>
    </div>
  );
}
