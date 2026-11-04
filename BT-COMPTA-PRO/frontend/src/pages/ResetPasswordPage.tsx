import { KeyRound } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import PasswordStrength from '../components/PasswordStrength';
import { Alert, Button, Field } from '../components/ui';
import AuthLayout from '../layouts/AuthLayout';
import { api, errorMessage } from '../services/api';

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const uid = params.get('uid') ?? '';
  const token = params.get('token') ?? '';
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (password !== confirm) return setError('Les deux mots de passe ne correspondent pas.');
    setError('');
    setLoading(true);
    try {
      await api.post('/auth/password-reset/confirm/', { uid, token, new_password: password });
      navigate('/connexion', { replace: true, state: { notice: 'Mot de passe réinitialisé. Connectez-vous avec votre nouveau mot de passe.' } });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  if (!uid || !token) {
    return (
      <AuthLayout title="Lien incomplet" subtitle="Ce lien de réinitialisation est invalide.">
        <Link to="/mot-de-passe-oublie" className="font-semibold text-brand-600 hover:underline">Faire une nouvelle demande</Link>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Nouveau mot de passe" subtitle="Choisissez un mot de passe que vous n'utilisez sur aucun autre site.">
      <form onSubmit={submit} className="space-y-4">
        {error && <Alert tone="error">{error} {error.includes('expiré') && <Link to="/mot-de-passe-oublie" className="font-semibold underline">Nouvelle demande</Link>}</Alert>}
        <Field label="Nouveau mot de passe">
          <input className="field" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} maxLength={128} autoComplete="new-password" autoFocus />
          <PasswordStrength password={password} />
        </Field>
        <Field label="Confirmer le mot de passe">
          <input className="field" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required autoComplete="new-password" />
        </Field>
        <Button type="submit" size="lg" className="w-full" loading={loading} icon={<KeyRound className="size-4" />}>Réinitialiser</Button>
      </form>
    </AuthLayout>
  );
}
