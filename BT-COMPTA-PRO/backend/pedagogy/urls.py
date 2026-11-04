from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ChapterViewSet, LessonViewSet, ModuleViewSet, ProgrammeLevelViewSet

router = DefaultRouter()
router.register('levels', ProgrammeLevelViewSet, basename='level')
router.register('modules', ModuleViewSet, basename='module')
router.register('chapters', ChapterViewSet, basename='chapter')
router.register('lessons', LessonViewSet, basename='lesson')

urlpatterns = [path('', include(router.urls))]
