import { ArrowRight, CheckCircle2 } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { Alert, Badge, Card, PageHeader, Progress, Spinner } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import type { Level } from '../types';

export default function ProgramPage() {
  const { level = 'BT1' } = useParams();
  const { data, loading, error } = useFetch<Level>(`/pedagogy/levels/${level}/`);

  if (loading) return <Spinner />;
  if (error || !data) return <Alert tone="error">{error ?? 'Niveau introuvable.'}</Alert>;

  const total = data.modules.reduce((s, m) => s + m.chapters_count, 0);
  const done = data.modules.reduce((s, m) => s + m.completed_count, 0);
  const accent = level === 'BT1' ? 'bg-brand-600' : 'bg-money-600';

  return (
    <div>
      <PageHeader eyebrow={`Programme ${data.code}`} title={data.title} subtitle={data.description} />
      <Card className="mb-6 flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
        <div className="flex-1">
          <div className="flex justify-between text-sm">
            <span className="font-medium text-slate-600">Progression globale</span>
            <span className="num font-semibold text-navy-900">{done}/{total} chapitres</span>
          </div>
          <Progress value={total ? (done / total) * 100 : 0} className="mt-2" />
        </div>
        <Alert tone="warning">Catalogue de travail : conformité au programme officiel malien à vérifier.</Alert>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.modules.map((m) => {
          const pct = m.chapters_count ? (m.completed_count / m.chapters_count) * 100 : 0;
          return (
            <Link key={m.id} to={`/app/modules/${m.id}`} className="group">
              <Card className="flex h-full flex-col p-5 transition group-hover:-translate-y-0.5 group-hover:shadow-lg">
                <div className="flex items-start justify-between">
                  <span className={`grid size-11 place-items-center rounded-xl text-sm font-bold text-white ${accent}`}>{m.code}</span>
                  {pct === 100 ? <Badge tone="green"><CheckCircle2 className="size-3" /> Terminé</Badge> : <Badge>{m.chapters_count} chapitres</Badge>}
                </div>
                <h3 className="mt-4 font-semibold leading-snug text-navy-900">{m.title}</h3>
                <p className="mt-1.5 line-clamp-3 flex-1 text-sm text-slate-500">{m.objectives}</p>
                <div className="mt-4 flex items-center gap-3">
                  <Progress value={pct} className="flex-1" />
                  <ArrowRight className="size-4 text-slate-300 transition group-hover:text-brand-600" />
                </div>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
