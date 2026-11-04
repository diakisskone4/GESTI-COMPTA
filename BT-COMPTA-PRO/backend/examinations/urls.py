from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .subjects import ExamSubjectViewSet
from .views import AttemptViewSet, ProgressView, QuestionViewSet, QuizViewSet

router = DefaultRouter()
router.register('quizzes', QuizViewSet, basename='quiz')
router.register('questions', QuestionViewSet, basename='question')
router.register('attempts', AttemptViewSet, basename='attempt')
router.register('subjects', ExamSubjectViewSet, basename='subject')

urlpatterns = [
    path('progress/', ProgressView.as_view(), name='progress'),
    path('', include(router.urls)),
]
