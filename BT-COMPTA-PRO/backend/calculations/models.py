from django.conf import settings
from django.db import models


class CalculationRecord(models.Model):
    """Historique des calculs effectués par un utilisateur."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calculations')
    slug = models.CharField(max_length=60, db_index=True)
    title = models.CharField(max_length=200)
    inputs = models.JSONField(default=dict)
    summary = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'calcul enregistré'

    def __str__(self):
        return f'{self.title} ({self.created_at:%d/%m/%Y})'
