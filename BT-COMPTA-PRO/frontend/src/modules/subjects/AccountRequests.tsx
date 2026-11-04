import { CheckCircle2, Inbox, XCircle } from 'lucide-react';
import { useState } from 'react';
import { Alert, Badge, Button, Card, EmptyState, Field, formatDate, Modal, Spinner } from '../../components/ui';
import { useFetch } from '../../hooks/useFetch';
import { api, errorMessage } from '../../services/api';
import type { User } from '../../types';

type Pending = User & { speciality: string; motivation: string; approval_status: string };

/** Demandes de comptes enseignants en attente de validation (espace administrateur). */
export default function AccountRequests({ onChange }: { onChange?: () => void }) {
  const { data, loading, error, reload } = useFetch<Pending[]>('/auth/users/?approval=pending');
  const [rejecting, setRejecting] = useState<Pending | null>(null);
  const [note, setNote] = useState('');
  const [msg, setMsg] = useState<{ tone: 'success' | 'error'; text: string } | null>(null);

  async function decide(u: Pending, decision: 'approve' | 'reject', reason = '') {
    setMsg(null);
    try {
      await api.post(`/auth/users/${u.id}/${decision}/`, { note: reason });
      setMsg({ tone: 'success', text: decision === 'approve'
        ? `${u.first_name} ${u.last_name} est maintenant enseignant. Un e-mail de confirmation lui a été envoyé.`
        : `Demande de ${u.first_name} ${u.last_name} refusée.` });
      reload();
      onChange?.();
    } catch (e) {
      setMsg({ tone: 'error', text: errorMessage(e) });
    }
  }

  if (loading) return <Spinner />;
  if (error) return <Alert tone="error">{error}</Alert>;
  return (
    <div className="space-y-3">
      {msg && <Alert tone={msg.tone} onClose={() => setMsg(null)}>{msg.text}</Alert>}
      {data?.length === 0 && <Card><EmptyState icon={<Inbox className="size-6" />} title="Aucune demande en attente" text="Les nouvelles demandes de comptes enseignants apparaîtront ici." /></Card>}
      {data?.map((u) => (
        <Card key={u.id} className="p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
            <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-navy-900 text-sm font-bold text-white">
              {`${u.first_name[0] ?? ''}${u.last_name[0] ?? ''}`.toUpperCase()}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold text-navy-900">{u.first_name} {u.last_name}</span>
                <Badge tone="amber">{u.role_label} · en attente</Badge>
                <span className="text-xs text-slate-400">demande du {formatDate(u.date_joined)}</span>
              </div>
              <div className="mt-1 text-sm text-slate-500">{[u.email, u.phone, `@${u.username}`].filter(Boolean).join(' · ')}</div>
              <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
                <div><dt className="text-xs text-slate-400">Établissement</dt><dd className="font-medium text-slate-700">{u.establishment || '—'}</dd></div>
                <div><dt className="text-xs text-slate-400">Matières</dt><dd className="font-medium text-slate-700">{u.speciality || '—'}</dd></div>
              </dl>
              {u.motivation && <p className="mt-3 whitespace-pre-line rounded-xl bg-paper px-4 py-3 text-sm text-slate-700">{u.motivation}</p>}
            </div>
            <div className="flex gap-2 lg:flex-col">
              <Button variant="success" size="sm" onClick={() => decide(u, 'approve')} icon={<CheckCircle2 className="size-4" />}>Valider</Button>
              <Button variant="danger" size="sm" onClick={() => { setRejecting(u); setNote(''); }} icon={<XCircle className="size-4" />}>Refuser</Button>
            </div>
          </div>
        </Card>
      ))}
      <Modal open={!!rejecting} onClose={() => setRejecting(null)} title="Refuser la demande">
        <div className="space-y-4">
          <Field label="Motif (communiqué au demandeur)">
            <input className="field" value={note} maxLength={255} onChange={(e) => setNote(e.target.value)} placeholder="Établissement non vérifiable…" />
          </Field>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setRejecting(null)}>Annuler</Button>
            <Button className="!bg-red-600 !text-white hover:!bg-red-700" onClick={() => { const u = rejecting!; setRejecting(null); decide(u, 'reject', note); }}>Refuser</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
