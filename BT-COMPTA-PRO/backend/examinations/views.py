from datetime import timedelta

from django.db.models import Avg, Count, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.params import int_param
from core.permissions import ReadOnlyOrTeacher, has_role

from .grading import grade_attempt
from .models import Attempt, Question, Quiz
from .serializers import AttemptSerializer, QuestionPublicSerializer, QuestionSerializer, QuizSerializer

GRACE = timedelta(seconds=30)


class QuizViewSet(viewsets.ModelViewSet):
    serializer_class = QuizSerializer
    permission_classes = [ReadOnlyOrTeacher]

    def get_queryset(self):
        qs = Quiz.objects.select_related('module').prefetch_related('questions', 'attempts')
        if not has_role(self.request.user, 'admin', 'teacher'):
            qs = qs.filter(is_published=True)
        p = self.request.query_params
        if p.get('level'):
            qs = qs.filter(level=p['level'])
        if p.get('kind'):
            qs = qs.filter(kind=p['kind'])
        module = int_param(self.request, 'module')
        if module is not None:
            qs = qs.filter(module_id=module)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def start(self, request, pk=None):
        quiz = self.get_object()
        if not quiz.questions.exists():
            raise ValidationError('Ce quiz ne contient encore aucune question.')
        attempt = Attempt.objects.create(user=request.user, quiz=quiz)
        questions = quiz.questions.prefetch_related('choices')
        return Response({
            'attempt': attempt.id,
            'started_at': attempt.started_at,
            'deadline': attempt.started_at + timedelta(minutes=quiz.duration_minutes),
            'quiz': QuizSerializer(quiz, context={'request': request}).data,
            'questions': QuestionPublicSerializer(questions, many=True).data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='questions-admin', permission_classes=[ReadOnlyOrTeacher])
    def questions_admin(self, request, pk=None):
        if not has_role(request.user, 'admin', 'teacher'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        quiz = self.get_object()
        return Response(QuestionSerializer(quiz.questions.prefetch_related('choices'), many=True).data)

    @action(detail=True, methods=['get'], permission_classes=[ReadOnlyOrTeacher])
    def results(self, request, pk=None):
        if not has_role(request.user, 'admin', 'teacher'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        quiz = self.get_object()
        attempts = quiz.attempts.filter(grade__isnull=False).select_related('user', 'quiz')
        stats = attempts.aggregate(avg=Avg('grade'), best=Max('grade'), n=Count('id'))
        return Response({'stats': stats, 'attempts': AttemptSerializer(attempts, many=True).data})


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [ReadOnlyOrTeacher]

    def get_queryset(self):
        if not has_role(self.request.user, 'admin', 'teacher'):
            return Question.objects.none()
        qs = Question.objects.prefetch_related('choices')
        quiz = int_param(self.request, 'quiz')
        return qs.filter(quiz_id=quiz) if quiz is not None else qs


class AttemptViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = AttemptSerializer

    def get_queryset(self):
        qs = Attempt.objects.select_related('quiz', 'user')
        if self.request.query_params.get('all') and has_role(self.request.user, 'admin', 'teacher'):
            return qs.filter(grade__isnull=False)
        return qs.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        attempt = get_object_or_404(Attempt, pk=pk, user=request.user)
        if attempt.finished_at:
            raise ValidationError('Cette tentative a déjà été remise.')
        answers = request.data.get('answers', {})
        if not isinstance(answers, dict):
            raise ValidationError({'answers': 'Format invalide.'})
        now = timezone.now()
        deadline = attempt.started_at + timedelta(minutes=attempt.quiz.duration_minutes)
        earned, total, grade, details = grade_attempt(attempt, answers)
        attempt.answers = answers
        attempt.details = details
        attempt.score, attempt.max_score, attempt.grade = earned, total, grade
        attempt.finished_at = now
        attempt.timed_out = now > deadline + GRACE
        attempt.save()
        return Response(AttemptSerializer(attempt).data)


class ProgressView(APIView):
    """Statistiques de progression de l'apprenant connecté."""

    def get(self, request):
        attempts = Attempt.objects.filter(user=request.user, grade__isnull=False).select_related('quiz')
        by_level = {}
        for level in ('BT1', 'BT2'):
            qs = attempts.filter(quiz__level=level)
            agg = qs.aggregate(avg=Avg('grade'), best=Max('grade'), n=Count('id'))
            by_level[level] = {k: (str(v) if v is not None and k != 'n' else v) for k, v in agg.items()}
        history = [{'date': a.finished_at, 'grade': str(a.grade), 'quiz': a.quiz.title, 'level': a.quiz.level}
                   for a in attempts.order_by('finished_at')[:100]]
        mistakes = []
        for a in attempts.order_by('-finished_at')[:20]:
            for d in a.details:
                if not d.get('correct'):
                    mistakes.append({'quiz': a.quiz.title, 'question': d.get('text'), 'expected': d.get('expected'),
                                     'explanation': d.get('explanation'), 'date': a.finished_at})
        return Response({'by_level': by_level, 'history': history, 'mistakes': mistakes[:30]})
