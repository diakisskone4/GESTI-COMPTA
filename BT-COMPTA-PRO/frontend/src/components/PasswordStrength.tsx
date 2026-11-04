import { Check, X } from 'lucide-react';
import { cx } from './ui';

const RULES: { label: string; test: (p: string) => boolean }[] = [
  { label: '8 caractères minimum', test: (p) => p.length >= 8 },
  { label: 'Une lettre', test: (p) => /[a-zA-Zà-ÿ]/.test(p) },
  { label: 'Un chiffre', test: (p) => /\d/.test(p) },
  { label: 'Un caractère spécial ou 12 caractères', test: (p) => /[^a-zA-Z0-9]/.test(p) || p.length >= 12 },
];

const LEVELS = [
  { label: 'Très faible', color: 'bg-red-500' },
  { label: 'Faible', color: 'bg-red-500' },
  { label: 'Moyen', color: 'bg-amber-500' },
  { label: 'Bon', color: 'bg-brand-600' },
  { label: 'Excellent', color: 'bg-money-600' },
];

export function passwordScore(p: string) {
  return RULES.filter((r) => r.test(p)).length;
}

/** Indicateur visuel ; la validation définitive reste faite par le serveur (règles Django). */
export default function PasswordStrength({ password }: { password: string }) {
  if (!password) return null;
  const score = passwordScore(password);
  const level = LEVELS[score];
  return (
    <div className="mt-2" aria-live="polite">
      <div className="flex gap-1">
        {[1, 2, 3, 4].map((i) => (
          <span key={i} className={cx('h-1.5 flex-1 rounded-full transition', i <= score ? level.color : 'bg-slate-200')} />
        ))}
      </div>
      <div className="mt-1.5 flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-semibold text-slate-600">Robustesse : {level.label}</span>
      </div>
      <ul className="mt-1 grid grid-cols-2 gap-x-3 gap-y-0.5">
        {RULES.map((r) => {
          const ok = r.test(password);
          return (
            <li key={r.label} className={cx('flex items-center gap-1 text-[11.5px]', ok ? 'text-money-700' : 'text-slate-400')}>
              {ok ? <Check className="size-3" /> : <X className="size-3" />} {r.label}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
