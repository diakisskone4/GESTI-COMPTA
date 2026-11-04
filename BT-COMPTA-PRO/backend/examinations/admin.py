from django.contrib import admin

from .models import Attempt, Choice, ExamSubject, Question, Quiz, SubjectWork


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'order', 'kind', 'text', 'points')
    list_filter = ('kind', 'quiz__level')
    inlines = [ChoiceInline]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'kind', 'duration_minutes', 'is_published')
    list_filter = ('level', 'kind', 'is_published')


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'grade', 'started_at', 'finished_at')
    list_filter = ('quiz__level',)


@admin.register(ExamSubject)
class ExamSubjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'kind', 'uploaded_by', 'correction_released', 'is_published', 'created_at')
    list_filter = ('level', 'kind', 'correction_released')


admin.site.register(SubjectWork)
