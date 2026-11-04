import logging

from .models import AuditLog

security_logger = logging.getLogger('btc.security')


def client_ip(request):
    if request is None:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_action(request, action, target=None, user=None, **details):
    """Enregistre une action sensible en base (consultable par l'administrateur) et dans logs/security.log."""
    if user is None:
        user = getattr(request, 'user', None)
    if user is not None and not getattr(user, 'is_authenticated', False):
        user = None
    ip = client_ip(request)
    entry = AuditLog.objects.create(
        user=user,
        action=action,
        target_type=target.__class__.__name__ if target is not None else '',
        target_id=str(getattr(target, 'pk', '') or ''),
        details=details,
        ip_address=ip,
    )
    security_logger.info('%s user=%s ip=%s target=%s:%s %s', action, getattr(user, 'username', '-'), ip,
                         entry.target_type, entry.target_id, details or '')
    return entry
