import { lazy, Suspense, type ReactNode } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { Spinner } from './components/ui';
import { useAuth } from './hooks/useAuth';
import AppLayout from './layouts/AppLayout';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProRegisterPage from './pages/ProRegisterPage';
import NotFoundPage from './pages/NotFoundPage';
import type { Role } from './types';

const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const ProgramPage = lazy(() => import('./pages/ProgramPage'));
const ModulePage = lazy(() => import('./pages/ModulePage'));
const CalculatorsPage = lazy(() => import('./pages/CalculatorsPage'));
const CalculatorPage = lazy(() => import('./pages/CalculatorPage'));
const CompaniesPage = lazy(() => import('./pages/CompaniesPage'));
const CompanyPage = lazy(() => import('./pages/CompanyPage'));
const AccountPlanPage = lazy(() => import('./pages/AccountPlanPage'));
const ExamsPage = lazy(() => import('./pages/ExamsPage'));
const SubjectsPage = lazy(() => import('./pages/SubjectsPage'));
const ExamTakePage = lazy(() => import('./pages/ExamTakePage'));
const AttemptPage = lazy(() => import('./pages/AttemptPage'));
const ProgressPage = lazy(() => import('./pages/ProgressPage'));
const TeacherPage = lazy(() => import('./pages/TeacherPage'));
const AdminPage = lazy(() => import('./pages/AdminPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'));

function RequireAuth({ children, roles }: { children: ReactNode; roles?: Role[] }) {
  const { user, loading, hasRole } = useAuth();
  const location = useLocation();
  if (loading) return <Spinner />;
  if (!user) return <Navigate to="/connexion" state={{ from: location.pathname }} replace />;
  if (roles && !hasRole(...roles)) return <Navigate to="/app" replace />;
  return <>{children}</>;
}

function GuestOnly({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  return user ? <Navigate to="/app" replace /> : <>{children}</>;
}

export default function App() {
  return (
    <Suspense fallback={<Spinner />}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/connexion" element={<GuestOnly><LoginPage /></GuestOnly>} />
        <Route path="/inscription" element={<GuestOnly><RegisterPage /></GuestOnly>} />
        <Route path="/inscription/professionnel" element={<GuestOnly><ProRegisterPage /></GuestOnly>} />
        <Route path="/mot-de-passe-oublie" element={<GuestOnly><ForgotPasswordPage /></GuestOnly>} />
        <Route path="/reinitialiser-mot-de-passe" element={<ResetPasswordPage />} />
        <Route path="/app" element={<RequireAuth><AppLayout /></RequireAuth>}>
          <Route index element={<DashboardPage />} />
          <Route path="formation/:level" element={<ProgramPage />} />
          <Route path="modules/:id" element={<ModulePage />} />
          <Route path="calculatrices" element={<CalculatorsPage />} />
          <Route path="calculatrices/:slug" element={<CalculatorPage />} />
          <Route path="comptabilite" element={<CompaniesPage />} />
          <Route path="comptabilite/:id" element={<CompanyPage />} />
          <Route path="plan-comptable" element={<AccountPlanPage />} />
          <Route path="examens" element={<ExamsPage />} />
          <Route path="sujets" element={<SubjectsPage />} />
          <Route path="examens/:id/passer" element={<ExamTakePage />} />
          <Route path="tentatives/:id" element={<AttemptPage />} />
          <Route path="progression" element={<ProgressPage />} />
          <Route path="profil" element={<ProfilePage />} />
          <Route path="enseignant" element={<RequireAuth roles={['teacher', 'admin']}><TeacherPage /></RequireAuth>} />
          <Route path="administration" element={<RequireAuth roles={['admin']}><AdminPage /></RequireAuth>} />
        </Route>
        <Route path="/login" element={<Navigate to="/connexion" replace />} />
        <Route path="/register" element={<Navigate to="/inscription" replace />} />
        <Route path="/dashboard" element={<Navigate to="/app" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
