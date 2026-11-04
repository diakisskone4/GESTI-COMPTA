from django.contrib import admin

from .models import Chapter, ChapterProgress, Lesson, Module, ProgrammeLevel


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ('order', 'title', 'calculator_slug')


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('level', 'code', 'title', 'official_check')
    list_filter = ('level', 'official_check')
    inlines = [ChapterInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'status', 'updated_at')
    list_filter = ('status', 'chapter__module__level')
    search_fields = ('title', 'content')


admin.site.register([ProgrammeLevel, Chapter, ChapterProgress])
