import {
  BarChart3, CheckCircle2, Clock, Eye, EyeOff, FileCheck2, FileText, Laptop, Lock, Pencil, PlayCircle, Plus, Trash2, Unlock,
} from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { useConfirm } from '../../components/ConfirmDialog';
import { Alert, Badge, Button, Card, cx, EmptyState, formatDate, formatNumber, Modal, Spinner } from '../../components/ui';
import { useFetch } from '../../hooks/useFetch';
import { api, errorMessage, openProtectedFile } from '../../services/api';
import type { ExamSubject, SubjectResults } from '../../types';
import SubjectForm from './SubjectForm';

function ResultsView({ subject }: { subject: ExamSubject }) {
  const { data, loading, error } = useFetch<SubjectResults>(`/exams/subjects/${subject.id}/results/`);
  if (loading) return <Spinner />;
  if (error || !data) return <Alert tone="error">{error}</Alert>;
  const s = data.summary;
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[['Sujet ouvert', s.opened], ['Correction consultée', s.corrected], ['Moyenne /20', s.average ? formatNumber(s.average, 2) : '—'],
          ['Admis (≥ 10)', s.graded ? `${s.passed}/${s.graded}` : '—']].map(([k, v]) => (
          <div key={k as string} className="rounded-xl bg-paper p-3 text-center">
            <div className="text-xs text-slate-500">{k}</div>
            <div className="num mt-0.5 text-lg font-bold text-navy-900">{v}</div>
          </div>
        ))}
      </div>
      {data.rows.length === 0 ? (
        <EmptyState icon={<BarChart3 className="size-6" />} title="Aucun apprenant pour l'instant" text="Les résultats apparaîtront dès que les apprenants ouvriront le sujet." />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="table-base">
            <thead><tr><th>Apprenant</th><th>Sujet ouvert</th><th>Correction vue</th><th className="text-right">Note /20</th>{subject.quiz && <th className="text-right">En ligne</th>}</tr></thead>
            <tbody>
              {data.rows.map((r) => (
                <tr key={r.username}>
                  <td className="font-medium text-navy-900">{r.student}<div className="text-xs font-normal text-slate-400">{r.level}</div></td>
                  <td className="whitespace-nowrap text-slate-500">{r.opened_at ? formatDate(r.opened_at) : '—'}</td>
                  <td className="whitespace-nowrap">{r.correction_viewed_at ? <Badge tone="green"><CheckCircle2 className="size-3" /> {formatDate(r.correction_viewed_at)}</Badge> : <span className="text-slate-400">—</span>}</td>
                  <td className="text-right">
                    {r.self_grade ? <Badge tone={Number(r.self_grade) >= 10 ? 'green' : 'red'}>{formatNumber(r.self_grade, 2)}</Badge> : <span className="text-slate-400">—</span>}
                    {r.comment && <div className="mt-1 max-w-48 truncate text-xs text-slate-400" title={r.comment}>{r.comment}</div>}
                  </td>
                  {subject.quiz && <td className="text-right">{r.online_grade ? <Badge tone="blue">{formatNumber(r.online_grade, 2)}</Badge> : '—'}</td>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-xs text-slate-500">« Note /20 » : note saisie par l'apprenant après comparaison avec le corrigé, ramenée sur 20. « En ligne » : meilleure note obtenue à l'épreuve corrigée automatiquement.</p>
    </div>
  );
}

function CorrectionPanel({ subject, onChange }: { subject: ExamSubject; onChange: () => void }) {
  const [text, setText] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [grade, setGrade] = useState(subject.my_work?.self_grade ? String((Number(subject.my_work.self_grade) * subject.total_points) / 20) : '');
  const [comment, setComment] = useState(subject.my_work?.comment ?? '');
  const [saved, setSaved] = useState('');
  const opened = text !== null;

  async function reveal() {
    setBusy(true);
    setError('');
    try {
      const { data } = await api.post(`/exams/subjects/${subject.id}/correct/`);
      setText(data.correction_text || '');
      if (!subject.my_work?.correction_viewed_at) onChange();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  async function saveGrade(e: FormEvent) {
    e.preventDefault();
    setError('');
    try {
      const { data } = await api.post(`/exams/subjects/${subject.id}/grade/`, { grade, comment });
      setSaved(`Note enregistrée : ${formatNumber(data.self_grade, 2)} / 20`);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  if (!subject.has_correction) return <p className="text-sm text-slate-500">Le corrigé n'a pas encore été déposé.</p>;
  if (!subject.correction_released) {
    return <div className="flex items-center gap-2 text-sm text-slate-500"><Lock className="size-4" /> La correction sera disponible lorsque l'enseignant la publiera.</div>;
  }
  return (
    <div className="space-y-4">
      {!opened && (
        <Button variant="success" onClick={reveal} loading={busy} icon={<FileCheck2 className="size-4" />}>Voir la correction</Button>
      )}
      {error && <Alert tone="error">{error}</Alert>}
      {opened && (
        <>
          {text ? <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap rounded-xl border border-money-600/20 bg-money-50/50 p-4 font-mono text-[13px] leading-relaxed text-slate-800">{text}</pre>
            : !subject.has_correction_file && <p className="text-sm text-slate-500">Corrigé vide.</p>}
          {subject.has_correction_file && (
            <Button variant="secondary" onClick={() => openProtectedFile(`/exams/subjects/${subject.id}/correction-file/`, subject.correction_name).catch((e) => setError(errorMessage(e)))} icon={<FileCheck2 className="size-4" />}>
              Ouvrir le corrigé ({subject.correction_name})
            </Button>
          )}
          <form onSubmit={saveGrade} className="rounded-xl bg-paper p-4">
            <div className="text-sm font-semibold text-navy-900">Mon résultat</div>
            <p className="text-xs text-slate-500">Comparez votre copie au corrigé et saisissez votre note : elle sera transmise à votre enseignant.</p>
            <div className="mt-3 flex flex-wrap items-end gap-2">
              <label className="block">
                <span className="label">Note obtenue</span>
                <span className="flex items-center gap-2">
                  <input className="field-sm num w-24 text-right" inputMode="decimal" value={grade} onChange={(e) => setGrade(e.target.value)} required />
                  <span className="text-sm text-slate-500">/ {subject.total_points}</span>
                </span>
              </label>
              <input className="field-sm min-w-48 flex-1" placeholder="Commentaire (difficultés rencontrées…)" maxLength={500} value={comment} onChange={(e) => setComment(e.target.value)} />
              <Button type="submit" size="sm">Enregistrer</Button>
            </div>
            {saved && <p className="mt-2 text-sm font-medium text-money-700">{saved}</p>}
          </form>
        </>
      )}
    </div>
  );
}

export default function SubjectList({ manage }: { manage: boolean }) {
  const [level, setLevel] = useState<'' | 'BT1' | 'BT2'>('');
  const { data, loading, error, reload } = useFetch<ExamSubject[]>(`/exams/subjects/${level ? `?level=${level}` : ''}`);
  const [editing, setEditing] = useState<ExamSubject | null | undefined>(undefined);
  const [results, setResults] = useState<ExamSubject | null>(null);
  const [open, setOpen] = useState<number | null>(null);
  const [msg, setMsg] = useState<{ tone: 'success' | 'error'; text: string } | null>(null);
  const confirm = useConfirm();

  async function act(fn: () => Promise<unknown>, ok: string) {
    setMsg(null);
    try {
      await fn();
      setMsg({ tone: 'success', text: ok });
      reload();
    } catch (e) {
      setMsg({ tone: 'error', text: errorMessage(e) });
    }
  }

  const openSubject = (s: ExamSubject) =>
    openProtectedFile(`/exams/subjects/${s.id}/subject-file/`, s.subject_name).then(() => { if (!manage && !s.my_work?.opened_at) reload(); })
      .catch((e) => setMsg({ tone: 'error', text: errorMessage(e) }));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="inline-flex gap-1 rounded-xl bg-white p-1 ring-1 ring-slate-200">
          {(['', 'BT1', 'BT2'] as const).map((l) => (
            <button key={l} onClick={() => setLevel(l)} className={cx('rounded-lg px-4 py-1.5 text-sm font-medium', level === l ? 'bg-navy-900 text-white' : 'text-slate-600 hover:bg-slate-50')}>{l || 'Tous'}</button>
          ))}
        </div>
        <div className="flex-1" />
        {manage && <Button onClick={() => setEditing(null)} icon={<Plus className="size-4" />}>Déposer un sujet</Button>}
      </div>
      {msg && <Alert tone={msg.tone} onClose={() => setMsg(null)}>{msg.text}</Alert>}
      {loading && <Spinner />}
      {error && <Alert tone="error">{error}</Alert>}
      {data?.length === 0 && (
        <Card><EmptyState icon={<FileText className="size-6" />} title="Aucun sujet pour le moment"
          text={manage ? 'Déposez votre premier sujet d\'examen avec son corrigé.' : 'Vos enseignants n\'ont pas encore déposé de sujet.'}
          action={manage ? <Button onClick={() => setEditing(null)} icon={<Plus className="size-4" />}>Déposer un sujet</Button> : undefined} /></Card>
      )}

      <div className="space-y-3">
        {data?.map((s) => (
          <Card key={s.id} className="overflow-hidden">
            <div className="flex flex-col gap-4 p-5 lg:flex-row lg:items-start">
              <span className={cx('grid size-12 shrink-0 place-items-center rounded-xl text-white', s.level === 'BT1' ? 'bg-brand-600' : 'bg-money-600')}><FileText className="size-5" /></span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={s.level === 'BT1' ? 'blue' : 'green'}>{s.level}</Badge>
                  <Badge>{s.kind_label}</Badge>
                  {s.correction_released ? <Badge tone="green"><Unlock className="size-3" /> Correction publiée</Badge>
                    : s.has_correction ? <Badge tone="amber"><Lock className="size-3" /> Correction masquée</Badge> : <Badge tone="slate">Sans corrigé</Badge>}
                  {manage && !s.is_published && <Badge tone="red">Non visible</Badge>}
                  {!manage && s.my_work?.self_grade && <Badge tone={Number(s.my_work.self_grade) >= 10 ? 'green' : 'red'}>Ma note : {formatNumber(s.my_work.self_grade, 2)}/20</Badge>}
                </div>
                <h3 className="mt-2 font-semibold text-navy-900">{s.title}</h3>
                <p className="mt-0.5 text-sm text-slate-500">
                  {[s.module_title, s.session, s.duration_minutes && `${s.duration_minutes} min`, `${s.total_points} points`, s.author && `par ${s.author}`].filter(Boolean).join(' · ')}
                </p>
                {s.description && <p className="mt-2 text-sm text-slate-600">{s.description}</p>}
                {manage && s.stats && (
                  <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
                    <span><strong className="text-navy-900">{s.stats.opened}</strong> ouverture(s)</span>
                    <span><strong className="text-navy-900">{s.stats.corrected}</strong> correction(s) consultée(s)</span>
                    <span><strong className="text-navy-900">{s.stats.graded}</strong> note(s)</span>
                    {s.stats.average && <span>Moyenne <strong className="text-navy-900">{formatNumber(s.stats.average, 2)}/20</strong></span>}
                  </div>
                )}
              </div>
              <div className="flex flex-wrap gap-2 lg:justify-end">
                <Button size="sm" variant="secondary" onClick={() => openSubject(s)} icon={<Eye className="size-4" />}>Sujet</Button>
                {manage ? (
                  <>
                    <Button size="sm" variant={s.correction_released ? 'secondary' : 'success'}
                      onClick={() => act(() => api.post(`/exams/subjects/${s.id}/release-correction/`, { released: !s.correction_released }),
                        s.correction_released ? 'Correction masquée aux apprenants.' : 'Correction publiée : les apprenants peuvent la consulter.')}
                      icon={s.correction_released ? <EyeOff className="size-4" /> : <FileCheck2 className="size-4" />}>
                      {s.correction_released ? 'Masquer la correction' : 'Publier la correction'}
                    </Button>
                    <Button size="sm" variant="secondary" onClick={() => setResults(s)} icon={<BarChart3 className="size-4" />}>Résultats</Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditing(s)} aria-label="Modifier"><Pencil className="size-4" /></Button>
                    <Button size="sm" variant="ghost" aria-label="Supprimer"
                      onClick={async () => (await confirm({ title: 'Supprimer ce sujet ?', message: `« ${s.title} », son corrigé et les résultats associés seront supprimés.`, confirmLabel: 'Supprimer', danger: true }))
                        && act(() => api.delete(`/exams/subjects/${s.id}/`), 'Sujet supprimé.')}>
                      <Trash2 className="size-4 text-red-500" />
                    </Button>
                  </>
                ) : (
                  <>
                    {s.quiz && (
                      <Link to={`/app/examens/${s.quiz}/passer`} className="inline-flex h-8 items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3 text-[13px] font-semibold text-slate-700 hover:bg-slate-50">
                        <Laptop className="size-4" /> Composer en ligne
                      </Link>
                    )}
                    <Button size="sm" variant={open === s.id ? 'primary' : 'success'} onClick={() => setOpen(open === s.id ? null : s.id)} icon={<PlayCircle className="size-4" />}>Corrections</Button>
                  </>
                )}
              </div>
            </div>
            {!manage && open === s.id && (
              <div className="border-t border-slate-100 bg-slate-50/50 p-5">
                {s.my_work?.opened_at ? null : (
                  <p className="mb-3 flex items-center gap-2 text-xs text-slate-500"><Clock className="size-3.5" /> Conseil : traitez d'abord le sujet dans les conditions de l'examen, puis consultez la correction.</p>
                )}
                <CorrectionPanel subject={s} onChange={reload} />
              </div>
            )}
          </Card>
        ))}
      </div>

      <Modal open={editing !== undefined} onClose={() => setEditing(undefined)} title={editing ? 'Modifier le sujet' : 'Déposer un sujet d\'examen'} wide>
        {editing !== undefined && <SubjectForm subject={editing} onDone={() => { setEditing(undefined); reload(); }} />}
      </Modal>
      <Modal open={!!results} onClose={() => setResults(null)} title={`Résultats — ${results?.title ?? ''}`} wide>
        {results && <ResultsView subject={results} />}
      </Modal>
    </div>
  );
}
