from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrateur'
        TEACHER = 'teacher', 'Enseignant'
        STUDENT = 'student', 'Apprenant'
        ACCOUNTANT = 'accountant', 'Technicien comptable'

    class Level(models.TextChoices):
        BT1 = 'BT1', 'BT1'
        BT2 = 'BT2', 'BT2'
        NONE = '', 'Non précisé'

    email = models.EmailField('adresse e-mail', unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    level = models.CharField(max_length=3, choices=Level.choices, default='', blank=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    establishment = models.CharField('établissement', max_length=150, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    class Approval(models.TextChoices):
        APPROVED = 'approved', 'Validé'
        PENDING = 'pending', 'En attente de validation'
        REJECTED = 'rejected', 'Refusé'

    approval_status = models.CharField('validation du compte', max_length=10, choices=Approval.choices, default=Approval.APPROVED)
    speciality = models.CharField('matière / spécialité', max_length=150, blank=True, default='')
    motivation = models.TextField('présentation de la demande', blank=True, default='')
    reviewed_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.CharField('motif de la décision', max_length=255, blank=True, default='')
    failed_login_attempts = models.PositiveSmallIntegerField('échecs de connexion consécutifs', default=0)
    locked_until = models.DateTimeField('verrouillé jusqu\'à', null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'utilisateur'

    @property
    def is_locked(self):
        from django.utils import timezone
        return bool(self.locked_until and self.locked_until > timezone.now())

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.username
