import { AlertTriangle, BookOpenCheck, Lightbulb, ListOrdered, Sigma, Table2 } from 'lucide-react';
import type { ReactNode } from 'react';
import { Card, cx, formatNumber } from '../../components/ui';
import type { CalcOutput } from '../../types';

function Section({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <Card className="overflow-hidden">
      <div className="flex items-center gap-2 border-b border-slate-100 px-5 py-3.5 text-sm font-semibold text-navy-900 [&_svg]:size-4 [&_svg]:text-brand-600">
        {icon}
        {title}
      </div>
      <div className="p-5">{children}</div>
    </Card>
  );
}

const isNumeric = (v: string) => /^-?[\d\s ]+(,\d+)?$/.test(v.trim()) && v.trim() !== '';

export default function ResultView({ output }: { output: CalcOutput }) {
  const groups = output.entries.reduce<Record<string, CalcOutput['entries']>>((acc, e) => {
    (acc[e.group || 'Écriture'] ||= []).push(e);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {output.results.map((r) => (
          <div key={r.key} className={cx('rounded-2xl border p-4', r.highlight ? 'border-transparent bg-navy-900 text-white shadow-lg shadow-navy-900/20' : 'border-slate-200 bg-white')}>
            <div className={cx('text-xs font-medium', r.highlight ? 'text-white/60' : 'text-slate-500')}>{r.label}</div>
            <div className={cx('num mt-1 text-lg font-bold tracking-tight', r.highlight ? 'text-white' : 'text-navy-900')}>{r.value}</div>
          </div>
        ))}
      </div>

      {output.warnings.length > 0 && (
        <div className="space-y-2 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          {output.warnings.map((w) => (
            <div key={w} className="flex gap-2"><AlertTriangle className="mt-0.5 size-4 shrink-0" /> {w}</div>
          ))}
        </div>
      )}

      {output.formulas.length > 0 && (
        <Section icon={<Sigma />} title="Formules utilisées">
          <ul className="space-y-1.5">
            {output.formulas.map((f) => (
              <li key={f} className="rounded-lg bg-paper px-3 py-2 font-mono text-[13px] text-navy-900">{f}</li>
            ))}
          </ul>
        </Section>
      )}

      {output.steps.length > 0 && (
        <Section icon={<ListOrdered />} title="Étapes détaillées">
          <ol className="space-y-2">
            {output.steps.map((s, i) => (
              <li key={i} className="flex flex-col gap-1 rounded-xl border border-slate-100 px-3.5 py-2.5 sm:flex-row sm:items-center sm:gap-4">
                <span className="grid size-6 shrink-0 place-items-center rounded-full bg-brand-50 text-xs font-bold text-brand-600">{i + 1}</span>
                <span className="font-medium text-slate-700 sm:w-64">{s.label}</span>
                <span className="flex-1 font-mono text-[13px] text-slate-500">{s.detail}</span>
                <span className="num font-semibold text-navy-900">{s.value}</span>
              </li>
            ))}
          </ol>
        </Section>
      )}

      {output.tables.map((t) => (
        <Section key={t.title} icon={<Table2 />} title={t.title}>
          <div className="-m-5 overflow-x-auto">
            <table className="table-base">
              <thead>
                <tr>{t.columns.map((c, i) => <th key={i}>{c}</th>)}</tr>
              </thead>
              <tbody>
                {t.rows.map((row, i) => (
                  <tr key={i} className="hover:bg-slate-50/60">
                    {row.map((v, j) => <td key={j} className={cx(isNumeric(v) && 'num whitespace-nowrap text-right')}>{v}</td>)}
                  </tr>
                ))}
              </tbody>
              {t.footer && (
                <tfoot>
                  <tr>{t.footer.map((v, j) => <td key={j} className={cx(isNumeric(v) && 'num whitespace-nowrap text-right')}>{v}</td>)}</tr>
                </tfoot>
              )}
            </table>
          </div>
        </Section>
      ))}

      {output.entries.length > 0 && (
        <Section icon={<BookOpenCheck />} title="Écritures comptables">
          <div className="space-y-5">
            {Object.entries(groups).map(([group, lines]) => {
              const td = lines.reduce((s, l) => s + Number(l.debit || 0), 0);
              const tc = lines.reduce((s, l) => s + Number(l.credit || 0), 0);
              return (
                <div key={group}>
                  <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{group}</div>
                  <div className="overflow-x-auto rounded-xl border border-slate-200">
                    <table className="table-base">
                      <thead><tr><th>Débit</th><th>Crédit</th><th>Intitulé</th><th className="text-right">Débit</th><th className="text-right">Crédit</th></tr></thead>
                      <tbody className="ledger-rule">
                        {lines.map((l, i) => (
                          <tr key={i}>
                            <td className="font-mono font-semibold text-navy-900">{l.debit ? l.account : ''}</td>
                            <td className="font-mono font-semibold text-navy-900">{l.credit ? l.account : ''}</td>
                            <td className={cx(l.credit && 'pl-8')}>{l.label}</td>
                            <td className="num text-right">{formatNumber(l.debit)}</td>
                            <td className="num text-right">{formatNumber(l.credit)}</td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot><tr><td colSpan={3}>Totaux</td><td className="num text-right">{formatNumber(td)}</td><td className="num text-right">{formatNumber(tc)}</td></tr></tfoot>
                    </table>
                  </div>
                </div>
              );
            })}
          </div>
        </Section>
      )}

      {output.interpretation.length > 0 && (
        <Section icon={<Lightbulb />} title="Interprétation pédagogique">
          <ul className="space-y-2 text-sm leading-relaxed text-slate-700">
            {output.interpretation.map((t) => <li key={t} className="flex gap-2"><span className="mt-2 size-1.5 shrink-0 rounded-full bg-money-600" />{t}</li>)}
          </ul>
        </Section>
      )}
    </div>
  );
}
