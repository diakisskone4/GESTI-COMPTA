import {
  ArrowRight, BookOpen, Building2, Calculator, ChevronRight, ClipboardCheck, FileText, GraduationCap, Inbox, ListTree, School, TrendingUp, Trophy,
} from 'lucide-react';
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { cx, formatDate, formatNumber } from '../../components/ui';
import type { User } from '../../types';
import { InstallCard } from './Install';

export interface DashboardData {
  levels: Record<'BT1' | 'BT2', { modules: number; chapters: number; completed: number; calculators: number }>;
  exams: { count: number; average: string | null; available: number; recent: { id: number; quiz: string; level: string; grade: string; date: string }[] };
  accounting: { companies: number; entries: number; drafts: number };
  calculations: { recent: { id: number; slug: string; title: string; date: string }[] };
  teaching?: { students: number; attempts: number; average: string | null; quizzes: number };
  admin?: { users: number; pending?: number; by_role: Record<string, number>; companies: number; entries: number };
}

/** Jauge circulaire : `value` de 0 à 1. */
function Ring({ value, label, tone = '#F2B65A', track = 'rgba(255,255,255,0.15)', size = 84 }: { value: number; label: string; tone?: string; track?: string; size?: number }) {
  const r = 42;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(1, value));
  return (
    <span className="relative grid shrink-0 place-items-center" style={{ width: size, height: size }}>
      <svg viewBox="0 0 100 100" className="absolute inset-0 -rotate-90" aria-hidden="true">
        <circle cx="50" cy="50" r={r} fill="none" stroke={track} strokeWidth="10" />
        {pct > 0 && <circle cx="50" cy="50" r={r} fill="none" stroke={tone} strokeWidth="10" strokeLinecap="round" strokeDasharray={`${pct * c} ${c}`} />}
      </svg>
      <span className="num text-[15px] font-extrabold">{label}</span>
    </span>
  );
}

function Widget({ to, className, children }: { to: string; className?: string; children: ReactNode }) {
  return <Link to={to} className={cx('card block p-4 transition active:scale-[0.98]', className)}>{children}</Link>;
}

function SectionHead({ title, to }: { title: string; to?: string }) {
  return (
    <div className="mb-2.5 mt-6 flex items-center justify-between">
      <h2 className="text-[15px] font-bold text-navy-900">{title}</h2>
      {to && <Link to={to} className="text-[13px] font-semibold text-brand-600">Tout voir</Link>}
    </div>
  );
}

const CALCS = [
  ['tva', 'HT / TVA / TTC', 'BT1'], ['facture', 'Facture complète', 'BT1'], ['amortissement', 'Amortissement', 'BT1'],
  ['cump', 'Fiche de stock', 'BT1'], ['repartition', 'Répartition', 'BT2'], ['seuil-rentabilite', 'Seuil de rentabilité', 'BT2'],
];

