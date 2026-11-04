import { useState, type FormEvent } from 'react';
import { Alert, Button, Card, Field, PageHeader } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import PasswordStrength from '../components/PasswordStrength';
import { api, errorMessage, session } from '../services/api';

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [form, setForm] = useState({ first_name: user?.first_name ?? '', last_name: user?.last_name ?? '', phone: user?.phone ?? '', establishment: user?.establishment ?? '', level: user?.level ?? '' });
  const [pwd, setPwd] = useState({ old_password: '', new_password: '' });
  const [msg, setMsg] = useState<{ tone: 'success' | 'error'; text: string } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  async function run(kind: string, fn: () => Promise<unknown>, ok: string) {
    setBusy(kind);
    setMsg(null);
    try {
      await fn();
      setMsg({ tone: 'success', text: ok });
    } catch (e) {
      setMsg({ tone: 'error', text: errorMessage(e) });
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader eyebrow={user?.role_label} title="Mon profil" subtitle={`${user?.username} · ${user?.email}`} />
      {msg && <div className="mb-4"><Alert tone={msg.tone} onClose={() => setMsg(null)}>{msg.text}</Alert></div>}
      <div className="space-y-6">
        <Card className="p-6">
          <form className="grid gap-4 sm:grid-cols-2" onSubmit={(e: FormEvent) => { e.preventDefault(); run('profile', async () => { await api.patch('/auth/me/', form); await refreshUser(); }, 'Profil mis à jour.'); }}>
            <Field label="Prénom"><input className="field" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} /></Field>
            <Field label="Nom"><input className="field" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} /></Field>
            <Field label="Téléphone"><input className="field" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></Field>
            <Field label="Établissement"><input className="field" value={form.establishment} onChange={(e) => setForm({ ...form, establishment: e.target.value })} /></Field>
            <Field label="Niveau">
              <select className="field" value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value as typeof form.level })}><option value="BT1">BT1</option><option value="BT2">BT2</option><option value="">Autre</option></select>
            </Field>
            <div className="flex items-end justify-end"><Button type="submit" loading={busy === 'profile'}>Enregistrer</Button></div>
          </form>
        </Card>
        <Card className="p-6">
          <h2 className="mb-4 font-semibold text-navy-900">Changer de mot de passe</h2>
          <form className="grid gap-4 sm:grid-cols-2" onSubmit={(e: FormEvent) => { e.preventDefault(); run('pwd', async () => { const { data } = await api.post('/auth/change-password/', pwd); session.set(data.access); setPwd({ old_password: '', new_password: '' }); }, 'Mot de passe modifié. Vos sessions sur les autres appareils ont été fermées.'); }}>
            <Field label="Mot de passe actuel"><input type="password" className="field" value={pwd.old_password} onChange={(e) => setPwd({ ...pwd, old_password: e.target.value })} required autoComplete="current-password" /></Field>
            <Field label="Nouveau mot de passe"><input type="password" className="field" value={pwd.new_password} onChange={(e) => setPwd({ ...pwd, new_password: e.target.value })} required minLength={8} maxLength={128} autoComplete="new-password" /><PasswordStrength password={pwd.new_password} /></Field>
            <div className="sm:col-span-2 flex justify-end"><Button type="submit" variant="secondary" loading={busy === 'pwd'}>Mettre à jour</Button></div>
          </form>
        </Card>
      </div>
    </div>
  );
}
