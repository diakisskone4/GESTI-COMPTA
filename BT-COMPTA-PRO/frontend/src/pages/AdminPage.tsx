import { Inbox, Lock, Search, ShieldCheck, Unlock, Users } from 'lucide-react';
import { useState } from 'react';
import { Alert, Badge, Button, Card, formatDate, PageHeader, Spinner, Tabs } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import AccountRequests from '../modules/subjects/AccountRequests';
import { useFetch } from '../hooks/useFetch';
import { api, errorMessage } from '../services/api';
import type { Role, User } from '../types';

type Tab = 'requests' | 'users' | 'audit' | 'rules';
interface Log { id: number; username: string; action: string; target_type: string; target_id: string; details: Record<string, unknown>; ip_address: string | null; created_at: string }
interface Rule { id: number; rule_type: string; rule_type_label: string; code: string; label: string; description: string; source: string; verified: boolean }
interface Rate { id: number; code: string; label: string; rate: string; source: string; verified: boolean }

const ROLES: { value: Role; label: string }[] = [
  { value: 'student', label: 'Apprenant' }, { value: 'teacher', label: 'Enseignant' },
  { value: 'accountant', label: 'Technicien comptable' }, { value: 'admin', label: 'Administrateur' },
];

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>('requests');
  const [search, setSearch] = useState('');
  const users = useFetch<User[]>(`/auth/users/${search ? `?search=${encodeURIComponent(search)}` : ''}`);
  const logs = useFetch<Log[]>(tab === 'audit' ? '/audit-logs/' : null);
  const rules = useFetch<Rule[]>(tab === 'rules' ? '/accounting/rules/' : null);
  const rates = useFetch<Rate[]>(tab === 'rules' ? '/accounting/tax-rates/' : null);
  const [msg, setMsg] = useState<{ tone: 'success' | 'error'; text: string } | null>(null);
  const { user: me } = useAuth();
  const pending = useFetch<User[]>('/auth/users/?approval=pending');
  const pendingCount = pending.data?.length ?? 0;

  async function unlock(u: User & { is_locked?: boolean }) {
    try {
      await api.post(`/auth/users/${u.id}/unlock/`);
      setMsg({ tone: 'success', text: `Compte ${u.username} déverrouillé.` });
      users.reload();
    } catch (e) {
      setMsg({ tone: 'error', text: errorMessage(e) });
    }
  }

  async function update(u: User, patch: Partial<User>) {
    setMsg(null);
    try {
      await api.patch(`/auth/users/${u.id}/`, patch);
      setMsg({ tone: 'success', text: `${u.username} mis à jour.` });
      users.reload();
    } catch (e) {
      setMsg({ tone: 'error', text: errorMessage(e) });
    }
  }

  return (
    <div>
      <PageHeader eyebrow="Administration" title="Gestion de la plateforme" subtitle="Utilisateurs et rôles, journal des actions sensibles, référentiels comptables et fiscaux." />
      <Tabs<Tab> value={tab} onChange={setTab} items={[
        { value: 'requests', label: pendingCount ? `Demandes de comptes (${pendingCount})` : 'Demandes de comptes', icon: <Inbox className="size-4" /> },
        { value: 'users', label: 'Utilisateurs', icon: <Users className="size-4" /> },
        { value: 'audit', label: 'Journal d\'audit', icon: <ShieldCheck className="size-4" /> },
        { value: 'rules', label: 'Règles et taux' },
      ]} />
      {msg && <div className="mb-4"><Alert tone={msg.tone} onClose={() => setMsg(null)}>{msg.text}</Alert></div>}

      {tab === 'requests' && <AccountRequests onChange={() => { pending.reload(); users.reload(); }} />}

      {tab === 'users' && (
        <Card className="overflow-hidden">
          <div className="border-b border-slate-100 p-4">
            <div className="relative max-w-sm">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
              <input className="field-sm pl-9" placeholder="Rechercher un utilisateur" value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
          </div>
          {users.loading ? <Spinner /> : (
            <div className="overflow-x-auto">
              <table className="table-base">
                <thead><tr><th>Utilisateur</th><th>E-mail</th><th>Niveau</th><th>Rôle</th><th>Inscrit le</th><th>Sécurité</th><th>Actif</th></tr></thead>
                <tbody>
                  {(users.data as (User & { is_locked?: boolean })[] | null)?.map((u) => (
                    <tr key={u.id}>
                      <td className="font-medium text-navy-900">{u.first_name} {u.last_name}<div className="text-xs font-normal text-slate-500">@{u.username}</div></td>
                      <td className="text-slate-600">{u.email}</td>
                      <td>{u.level || '—'}</td>
                      <td>
                        <select className="field-sm w-auto" value={u.role} disabled={u.id === me?.id} title={u.id === me?.id ? 'Vous ne pouvez pas modifier votre propre rôle' : undefined} onChange={(e) => update(u, { role: e.target.value as Role })}>
                          {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                        </select>
                      </td>
                      <td className="whitespace-nowrap text-slate-500">{formatDate(u.date_joined)}</td>
                      <td>
                        {u.is_locked ? (
                          <Button size="sm" variant="secondary" onClick={() => unlock(u)} icon={<Unlock className="size-3.5" />}>Déverrouiller</Button>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs text-slate-400"><Lock className="size-3" /> Normal</span>
                        )}
                      </td>
                      <td><input type="checkbox" disabled={u.id === me?.id} className="size-4 accent-money-600" checked={u.is_active} onChange={(e) => update(u, { is_active: e.target.checked })} aria-label="Compte actif" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {tab === 'audit' && (logs.loading ? <Spinner /> : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead><tr><th>Date</th><th>Utilisateur</th><th>Action</th><th>Objet</th><th>Détails</th><th>IP</th></tr></thead>
              <tbody>
                {logs.data?.map((l) => (
                  <tr key={l.id}>
                    <td className="whitespace-nowrap text-slate-500">{new Date(l.created_at).toLocaleString('fr-FR')}</td>
                    <td className="font-medium">{l.username || '—'}</td>
                    <td><Badge tone={l.action.includes('failed') ? 'red' : 'blue'}>{l.action}</Badge></td>
                    <td className="text-slate-500">{l.target_type} {l.target_id}</td>
                    <td className="max-w-xs truncate font-mono text-xs text-slate-500">{Object.keys(l.details).length ? JSON.stringify(l.details) : ''}</td>
                    <td className="font-mono text-xs text-slate-500">{l.ip_address}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ))}

      {tab === 'rules' && (
        <div className="space-y-6">
          <Card className="overflow-hidden">
            <div className="border-b border-slate-100 px-5 py-3.5 font-semibold text-navy-900">Taux fiscaux versionnés</div>
            <table className="table-base">
              <thead><tr><th>Code</th><th>Libellé</th><th className="text-right">Taux</th><th>Source</th><th>Statut</th></tr></thead>
              <tbody>{rates.data?.map((r) => <tr key={r.id}><td className="font-mono">{r.code}</td><td>{r.label}</td><td className="num text-right">{Number(r.rate)} %</td><td className="text-xs text-slate-500">{r.source}</td><td>{r.verified ? <Badge tone="green">Vérifié</Badge> : <Badge tone="amber">À vérifier</Badge>}</td></tr>)}</tbody>
            </table>
          </Card>
          <Card className="overflow-hidden">
            <div className="border-b border-slate-100 px-5 py-3.5 font-semibold text-navy-900">Règles comptables OHADA et dispositions fiscales maliennes</div>
            <ul className="divide-y divide-slate-100">
              {rules.data?.map((r) => (
                <li key={r.id} className="px-5 py-3.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={r.rule_type === 'ohada' ? 'blue' : 'green'}>{r.rule_type_label}</Badge>
                    <span className="font-semibold text-navy-900">{r.label}</span>
                    {!r.verified && <Badge tone="amber">À vérifier</Badge>}
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{r.description}</p>
                  <p className="mt-0.5 text-xs text-slate-400">Source : {r.source}</p>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      )}
    </div>
  );
}
