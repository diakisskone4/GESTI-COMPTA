import { PageHeader } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import SubjectList from '../modules/subjects/SubjectList';

export default function SubjectsPage() {
  const { hasRole } = useAuth();
  const manage = hasRole('teacher', 'admin');
  return (
    <div>
      <PageHeader
        eyebrow="Examens"
        title="Sujets & corrigés"
        subtitle={manage
          ? 'Déposez vos sujets d\'examen et leurs corrigés, publiez la correction en un clic et suivez les résultats de vos apprenants.'
          : 'Entraînez-vous sur les sujets déposés par vos enseignants, puis consultez la correction et enregistrez votre note.'}
      />
      <SubjectList manage={manage} />
    </div>
  );
}
