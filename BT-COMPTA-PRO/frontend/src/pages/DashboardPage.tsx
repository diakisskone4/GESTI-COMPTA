import { ArrowRight, BookOpen, Building2, Calculator, ClipboardCheck, GraduationCap, History, Trophy, Users } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Alert, Badge, Card, formatDate, formatNumber, PageHeader, Progress, Spinner, Stat } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import { useFetch } from '../hooks/useFetch';
import MobileHome, { type DashboardData as Dashboard } from '../modules/mobile/MobileHome';


const QUICK = [
  { to: '/app/calculatrices/tva', label: 'HT / TVA / TTC', level: 'BT1' },
  { to: '/app/calculatrices/facture', label: 'Facture complète', level: 'BT1' },
  { to: '/app/calculatrices/amortissement', label: 'Amortissements', level: 'BT1' },
  { to: '/app/calculatrices/cump', label: 'Fiche de stock CUMP', level: 'BT1' },
  { to: '/app/calculatrices/repartition', label: 'Tableau de répartition', level: 'BT2' },
  { to: '/app/calculatrices/seuil-rentabilite', label: 'Seuil de rentabilité', level: 'BT2' },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const { data, loading, error } = useFetch<Dashboard>('/dashboard/');
  const hour = new Date().getHours();
  const greet = hour < 18 ? 'Bonjour' : 'Bonsoir';

  if (loading) return <Spinner />;
  if (error || !data) return <Alert tone="error">{error}</Alert>;

  return (
    <>
    <div className="lg:hidden"><MobileHome data={data} user={user} /></div>
    <div className="hidden space-y-6 lg:block">
      <PageHeader
        eyebrow={new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })}
        title={`${greet}, ${user?.first_name || user?.username}`}
        subtitle="Reprenez votre formation, lancez un calcul ou poursuivez la saisie comptable."
      />

      <div className="grid gap-4 md:grid-cols-2">
        {(['BT1', 'BT2'] as const).map((code) => {
          const lv = data.levels[code];
          const pct = lv.chapters ? (lv.completed / lv.chapters) * 100 : 0;
          return (
            <Link key={code} to={`/app/formation/${code}`} className="group">
              <Card className="relative overflow-hidden p-6 transition group-hover:-translate-y-0.5 group-hover:shadow-lg">
                <div className={`absolute -right-10 -top-10 size-36 rounded-full opacity-10 ${code === 'BT1' ? 'bg-brand-600' : 'bg-money-600'}`} />
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className={`grid size-12 place-items-center rounded-2xl text-sm font-extrabold text-white ${code === 'BT1' ? 'bg-brand-600' : 'bg-money-600'}`}>{code}</span>
                    <div>
                      <div className="font-semibold text-navy-900">{code === 'BT1' ? 'Comptabilité générale' : 'Comptabilité approfondie et analytique'}</div>
                      <div className="text-xs text-slate-500">{lv.modules} modules · {lv.chapters} chapitres · {lv.calculators} calculatrices</div>
                    </div>
                  </div>
                  <ArrowRight className="size-5 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-brand-600" />
                </div>
                <div className="mt-6 flex items-center justify-between text-xs text-slate-500">
                  <span>Progression</span>
                  <span className="num font-semibold text-navy-900">{lv.completed}/{lv.chapters} chapitres · {Math.round(pct)} %</span>
                </div>
                <Progress value={pct} className="mt-2" />
              </Card>
            </Link>
          );
        })}
      </div>

      <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
        <Stat label="Examens passés" value={data.exams.count} hint={`${data.exams.available} disponibles`} icon={<ClipboardCheck className="size-5" />} />
        <Stat label="Moyenne" value={data.exams.average ? `${formatNumber(data.exams.average, 2)} / 20` : '—'} icon={<Trophy className="size-5" />} tone="green" />
        <Stat label="Entreprises suivies" value={data.accounting.companies} hint={`${data.accounting.entries} écritures`} icon={<Building2 className="size-5" />} tone="navy" />
        <Stat label="Brouillards à valider" value={data.accounting.drafts} icon={<History className="size-5" />} tone="amber" />
      </div>

      {(data.teaching || data.admin) && (
        <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
          {data.teaching && (
            <>
              <Stat label="Apprenants inscrits" value={data.teaching.students} icon={<GraduationCap className="size-5" />} />
              <Stat label="Copies corrigées" value={data.teaching.attempts} hint={data.teaching.average ? `Moyenne ${formatNumber(data.teaching.average, 2)} / 20` : undefined} icon={<ClipboardCheck className="size-5" />} tone="green" />
            </>
          )}
          {data.admin && (
            <>
              <Stat label="Utilisateurs" value={data.admin.users} icon={<Users className="size-5" />} tone="navy" />
              <Stat label="Écritures (plateforme)" value={formatNumber(data.admin.entries)} hint={`${data.admin.companies} entreprises`} icon={<BookOpen className="size-5" />} tone="amber" />
            </>
          )}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="p-6 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-navy-900">Calculatrices fréquentes</h2>
            <Link to="/app/calculatrices" className="text-sm font-medium text-brand-600 hover:underline">Toutes</Link>
          </div>
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            {QUICK.map((q) => (
              <Link key={q.to} to={q.to} className="flex items-center gap-3 rounded-xl border border-slate-200 px-3.5 py-3 transition hover:border-brand-600/40 hover:bg-brand-50/50">
                <span className="grid size-9 place-items-center rounded-lg bg-paper text-brand-600"><Calculator className="size-4" /></span>
                <span className="flex-1 text-sm font-medium text-slate-700">{q.label}</span>
                <Badge tone={q.level === 'BT1' ? 'blue' : 'green'}>{q.level}</Badge>
              </Link>
            ))}
          </div>
        </Card>
        <Card className="p-6">
          <h2 className="font-semibold text-navy-900">Derniers résultats</h2>
          {data.exams.recent.length === 0 ? (
            <p className="mt-4 text-sm text-slate-500">
              Aucun examen passé. <Link to="/app/examens" className="font-medium text-brand-600 hover:underline">Commencer un quiz</Link>
            </p>
          ) : (
            <ul className="mt-4 divide-y divide-slate-100">
              {data.exams.recent.map((r) => (
                <li key={r.id}>
                  <Link to={`/app/tentatives/${r.id}`} className="flex items-center justify-between gap-3 py-2.5">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium text-slate-700">{r.quiz}</div>
                      <div className="text-xs text-slate-400">{r.level} · {formatDate(r.date)}</div>
                    </div>
                    <Badge tone={Number(r.grade) >= 10 ? 'green' : 'red'}>{formatNumber(r.grade, 2)}/20</Badge>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
    </>
  );
}
