import { AlertTriangle, CheckCircle2, Info, Loader2, X } from 'lucide-react';
import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { Link } from 'react-router-dom';

export function cx(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}

const NUMBER = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 });

/** Formate un montant (string Decimal ou number) en français : 1 234 567,5 */
export function formatNumber(value: string | number | null | undefined, digits?: number) {
  if (value === null || value === undefined || value === '') return '';
  const n = typeof value === 'number' ? value : Number(value);
  if (Number.isNaN(n)) return String(value);
  return digits === undefined ? NUMBER.format(n) : n.toLocaleString('fr-FR', { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function formatDate(value: string | null | undefined) {
  if (!value) return '';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString('fr-FR');
}

type Variant = 'primary' | 'secondary' | 'success' | 'ghost' | 'danger';

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-brand-600 text-white hover:bg-brand-700 shadow-sm shadow-brand-600/20',
  success: 'bg-money-600 text-white hover:bg-money-700 shadow-sm shadow-money-600/20',
  secondary: 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50',
  ghost: 'text-slate-600 hover:bg-slate-100',
  danger: 'border border-red-200 bg-white text-red-600 hover:bg-red-50',
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: ReactNode;
}

export function Button({ variant = 'primary', size = 'md', loading, icon, className, children, disabled, ...props }: ButtonProps) {
  const sizes = { sm: 'h-10 lg:h-8 px-3 text-[13px] gap-1.5', md: 'h-10 px-4 text-sm gap-2', lg: 'h-12 px-6 text-[15px] gap-2' };
  return (
    <button
      className={cx(
        'inline-flex select-none items-center justify-center rounded-xl font-semibold transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-brand-600/25 disabled:cursor-not-allowed disabled:opacity-60',
        sizes[size],
        VARIANTS[variant],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Loader2 className="size-4 animate-spin" /> : icon}
      {children}
    </button>
  );
}

export function ButtonLink({ to, variant = 'primary', className, children, icon }: { to: string; variant?: Variant; className?: string; children: ReactNode; icon?: ReactNode }) {
  return (
    <Link to={to} className={cx('inline-flex h-10 items-center justify-center gap-2 rounded-xl px-4 text-sm font-semibold transition', VARIANTS[variant], className)}>
      {icon}
      {children}
    </Link>
  );
}

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cx('card', className)}>{children}</div>;
}

export function PageHeader({ title, subtitle, eyebrow, actions }: { title: string; subtitle?: ReactNode; eyebrow?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {eyebrow && <div className="mb-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-brand-600">{eyebrow}</div>}
        <h1 className="text-2xl font-bold tracking-tight text-navy-900 sm:text-[28px]">{title}</h1>
        {subtitle && <p className="mt-1.5 max-w-3xl text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function Badge({ children, tone = 'slate', className }: { children: ReactNode; tone?: 'slate' | 'blue' | 'green' | 'amber' | 'red' | 'navy'; className?: string }) {
  const tones = {
    slate: 'bg-slate-100 text-slate-600',
    blue: 'bg-brand-50 text-brand-700',
    green: 'bg-money-50 text-money-700',
    amber: 'bg-amber-50 text-amber-700',
    red: 'bg-red-50 text-red-600',
    navy: 'bg-navy-900 text-white',
  };
  return <span className={cx('inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold', tones[tone], className)}>{children}</span>;
}

export function Spinner({ label = 'Chargement…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-sm text-slate-500">
      <Loader2 className="size-5 animate-spin text-brand-600" /> {label}
    </div>
  );
}

export function Alert({ tone = 'info', children, onClose }: { tone?: 'info' | 'success' | 'warning' | 'error'; children: ReactNode; onClose?: () => void }) {
  const styles = {
    info: ['border-brand-100 bg-brand-50 text-navy-800', Info],
    success: ['border-money-600/20 bg-money-50 text-money-700', CheckCircle2],
    warning: ['border-amber-200 bg-amber-50 text-amber-800', AlertTriangle],
    error: ['border-red-200 bg-red-50 text-red-700', AlertTriangle],
  } as const;
  const [cls, Icon] = styles[tone];
  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={cx('flex items-start gap-3 rounded-xl border px-4 py-3 text-sm', cls)}>
      <Icon className="mt-0.5 size-4 shrink-0" />
      <div className="min-w-0 flex-1">{children}</div>
      {onClose && (
        <button onClick={onClose} className="opacity-60 hover:opacity-100" aria-label="Fermer">
          <X className="size-4" />
        </button>
      )}
    </div>
  );
}

export function EmptyState({ icon, title, text, action }: { icon: ReactNode; title: string; text?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center px-6 py-14 text-center">
      <div className="mb-4 grid size-14 place-items-center rounded-2xl bg-brand-50 text-brand-600">{icon}</div>
      <h3 className="text-base font-semibold text-navy-900">{title}</h3>
      {text && <p className="mt-1 max-w-md text-sm text-slate-500">{text}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function Stat({ label, value, hint, icon, tone = 'blue' }: { label: string; value: ReactNode; hint?: ReactNode; icon?: ReactNode; tone?: 'blue' | 'green' | 'navy' | 'amber' }) {
  const tones = { blue: 'bg-brand-50 text-brand-600', green: 'bg-money-50 text-money-600', navy: 'bg-navy-900 text-white', amber: 'bg-amber-50 text-amber-600' };
  return (
    <Card className="p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[13px] font-medium text-slate-500">{label}</div>
          <div className="num mt-2 text-2xl font-bold tracking-tight text-navy-900">{value}</div>
          {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
        </div>
        {icon && <div className={cx('hidden size-10 shrink-0 place-items-center rounded-xl sm:grid', tones[tone])}>{icon}</div>}
      </div>
    </Card>
  );
}

export function Progress({ value, className }: { value: number; className?: string }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className={cx('h-2 overflow-hidden rounded-full bg-slate-100', className)} role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
      <div className="h-full rounded-full bg-gradient-to-r from-brand-600 to-money-600 transition-all" style={{ width: `${pct}%` }} />
    </div>
  );
}

export function Tabs<T extends string>({ value, onChange, items }: { value: T; onChange: (v: T) => void; items: { value: T; label: string; icon?: ReactNode }[] }) {
  return (
    <div className="no-print -mx-1 mb-5 flex gap-1 overflow-x-auto px-1 pb-1 [scrollbar-width:none]">
      {items.map((it) => (
        <button
          key={it.value}
          onClick={() => onChange(it.value)}
          className={cx(
            'inline-flex shrink-0 items-center gap-2 rounded-xl px-3.5 py-2 text-sm font-medium transition',
            value === it.value ? 'bg-navy-900 text-white shadow-sm' : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50',
          )}
        >
          {it.icon}
          {it.label}
        </button>
      ))}
    </div>
  );
}

export function Field({ label, children, hint, error }: { label: string; children: ReactNode; hint?: string; error?: string }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
      {hint && !error && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
    </label>
  );
}

export function Modal({ open, onClose, title, children, wide }: { open: boolean; onClose: () => void; title: string; children: ReactNode; wide?: boolean }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-navy-950/50 p-0 backdrop-blur-sm sm:items-center sm:p-4" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cx('sheet max-h-[92dvh] w-full overflow-y-auto rounded-t-3xl bg-white pb-[env(safe-area-inset-bottom)] shadow-2xl sm:rounded-3xl', wide ? 'sm:max-w-4xl' : 'sm:max-w-lg')}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-100 bg-white/95 px-5 py-4 backdrop-blur">
          <h2 className="text-base font-semibold text-navy-900">{title}</h2>
          <button onClick={onClose} className="-mr-1.5 grid size-10 place-items-center rounded-lg text-slate-500 hover:bg-slate-100" aria-label="Fermer">
            <X className="size-5" />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}
