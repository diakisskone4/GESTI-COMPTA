import random

from rest_framework import serializers

from .models import Attempt, Choice, Question, Quiz


class ChoicePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ('id', 'text')


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ('id', 'text', 'is_correct')


class QuestionPublicSerializer(serializers.ModelSerializer):
    """Question telle que vue par l'apprenant pendant l'épreuve (sans la réponse)."""

    choices = serializers.SerializerMethodField()
    multiple = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ('id', 'kind', 'text', 'points', 'order', 'choices', 'multiple')

    def get_choices(self, obj):
        # Ordre aléatoire à chaque épreuve : la position ne doit pas trahir la bonne réponse.
        choices = list(obj.choices.all())
        random.shuffle(choices)
        return ChoicePublicSerializer(choices, many=True).data

    def get_multiple(self, obj):
        return sum(1 for c in obj.choices.all() if c.is_correct) > 1


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ('id', 'quiz', 'kind', 'text', 'explanation', 'points', 'order', 'answer_numeric', 'tolerance',
                  'expected_entry', 'choices')

    def validate(self, attrs):
        kind = attrs.get('kind', getattr(self.instance, 'kind', Question.Kind.MCQ))
        if kind == Question.Kind.MCQ and 'choices' in attrs:
            if not any(c.get('is_correct') for c in attrs['choices']):
                raise serializers.ValidationError({'choices': 'Au moins une bonne réponse est requise.'})
        if kind == Question.Kind.NUMERIC and attrs.get('answer_numeric', getattr(self.instance, 'answer_numeric', None)) is None:
            raise serializers.ValidationError({'answer_numeric': 'Réponse numérique attendue.'})
        return attrs

    def create(self, validated_data):
        choices = validated_data.pop('choices', [])
        question = Question.objects.create(**validated_data)
        Choice.objects.bulk_create([Choice(question=question, **c) for c in choices])
        return question

    def update(self, instance, validated_data):
        choices = validated_data.pop('choices', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if choices is not None:
            instance.choices.all().delete()
            Choice.objects.bulk_create([Choice(question=instance, **c) for c in choices])
        return instance


class QuizSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()
    kind_label = serializers.CharField(source='get_kind_display', read_only=True)
    module_title = serializers.CharField(source='module.title', default='', read_only=True)
    best_grade = serializers.SerializerMethodField()
    attempts_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ('id', 'title', 'level', 'module', 'module_title', 'kind', 'kind_label', 'description',
                  'duration_minutes', 'is_published', 'questions_count', 'best_grade', 'attempts_count', 'created_at')
        read_only_fields = ('created_at',)

    def get_questions_count(self, obj):
        return len(obj.questions.all())

    def _mine(self, obj):
        request = self.context.get('request')
        if not request:
            return []
        return [a for a in obj.attempts.all() if a.user_id == request.user.id and a.grade is not None]

    def get_best_grade(self, obj):
        grades = [a.grade for a in self._mine(obj)]
        return str(max(grades)) if grades else None

    def get_attempts_count(self, obj):
        return len(self._mine(obj))


class AttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    quiz_level = serializers.CharField(source='quiz.level', read_only=True)
    quiz_kind = serializers.CharField(source='quiz.kind', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Attempt
        fields = ('id', 'quiz', 'quiz_title', 'quiz_level', 'quiz_kind', 'username', 'full_name', 'started_at',
                  'finished_at', 'score', 'max_score', 'grade', 'details', 'timed_out')

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
