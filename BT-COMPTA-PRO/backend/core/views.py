from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounting.models import Company, JournalEntry
from calculations.engines import REGISTRY
from calculations.models import CalculationRecord
from examinations.models import Attempt, Quiz
from pedagogy.models import Chapter, ChapterProgress, Module

from .models import AuditLog
from .permissions import IsAdmin, has_role
from .serializers import AuditLogSerializer

User = get_user_model()


class DashboardView(APIView):
    """Indicateurs du tableau de bord adaptés au rôle de l'utilisateur."""

    def get(self, request):
        user = request.user
        done = set(ChapterProgress.objects.filter(user=user).values_list('chapter_id', flat=True))
        levels = {}
        for code in ('BT1', 'BT2'):
            chapters = list(Chapter.objects.filter(module__level__code=code).values_list('id', flat=True))
            levels[code] = {
                'modules': Module.objects.filter(level__code=code).count(),
                'chapters': len(chapters),
                'completed': len(done.intersection(chapters)),
                'calculators': sum(1 for c in REGISTRY.values() if c.level == code),
            }
        attempts = Attempt.objects.filter(user=user, grade__isnull=False).select_related('quiz').order_by('-finished_at')
        data = {
            'levels': levels,
            'exams': {
                'count': attempts.count(),
                'average': str(attempts.aggregate(a=Avg('grade'))['a'] or '') or None,
                'recent': [{'id': a.id, 'quiz': a.quiz.title, 'level': a.quiz.level, 'grade': str(a.grade),
                            'date': a.finished_at} for a in attempts[:5]],
                'available': Quiz.objects.filter(is_published=True).count(),
            },
            'accounting': {
                'companies': Company.objects.filter(owner=user).count(),
                'entries': JournalEntry.objects.filter(company__owner=user).count(),
                'drafts': JournalEntry.objects.filter(company__owner=user, status='draft').count(),
            },
            'calculations': {
                'recent': [{'id': r.id, 'slug': r.slug, 'title': r.title, 'date': r.created_at}
                           for r in CalculationRecord.objects.filter(user=user)[:5]],
            },
        }
        if has_role(user, 'admin', 'teacher'):
            all_attempts = Attempt.objects.filter(grade__isnull=False)
            data['teaching'] = {
                'students': User.objects.filter(role='student').count(),
                'attempts': all_attempts.count(),
                'average': str(all_attempts.aggregate(a=Avg('grade'))['a'] or '') or None,
                'quizzes': Quiz.objects.count(),
            }
        if has_role(user, 'admin'):
            data['admin'] = {
                'users': User.objects.count(),
                'pending': User.objects.filter(approval_status='pending').count(),
                'by_role': dict(User.objects.values_list('role').annotate(n=Count('id'))),
                'companies': Company.objects.count(),
                'entries': JournalEntry.objects.count(),
            }
        return Response(data)


class AuditLogView(ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        return AuditLog.objects.select_related('user')[:200]
