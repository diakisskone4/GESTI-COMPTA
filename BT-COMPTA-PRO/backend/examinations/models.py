from decimal import Decimal

from django.conf import settings
from django.db import models


class Quiz(models.Model):
    class Kind(models.TextChoices):
        QUIZ = 'quiz', 'Quiz d\'entraînement'
        EVALUATION = 'evaluation', 'Évaluation'
        MOCK = 'mock', 'Examen blanc'

    title = models.CharField(max_length=200)
    level = models.CharField(max_length=3, choices=[('BT1', 'BT1'), ('BT2', 'BT2')])
    module = models.ForeignKey('pedagogy.Module', null=True, blank=True, on_delete=models.SET_NULL, related_name='quizzes')
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.QUIZ)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=20)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='quizzes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['level', 'kind', 'title']
        verbose_name = 'quiz / examen'

    def __str__(self):
        return self.title


class Question(models.Model):
    class Kind(models.TextChoices):
        MCQ = 'mcq', 'Choix multiple'
        NUMERIC = 'numeric', 'Calcul (réponse numérique)'
        ENTRY = 'entry', 'Saisie d\'écriture comptable'

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.MCQ)
    text = models.TextField()
    explanation = models.TextField('correction détaillée', blank=True)
    points = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1'))
    order = models.PositiveIntegerField(default=1)
    answer_numeric = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    tolerance = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal('0.5'))
    expected_entry = models.JSONField(default=list, blank=True,
                                      help_text='Liste de lignes attendues : [{"account": "601", "debit": "1000", "credit": "0"}]')

    class Meta:
        ordering = ['quiz', 'order']

    def __str__(self):
        return self.text[:60]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0'))
    max_score = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0'))
    grade = models.DecimalField('note sur 20', max_digits=5, decimal_places=2, null=True, blank=True)
    answers = models.JSONField(default=dict, blank=True)
    details = models.JSONField(default=list, blank=True)
    timed_out = models.BooleanField(default=False)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user} — {self.quiz} — {self.grade}'


def _subject_path(instance, filename):
    from core.uploads import random_path
    return random_path('sujets')(instance, filename)


def _correction_path(instance, filename):
    from core.uploads import random_path
    return random_path('corriges')(instance, filename)


class ExamSubject(models.Model):
    """Sujet d'examen déposé par un enseignant, avec son corrigé."""

    class Kind(models.TextChoices):
        ANNALE = 'annale', 'Annale / sujet d\'examen'
        MOCK = 'mock', 'Examen blanc'
        HOMEWORK = 'devoir', 'Devoir'
        EXERCISE = 'td', 'Travaux dirigés'

    title = models.CharField(max_length=200)
    level = models.CharField(max_length=3, choices=[('BT1', 'BT1'), ('BT2', 'BT2')])
    module = models.ForeignKey('pedagogy.Module', null=True, blank=True, on_delete=models.SET_NULL, related_name='subjects')
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.MOCK)
    session = models.CharField('session / année', max_length=60, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    total_points = models.PositiveIntegerField(default=20)
    description = models.TextField('consignes', blank=True)
    subject_file = models.FileField(upload_to=_subject_path)
    subject_name = models.CharField(max_length=255)
    correction_file = models.FileField(upload_to=_correction_path, null=True, blank=True)
    correction_name = models.CharField(max_length=255, blank=True)
    correction_text = models.TextField('barème et résultats détaillés', blank=True)
    correction_released = models.BooleanField('correction visible des apprenants', default=False)
    quiz = models.ForeignKey(Quiz, null=True, blank=True, on_delete=models.SET_NULL, related_name='subjects',
                             help_text='Épreuve en ligne corrigée automatiquement (facultatif).')
    is_published = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='exam_subjects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'sujet d\'examen'

    def __str__(self):
        return self.title

    @property
    def has_correction(self):
        return bool(self.correction_file or self.correction_text.strip())


class SubjectWork(models.Model):
    """Suivi d'un apprenant sur un sujet : ouverture, consultation du corrigé, note obtenue."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subject_works')
    subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name='works')
    opened_at = models.DateTimeField(null=True, blank=True)
    correction_viewed_at = models.DateTimeField(null=True, blank=True)
    self_grade = models.DecimalField('note obtenue', max_digits=5, decimal_places=2, null=True, blank=True)
    comment = models.CharField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'subject'], name='unique_subject_work')]
