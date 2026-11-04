from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', default='', read_only=True)

    class Meta:
        model = AuditLog
        fields = ('id', 'username', 'action', 'target_type', 'target_id', 'details', 'ip_address', 'created_at')
