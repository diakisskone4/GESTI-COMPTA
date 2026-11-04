import { BarChart3, Eye, EyeOff, Plus, Trash2 } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Alert, Badge, Button, Card, Field, formatDate, formatNumber, Modal, PageHeader, Spinner, Tabs } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import SubjectList from '../modules/subjects/SubjectList';
import { api, errorMessage } from '../services/api';
import type { Attempt, Module, Quiz } from '../types';

type Tab = 'subjects' | 'quizzes' | 'results';

interface DraftQuestion { kind: 'mcq' | 'numeric'; text: string; explanation: string; points: string; answer_numeric: string; choices: { text: string; is_correct: boolean }[] }
const blank = (): DraftQuestion => ({ kind: 'mcq', text: '', explanation: '', points: '1', answer_numeric: '', choices: [{ text: '', is_correct: true }, { text: '', is_correct: false }] });

function QuizCreator({ onDone }: { onDone: () => void }) {
  const modules = useFetch<Module[]>('/pedagogy/modules/');
  const [quiz, setQuiz] = useState({ title: '', level: 'BT1', module: '', kind: 'quiz', duration_minutes: '20', description: '' });
  const [questions, setQuestions] = useState<DraftQuestion[]>([blank()]);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const upd = (i: number, patch: Partial<DraftQuestion>) => setQuestions((qs) => qs.map((q, j) => (j === i ? { ...q, ...patch } : q)));

  async function save(e: FormEvent) {
    e.preventDefault();
    setErr('');
    setBusy(true);
    try {
      const { data } = await api.post<Quiz>('/exams/quizzes/', { ...quiz, module: quiz.module || null, duration_minutes: Number(quiz.duration_minutes) });
      for (const [i, q] of questions.entries()) {
        await api.post('/exams/questions/', {
          quiz: data.id, order: i + 1, kind: q.kind, text: q.text, explanation: q.explanation, points: q.points,
          ...(q.kind === 'mcq' ? { choices: q.choices.filter((c) => c.text) } : { answer_numeric: q.answer_numeric.replace(',', '.'), choices: [] }),
        });
      }
      onDone();
    } catch (error) {
      setErr(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save} className="space-y-4">
      {err && <Alert tone="error">{err}</Alert>}
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Titre"><input className="field" value={quiz.title} onChange={(e) => setQuiz({ ...quiz, title: e.target.value })} required /></Field>
        <Field label="Type">
          <select className="field" value={quiz.kind} onChange={(e) => setQuiz({ ...quiz, kind: e.target.value })}>
            <option value="quiz">Quiz d'entraînement</option><option value="evaluation">Évaluation</option><option value="mock">Examen blanc</option>
          </select>
        </Field>
        <Field label="Niveau">
          <select className="field" value={quiz.level} onChange={(e) => setQuiz({ ...quiz, level: e.target.value, module: '' })}><option>BT1</option><option>BT2</option></select>
        </Field>
        <Field label="Module">
          <select className="field" value={quiz.module} onChange={(e) => setQuiz({ ...quiz, module: e.target.value })}>
            <option value="">— Aucun (épreuve transversale)</option>
            {modules.data?.filter((m) => m.level_code === quiz.level).map((m) => <option key={m.id} value={m.id}>{m.code} — {m.title}</option>)}
          </select>
        </Field>
        <Field label="Durée (minutes)"><input className="field" type="number" min={1} value={quiz.duration_minutes} onChange={(e) => setQuiz({ ...quiz, duration_minutes: e.target.value })} /></Field>
      </div>
      {questions.map((q, i) => (
        <Card key={i} className="space-y-3 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-navy-900">Question {i + 1}</span>
            <div className="flex gap-2">
              <select className="field-sm w-auto" value={q.kind} onChange={(e) => upd(i, { kind: e.target.value as DraftQuestion['kind'] })}><option value="mcq">QCM</option><option value="numeric">Calcul</option></select>
              <input className="field-sm w-20" value={q.points} onChange={(e) => upd(i, { points: e.target.value })} aria-label="Points" title="Points" />
              <button type="button" onClick={() => setQuestions((qs) => qs.filter((_, j) => j !== i))} className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600" aria-label="Supprimer"><Trash2 className="size-4" /></button>
            </div>
          </div>
          <textarea className="field min-h-20" placeholder="Énoncé" value={q.text} onChange={(e) => upd(i, { text: e.target.value })} required />
          {q.kind === 'mcq' ? (
            <div className="space-y-2">
              {q.choices.map((c, j) => (
                <div key={j} className="flex items-center gap-2">
                  <input type="checkbox" className="size-4 accent-money-600" checked={c.is_correct} onChange={(e) => upd(i, { choices: q.choices.map((x, k) => (k === j ? { ...x, is_correct: e.target.checked } : x)) })} title="Bonne réponse" />
                  <input className="field-sm" placeholder={`Choix ${j + 1}`} value={c.text} onChange={(e) => upd(i, { choices: q.choices.map((x, k) => (k === j ? { ...x, text: e.target.value } : x)) })} />
                </div>
              ))}
              <Button type="button" size="sm" variant="ghost" onClick={() => upd(i, { choices: [...q.choices, { text: '', is_correct: false }] })} icon={<Plus className="size-4" />}>Choix</Button>
            </div>
          ) : (
            <input className="field num max-w-xs" placeholder="Réponse attendue" value={q.answer_numeric} onChange={(e) => upd(i, { answer_numeric: e.target.value })} required />
          )}
          <textarea className="field min-h-16" placeholder="Correction détaillée (affichée après remise)" value={q.explanation} onChange={(e) => upd(i, { explanation: e.target.value })} />
        </Card>
      ))}
      <div className="flex flex-wrap justify-between gap-2">
        <Button type="button" variant="secondary" onClick={() => setQuestions((qs) => [...qs, blank()])} icon={<Plus className="size-4" />}>Ajouter une question</Button>
        <Button type="submit" loading={busy}>Publier</Button>
      </div>
    </form>
  );
}

export default function TeacherPage() {
  const [tab, setTab] = useState<Tab>('subjects');
  const quizzes = useFetch<Quiz[]>('/exams/quizzes/');
  const results = useFetch<Attempt[]>(tab === 'results' ? '/exams/attempts/?all=1' : null);
  const [creating, setCreating] = useState(false);
  const [stats, setStats] = useState<{ quiz: Quiz; data: { stats: { avg: string | null; best: string | null; n: number }; attempts: Attempt[] } } | null>(null);
  const [msg, setMsg] = useState('');

  async function togglePublish(q: Quiz) {
    try {
      await api.patch(`/exams/quizzes/${q.id}/`, { is_published: !q.is_published });
      quizzes.reload();
    } catch (e) {
      setMsg(errorMessage(e));
    }
  }

  return (
    <div>
      <PageHeader eyebrow="Espace enseignant" title="Épreuves et suivi des apprenants"
        subtitle="Déposez vos sujets d'examen avec leurs corrigés, créez des épreuves en ligne et suivez les résultats."
        actions={tab === 'quizzes' ? <Button onClick={() => setCreating(true)} icon={<Plus className="size-4" />}>Nouvelle épreuve en ligne</Button> : undefined} />
      <Tabs<Tab> value={tab} onChange={setTab} items={[
        { value: 'subjects', label: 'Sujets d\'examen' },
        { value: 'quizzes', label: 'Épreuves en ligne' },
        { value: 'results', label: 'Résultats des épreuves en ligne' },
      ]} />
      {tab === 'subjects' && <SubjectList manage />}
      {msg && <Alert tone="error" onClose={() => setMsg('')}>{msg}</Alert>}
      {tab === 'quizzes' && (quizzes.loading ? <Spinner /> : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead><tr><th>Épreuve</th><th>Niveau</th><th>Type</th><th>Questions</th><th>Statut</th><th /></tr></thead>
              <tbody>
                {quizzes.data?.map((q) => (
                  <tr key={q.id}>
                    <td className="font-medium text-navy-900">{q.title}<div className="text-xs font-normal text-slate-500">{q.module_title}</div></td>
                    <td><Badge tone={q.level === 'BT1' ? 'blue' : 'green'}>{q.level}</Badge></td>
                    <td className="text-slate-600">{q.kind_label}</td>
                    <td className="num">{q.questions_count}</td>
                    <td>{q.is_published ? <Badge tone="green">Publiée</Badge> : <Badge>Masquée</Badge>}</td>
                    <td className="whitespace-nowrap text-right">
                      <Button size="sm" variant="ghost" onClick={async () => setStats({ quiz: q, data: (await api.get(`/exams/quizzes/${q.id}/results/`)).data })} icon={<BarChart3 className="size-4" />}>Résultats</Button>
                      <Button size="sm" variant="ghost" onClick={() => togglePublish(q)} aria-label={q.is_published ? 'Masquer' : 'Publier'}>{q.is_published ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ))}
      {tab === 'results' && (results.loading ? <Spinner /> : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead><tr><th>Apprenant</th><th>Épreuve</th><th>Date</th><th className="text-right">Note</th></tr></thead>
              <tbody>
                {results.data?.map((a) => (
                  <tr key={a.id}><td className="font-medium text-navy-900">{a.full_name}</td><td>{a.quiz_title}</td><td>{formatDate(a.finished_at)}</td>
                    <td className="text-right"><Badge tone={Number(a.grade) >= 10 ? 'green' : 'red'}>{formatNumber(a.grade, 2)}/20</Badge></td></tr>
                ))}
                {results.data?.length === 0 && <tr><td colSpan={4} className="py-8 text-center text-slate-500">Aucune copie pour le moment.</td></tr>}
              </tbody>
            </table>
          </div>
        </Card>
      ))}
      <Modal open={creating} onClose={() => setCreating(false)} title="Nouvelle épreuve" wide>
        {creating && <QuizCreator onDone={() => { setCreating(false); quizzes.reload(); }} />}
      </Modal>
      <Modal open={!!stats} onClose={() => setStats(null)} title={stats?.quiz.title ?? ''} wide>
        {stats && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3 text-center">
              {[['Copies', stats.data.stats.n], ['Moyenne', stats.data.stats.avg ? formatNumber(stats.data.stats.avg, 2) : '—'], ['Meilleure', stats.data.stats.best ? formatNumber(stats.data.stats.best, 2) : '—']].map(([k, v]) => (
                <div key={k as string} className="rounded-xl bg-paper p-3"><div className="text-xs text-slate-500">{k}</div><div className="num text-lg font-bold text-navy-900">{v}</div></div>
              ))}
            </div>
            <ul className="divide-y divide-slate-100">
              {stats.data.attempts.map((a) => <li key={a.id} className="flex justify-between py-2 text-sm"><span>{a.full_name} · {formatDate(a.finished_at)}</span><span className="num font-semibold">{formatNumber(a.grade, 2)}/20</span></li>)}
            </ul>
          </div>
        )}
      </Modal>
    </div>
  );
}
