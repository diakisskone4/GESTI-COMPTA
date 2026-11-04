import { Briefcase, CheckCircle2, Clock, GraduationCap, Send, ShieldCheck } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import PasswordStrength from '../components/PasswordStrength';
import { Alert, Button, cx, Field } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import AuthLayout from '../layouts/AuthLayout';
import { api, errorMessage, session } from '../services/api';

type ProRole = 'teacher' | 'accountant';

const ROLES: { value: ProRole; label: string; icon: typeof GraduationCap; text: string; access: string }[] = [
  { value: 'teacher', label: 'Enseignant', icon: GraduationCap, text: 'Professeur, formateur, centre de formation',
    access: 'Validation par un administrateur' },
  { value: 'accountant', label: 'Technicien comptable', icon: Briefcase, text: 'Cabinet, entreprise, comptable indépendant',
    access: 'Accès immédiat' },
];

export default function ProRegisterPage() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [role, setRole] = useState<ProRole>('teacher');
  const [form, setForm] = useState({ first_name: '', last_name: '', username: '', email: '', phone: '', establishment: '',
    speciality: '', motivation: '', password: '' });
  const [error, setError] = useState('');
  const [pending, setPending] = useState('');
  const [loading, setLoading] = useState(false);
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const teacher = role === 'teacher';

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data, status } = await api.post('/auth/register/pro/', { ...form, role });
      if (status === 202) {
        setPending(data.detail);
      } else {
        session.set(data.access);
        await refreshUser();
        navigate('/app', { replace: true });
      }
    } catch (err) {
      setError(errorMessage(err, 'Inscription impossible.'));
    } finally {
      setLoading(false);
    }
  }

  if (pending) {
    return (
      <AuthLayout title="Demande envoyée" subtitle="Merci ! Votre demande de compte enseignant est en cours d'examen.">
        <div className="space-y-5">
          <div className="flex gap-3 rounded-2xl border border-money-600/20 bg-money-50 p-4 text-sm text-money-700">
            <CheckCircle2 className="mt-0.5 size-5 shrink-0" /> {pending}
          </div>
          <ol className="space-y-3 text-sm text-slate-600">
            {['Un administrateur vérifie votre établissement et vos informations.', 'Vous recevez un e-mail dès la validation.',
              'Vous vous connectez avec l\'identifiant et le mot de passe choisis.'].map((t, i) => (
              <li key={t} className="flex gap-3"><span className="grid size-6 shrink-0 place-items-center rounded-full bg-brand-50 text-xs font-bold text-brand-600">{i + 1}</span>{t}</li>
            ))}
          </ol>
          <Link to="/" className="inline-flex text-sm font-semibold text-brand-600 hover:underline">Retour à l'accueil</Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Espace professionnel" subtitle="Inscription des enseignants et des techniciens comptables.">
      <form onSubmit={submit} className="space-y-4">
        {error && <Alert tone="error">{error}</Alert>}
        <div className="grid gap-2 sm:grid-cols-2" role="radiogroup" aria-label="Profil professionnel">
          {ROLES.map((r) => (
            <button type="button" role="radio" aria-checked={role === r.value} key={r.value} onClick={() => setRole(r.value)}
              className={cx('rounded-xl border p-3.5 text-left transition', role === r.value ? 'border-brand-600 bg-brand-50 ring-4 ring-brand-600/10' : 'border-slate-200 bg-white hover:border-slate-300')}>
              <div className="flex items-center gap-2 text-sm font-semibold text-navy-900"><r.icon className="size-4 text-brand-600" /> {r.label}</div>
              <div className="mt-0.5 text-xs text-slate-500">{r.text}</div>
              <div className={cx('mt-2 inline-flex items-center gap-1 text-[11px] font-semibold', r.value === 'teacher' ? 'text-amber-700' : 'text-money-700')}>
                {r.value === 'teacher' ? <Clock className="size-3" /> : <CheckCircle2 className="size-3" />} {r.access}
              </div>
            </button>
          ))}
        </div>
        {teacher && (
          <Alert tone="info">
            Le compte enseignant donne accès aux corrigés et aux résultats des apprenants : il est activé après vérification par un administrateur.
          </Alert>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Prénom"><input className="field" value={form.first_name} onChange={set('first_name')} required autoComplete="given-name" /></Field>
          <Field label="Nom"><input className="field" value={form.last_name} onChange={set('last_name')} required autoComplete="family-name" /></Field>
          <Field label="Nom d'utilisateur"><input className="field" value={form.username} onChange={set('username')} required autoComplete="username" /></Field>
          <Field label="Téléphone"><input className="field" value={form.phone} onChange={set('phone')} required placeholder="+223 …" autoComplete="tel" /></Field>
        </div>
        <Field label="E-mail professionnel"><input className="field" type="email" value={form.email} onChange={set('email')} required autoComplete="email" /></Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={teacher ? 'Établissement' : 'Cabinet / entreprise'}>
            <input className="field" value={form.establishment} onChange={set('establishment')} required placeholder={teacher ? 'Lycée, IFP, centre…' : 'Nom du cabinet'} />
          </Field>
          <Field label={teacher ? 'Matières enseignées' : 'Spécialité (facultatif)'}>
            <input className="field" value={form.speciality} onChange={set('speciality')} required={teacher} placeholder={teacher ? 'Comptabilité générale, analytique…' : 'Fiscalité, paie…'} />
          </Field>
        </div>
        {teacher && (
          <Field label="Présentation de votre demande" hint="Classes enseignées, ancienneté, fonction… (20 caractères minimum)">
            <textarea className="field min-h-24" value={form.motivation} onChange={set('motivation')} required minLength={20} maxLength={1000} />
          </Field>
        )}
        <Field label="Mot de passe">
          <input className="field" type="password" value={form.password} onChange={set('password')} required minLength={8} maxLength={128} autoComplete="new-password" />
          <PasswordStrength password={form.password} />
        </Field>
        <Button type="submit" size="lg" className="w-full" loading={loading} icon={teacher ? <Send className="size-4" /> : <ShieldCheck className="size-4" />}>
          {teacher ? 'Envoyer ma demande' : 'Créer mon compte professionnel'}
        </Button>
        <p className="text-center text-sm text-slate-500">
          Vous êtes élève ? <Link to="/inscription" className="font-semibold text-brand-600 hover:underline">Inscription apprenant</Link>
          {' · '}<Link to="/connexion" className="font-semibold text-brand-600 hover:underline">Se connecter</Link>
        </p>
      </form>
    </AuthLayout>
  );
}
