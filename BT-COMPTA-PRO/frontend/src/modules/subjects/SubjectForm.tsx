import { FileUp, Paperclip, Upload, X } from 'lucide-react';
import { useRef, useState, type FormEvent } from 'react';
import { Alert, Button, Field } from '../../components/ui';
import { useFetch } from '../../hooks/useFetch';
import { api, errorMessage } from '../../services/api';
import type { ExamSubject, Module, Quiz } from '../../types';

const MAX_MB = 10;
const ACCEPT = '.pdf,.docx,.png,.jpg,.jpeg';

function FilePicker({ label, file, current, onChange, onRemove, required }: {
  label: string; file: File | null; current?: string; onChange: (f: File | null) => void; onRemove?: () => void; required?: boolean;
}) {
  const ref = useRef<HTMLInputElement>(null);
  const [error, setError] = useState('');
  function pick(f: File | null) {
    setError('');
    if (f && f.size > MAX_MB * 1024 * 1024) {
      setError(`Fichier trop volumineux (${MAX_MB} Mo maximum).`);
      return;
    }
    onChange(f);
  }
  const name = file?.name ?? current;
  return (
    <div>
      <span className="label">{label}{required && <span className="text-red-500"> *</span>}</span>
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files?.[0] ?? null); }}
        className="flex items-center gap-3 rounded-xl border-2 border-dashed border-slate-300 bg-paper/60 px-4 py-3.5 transition hover:border-brand-600/50"
      >
        <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-white text-brand-600 ring-1 ring-slate-200">
          {name ? <Paperclip className="size-5" /> : <FileUp className="size-5" />}
        </span>
        <div className="min-w-0 flex-1 text-sm">
          {name ? (
            <>
              <div className="truncate font-medium text-navy-900">{name}</div>
              <div className="text-xs text-slate-500">{file ? `${(file.size / 1024 / 1024).toFixed(2)} Mo · nouveau fichier` : 'Fichier actuel'}</div>
            </>
          ) : (
            <>
              <div className="font-medium text-slate-700">Glissez un fichier ou parcourez</div>
              <div className="text-xs text-slate-500">PDF, Word (.docx), PNG ou JPG · {MAX_MB} Mo max.</div>
            </>
          )}
        </div>
        <Button type="button" size="sm" variant="secondary" onClick={() => ref.current?.click()}>{name ? 'Remplacer' : 'Parcourir'}</Button>
        {(file || (current && onRemove)) && (
          <button type="button" onClick={() => { if (file) onChange(null); else onRemove?.(); }} className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600" aria-label="Retirer le fichier">
            <X className="size-4" />
          </button>
        )}
        <input ref={ref} type="file" accept={ACCEPT} className="hidden" onChange={(e) => pick(e.target.files?.[0] ?? null)} />
      </div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}

