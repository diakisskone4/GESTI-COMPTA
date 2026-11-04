import { Plus, Trash2 } from 'lucide-react';
import type { FieldSpec } from '../../types';
import { Button, cx } from '../../components/ui';

export type FormValues = Record<string, unknown>;
type Row = Record<string, string>;

export function initialValues(fields: FieldSpec[]): FormValues {
  const values: FormValues = {};
  for (const f of fields) {
    if (f.type === 'table') values[f.name] = Array.isArray(f.default) ? (f.default as Row[]).map((r) => ({ ...r })) : [];
    else values[f.name] = f.default === undefined || f.default === null ? '' : String(f.default);
  }
  return values;
}

function inputMode(type: string) {
  return type === 'money' || type === 'number' || type === 'percent' ? 'decimal' : type === 'integer' ? 'numeric' : undefined;
}

function suffix(type: string) {
  if (type === 'money') return 'FCFA';
  if (type === 'percent') return '%';
  return null;
}

function Scalar({ field, value, onChange, small }: { field: FieldSpec; value: string; onChange: (v: string) => void; small?: boolean }) {
  const cls = small ? 'field-sm' : 'field';
  if (field.type === 'select') {
    return (
      <select className={cls} value={value} onChange={(e) => onChange(e.target.value)}>
        {!small && !field.options?.some((o) => o.value === value) && <option value="">—</option>}
        {small && <option value="">—</option>}
        {field.options?.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    );
  }
  if (field.type === 'date') return <input type="date" className={cls} value={value} onChange={(e) => onChange(e.target.value)} />;
  const unit = !small && suffix(field.type);
  return (
    <div className="relative">
      <input
        className={cx(cls, unit && 'pr-14', field.type !== 'text' && 'num text-right')}
        inputMode={inputMode(field.type)}
        value={value}
        placeholder={field.type === 'text' ? '' : '0'}
        onChange={(e) => onChange(e.target.value)}
      />
      {unit && <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-xs font-medium text-slate-400">{unit}</span>}
    </div>
  );
}

function TableField({ field, rows, onChange }: { field: FieldSpec; rows: Row[]; onChange: (rows: Row[]) => void }) {
  const cols = field.columns ?? [];
  const update = (i: number, name: string, v: string) => onChange(rows.map((r, j) => (j === i ? { ...r, [name]: v } : r)));
  const add = () => onChange([...rows, Object.fromEntries(cols.map((c) => [c.name, '']))]);
  const remove = (i: number) => onChange(rows.filter((_, j) => j !== i));
  return (
    <div className="min-w-0 sm:col-span-2">
      <div className="mb-1.5 flex items-center justify-between">
        <span className="label mb-0">{field.label}</span>
        <Button type="button" size="sm" variant="secondary" onClick={add} icon={<Plus className="size-3.5" />}>Ligne</Button>
      </div>
      {/* Tableau sur grand écran, fiches empilées sur téléphone */}
      <div className="overflow-x-auto rounded-xl border-slate-200 sm:border">
        <table className="w-full text-sm max-sm:block sm:min-w-[560px]">
          <thead className="max-sm:hidden">
            <tr className="bg-slate-50 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              <th className="w-8 px-2 py-2">#</th>
              {cols.map((c) => <th key={c.name} className="px-2 py-2">{c.label}</th>)}
              <th className="w-10" />
            </tr>
          </thead>
          <tbody className="max-sm:block max-sm:space-y-2.5">
            {rows.map((row, i) => (
              <tr key={i} className="border-slate-100 max-sm:relative max-sm:grid max-sm:grid-cols-2 max-sm:gap-x-2 max-sm:gap-y-2 max-sm:rounded-xl max-sm:border max-sm:border-slate-200 max-sm:bg-paper/60 max-sm:p-3 sm:border-t">
                <td className="num px-2 py-1.5 text-xs text-slate-400 max-sm:col-span-2 max-sm:p-0 max-sm:font-semibold"><span className="sm:hidden">Ligne </span>{i + 1}</td>
                {cols.map((c) => (
                  <td key={c.name} className={cx('px-1.5 py-1.5 max-sm:min-w-0 max-sm:p-0', (c.type === 'text' || c.type === 'select') && cols.length !== 2 && 'max-sm:col-span-2')}>
                    <span className="mb-1 block text-xs font-medium text-slate-500 sm:hidden">{c.label}</span>
                    <Scalar field={c} small value={row[c.name] ?? ''} onChange={(v) => update(i, c.name, v)} />
                  </td>
                ))}
                <td className="px-1.5 max-sm:absolute max-sm:right-1 max-sm:top-1 max-sm:p-0">
                  <button type="button" onClick={() => remove(i)} className="rounded-lg p-1.5 text-slate-400 max-sm:p-2 hover:bg-red-50 hover:text-red-600" aria-label="Supprimer la ligne">
                    <Trash2 className="size-4" />
                  </button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr className="max-sm:block"><td colSpan={cols.length + 2} className="px-3 py-6 text-center max-sm:block text-sm text-slate-400">Aucune ligne. Cliquez sur « Ligne » pour en ajouter.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function DynamicForm({ fields, values, onChange, errorField }: { fields: FieldSpec[]; values: FormValues; onChange: (v: FormValues) => void; errorField?: string | null }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {fields.map((f) =>
        f.type === 'table' ? (
          <TableField key={f.name} field={f} rows={(values[f.name] as Row[]) ?? []} onChange={(rows) => onChange({ ...values, [f.name]: rows })} />
        ) : (
          <label key={f.name} className={cx('block', errorField === f.name && '[&_.field]:border-red-400')}>
            <span className="label">
              {f.label}
              {f.required && <span className="text-red-500"> *</span>}
            </span>
            <Scalar field={f} value={String(values[f.name] ?? '')} onChange={(v) => onChange({ ...values, [f.name]: v })} />
            {f.help && <span className="mt-1 block text-xs leading-snug text-slate-500">{f.help}</span>}
          </label>
        ),
      )}
    </div>
  );
}
