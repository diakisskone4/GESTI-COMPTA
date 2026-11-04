import { AlertTriangle } from 'lucide-react';
import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';
import { Button } from './ui';

interface ConfirmOptions {
  title: string;
  message: ReactNode;
  confirmLabel?: string;
  danger?: boolean;
}

const ConfirmContext = createContext<(o: ConfirmOptions) => Promise<boolean>>(async () => false);

/** Remplace window.confirm par une boîte de dialogue cohérente avec l'interface. */
export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [options, setOptions] = useState<ConfirmOptions | null>(null);
  const resolver = useRef<(v: boolean) => void>(() => undefined);

  const confirm = useCallback((o: ConfirmOptions) => {
    setOptions(o);
    return new Promise<boolean>((resolve) => {
      resolver.current = resolve;
    });
  }, []);

  const close = (value: boolean) => {
    resolver.current(value);
    setOptions(null);
  };

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {options && (
        <div className="fixed inset-0 z-[60] flex items-end justify-center bg-navy-950/50 backdrop-blur-sm sm:items-center sm:p-4" onClick={() => close(false)}>
          <div role="alertdialog" aria-modal="true" aria-labelledby="confirm-title" className="w-full rounded-t-3xl bg-white p-6 shadow-2xl sm:max-w-md sm:rounded-3xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex gap-4">
              <span className={`grid size-11 shrink-0 place-items-center rounded-2xl ${options.danger ? 'bg-red-50 text-red-600' : 'bg-brand-50 text-brand-600'}`}>
                <AlertTriangle className="size-5" />
              </span>
              <div>
                <h2 id="confirm-title" className="font-semibold text-navy-900">{options.title}</h2>
                <div className="mt-1.5 text-sm text-slate-600">{options.message}</div>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="secondary" onClick={() => close(false)} autoFocus>Annuler</Button>
              <Button variant={options.danger ? 'danger' : 'primary'} className={options.danger ? '!bg-red-600 !text-white hover:!bg-red-700' : ''} onClick={() => close(true)}>
                {options.confirmLabel ?? 'Confirmer'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  return useContext(ConfirmContext);
}