export default function SubjectForm({ subject, onDone }: { subject?: ExamSubject | null; onDone: () => void }) {
  const modules = useFetch<Module[]>('/pedagogy/modules/');
  const quizzes = useFetch<Quiz[]>('/exams/quizzes/');
  const [form, setForm] = useState({
    title: subject?.title ?? '', level: subject?.level ?? 'BT1', module: subject?.module ? String(subject.module) : '',
    kind: subject?.kind ?? 'mock', session: subject?.session ?? '', duration_minutes: subject?.duration_minutes ? String(subject.duration_minutes) : '',
    total_points: String(subject?.total_points ?? 20), description: subject?.description ?? '', correction_text: subject?.correction_text ?? '',
    quiz: subject?.quiz ? String(subject.quiz) : '', correction_released: subject?.correction_released ?? false, is_published: subject?.is_published ?? true,
  });
  const [subjectFile, setSubjectFile] = useState<File | null>(null);
  const [correctionFile, setCorrectionFile] = useState<File | null>(null);
  const [removeCorrection, setRemoveCorrection] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState<number | null>(null);
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError('');
    if (!subject && !subjectFile) return setError('Joignez le fichier du sujet.');
    const data = new FormData();
    Object.entries(form).forEach(([k, v]) => {
      if (typeof v === 'boolean') data.append(k, v ? 'true' : 'false');
      else if (v !== '' || k === 'correction_text' || k === 'description' || k === 'session') data.append(k, v);
    });
    if (!form.module) data.append('module', '');
    if (!form.quiz) data.append('quiz', '');
    if (subjectFile) data.append('subject_file', subjectFile);
    if (correctionFile) data.append('correction_file', correctionFile);
    if (removeCorrection && !correctionFile) data.append('remove_correction_file', 'true');
    setProgress(0);
    try {
      const config = { onUploadProgress: (p: { loaded: number; total?: number }) => setProgress(p.total ? Math.round((p.loaded / p.total) * 100) : null) };
      if (subject) await api.patch(`/exams/subjects/${subject.id}/`, data, config);
      else await api.post('/exams/subjects/', data, config);
      onDone();
    } catch (err) {
      setError(errorMessage(err, 'Envoi impossible.'));
    } finally {
      setProgress(null);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      {error && <Alert tone="error">{error}</Alert>}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2"><Field label="Titre du sujet"><input className="field" value={form.title} onChange={set('title')} required maxLength={200} placeholder="Examen blanc BT1 — Travaux d'inventaire" /></Field></div>
        <Field label="Niveau">
          <select className="field" value={form.level} onChange={(e) => setForm((f) => ({ ...f, level: e.target.value as 'BT1' | 'BT2', module: '' }))}><option>BT1</option><option>BT2</option></select>
        </Field>
        <Field label="Type">
          <select className="field" value={form.kind} onChange={set('kind')}>
            <option value="mock">Examen blanc</option><option value="annale">Annale / sujet d'examen</option><option value="devoir">Devoir</option><option value="td">Travaux dirigés</option>
          </select>
        </Field>
        <Field label="Module (facultatif)">
          <select className="field" value={form.module} onChange={set('module')}>
            <option value="">— Tout le programme</option>
            {modules.data?.filter((m) => m.level_code === form.level).map((m) => <option key={m.id} value={m.id}>{m.code} — {m.title}</option>)}
          </select>
        </Field>
        <Field label="Session / année"><input className="field" value={form.session} onChange={set('session')} placeholder="Juin 2026" maxLength={60} /></Field>
        <Field label="Durée (minutes)"><input className="field" type="number" min={1} value={form.duration_minutes} onChange={set('duration_minutes')} placeholder="180" /></Field>
        <Field label="Barème total (points)"><input className="field" type="number" min={1} max={200} value={form.total_points} onChange={set('total_points')} required /></Field>
        <div className="sm:col-span-2"><Field label="Consignes (facultatif)"><textarea className="field min-h-16" value={form.description} onChange={set('description')} maxLength={3000} placeholder="Documents autorisés, calculatrice…" /></Field></div>
      </div>

      <div className="space-y-4 rounded-2xl bg-paper p-4">
        <div className="text-sm font-semibold text-navy-900">Sujet</div>
        <FilePicker label="Fichier du sujet" required={!subject} file={subjectFile} current={subject?.subject_name} onChange={setSubjectFile} />
      </div>

      <div className="space-y-4 rounded-2xl bg-paper p-4">
        <div className="text-sm font-semibold text-navy-900">Corrigé</div>
        <FilePicker label="Fichier du corrigé (facultatif)" file={correctionFile}
          current={removeCorrection ? undefined : subject?.correction_name || undefined}
          onChange={(f) => { setCorrectionFile(f); if (f) setRemoveCorrection(false); }} onRemove={() => setRemoveCorrection(true)} />
        <Field label="Barème et résultats détaillés (facultatif)" hint="Affiché à l'apprenant lorsqu'il clique sur « Voir la correction ».">
          <textarea className="field min-h-28 font-mono text-[13px]" value={form.correction_text} onChange={set('correction_text')} maxLength={20000}
            placeholder={'Exercice 1 (6 pts)\n601 Achats de marchandises   D 500 000\n4452 TVA récupérable        D  90 000\n401 Fournisseurs                        C 590 000'} />
        </Field>
        <Field label="Épreuve en ligne associée (facultatif)" hint="L'apprenant pourra composer en ligne avec correction automatique et note sur 20.">
          <select className="field" value={form.quiz} onChange={set('quiz')}>
            <option value="">— Aucune</option>
            {quizzes.data?.filter((q) => q.level === form.level).map((q) => <option key={q.id} value={q.id}>{q.title}</option>)}
          </select>
        </Field>
      </div>

      <div className="space-y-2.5">
        <label className="flex items-center gap-2.5 text-sm text-slate-700">
          <input type="checkbox" className="size-4 accent-brand-600" checked={form.is_published} onChange={(e) => setForm((f) => ({ ...f, is_published: e.target.checked }))} />
          Sujet visible par les apprenants
        </label>
        <label className="flex items-center gap-2.5 text-sm text-slate-700">
          <input type="checkbox" className="size-4 accent-money-600" checked={form.correction_released} onChange={(e) => setForm((f) => ({ ...f, correction_released: e.target.checked }))} />
          Correction disponible immédiatement (sinon, publiez-la plus tard en un clic)
        </label>
      </div>

      {progress !== null && (
        <div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full bg-brand-600 transition-all" style={{ width: `${progress}%` }} /></div>
      )}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onDone}>Annuler</Button>
        <Button type="submit" loading={progress !== null} icon={<Upload className="size-4" />}>{subject ? 'Enregistrer' : 'Déposer le sujet'}</Button>
      </div>
    </form>
  );
}