export default function MobileHome({ data, user }: { data: DashboardData; user: User | null }) {
  const level = user?.level || 'BT1';
  const lv = data.levels[level];
  const pct = lv.chapters ? lv.completed / lv.chapters : 0;
  const pro = user?.role === 'accountant';
  const staff = user?.role === 'teacher' || user?.role === 'admin';
  const average = data.exams.average ? Number(data.exams.average) : null;
  const hour = new Date().getHours();

  const apps: [string, string, ReactNode, string][] = [
    ['/app/formation/BT1', 'BT1', <BookOpen key="a" />, 'bg-brand-600'],
    ['/app/formation/BT2', 'BT2', <GraduationCap key="b" />, 'bg-money-600'],
    ['/app/calculatrices', 'Calculs', <Calculator key="c" />, 'bg-[#E8A33D]'],
    ['/app/comptabilite', 'Comptabilité', <Building2 key="d" />, 'bg-navy-800'],
    ['/app/examens', 'Examens', <ClipboardCheck key="e" />, 'bg-[#7C5CD6]'],
    ['/app/sujets', 'Sujets', <FileText key="f" />, 'bg-[#D9534F]'],
    ['/app/plan-comptable', 'Plan', <ListTree key="g" />, 'bg-[#2A9D9D]'],
    ['/app/progression', 'Progrès', <TrendingUp key="h" />, 'bg-[#4F7CAC]'],
  ];

  return (
    <div className="-mt-5">
      {/* Widget principal : prolonge la barre d'application */}
      <section className="-mx-4 rounded-b-[28px] bg-navy-900 px-4 pb-6 pt-4 text-white sm:-mx-6 sm:px-6">
        <p className="text-sm text-white/65">{hour < 18 ? 'Bonjour' : 'Bonsoir'},</p>
        <h1 className="truncate text-2xl font-extrabold tracking-tight">{user?.first_name || user?.username}</h1>
        {pro ? (
          <Link to="/app/comptabilite" className="mt-4 flex items-center gap-4 rounded-2xl bg-white/[0.08] p-4 active:bg-white/[0.12]">
            <span className="num grid size-16 shrink-0 place-items-center rounded-2xl bg-[#E8A33D] text-2xl font-extrabold text-navy-950">{data.accounting.companies}</span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-bold">Mes dossiers comptables</span>
              <span className="block text-xs text-white/65">{data.accounting.entries} écritures · {data.accounting.drafts} à valider</span>
            </span>
            <ChevronRight className="size-5 text-white/50" />
          </Link>
        ) : (
          <Link to={`/app/formation/${level}`} className="mt-4 flex items-center gap-4 rounded-2xl bg-white/[0.08] p-3.5 active:bg-white/[0.12]">
            <Ring value={pct} label={`${Math.round(pct * 100)} %`} />
            <span className="min-w-0 flex-1">
              <span className="block text-xs font-bold uppercase tracking-wider text-[#F2B65A]">Formation {level}</span>
              <span className="mt-0.5 block text-[15px] font-bold leading-snug">{lv.completed === 0 ? 'Commencer le programme' : 'Reprendre mes cours'}</span>
              <span className="block text-xs text-white/65">{lv.completed} / {lv.chapters} chapitres terminés</span>
            </span>
            <ArrowRight className="size-5 shrink-0 text-white/60" />
          </Link>
        )}
      </section>

      <InstallCard className="mt-4" />

      {/* Lanceur d'applications */}
      <section className="card mt-4 grid grid-cols-4 gap-y-4 p-4 md:grid-cols-8">
        {apps.map(([to, label, icon, color]) => (
          <Link key={to} to={to} className="flex flex-col items-center gap-1.5 active:scale-95">
            <span className={cx('grid size-12 place-items-center rounded-2xl text-white shadow-sm [&_svg]:size-[22px]', color)}>{icon}</span>
            <span className="max-w-full truncate text-[11.5px] font-medium text-slate-700">{label}</span>
          </Link>
        ))}
      </section>

      {/* Alertes de gestion */}
      {!!data.admin?.pending && (
        <Link to="/app/administration" className="mt-4 flex items-center gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 active:scale-[0.99]">
          <Inbox className="size-5 shrink-0 text-amber-700" />
          <span className="flex-1 text-sm font-semibold text-amber-800">{data.admin.pending} demande(s) de compte à traiter</span>
          <ChevronRight className="size-5 text-amber-700/60" />
        </Link>
      )}

      {/* Indicateurs */}
      <SectionHead title="Mes indicateurs" />
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Widget to="/app/progression" className="flex items-center gap-3">
          <span className="text-navy-900">
            <Ring value={(average ?? 0) / 20} label={average === null ? '—' : formatNumber(average, 1)} tone="#16A36A" track="#E8EDF3" size={60} />
          </span>
          <span className="min-w-0 text-xs font-medium leading-snug text-slate-500">Moyenne sur 20</span>
        </Widget>
        <Widget to="/app/examens">
          <div className="flex items-center justify-between text-slate-400"><Trophy className="size-4" /></div>
          <div className="num mt-1 text-2xl font-extrabold text-navy-900">{data.exams.count}</div>
          <div className="text-xs font-medium text-slate-500">épreuve(s) · {data.exams.available} disponibles</div>
        </Widget>
        {staff && data.teaching ? (
          <>
            <Widget to="/app/enseignant">
              <School className="size-4 text-slate-400" />
              <div className="num mt-1 text-2xl font-extrabold text-navy-900">{data.teaching.students}</div>
              <div className="text-xs font-medium text-slate-500">apprenants inscrits</div>
            </Widget>
            <Widget to="/app/enseignant">
              <ClipboardCheck className="size-4 text-slate-400" />
              <div className="num mt-1 text-2xl font-extrabold text-navy-900">{data.teaching.attempts}</div>
              <div className="text-xs font-medium text-slate-500">copies corrigées</div>
            </Widget>
          </>
        ) : (
          <>
            <Widget to="/app/comptabilite">
              <Building2 className="size-4 text-slate-400" />
              <div className="num mt-1 text-2xl font-extrabold text-navy-900">{data.accounting.companies}</div>
              <div className="text-xs font-medium text-slate-500">dossier(s) comptable(s)</div>
            </Widget>
            <Widget to="/app/comptabilite">
              <FileText className="size-4 text-slate-400" />
              <div className="num mt-1 text-2xl font-extrabold text-navy-900">{data.accounting.drafts}</div>
              <div className="text-xs font-medium text-slate-500">brouillard(s) à valider</div>
            </Widget>
          </>
        )}
      </section>

      {/* Calculatrices : défilement horizontal */}
      <SectionHead title="Calculatrices fréquentes" to="/app/calculatrices" />
      <section className="-mx-4 flex snap-x snap-mandatory gap-3 overflow-x-auto scroll-px-4 px-4 pb-1 sm:scroll-px-6 [scrollbar-width:none] sm:-mx-6 sm:px-6">
        {CALCS.map(([slug, label, lvl]) => (
          <Link key={slug} to={`/app/calculatrices/${slug}`} className="card flex w-36 shrink-0 snap-start flex-col justify-between gap-5 p-3.5 active:scale-[0.98]">
            <span className={cx('grid size-9 place-items-center rounded-xl', lvl === 'BT1' ? 'bg-brand-50 text-brand-600' : 'bg-money-50 text-money-600')}><Calculator className="size-[18px]" /></span>
            <span className="text-[13px] font-semibold leading-tight text-navy-900">{label}</span>
          </Link>
        ))}
      </section>

      {/* Résultats */}
      {data.exams.recent.length > 0 && (
        <>
          <SectionHead title="Derniers résultats" to="/app/progression" />
          <ul className="card divide-y divide-slate-100">
            {data.exams.recent.slice(0, 3).map((r) => (
              <li key={r.id}>
                <Link to={`/app/tentatives/${r.id}`} className="flex items-center gap-3 p-3.5 active:bg-slate-50">
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-semibold text-navy-900">{r.quiz}</span>
                    <span className="block text-xs text-slate-500">{r.level} · {formatDate(r.date)}</span>
                  </span>
                  <span className={cx('num rounded-lg px-2 py-1 text-sm font-bold', Number(r.grade) >= 10 ? 'bg-money-50 text-money-700' : 'bg-red-50 text-red-600')}>{formatNumber(r.grade, 1)}/20</span>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
