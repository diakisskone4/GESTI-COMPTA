from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import ReadOnlyOrTeacher

from .models import Chapter, ChapterProgress, Lesson, Module, ProgrammeLevel
from .serializers import (ChapterSerializer, LessonSerializer, ModuleDetailSerializer, ModuleListSerializer,
                          ProgrammeLevelSerializer)


class ProgressContextMixin:
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        user = self.request.user
        ctx['completed_ids'] = set(ChapterProgress.objects.filter(user=user).values_list('chapter_id', flat=True)) \
            if user.is_authenticated else set()
        return ctx


class ProgrammeLevelViewSet(ProgressContextMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ProgrammeLevel.objects.prefetch_related('modules__chapters', 'modules__level')
    serializer_class = ProgrammeLevelSerializer
    lookup_field = 'code'


class ModuleViewSet(ProgressContextMixin, viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrTeacher]

    def get_queryset(self):
        qs = Module.objects.select_related('level').prefetch_related(
            Prefetch('chapters', queryset=Chapter.objects.prefetch_related('lessons')))
        level = self.request.query_params.get('level')
        return qs.filter(level__code=level) if level else qs

    def get_serializer_class(self):
        return ModuleListSerializer if self.action == 'list' else ModuleDetailSerializer


class ChapterViewSet(ProgressContextMixin, viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrTeacher]
    serializer_class = ChapterSerializer
    queryset = Chapter.objects.prefetch_related('lessons')

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        chapter = self.get_object()
        if request.method == 'DELETE':
            ChapterProgress.objects.filter(user=request.user, chapter=chapter).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        ChapterProgress.objects.get_or_create(user=request.user, chapter=chapter)
        return Response({'completed': True})


class LessonViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrTeacher]
    serializer_class = LessonSerializer

    def get_queryset(self):
        qs = Lesson.objects.all()
        if self.request.user.role not in ('admin', 'teacher') and not self.request.user.is_superuser:
            qs = qs.filter(status=Lesson.Status.PUBLISHED)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
