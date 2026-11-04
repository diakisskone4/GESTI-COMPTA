import { cx } from './ui';

export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={cx('size-9 shrink-0', className)} aria-hidden="true">
      <rect width="64" height="64" rx="14" fill="#102B55" />
      <rect x="0.75" y="0.75" width="62.5" height="62.5" rx="13.5" fill="none" stroke="rgba(255,255,255,0.16)" strokeWidth="1.5" />
      <text x="32" y="38" textAnchor="middle" fontFamily="Inter Variable, Arial, sans-serif" fontWeight="800" fontSize="25" fill="#fff">
        BT
      </text>
      <rect x="12" y="44" width="40" height="5" rx="2.5" fill="#16A36A" />
      <circle cx="50" cy="15" r="5" fill="#1683D8" />
    </svg>
  );
}

export function Logo({ light, className }: { light?: boolean; className?: string }) {
  return (
    <span className={cx('flex items-center gap-2.5', className)}>
      <LogoMark />
      <span className="leading-tight">
        <span className={cx('block text-[15px] font-extrabold tracking-tight', light ? 'text-white' : 'text-navy-900')}>
          BT COMPTA <span className="text-money-600">PRO</span>
        </span>
        <span className={cx('block text-[11px] font-medium', light ? 'text-white/55' : 'text-slate-500')}>SYSCOHADA · Mali</span>
      </span>
    </span>
  );
}
