import {
  ArrowRight, BookOpen, Briefcase, Building2, Calculator, CheckCircle2, ChevronDown, ClipboardCheck, FileSpreadsheet,
  GraduationCap, Languages, Menu, School, ShieldCheck, Sigma, Smartphone, WifiOff, X,
} from 'lucide-react';
import { useEffect, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { Logo } from '../components/Logo';
import { cx } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import { InstallCard } from '../modules/mobile/Install';

const BT1 = ['Généralités sur la comptabilité', 'Bilan et compte de résultat', 'Comptes et partie double', 'Documents comptables',
  'Factures et opérations commerciales', 'Gestion des stocks', 'Rapprochement bancaire', 'Amortissements', 'Dépréciations et provisions',
  'Travaux d\'inventaire'];
const BT2 = ['Comptabilité générale approfondie', 'Comptabilité analytique', 'Calcul des coûts', 'Coûts complets',
  'Coûts partiels et seuil de rentabilité', 'Coûts préétablis et écarts', 'Budgets et gestion prévisionnelle', 'Analyse financière'];

const NAV = [['#mali', 'Notre approche'], ['#acteurs', 'Pour qui ?'], ['#programme', 'Programme'], ['#faq', 'Questions']];

/** Motif bogolan (tissu traditionnel malien) réutilisé comme élément décoratif. */
function Bogolan({ className, color = '#E8B866' }: { className?: string; color?: string }) {
  return (
    <svg className={className} aria-hidden="true">
      <defs>
        <pattern id={`bg-${color.slice(1)}`} width="96" height="48" patternUnits="userSpaceOnUse">
          <path d="M0 24 L12 12 L24 24 L36 12 L48 24" fill="none" stroke={color} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="66" cy="16" r="2.6" fill={color} /><circle cx="78" cy="16" r="2.6" fill={color} />
          <circle cx="66" cy="32" r="2.6" fill={color} /><circle cx="78" cy="32" r="2.6" fill={color} />
          <path d="M90 6 v36 M54 6 v36" stroke={color} strokeWidth="1.6" opacity="0.7" />
          <path d="M6 38 h36" stroke={color} strokeWidth="1.2" strokeDasharray="3 5" opacity="0.8" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#bg-${color.slice(1)})`} />
    </svg>
  );
}

function SectionTitle({ eyebrow, title, text, center }: { eyebrow: string; title: string; text?: string; center?: boolean }) {
  return (
    <div className={cx('max-w-2xl', center && 'mx-auto text-center')}>
      <div className={cx('flex items-center gap-2 text-xs font-bold uppercase tracking-[0.18em] text-[#B8741A]', center && 'justify-center')}>
        <span className="h-px w-6 bg-[#B8741A]" /> {eyebrow}
      </div>
      <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-navy-900 sm:text-[2.35rem] sm:leading-tight">{title}</h2>
      {text && <p className="mt-4 text-[15.5px] leading-relaxed text-slate-600">{text}</p>}
    </div>
  );
}

function Faq({ q, children }: { q: string; children: ReactNode }) {
  return (
    <details className="group rounded-2xl border border-slate-200 bg-white px-5 py-4 open:shadow-sm">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-semibold text-navy-900">
        {q}
        <ChevronDown className="size-5 shrink-0 text-slate-400 transition group-open:rotate-180" />
      </summary>
      <div className="mt-3 text-sm leading-relaxed text-slate-600">{children}</div>
    </details>
  );
}

function LedgerCard() {
  const rows = [['601', 'Achats de marchandises', '500 000', ''], ['4452', 'TVA récupérable sur achats', '90 000', ''], ['401', 'Fournisseurs', '', '590 000']];
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl shadow-navy-900/10">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-brand-600">Journal des achats</div>
          <div className="text-sm font-semibold text-navy-900">FA-0142 · Ets Diallo & Frères, Bamako</div>
        </div>
        <span className="inline-flex items-center gap-1 rounded-full bg-money-50 px-2.5 py-1 text-xs font-semibold text-money-700"><CheckCircle2 className="size-3.5" /> Équilibrée</span>
      </div>
      <table className="w-full text-sm">
        <thead><tr className="bg-slate-50 text-left text-[11px] uppercase tracking-wide text-slate-500"><th className="px-5 py-2 font-semibold">Compte</th><th className="hidden px-2 py-2 font-semibold sm:table-cell">Intitulé</th><th className="px-3 py-2 text-right font-semibold">Débit</th><th className="px-5 py-2 text-right font-semibold">Crédit</th></tr></thead>
        <tbody className="ledger-rule">
          {rows.map(([c, l, d, k]) => (
            <tr key={c} className="border-t border-slate-100">
              <td className="px-5 py-2.5 font-mono text-[13px] font-semibold text-navy-900">{c}</td>
              <td className="hidden px-2 py-2.5 text-slate-600 sm:table-cell">{l}</td>
              <td className="num px-3 py-2.5 text-right">{d}</td><td className="num px-5 py-2.5 text-right">{k}</td>
            </tr>
          ))}
        </tbody>
        <tfoot><tr className="border-t-2 border-slate-200 bg-slate-50 font-semibold text-navy-900"><td className="px-5 py-2.5">Totaux</td><td className="hidden sm:table-cell" /><td className="num px-3 py-2.5 text-right">590 000</td><td className="num px-5 py-2.5 text-right">590 000</td></tr></tfoot>
      </table>
      <div className="grid grid-cols-3 divide-x divide-slate-100 border-t border-slate-100 text-center">
        {[['TVA 18 %', '90 000'], ['Net à payer', '590 000'], ['Devise', 'FCFA']].map(([k, v]) => (
          <div key={k} className="px-3 py-3"><div className="text-[11px] text-slate-500">{k}</div><div className="num text-sm font-bold text-navy-900">{v}</div></div>
        ))}
      </div>
    </div>
  );
}

