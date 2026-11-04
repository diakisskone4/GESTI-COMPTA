from django.conf import settings
from django.db import models


class ProgrammeLevel(models.Model):
    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'niveau'

    def __str__(self):
        return f'{self.code} — {self.title}'


class Module(models.Model):
    level = models.ForeignKey(ProgrammeLevel, on_delete=models.CASCADE, related_name='modules')
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    objectives = models.TextField('objectifs pédagogiques', blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    official_check = models.BooleanField('conformité au programme officiel vérifiée', default=False)

    class Meta:
        ordering = ['level', 'order']
        constraints = [models.UniqueConstraint(fields=['level', 'code'], name='unique_module_code')]

    def __str__(self):
        return f'{self.level.code} {self.code} : {self.title}'


class Chapter(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    summary = models.TextField('résumé / définition', blank=True)
    formulas = models.TextField(blank=True)
    calculator_slug = models.CharField(max_length=60, blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['module', 'order']

    def __str__(self):
        return self.title


class Lesson(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Brouillon'
        PUBLISHED = 'published', 'Publiée'

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    objectives = models.TextField(blank=True)
    content = models.TextField(blank=True)
    definitions = models.TextField(blank=True)
    formulas = models.TextField(blank=True)
    example = models.TextField('exemple pratique', blank=True)
    order = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PUBLISHED)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='lessons')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['chapter', 'order']

    def __str__(self):
        return self.title


class ChapterProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chapter_progress')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='progress')
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'chapter'], name='unique_chapter_progress')]
