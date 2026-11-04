from rest_framework import serializers

from .models import Chapter, Lesson, Module, ProgrammeLevel


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ('id', 'chapter', 'title', 'objectives', 'content', 'definitions', 'formulas', 'example', 'order',
                  'status', 'updated_at')
        read_only_fields = ('updated_at',)


class ChapterSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Chapter
        fields = ('id', 'module', 'title', 'summary', 'formulas', 'calculator_slug', 'order', 'lessons', 'completed')

    def get_lessons(self, obj):
        request = self.context.get('request')
        lessons = obj.lessons.all()
        if not (request and request.user.is_authenticated and request.user.role in ('admin', 'teacher')):
            lessons = [l for l in lessons if l.status == Lesson.Status.PUBLISHED]
        return LessonSerializer(lessons, many=True).data

    def get_completed(self, obj):
        done = self.context.get('completed_ids')
        return obj.id in done if done is not None else False


class ModuleListSerializer(serializers.ModelSerializer):
    level_code = serializers.CharField(source='level.code', read_only=True)
    chapters_count = serializers.SerializerMethodField()
    completed_count = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ('id', 'level', 'level_code', 'code', 'title', 'objectives', 'description', 'order', 'official_check',
                  'chapters_count', 'completed_count')

    def get_chapters_count(self, obj):
        return len(obj.chapters.all())

    def get_completed_count(self, obj):
        done = self.context.get('completed_ids') or set()
        return sum(1 for c in obj.chapters.all() if c.id in done)


class ModuleDetailSerializer(ModuleListSerializer):
    chapters = ChapterSerializer(many=True, read_only=True)

    class Meta(ModuleListSerializer.Meta):
        fields = ModuleListSerializer.Meta.fields + ('chapters',)


class ProgrammeLevelSerializer(serializers.ModelSerializer):
    modules = ModuleListSerializer(many=True, read_only=True)

    class Meta:
        model = ProgrammeLevel
        fields = ('id', 'code', 'title', 'description', 'modules')
