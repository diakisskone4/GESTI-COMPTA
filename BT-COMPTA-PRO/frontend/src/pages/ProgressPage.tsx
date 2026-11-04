import { AlertCircle, ClipboardCheck, Trophy } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Alert, Card, EmptyState, formatDate, formatNumber, PageHeader, Spinner, Stat } from '../components/ui';
import { useFetch } from '../hooks/useFetch';

interface ProgressData {
  by_level: Record<'BT1' | 'BT2', { avg: string | null; best: string | null; n: number }>;
  history: { date: string; grade: string; quiz: string; level: string }[];
  mistakes: { quiz: string; question: string; expected: string; explanation: string; date: string }[];
}

function GradeChart({ points }: { points: { grade: number; label: string }[] }) {
  if (points.length < 2) return <p className="text-sm text-slate-500">Passez au moins deux épreuves pour afficher la courbe de progression.</p>;
  const w = 640, h = 200, pad = 28;
  const x = (i: number) => pad + (i * (w - pad * 2)) / (points.length - 1);
  const y = (g: number) => h - pad - (g / 20) * (h - pad * 2);
  const path = points.map((p, i) => `${i ? 'L' : 'M'}${x(i)},${y(p.grade)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-52 w-full" role="img" aria-label="Évolution des notes sur 20">
      {[0, 10, 20].map((g) => (
        <g key={g}>
          <line x1={pad} x2={w - pad} y1={y(g)} y2={y(g)} stroke={g === 10 ? '#16A36A' : '#E2E8F0'} strokeDasharray={g === 10 ? '4 4' : undefined} />
          <text x={4} y={y(g) + 4} fontSize="11" fill="#94A3B8">{g}</text>
        </g>
      ))}
      <path d={`${path} L${x(points.length - 1)},${h - pad} L${x(0)},${h - pad} Z`} fill="rgba(22,131,216,0.08)" />
      <path d={path} fill="none" stroke="#1683D8" strokeWidth="2.5" strokeLinejoin="round" />
      {points.map((p, i) => (
        <circle key={i} cx={x(i)} cy={y(p.grade)} r="4" fill="#fff" stroke="#102B55" strokeWidth="2"><title>{`${p.label} : ${p.grade}/20`}</title></circle>
      ))}
    </svg>
  );
}

export default function ProgressPage() {
  const { data, loading, error } = useFetch<ProgressData>('/exams/progress/');
  if (loading) return <Spinner />;
  if (error || !data) return <Alert tone="error">{error}</Alert>;
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Suivi de l'apprenant" title="Ma progression" subtitle="Vos notes, leur évolution et les erreurs à retravailler." />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {(['BT1', 'BT2'] as const).flatMap((l) => [
          <Stat key={`${l}a`} label={`Moyenne ${l}`} value={data.by_level[l].avg ? `${formatNumber(data.by_level[l].avg, 2)}/20` : '—'} hint={`${data.by_level[l].n} épreuve(s)`} icon={<ClipboardCheck className="size-5" />} tone={l === 'BT1' ? 'blue' : 'green'} />,
          <Stat key={`${l}b`} label={`Meilleure note ${l}`} value={data.by_level[l].best ? `${formatNumber(data.by_level[l].best, 2)}/20` : '—'} icon={<Trophy className="size-5" />} tone="amber" />,
        ])}
      </div>
      <Card className="p-6">
        <h2 className="mb-4 font-semibold text-navy-900">Évolution des notes</h2>
        <GradeChart points={data.history.map((h) => ({ grade: Number(h.grade), label: h.quiz }))} />
      </Card>
      <Card className="p-6">
        <h2 className="font-semibold text-navy-900">Erreurs à retravailler</h2>
        {data.mistakes.length === 0 ? (
          <EmptyState icon={<Trophy className="size-6" />} title="Aucune erreur récente" text="Passez un quiz pour alimenter ce carnet d'erreurs." action={<Link className="text-sm font-semibold text-brand-600" to="/app/examens">Voir les quiz</Link>} />
        ) : (
          <ul className="mt-4 space-y-3">
            {data.mistakes.map((m, i) => (
              <li key={i} className="rounded-xl border border-slate-200 p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="mt-0.5 size-4 shrink-0 text-red-500" />
                  <div className="min-w-0">
                    <div className="text-xs text-slate-400">{m.quiz} · {formatDate(m.date)}</div>
                    <p className="mt-1 text-sm font-medium text-slate-800">{m.question}</p>
                    <p className="mt-1 text-sm text-slate-600">Attendu : <strong className="font-mono text-navy-900">{m.expected}</strong></p>
                    {m.explanation && <p className="mt-2 rounded-lg bg-paper px-3 py-2 text-sm text-slate-600">{m.explanation}</p>}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
