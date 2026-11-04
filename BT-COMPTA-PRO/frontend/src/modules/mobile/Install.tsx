import { Download, EllipsisVertical, Share, SquarePlus, X } from 'lucide-react';
import { useState, useSyncExternalStore, type ReactNode } from 'react';
import { Modal, cx } from '../../components/ui';
import { canPrompt, getPlatform, isInstalled, promptInstall, subscribe } from '../../services/install';

const DISMISS_KEY = 'btc.install.dismissed';

function wasDismissed() {
  try {
    return localStorage.getItem(DISMISS_KEY) === '1';
  } catch {
    return false;
  }
}

function Step({ n, children }: { n: number; children: ReactNode }) {
  return (
    <li className="flex items-start gap-3 text-sm text-slate-700">
      <span className="grid size-6 shrink-0 place-items-center rounded-full bg-navy-900 text-xs font-bold text-white">{n}</span>
      <span className="pt-0.5">{children}</span>
    </li>
  );
}

const Key = ({ children }: { children: ReactNode }) => (
  <span className="mx-0.5 inline-flex items-center gap-1 rounded-md bg-slate-100 px-1.5 py-0.5 align-middle text-xs font-semibold text-navy-900 [&_svg]:size-3.5">{children}</span>
);

/** Instructions manuelles : iPhone et iPad n'autorisent pas l'installation par un bouton. */
function Guide({ open, onClose }: { open: boolean; onClose: () => void }) {
  const platform = getPlatform();
  return (
    <Modal open={open} onClose={onClose} title="Installer BT COMPTA PRO">
      <ol className="space-y-4">
        {platform === 'ios' ? (
          <>
            <Step n={1}>Ouvrez cette page dans <strong>Safari</strong>.</Step>
            <Step n={2}>Touchez le bouton <Key><Share /> Partager</Key> dans la barre de Safari.</Step>
            <Step n={3}>Choisissez <Key><SquarePlus /> Sur l'écran d'accueil</Key>.</Step>
            <Step n={4}>Touchez <Key>Ajouter</Key> : l'icône apparaît avec vos applications.</Step>
          </>
        ) : platform === 'android' ? (
          <>
            <Step n={1}>Ouvrez cette page dans <strong>Chrome</strong> (ou Samsung Internet).</Step>
            <Step n={2}>Touchez le menu <Key><EllipsisVertical /></Key> en haut à droite.</Step>
            <Step n={3}>Choisissez <Key>Installer l'application</Key> ou <Key>Ajouter à l'écran d'accueil</Key>.</Step>
          </>
        ) : (
          <>
            <Step n={1}>Dans Chrome ou Edge, cliquez sur l'icône d'installation à droite de la barre d'adresse.</Step>
            <Step n={2}>Confirmez avec <Key>Installer</Key>.</Step>
            <Step n={3}>Sur téléphone ou tablette, ouvrez ce site pour l'installer sur l'appareil.</Step>
          </>
        )}
      </ol>
    </Modal>
  );
}

export function useInstall() {
  const prompt = useSyncExternalStore(subscribe, canPrompt);
  const [guide, setGuide] = useState(false);
  const start = async () => {
    if (prompt) await promptInstall();
    else setGuide(true);
  };
  return { installed: isInstalled(), start, guideNode: <Guide open={guide} onClose={() => setGuide(false)} /> };
}

/** Widget d'installation, masqué une fois l'application installée ou la carte fermée. */
export function InstallCard({ className }: { className?: string }) {
  const { installed, start, guideNode } = useInstall();
  const [hidden, setHidden] = useState(wasDismissed);
  if (installed || hidden) return null;
  const dismiss = () => {
    setHidden(true);
    try {
      localStorage.setItem(DISMISS_KEY, '1');
    } catch {
      /* préférence non conservée */
    }
  };
  return (
    <div className={cx('relative flex items-center gap-3 rounded-2xl bg-gradient-to-r from-brand-700 to-brand-600 p-4 text-white', className)}>
      <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-white/15"><Download className="size-5" /></span>
      <div className="min-w-0 flex-1 pr-5">
        <div className="text-sm font-bold">Installez l'application</div>
        <div className="text-xs text-white/80">Accès direct depuis votre écran d'accueil.</div>
      </div>
      <button onClick={start} className="h-9 shrink-0 rounded-lg bg-white px-3.5 text-[13px] font-bold text-navy-900">Installer</button>
      <button onClick={dismiss} className="absolute right-1 top-1 grid size-7 place-items-center text-white/70" aria-label="Masquer"><X className="size-4" /></button>
      {guideNode}
    </div>
  );
}
