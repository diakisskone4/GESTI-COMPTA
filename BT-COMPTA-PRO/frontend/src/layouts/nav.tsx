import {
  BookOpen, Building2, Calculator, ClipboardCheck, FileText, GraduationCap, House, LayoutDashboard, LayoutGrid, ListTree, School, ShieldCheck,
  TrendingUp,
} from 'lucide-react';
import type { ReactNode } from 'react';
import type { Role, User } from '../types';

export interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
  roles?: Role[];
  end?: boolean;
  badge?: 'BT1' | 'BT2';
}

export const SECTIONS: { title: string; items: NavItem[] }[] = [
  {
    title: '',
    items: [{ to: '/app', label: 'Tableau de bord', icon: <LayoutDashboard />, end: true }],
  },
  {
    title: 'Formation',
    items: [
      { to: '/app/formation/BT1', label: 'Comptabilité générale', icon: <BookOpen />, badge: 'BT1' },
      { to: '/app/formation/BT2', label: 'Analytique & gestion', icon: <GraduationCap />, badge: 'BT2' },
      { to: '/app/examens', label: 'Quiz & examens', icon: <ClipboardCheck /> },
      { to: '/app/sujets', label: 'Sujets & corrigés', icon: <FileText /> },
      { to: '/app/progression', label: 'Ma progression', icon: <TrendingUp /> },
    ],
  },
  {
    title: 'Comptabilité',
    items: [
      { to: '/app/calculatrices', label: 'Calculatrices', icon: <Calculator /> },
      { to: '/app/comptabilite', label: 'Gestion comptable', icon: <Building2 /> },
      { to: '/app/plan-comptable', label: 'Plan comptable', icon: <ListTree /> },
    ],
  },
  {
    title: 'Gestion',
    items: [
      { to: '/app/enseignant', label: 'Espace enseignant', icon: <School />, roles: ['teacher', 'admin'] },
      { to: '/app/administration', label: 'Administration', icon: <ShieldCheck />, roles: ['admin'] },
    ],
  },
];

export interface Tab {
  to: string;
  label: string;
  icon: ReactNode;
  /** Préfixes d'URL pour lesquels l'onglet est actif. */
  match: string[];
}

/** Barre d'onglets du téléphone et de la tablette, adaptée au métier de l'utilisateur. */
export function tabsFor(user: User | null): Tab[] {
  const home: Tab = { to: '/app', label: 'Accueil', icon: <House />, match: [] };
  const more: Tab = { to: '/app/plus', label: 'Menu', icon: <LayoutGrid />, match: ['/app/plus', '/app/profil', '/app/progression', '/app/administration'] };
  const calc: Tab = { to: '/app/calculatrices', label: 'Calculs', icon: <Calculator />, match: ['/app/calculatrices'] };
  const courses: Tab = { to: `/app/formation/${user?.level || 'BT1'}`, label: 'Cours', icon: <BookOpen />, match: ['/app/formation', '/app/modules'] };
  if (user?.role === 'accountant') {
    return [home, { to: '/app/comptabilite', label: 'Dossiers', icon: <Building2 />, match: ['/app/comptabilite'] }, calc,
      { to: '/app/plan-comptable', label: 'Plan', icon: <ListTree />, match: ['/app/plan-comptable'] }, more];
  }
  if (user?.role === 'teacher' || user?.role === 'admin') {
    return [home, courses, { to: '/app/sujets', label: 'Sujets', icon: <FileText />, match: ['/app/sujets'] },
      { to: '/app/enseignant', label: 'Enseigner', icon: <School />, match: ['/app/enseignant'] }, more];
  }
  return [home, courses, calc, { to: '/app/examens', label: 'Examens', icon: <ClipboardCheck />, match: ['/app/examens', '/app/tentatives', '/app/sujets'] }, more];
}

const TITLES: [string, string][] = [
  ['/app/plus', 'Menu'], ['/app/profil', 'Mon profil'], ['/app/progression', 'Ma progression'], ['/app/sujets', 'Sujets & corrigés'],
  ['/app/plan-comptable', 'Plan comptable'], ['/app/enseignant', 'Espace enseignant'], ['/app/administration', 'Administration'],
  ['/app/comptabilite/', 'Dossier comptable'], ['/app/comptabilite', 'Gestion comptable'], ['/app/calculatrices/', 'Calculatrice'],
  ['/app/calculatrices', 'Calculatrices'], ['/app/modules/', 'Module'], ['/app/formation/', 'Formation'], ['/app/tentatives/', 'Résultat'],
  ['/app/examens/', 'Épreuve'], ['/app/examens', 'Quiz & examens'],
];

export function titleFor(path: string) {
  return TITLES.find(([prefix]) => path.startsWith(prefix))?.[1] ?? '';
}
