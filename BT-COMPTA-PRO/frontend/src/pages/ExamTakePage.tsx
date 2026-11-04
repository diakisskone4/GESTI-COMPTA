import { Clock, Plus, Send, Trash2 } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useConfirm } from '../components/ConfirmDialog';
import { Alert, Badge, Button, Card, cx, Spinner } from '../components/ui';
import { api, errorMessage } from '../services/api';
import type { PublicQuestion, Quiz } from '../types';

interface Session { attempt: number; deadline: string; quiz: Quiz; questions: PublicQuestion[] }
type EntryLine = { account: string; debit: string; credit: string };
type Answer = number[] | string | EntryLine[];

function EntryAnswer({ value, onChange }: { value: EntryLine[]; onChange: (v: EntryLine[]) => void }) {
  const lines = value.length ? value : [{ account: '', debit: '', credit: '' }, { account: '', debit: '', credit: '' }];
  const set = (i: number, patch: Partial<EntryLine>) => onChange(lines.map((l, j) => (j === i ? { ...l, ...patch } : l)));
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-[1fr_1fr_1fr_36px] gap-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500"><span>Compte</span><span>Débit</span><span>Crédit</span><span /></div>
      {lines.map((l, i) => (
        <div key={i} className="grid grid-cols-[1fr_1fr_1fr_36px] gap-2">
          <input className="field-sm font-mono" placeholder="601" value={l.account} onChange={(e) => set(i, { account: e.target.value })} />
          <input className="field-sm num text-right" inputMode="decimal" value={l.debit} onChange={(e) => set(i, { debit: e.target.value })} />
          <input className="field-sm num text-right" inputMode="decimal" value={l.credit} onChange={(e) => set(i, { credit: e.target.value })} />
          <button type="button" onClick={() => onChange(lines.filter((_, j) => j !== i))} className="grid place-items-center rounded-lg text-slate-400 hover:bg-red-50 hover:text-red-600" aria-label="Supprimer"><Trash2 className="size-4" /></button>
        </div>
      ))}
      <Button type="button" size="sm" variant="ghost" onClick={() => onChange([...lines, { account: '', debit: '', credit: '' }])} icon={<Plus className="size-4" />}>Ligne</Button>
    </div>
  );
}

export default function ExamTakePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [left, setLeft] = useState(0);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const confirm = useConfirm();
  const started = useRef(false);
  const submitted = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    api.post<Session>(`/exams/quizzes/${id}/start/`).then((r) => setSession(r.data)).catch((e) => setError(errorMessage(e)));
  }, [id]);

  const submit = useCallback(async () => {
    if (!session || submitted.current) return;
    submitted.current = true;
    setSubmitting(true);
    try {
      await api.post(`/exams/attempts/${session.attempt}/submit/`, { answers });
      navigate(`/app/tentatives/${session.attempt}`, { replace: true });
    } catch (e) {
      submitted.current = false;
      setError(errorMessage(e));
      setSubmitting(false);
    }
  }, [session, answers, navigate]);

  useEffect(() => {
    if (!session) return;
    const tick = () => {
      const s = Math.max(0, Math.floor((new Date(session.deadline).getTime() - Date.now()) / 1000));
      setLeft(s);
      if (s === 0) submit();
    };
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, [session, submit]);

  if (error && !session) return <Alert tone="error">{error}</Alert>;
  if (!session) return <Spinner label="Préparation de l'épreuve…" />;

  const answered = session.questions.filter((q) => {
    const a = answers[q.id];
    return Array.isArray(a) ? a.length > 0 : !!a;
  }).length;
  const mm = String(Math.floor(left / 60)).padStart(2, '0');
  const ss = String(left % 60).padStart(2, '0');

  return (
    <div className="mx-auto max-w-3xl">
      <div className="sticky top-appbar z-20 -mx-4 mb-6 border-b border-slate-200 bg-paper/90 px-4 py-3 backdrop-blur sm:mx-0 sm:rounded-2xl sm:border sm:bg-white/90">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="truncate font-semibold text-navy-900">{session.quiz.title}</div>
            <div className="text-xs text-slate-500">{answered}/{session.questions.length} réponses</div>
          </div>
          <span className={cx('num inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 font-mono text-sm font-bold', left < 120 ? 'bg-red-50 text-red-600' : 'bg-navy-900 text-white')}>
            <Clock className="size-4" /> {mm}:{ss}
          </span>
        </div>
      </div>

      <div className="space-y-4">
        {session.questions.map((q, i) => (
          <Card key={q.id} className="p-5 sm:p-6">
            <div className="mb-3 flex items-center gap-2">
              <span className="grid size-7 place-items-center rounded-full bg-navy-900 text-xs font-bold text-white">{i + 1}</span>
              <Badge>{q.kind === 'mcq' ? (q.multiple ? 'Plusieurs réponses' : 'QCM') : q.kind === 'numeric' ? 'Calcul' : 'Saisie d\'écriture'}</Badge>
              <span className="ml-auto text-xs text-slate-400">{Number(q.points)} pt{Number(q.points) > 1 ? 's' : ''}</span>
            </div>
            <p className="mb-4 font-medium leading-relaxed text-slate-800">{q.text}</p>
            {q.kind === 'mcq' && (
              <div className="space-y-2">
                {q.choices.map((c) => {
                  const current = (answers[q.id] as number[]) ?? [];
                  const checked = current.includes(c.id);
                  return (
                    <label key={c.id} className={cx('flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 text-sm transition', checked ? 'border-brand-600 bg-brand-50 ring-2 ring-brand-600/15' : 'border-slate-200 hover:bg-slate-50')}>
                      <input
                        type={q.multiple ? 'checkbox' : 'radio'}
                        name={`q${q.id}`}
                        checked={checked}
                        className="size-4 accent-brand-600"
                        onChange={() => setAnswers((a) => ({ ...a, [q.id]: q.multiple ? (checked ? current.filter((x) => x !== c.id) : [...current, c.id]) : [c.id] }))}
                      />
                      {c.text}
                    </label>
                  );
                })}
              </div>
            )}
            {q.kind === 'numeric' && (
              <input className="field num max-w-xs text-right" inputMode="decimal" placeholder="Votre réponse" value={(answers[q.id] as string) ?? ''} onChange={(e) => setAnswers((a) => ({ ...a, [q.id]: e.target.value }))} />
            )}
            {q.kind === 'entry' && <EntryAnswer value={(answers[q.id] as EntryLine[]) ?? []} onChange={(v) => setAnswers((a) => ({ ...a, [q.id]: v }))} />}
          </Card>
        ))}
      </div>
      {error && <div className="mt-4"><Alert tone="error">{error}</Alert></div>}
      <div className="mt-6 flex justify-end">
        <Button size="lg" variant="success" loading={submitting} onClick={async () => (answered === session.questions.length || (await confirm({ title: 'Remettre la copie ?', message: `${session.questions.length - answered} question(s) sans réponse. Une copie remise ne peut plus être modifiée.`, confirmLabel: 'Remettre' }))) && submit()} icon={<Send className="size-4" />}>
          Remettre ma copie
        </Button>
      </div>
    </div>
  );
}
