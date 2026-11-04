import { Briefcase, UserPlus } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import PasswordStrength from '../components/PasswordStrength';
import { Alert, Button, Field } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import AuthLayout from '../layouts/AuthLayout';
import { errorMessage } from '../services/api';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ first_name: '', last_name: '', username: '', email: '', phone: '', establishment: '', level: 'BT1', role: 'student', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(form);
      navigate('/app', { replace: true });
    } catch (err) {
      setError(errorMessage(err, 'Inscription impossible.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Inscription apprenant" subtitle="Élève ou étudiant en BT1 / BT2 : créez votre espace de formation gratuitement.">
      <form onSubmit={submit} className="space-y-4">
        {error && <Alert tone="error">{error}</Alert>}
        <Link to="/inscription/professionnel" className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-3.5 transition hover:border-brand-600/40 hover:bg-brand-50/50">
          <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-navy-900 text-white"><Briefcase className="size-4" /></span>
          <span className="min-w-0 flex-1 text-sm">
            <span className="block font-semibold text-navy-900">Enseignant ou technicien comptable ?</span>
            <span className="block text-xs text-slate-500">Utilisez l'inscription professionnelle</span>
          </span>
          <span className="text-sm font-semibold text-brand-600">→</span>
        </Link>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Prénom"><input className="field" value={form.first_name} onChange={set('first_name')} required autoComplete="given-name" /></Field>
          <Field label="Nom"><input className="field" value={form.last_name} onChange={set('last_name')} required autoComplete="family-name" /></Field>
          <Field label="Nom d'utilisateur"><input className="field" value={form.username} onChange={set('username')} required autoComplete="username" /></Field>
          <Field label="Téléphone"><input className="field" value={form.phone} onChange={set('phone')} placeholder="+223 …" autoComplete="tel" /></Field>
        </div>
        <Field label="E-mail"><input className="field" type="email" value={form.email} onChange={set('email')} required autoComplete="email" /></Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Établissement"><input className="field" value={form.establishment} onChange={set('establishment')} placeholder="Lycée, centre…" /></Field>
          <Field label="Niveau">
            <select className="field" value={form.level} onChange={set('level')}>
              <option value="BT1">BT1</option>
              <option value="BT2">BT2</option>
              <option value="">Autre</option>
            </select>
          </Field>
        </div>
        <Field label="Mot de passe">
          <input className="field" type="password" value={form.password} onChange={set('password')} required minLength={8} maxLength={128} autoComplete="new-password" />
          <PasswordStrength password={form.password} />
        </Field>
        <p className="text-xs leading-relaxed text-slate-500">
          En créant un compte, vous acceptez que vos données (identité, résultats, dossiers comptables) soient utilisées uniquement pour le fonctionnement
          de la plateforme. Elles ne sont ni revendues ni partagées.
        </p>
        <Button type="submit" variant="success" size="lg" className="w-full" loading={loading} icon={<UserPlus className="size-4" />}>
          Créer mon compte
        </Button>
        <p className="text-center text-sm text-slate-500">
          Déjà inscrit ? <Link to="/connexion" className="font-semibold text-brand-600 hover:underline">Se connecter</Link>
        </p>
      </form>
    </AuthLayout>
  );
}
