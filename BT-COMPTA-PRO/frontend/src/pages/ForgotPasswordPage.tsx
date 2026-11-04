import { MailCheck, Send } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Button, Field } from '../components/ui';
import AuthLayout from '../layouts/AuthLayout';
import { api, errorMessage } from '../services/api';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await api.post('/auth/password-reset/', { email });
      setSent(data.detail);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Mot de passe oublié" subtitle="Saisissez l'adresse e-mail de votre compte : vous recevrez un lien valable une heure.">
      {sent ? (
        <div className="space-y-5">
          <div className="flex items-start gap-3 rounded-2xl border border-money-600/20 bg-money-50 p-4 text-sm text-money-700">
            <MailCheck className="mt-0.5 size-5 shrink-0" /> {sent}
          </div>
          <p className="text-sm text-slate-500">Pensez à vérifier vos courriers indésirables. Le lien ne peut être utilisé qu'une seule fois.</p>
          <Link to="/connexion" className="inline-flex text-sm font-semibold text-brand-600 hover:underline">Retour à la connexion</Link>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          {error && <Alert tone="error">{error}</Alert>}
          <Field label="Adresse e-mail">
            <input className="field" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus autoComplete="email" />
          </Field>
          <Button type="submit" size="lg" className="w-full" loading={loading} icon={<Send className="size-4" />}>Envoyer le lien</Button>
          <p className="text-center text-sm text-slate-500"><Link to="/connexion" className="font-semibold text-brand-600 hover:underline">Retour à la connexion</Link></p>
        </form>
      )}
    </AuthLayout>
  );
}
