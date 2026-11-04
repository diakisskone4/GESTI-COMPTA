import { RefreshCw } from 'lucide-react';
import { Component, type ErrorInfo, type ReactNode } from 'react';
import { LogoMark } from './Logo';

/** Évite l'écran blanc : affiche une page d'erreur propre si un composant plante. */
export default class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Erreur d\'interface', error, info.componentStack);
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="grid min-h-screen place-items-center bg-paper p-6 text-center">
        <div className="max-w-md">
          <LogoMark className="mx-auto size-14" />
          <h1 className="mt-6 text-xl font-bold text-navy-900">Un problème inattendu est survenu</h1>
          <p className="mt-2 text-sm text-slate-500">Vos données enregistrées ne sont pas affectées. Rechargez la page pour continuer.</p>
          <button onClick={() => window.location.reload()} className="mt-6 inline-flex h-10 items-center gap-2 rounded-xl bg-brand-600 px-4 text-sm font-semibold text-white hover:bg-brand-700">
            <RefreshCw className="size-4" /> Recharger
          </button>
        </div>
      </div>
    );
  }
}
