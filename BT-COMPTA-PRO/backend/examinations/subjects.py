"""Sujets d'examen déposés par les enseignants : consultation, correction en un clic, suivi des résultats."""
from decimal import Decimal

from django.db.models import Avg, Count, Max, Q
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.audit import log_action
from core.params import int_param
from core.permissions import ReadOnlyOrTeacher, has_role
from core.uploads import content_type_for, validate_upload

from .models import Attempt, ExamSubject, SubjectWork


def is_staff_user(user):
    return has_role(user, 'admin', 'teacher')


class ExamSubjectSerializer(serializers.ModelSerializer):
    subject_file = serializers.FileField(write_only=True, required=False)
    correction_file = serializers.FileField(write_only=True, required=False, allow_null=True)
    remove_correction_file = serializers.BooleanField(write_only=True, required=False, default=False)
    # En multipart, une case absente vaut « faux » pour DRF : on impose explicitement les valeurs par défaut.
    is_published = serializers.BooleanField(required=False, default=True)
    correction_released = serializers.BooleanField(required=False, default=False)
    kind_label = serializers.CharField(source='get_kind_display', read_only=True)
    module_title = serializers.CharField(source='module.title', default='', read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', default='', read_only=True)
    author = serializers.SerializerMethodField()
    has_correction = serializers.BooleanField(read_only=True)
    has_correction_file = serializers.SerializerMethodField()
    my_work = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = ExamSubject
        fields = ('id', 'title', 'level', 'module', 'module_title', 'kind', 'kind_label', 'session', 'duration_minutes',
                  'total_points', 'description', 'subject_file', 'subject_name', 'correction_file', 'correction_name',
                  'remove_correction_file', 'correction_text', 'correction_released', 'quiz', 'quiz_title',
                  'is_published', 'author', 'has_correction', 'has_correction_file', 'my_work', 'stats',
                  'created_at', 'updated_at')
        read_only_fields = ('subject_name', 'correction_name', 'created_at', 'updated_at')
        extra_kwargs = {'title': {'max_length': 200}, 'description': {'max_length': 3000},
                        'correction_text': {'max_length': 20000}}

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and not is_staff_user(request.user) and not instance.correction_released:
            data['correction_text'] = ''  # jamais transmis avant publication de la correction
        return data

    def get_author(self, obj):
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username if obj.uploaded_by else ''

    def get_has_correction_file(self, obj):
        return bool(obj.correction_file)

    def get_my_work(self, obj):
        works = self.context.get('works') or {}
        w = works.get(obj.id)
        if not w:
            return None
        return {'opened_at': w.opened_at, 'correction_viewed_at': w.correction_viewed_at,
                'self_grade': str(w.self_grade) if w.self_grade is not None else None, 'comment': w.comment}

    def get_stats(self, obj):
        request = self.context.get('request')
        if not request or not is_staff_user(request.user):
            return None
        return {'opened': getattr(obj, 'n_opened', 0), 'corrected': getattr(obj, 'n_corrected', 0),
                'graded': getattr(obj, 'n_graded', 0),
                'average': str(round(obj.avg_grade, 2)) if getattr(obj, 'avg_grade', None) is not None else None}

    def validate_subject_file(self, f):
        return validate_upload(f, 'Sujet')

    def validate_correction_file(self, f):
        return validate_upload(f, 'Corrigé') if f else f

    def validate_quiz(self, quiz):
        return quiz

    def validate(self, attrs):
        if not self.instance and not attrs.get('subject_file'):
            raise ValidationError({'subject_file': 'Le fichier du sujet est obligatoire.'})
        if attrs.get('total_points') is not None and not (1 <= attrs['total_points'] <= 200):
            raise ValidationError({'total_points': 'Barème entre 1 et 200 points.'})
        return attrs

    def _apply_files(self, instance, attrs):
        sub = attrs.pop('subject_file', None)
        cor = attrs.pop('correction_file', None)
        remove = attrs.pop('remove_correction_file', False)
        if sub:
            if instance.subject_file:
                instance.subject_file.delete(save=False)
            instance.subject_name = sub.name[:255]
            instance.subject_file = sub
        if remove and instance.correction_file:
            instance.correction_file.delete(save=False)
            instance.correction_file, instance.correction_name = None, ''
        if cor:
            if instance.correction_file:
                instance.correction_file.delete(save=False)
            instance.correction_name = cor.name[:255]
            instance.correction_file = cor

    def create(self, validated_data):
        instance = ExamSubject(uploaded_by=self.context['request'].user)
        self._apply_files(instance, validated_data)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        self._apply_files(instance, validated_data)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance


class ExamSubjectViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSubjectSerializer
    permission_classes = [ReadOnlyOrTeacher]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = ExamSubject.objects.select_related('module', 'quiz', 'uploaded_by')
        user = self.request.user
        if is_staff_user(user):
            qs = qs.annotate(
                n_opened=Count('works', filter=Q(works__opened_at__isnull=False), distinct=True),
                n_corrected=Count('works', filter=Q(works__correction_viewed_at__isnull=False), distinct=True),
                n_graded=Count('works', filter=Q(works__self_grade__isnull=False), distinct=True),
                avg_grade=Avg('works__self_grade'))
        else:
            qs = qs.filter(is_published=True)
        level = self.request.query_params.get('level')
        if level in ('BT1', 'BT2'):
            qs = qs.filter(level=level)
        module = int_param(self.request, 'module')
        if module is not None:
            qs = qs.filter(module_id=module)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.request.user.is_authenticated:
            ctx['works'] = {w.subject_id: w for w in SubjectWork.objects.filter(user=self.request.user)}
        return ctx

    def _check_owner(self, subject):
        user = self.request.user
        if not has_role(user, 'admin') and subject.uploaded_by_id != user.id:
            raise PermissionDenied('Seul l\'auteur du sujet ou un administrateur peut le modifier.')

    def perform_create(self, serializer):
        subject = serializer.save()
        log_action(self.request, 'subject.uploaded', subject, title=subject.title)

    def perform_update(self, serializer):
        self._check_owner(serializer.instance)
        subject = serializer.save()
        log_action(self.request, 'subject.updated', subject)

    def perform_destroy(self, instance):
        self._check_owner(instance)
        log_action(self.request, 'subject.deleted', instance, title=instance.title)
        for f in (instance.subject_file, instance.correction_file):
            if f:
                f.delete(save=False)
        instance.delete()

    # --- Fichiers : jamais d'URL publique, contrôle des droits à chaque téléchargement ----------------

    def _serve(self, field, name):
        if not field:
            raise Http404('Fichier introuvable.')
        try:
            handle = field.open('rb')
        except FileNotFoundError:
            raise Http404('Fichier introuvable sur le serveur.')
        response = FileResponse(handle, content_type=content_type_for(field.name), as_attachment=False, filename=name)
        response['X-Content-Type-Options'] = 'nosniff'
        response['Content-Security-Policy'] = "default-src 'none'; sandbox"
        response['Cache-Control'] = 'private, no-store'
        return response

    def _work(self, subject):
        work, _ = SubjectWork.objects.get_or_create(user=self.request.user, subject=subject)
        return work

    @action(detail=True, methods=['get'], url_path='subject-file', permission_classes=[IsAuthenticated])
    def subject_file(self, request, pk=None):
        subject = self.get_object()
        if not is_staff_user(request.user):
            work = self._work(subject)
            if not work.opened_at:
                work.opened_at = timezone.now()
                work.save(update_fields=['opened_at', 'updated_at'])
        return self._serve(subject.subject_file, subject.subject_name)

    @action(detail=True, methods=['get'], url_path='correction-file', permission_classes=[IsAuthenticated])
    def correction_file(self, request, pk=None):
        subject = self.get_object()
        if not is_staff_user(request.user) and not subject.correction_released:
            raise PermissionDenied('La correction n\'est pas encore disponible.')
        return self._serve(subject.correction_file, subject.correction_name or 'corrige')

    # --- Apprenant : correction en un clic et note obtenue --------------------------------------------

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def correct(self, request, pk=None):
        """Bouton « Voir la correction » : renvoie le corrigé et enregistre la consultation."""
        subject = self.get_object()
        if not subject.has_correction:
            raise ValidationError('Aucun corrigé n\'a encore été déposé pour ce sujet.')
        if not subject.correction_released and not is_staff_user(request.user):
            raise PermissionDenied('L\'enseignant n\'a pas encore publié la correction de ce sujet.')
        if not is_staff_user(request.user):
            work = self._work(subject)
            now = timezone.now()
            work.opened_at = work.opened_at or now
            work.correction_viewed_at = work.correction_viewed_at or now
            work.save()
        return Response({'correction_text': subject.correction_text, 'has_correction_file': bool(subject.correction_file),
                         'correction_name': subject.correction_name, 'total_points': subject.total_points})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def grade(self, request, pk=None):
        """L'apprenant enregistre la note obtenue après comparaison avec le corrigé."""
        subject = self.get_object()
        work = self._work(subject)
        if not work.correction_viewed_at:
            raise ValidationError('Consultez la correction avant d\'enregistrer votre note.')
        try:
            value = Decimal(str(request.data.get('grade', '')).replace(',', '.'))
        except Exception:
            raise ValidationError({'grade': 'Note invalide.'})
        if not (0 <= value <= subject.total_points):
            raise ValidationError({'grade': f'La note doit être comprise entre 0 et {subject.total_points}.'})
        work.self_grade = (value * 20 / subject.total_points).quantize(Decimal('0.01'))
        work.comment = str(request.data.get('comment', ''))[:500]
        work.save()
        return Response({'self_grade': str(work.self_grade), 'comment': work.comment})

    # --- Enseignant : publication de la correction et résultats ---------------------------------------

    @action(detail=True, methods=['post'], url_path='release-correction')
    def release_correction(self, request, pk=None):
        subject = self.get_object()
        self._check_owner(subject)
        release = bool(request.data.get('released', not subject.correction_released))
        if release and not subject.has_correction:
            raise ValidationError('Déposez un corrigé (fichier ou texte) avant de publier la correction.')
        subject.correction_released = release
        subject.save(update_fields=['correction_released', 'updated_at'])
        log_action(request, 'subject.correction_released' if release else 'subject.correction_hidden', subject)
        return Response(self.get_serializer(self.get_queryset().get(pk=subject.pk)).data)

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        if not is_staff_user(request.user):
            raise PermissionDenied()
        subject = self.get_object()
        online = {}
        if subject.quiz_id:
            for row in (Attempt.objects.filter(quiz_id=subject.quiz_id, grade__isnull=False)
                        .values('user_id').annotate(best=Max('grade'), n=Count('id'))):
                online[row['user_id']] = row
        works = subject.works.select_related('user').order_by('user__last_name', 'user__first_name')
        rows, seen = [], set()
        for w in works:
            seen.add(w.user_id)
            o = online.get(w.user_id, {})
            rows.append({'student': w.user.get_full_name() or w.user.username, 'username': w.user.username,
                         'level': w.user.level, 'opened_at': w.opened_at, 'correction_viewed_at': w.correction_viewed_at,
                         'self_grade': str(w.self_grade) if w.self_grade is not None else None, 'comment': w.comment,
                         'online_grade': str(o['best']) if o.get('best') is not None else None, 'online_attempts': o.get('n', 0)})
        if online:
            from django.contrib.auth import get_user_model
            for u in get_user_model().objects.filter(pk__in=[k for k in online if k not in seen]):
                o = online[u.pk]
                rows.append({'student': u.get_full_name() or u.username, 'username': u.username, 'level': u.level,
                             'opened_at': None, 'correction_viewed_at': None, 'self_grade': None, 'comment': '',
                             'online_grade': str(o['best']), 'online_attempts': o['n']})
        grades = [Decimal(r['self_grade']) for r in rows if r['self_grade']] + \
                 [Decimal(r['online_grade']) for r in rows if r['online_grade'] and not r['self_grade']]
        return Response({
            'subject': subject.title,
            'summary': {'students': len(rows), 'opened': sum(1 for r in rows if r['opened_at']),
                        'corrected': sum(1 for r in rows if r['correction_viewed_at']),
                        'average': str(round(sum(grades) / len(grades), 2)) if grades else None,
                        'passed': sum(1 for g in grades if g >= 10), 'graded': len(grades)},
            'rows': rows,
        })
