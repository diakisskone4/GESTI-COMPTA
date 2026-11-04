from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Journal des actions sensibles (connexion, validation d'écriture, changement de rôle...)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_logs')
    action = models.CharField(max_length=80)
    target_type = models.CharField(max_length=80, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "journal d'audit"

    def __str__(self):
        return f'{self.created_at:%Y-%m-%d %H:%M} {self.action}'
