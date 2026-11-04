import { Link } from 'react-router-dom';
import { LogoMark } from '../components/Logo';

export default function NotFoundPage() {
  return (
    <div className="grid min-h-screen place-items-center bg-paper p-6 text-center">
      <div>
        <LogoMark className="mx-auto size-14" />
        <div className="num mt-6 text-6xl font-extrabold text-navy-900">404</div>
        <h1 className="mt-2 text-lg font-semibold text-navy-900">Page introuvable</h1>
        <p className="mt-1 text-sm text-slate-500">Cette page n'existe pas ou a été déplacée.</p>
        <Link to="/" className="mt-6 inline-flex h-10 items-center rounded-xl bg-brand-600 px-4 text-sm font-semibold text-white hover:bg-brand-700">Retour à l'accueil</Link>
      </div>
    </div>
  );
}