export default function HomePage() {
  const { user } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [menu, setMenu] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div className="min-h-screen bg-paper">
      {/* En-tête */}
      <header className={cx('fixed inset-x-0 top-0 z-40 transition-all duration-300', scrolled || menu ? 'bg-navy-950/95 shadow-lg shadow-navy-950/20 backdrop-blur-md' : 'bg-transparent')}>
        <div className="mx-auto flex h-[72px] max-w-7xl items-center justify-between gap-6 px-4 sm:px-6">
          <Link to="/" aria-label="BT COMPTA PRO — accueil"><Logo light /></Link>
          <nav className="hidden items-center gap-1 lg:flex" aria-label="Sections">
            {NAV.map(([href, label]) => <a key={href} href={href} className="rounded-lg px-3.5 py-2 text-sm font-medium text-white/75 transition hover:text-white">{label}</a>)}
          </nav>
          <div className="flex items-center gap-2">
            {user ? (
              <Link to="/app" className="inline-flex h-10 items-center gap-2 rounded-xl bg-white px-4 text-sm font-semibold text-navy-900 hover:bg-brand-50">Mon espace <ArrowRight className="size-4" /></Link>
            ) : (
              <>
                <Link to="/connexion" className="hidden h-10 items-center rounded-xl px-4 text-sm font-semibold text-white hover:bg-white/10 sm:inline-flex">Connexion</Link>
                <Link to="/inscription" className="inline-flex h-10 items-center rounded-xl bg-[#E8A33D] px-4 text-sm font-bold text-navy-950 shadow-lg shadow-[#E8A33D]/25 transition hover:bg-[#F2B65A]">S'inscrire</Link>
              </>
            )}
            <button className="rounded-lg p-2 text-white lg:hidden" onClick={() => setMenu((m) => !m)} aria-label="Menu" aria-expanded={menu}>
              {menu ? <X className="size-5" /> : <Menu className="size-5" />}
            </button>
          </div>
        </div>
        {menu && (
          <nav className="border-t border-white/10 px-4 pb-4 lg:hidden" aria-label="Sections">
            {NAV.map(([href, label]) => <a key={href} href={href} onClick={() => setMenu(false)} className="block rounded-lg px-3 py-3 text-sm font-medium text-white/85 hover:bg-white/5">{label}</a>)}
            {!user && <Link to="/connexion" className="block rounded-lg px-3 py-3 text-sm font-medium text-white/85 hover:bg-white/5">Connexion</Link>}
          </nav>
        )}
      </header>

      {/* Héros : illustration originale — crépuscule sahélien, architecture en banco, baobabs, bogolan */}
      <section className="relative isolate flex min-h-[640px] items-center overflow-hidden bg-navy-950 pb-36 pt-32 text-white sm:min-h-[720px] lg:min-h-[100svh] lg:pb-44">
        <div className="absolute inset-0 -z-20 bg-[url('/images/hero-mali.svg')] bg-cover bg-[position:70%_bottom] sm:bg-bottom" role="img"
          aria-label="Illustration : coucher de soleil sur une mosquée en banco et des baobabs, au Sahel" />
        <div className="absolute inset-0 -z-10 bg-gradient-to-r from-navy-950/95 via-navy-950/75 to-navy-950/10 lg:via-navy-950/55" />
        <div className="absolute inset-x-0 bottom-0 -z-10 h-40 bg-gradient-to-t from-navy-950/60 to-transparent" />

        <div className="mx-auto w-full max-w-7xl px-4 sm:px-6">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2.5 rounded-full border border-white/15 bg-white/[0.06] py-1.5 pl-1.5 pr-4 text-xs font-medium text-white/85 backdrop-blur">
              <span className="flex h-5 overflow-hidden rounded-full ring-1 ring-white/20" aria-hidden="true">
                <span className="w-2 bg-[#14B53A]" /><span className="w-2 bg-[#FCD116]" /><span className="w-2 bg-[#CE1126]" />
              </span>
              Enseignement technique et professionnel · Mali
            </div>
            <h1 className="mt-7 text-[2.6rem] font-extrabold leading-[1.04] tracking-tight sm:text-6xl lg:text-[4.1rem]">
              Réussir son <span className="text-[#F2B65A]">BT en comptabilité</span>, de Bamako à Tombouctou.
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-white/75 sm:text-lg">
              Cours BT1 et BT2, calculatrices qui détaillent chaque étape, saisie comptable SYSCOHADA en FCFA et sujets d'examen corrigés par vos enseignants :
              tout pour préparer l'examen et entrer dans le métier.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Link to={user ? '/app' : '/inscription'} className="inline-flex h-[52px] items-center justify-center gap-2 rounded-xl bg-[#E8A33D] px-7 text-[15px] font-bold text-navy-950 shadow-xl shadow-[#E8A33D]/25 transition hover:-translate-y-0.5 hover:bg-[#F2B65A]">
                {user ? 'Accéder à mon espace' : 'Je suis élève — commencer'} <ArrowRight className="size-4" />
              </Link>
              {!user && (
                <Link to="/inscription/professionnel" className="inline-flex h-[52px] items-center justify-center gap-2 rounded-xl border border-white/25 bg-white/[0.06] px-7 text-[15px] font-semibold text-white backdrop-blur transition hover:bg-white/[0.12]">
                  <School className="size-4" /> Enseignant ou comptable
                </Link>
              )}
            </div>
            <ul className="mt-9 flex flex-wrap gap-x-6 gap-y-2 text-sm text-white/70">
              {['SYSCOHADA révisé', 'Montants en FCFA', 'Gratuit pour les apprenants'].map((t) => (
                <li key={t} className="flex items-center gap-2"><CheckCircle2 className="size-4 text-[#F2B65A]" /> {t}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Chiffres clés */}
      <section className="relative z-10 mx-auto -mt-24 max-w-6xl px-4 sm:px-6">
        <div className="grid grid-cols-2 overflow-hidden rounded-3xl bg-white shadow-2xl shadow-navy-950/15 ring-1 ring-slate-200/70 lg:grid-cols-4">
          {[['18', 'modules BT1 et BT2', BookOpen], ['151', 'chapitres de cours', GraduationCap], ['40', 'calculatrices guidées', Calculator], ['233', 'comptes SYSCOHADA', Sigma]].map(([n, l, Icon], i) => {
            const I = Icon as typeof BookOpen;
            return (
              <div key={l as string} className={cx('flex items-center gap-4 p-5 sm:p-7', i % 2 === 0 && 'border-r border-slate-100', i < 2 && 'border-b border-slate-100 lg:border-b-0', i === 1 && 'lg:border-r')}>
                <span className="hidden size-12 shrink-0 place-items-center rounded-2xl bg-[#FBF1E1] text-[#B8741A] sm:grid"><I className="size-5" /></span>
                <div><div className="num text-3xl font-extrabold tracking-tight text-navy-900">{n as string}</div><div className="text-[13px] text-slate-500">{l as string}</div></div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Installation sur téléphone et tablette */}
      <div className="mx-auto mt-6 max-w-6xl px-4 sm:px-6 lg:hidden"><InstallCard /></div>

      {/* Approche adaptée au Mali */}
      <section id="mali" className="mx-auto max-w-7xl scroll-mt-24 px-4 py-24 sm:px-6">
        <SectionTitle eyebrow="Pensé pour le Mali" title="Une plateforme conçue pour la réalité des classes maliennes"
          text="Des contenus en français, alignés sur le SYSCOHADA révisé et la monnaie FCFA, utilisables même avec une connexion faible." />
        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { icon: Sigma, title: 'SYSCOHADA & FCFA', text: 'Plan comptable OHADA révisé, montants en francs CFA, TVA et écritures conformes à l\'enseignement.' },
            { icon: WifiOff, title: 'Connexion faible', text: 'Application légère et installable : le programme reste consultable même hors connexion.' },
            { icon: Smartphone, title: 'Sur téléphone', text: 'Pensée d\'abord pour le smartphone, aussi confortable sur tablette et ordinateur.' },
            { icon: Languages, title: 'En français', text: 'Vocabulaire et méthodes des examens du BT, explications claires et pas à pas.' },
          ].map((f) => (
            <div key={f.title} className="group rounded-3xl border border-slate-200 bg-white p-6 transition hover:-translate-y-1 hover:border-[#E8A33D]/40 hover:shadow-xl hover:shadow-navy-900/5">
              <span className="grid size-12 place-items-center rounded-2xl bg-navy-900 text-[#F2B65A] transition group-hover:bg-[#E8A33D] group-hover:text-navy-950"><f.icon className="size-5" /></span>
              <h3 className="mt-5 text-lg font-bold text-navy-900">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{f.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Démonstration produit */}
      <section className="relative overflow-hidden bg-white">
        <div className="mx-auto grid max-w-7xl items-center gap-14 px-4 py-24 sm:px-6 lg:grid-cols-2">
          <div>
            <SectionTitle eyebrow="Apprendre en pratiquant" title="Chaque calcul expliqué, chaque écriture vérifiée"
              text="Facture, TVA, amortissement, stocks FIFO et CUMP, seuil de rentabilité… L'application affiche la formule, les étapes, le résultat et l'écriture comptable correspondante." />
            <ul className="mt-8 space-y-4">
              {[[Calculator, '40 calculatrices BT1 et BT2', 'Résultats exacts au franc près, export PDF et Excel.'],
                [Building2, 'Un vrai logiciel comptable', 'Journal, grand livre, balance, bilan et compte de résultat générés automatiquement.'],
                [ShieldCheck, 'Rigueur professionnelle', 'Une écriture validée est verrouillée ; la correction se fait par contre-passation.']].map(([Icon, t, d]) => {
                const I = Icon as typeof Calculator;
                return (
                  <li key={t as string} className="flex gap-4">
                    <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600"><I className="size-5" /></span>
                    <div><div className="font-semibold text-navy-900">{t as string}</div><div className="text-sm text-slate-600">{d as string}</div></div>
                  </li>
                );
              })}
            </ul>
          </div>
          <div className="relative">
            <div className="absolute -inset-6 -z-0 rounded-[2.5rem] bg-gradient-to-br from-[#FBF1E1] via-white to-brand-50" />
            <div className="relative"><LedgerCard /></div>
          </div>
        </div>
      </section>

      {/* Pour qui */}
      <section id="acteurs" className="mx-auto max-w-7xl scroll-mt-24 px-4 py-24 sm:px-6">
        <SectionTitle center eyebrow="Pour qui ?" title="Un espace pour chaque acteur de la formation" />
        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {[
            { icon: GraduationCap, who: 'Apprenants BT1 et BT2', items: ['Cours structurés par module', 'Quiz et examens blancs notés sur 20', 'Sujets d\'examen et corrigés', 'Suivi de progression et carnet d\'erreurs'], cta: 'Inscription gratuite', to: '/inscription', accent: true },
            { icon: School, who: 'Enseignants et formateurs', items: ['Dépôt de sujets et de corrigés', 'Publication de la correction en un clic', 'Résultats de chaque apprenant', 'Création d\'épreuves en ligne'], cta: 'Demander un compte enseignant', to: '/inscription/professionnel' },
            { icon: Briefcase, who: 'Techniciens comptables', items: ['Dossiers d\'entreprises', 'Saisie en partie double', 'États financiers SYSCOHADA', 'Exports PDF et Excel'], cta: 'Créer un compte professionnel', to: '/inscription/professionnel' },
          ].map((c) => (
            <div key={c.who} className={cx('flex flex-col rounded-3xl p-7', c.accent ? 'bg-navy-900 text-white shadow-2xl shadow-navy-900/20' : 'border border-slate-200 bg-white')}>
              <span className={cx('grid size-12 place-items-center rounded-2xl', c.accent ? 'bg-[#E8A33D] text-navy-950' : 'bg-brand-50 text-brand-600')}><c.icon className="size-5" /></span>
              <h3 className={cx('mt-5 text-xl font-bold', c.accent ? 'text-white' : 'text-navy-900')}>{c.who}</h3>
              <ul className="mt-5 flex-1 space-y-3">
                {c.items.map((i) => (
                  <li key={i} className={cx('flex items-start gap-2.5 text-sm', c.accent ? 'text-white/80' : 'text-slate-600')}>
                    <CheckCircle2 className={cx('mt-0.5 size-4 shrink-0', c.accent ? 'text-[#F2B65A]' : 'text-money-600')} /> {i}
                  </li>
                ))}
              </ul>
              {!user && (
                <Link to={c.to} className={cx('mt-7 inline-flex h-11 items-center justify-center gap-2 rounded-xl text-sm font-semibold transition',
                  c.accent ? 'bg-[#E8A33D] text-navy-950 hover:bg-[#F2B65A]' : 'border border-slate-300 text-navy-900 hover:bg-slate-50')}>
                  {c.cta} <ArrowRight className="size-4" />
                </Link>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Programme */}
      <section id="programme" className="scroll-mt-24 border-y border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-24 sm:px-6">
          <SectionTitle eyebrow="Programme" title="Les deux années du Brevet de Technicien"
            text="Un parcours progressif, de la partie double à l'analyse financière." />
          <div className="mt-12 grid gap-6 lg:grid-cols-2">
            {([['BT1', 'Comptabilité générale', BT1, 'bg-brand-600'], ['BT2', 'Comptabilité approfondie et analytique', BT2, 'bg-money-600']] as const).map(([code, title, list, color]) => (
              <div key={code} className="rounded-3xl border border-slate-200 bg-paper/50 p-6 sm:p-8">
                <div className="flex items-center gap-4">
                  <span className={`grid size-14 place-items-center rounded-2xl text-base font-extrabold text-white ${color}`}>{code}</span>
                  <div><div className="text-xl font-bold text-navy-900">{title}</div><div className="text-sm text-slate-500">{list.length} modules</div></div>
                </div>
                <ol className="mt-6 grid gap-2 sm:grid-cols-2">
                  {list.map((m, i) => (
                    <li key={m} className="flex items-start gap-3 rounded-xl bg-white px-3.5 py-3 text-sm text-slate-700 ring-1 ring-slate-200/70">
                      <span className="num mt-px text-xs font-bold text-[#B8741A]">{String(i + 1).padStart(2, '0')}</span>{m}
                    </li>
                  ))}
                </ol>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Comment ça marche */}
      <section className="mx-auto max-w-7xl px-4 py-24 sm:px-6">
        <SectionTitle center eyebrow="Comment ça marche" title="Trois étapes pour progresser" />
        <div className="relative mt-14 grid gap-6 md:grid-cols-3">
          <div className="absolute left-[16%] right-[16%] top-7 hidden h-px border-t-2 border-dashed border-[#E8A33D]/40 md:block" />
          {[[ClipboardCheck, 'Je crée mon compte', 'Gratuit pour les apprenants. Les enseignants sont vérifiés par un administrateur.'],
            [BookOpen, 'J\'apprends et je m\'exerce', 'Cours, calculatrices guidées et saisie d\'écritures sur des dossiers d\'entraînement.'],
            [FileSpreadsheet, 'Je m\'évalue', 'Examens blancs notés sur 20, sujets corrigés et suivi de mes erreurs.']].map(([Icon, t, d], i) => {
            const I = Icon as typeof BookOpen;
            return (
              <div key={t as string} className="relative text-center">
                <span className="relative mx-auto grid size-14 place-items-center rounded-2xl bg-navy-900 text-[#F2B65A] shadow-lg shadow-navy-900/20">
                  <I className="size-6" />
                  <span className="absolute -right-2 -top-2 grid size-6 place-items-center rounded-full bg-[#E8A33D] text-xs font-bold text-navy-950">{i + 1}</span>
                </span>
                <h3 className="mt-5 text-lg font-bold text-navy-900">{t as string}</h3>
                <p className="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-slate-600">{d as string}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="scroll-mt-24 border-t border-slate-200 bg-white">
        <div className="mx-auto grid max-w-7xl gap-12 px-4 py-24 sm:px-6 lg:grid-cols-[1fr_1.4fr]">
          <SectionTitle eyebrow="Questions fréquentes" title="Vous vous posez une question ?"
            text="Si votre question n'apparaît pas ici, demandez à votre établissement ou à votre enseignant." />
          <div className="space-y-3">
            <Faq q="L'application est-elle gratuite pour les élèves ?">Oui. L'inscription apprenant est gratuite et donne accès aux cours, calculatrices, quiz et sujets publiés par les enseignants.</Faq>
            <Faq q="Les contenus suivent-ils le SYSCOHADA révisé ?">Les écritures et le plan de comptes utilisent le SYSCOHADA révisé. Les éléments à confirmer sur les textes officiels (fiscalité malienne, intitulés du programme) sont signalés dans l'application.</Faq>
            <Faq q="Puis-je l'utiliser sans bonne connexion Internet ?">L'application est légère et s'installe sur le téléphone. Le programme reste consultable hors connexion ; les calculs, la saisie et les examens nécessitent une connexion.</Faq>
            <Faq q="Comment un enseignant obtient-il son compte ?">Par l'inscription professionnelle : il indique son établissement et ses matières. Un administrateur vérifie la demande et l'enseignant est prévenu par e-mail.</Faq>
            <Faq q="Mes données sont-elles protégées ?">Connexion chiffrée, mots de passe protégés, sessions sécurisées et accès limité selon le rôle. Vos données ne sont ni revendues ni partagées.</Faq>
          </div>
        </div>
      </section>

      {/* Appel à l'action */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
        <div className="relative isolate overflow-hidden rounded-[2rem] bg-navy-900 px-6 py-14 text-white sm:px-14">
          <Bogolan className="absolute inset-0 -z-10 h-full w-full opacity-[0.08]" />
          <div className="absolute -right-24 -top-24 -z-10 size-80 rounded-full bg-[#E8A33D]/25 blur-3xl" />
          <div className="flex flex-col items-start justify-between gap-8 lg:flex-row lg:items-center">
            <div>
              <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Prêt à préparer votre BT ?</h2>
              <p className="mt-3 max-w-xl text-white/70">Rejoignez la plateforme et progressez chaque semaine, à votre rythme, avec l'appui de vos enseignants.</p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Link to={user ? '/app' : '/inscription'} className="inline-flex h-12 items-center justify-center gap-2 rounded-xl bg-[#E8A33D] px-6 font-bold text-navy-950 hover:bg-[#F2B65A]">
                {user ? 'Mon espace' : 'Créer mon compte élève'} <ArrowRight className="size-4" />
              </Link>
              {!user && <Link to="/inscription/professionnel" className="inline-flex h-12 items-center justify-center rounded-xl border border-white/25 px-6 font-semibold hover:bg-white/10">Espace professionnel</Link>}
            </div>
          </div>
        </div>
      </section>

      {/* Pied de page */}
      <footer className="relative bg-navy-950 text-white">
        <Bogolan className="block h-6 w-full opacity-30" />
        <div className="mx-auto grid max-w-7xl gap-10 px-4 py-14 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div>
            <Logo light />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-white/55">Plateforme de formation et de gestion comptable pour l'enseignement technique et professionnel au Mali.</p>
          </div>
          {[['Formation', [['Programme BT1 et BT2', '#programme'], ['Notre approche', '#mali'], ['Questions fréquentes', '#faq']]],
            ['Accès', [['Connexion', '/connexion'], ['Inscription apprenant', '/inscription'], ['Espace professionnel', '/inscription/professionnel']]],
            ['Référentiels', [['SYSCOHADA révisé', '#mali'], ['Montants en FCFA', '#mali'], ['Mot de passe oublié', '/mot-de-passe-oublie']]]].map(([title, links]) => (
            <div key={title as string}>
              <div className="text-xs font-bold uppercase tracking-[0.16em] text-[#F2B65A]">{title as string}</div>
              <ul className="mt-4 space-y-2.5">
                {(links as string[][]).map(([l, href]) => (
                  <li key={l}>{href.startsWith('#') ? <a href={href} className="text-sm text-white/65 hover:text-white">{l}</a> : <Link to={href} className="text-sm text-white/65 hover:text-white">{l}</Link>}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="border-t border-white/10">
          <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-6 text-xs text-white/45 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <span>© {new Date().getFullYear()} BT COMPTA PRO · Tous droits réservés</span>
            <span>Montants en FCFA · Référentiel SYSCOHADA révisé</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
