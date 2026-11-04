import { Eye, EyeOff, LogIn } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Alert, Button, Field } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import AuthLayout from '../layouts/AuthLayout';
import { errorMessage } from '../services/api';

export default function LoginPage() {
  const { login, logoutReason } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [show, setShow] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const notice = (location.state as { notice?: string } | null)?.notice;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(identifier, password);
      const from = (location.state as { from?: string } | null)?.from;
      navigate(from && from.startsWith('/app') ? from : '/app', { replace: true });
    } catch (err) {
      setError(errorMessage(err, 'Connexion impossible.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Bon retour 👋" subtitle={<>Connectez-vous à votre espace BT COMPTA PRO.</>}>
      <form onSubmit={submit} className="space-y-4">
        {notice && <Alert tone="success">{notice}</Alert>}
        {!notice && logoutReason === 'idle' && <Alert tone="info">Vous avez été déconnecté après une période d'inactivité.</Alert>}
        {!notice && logoutReason === 'expired' && <Alert tone="info">Votre session a expiré. Veuillez vous reconnecter.</Alert>}
        {error && <Alert tone="error">{error}</Alert>}
        <Field label="Nom d'utilisateur ou e-mail">
          <input className="field" autoComplete="username" maxLength={254} value={identifier} onChange={(e) => setIdentifier(e.target.value)} required autoFocus />
        </Field>
        <div className="-mb-2 flex justify-end">
          <Link to="/mot-de-passe-oublie" className="text-[13px] font-medium text-brand-600 hover:underline">Mot de passe oublié ?</Link>
        </div>
        <Field label="Mot de passe">
          <div className="relative">
            <input className="field pr-11" type={show ? 'text' : 'password'} autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            <button type="button" onClick={() => setShow((s) => !s)} className="absolute inset-y-0 right-0 grid w-11 place-items-center text-slate-400 hover:text-slate-600" aria-label={show ? 'Masquer' : 'Afficher'}>
              {show ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
        </Field>
        <Button type="submit" size="lg" className="w-full" loading={loading} icon={<LogIn className="size-4" />}>
          Se connecter
        </Button>
        <p className="text-center text-sm text-slate-500">
          Pas encore de compte ?{' '}
          <Link to="/inscription" className="font-semibold text-brand-600 hover:underline">Créer un compte</Link>
        </p>
      </form>
    </AuthLayout>
  );
}
