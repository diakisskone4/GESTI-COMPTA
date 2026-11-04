"""Services de sécurité de l'authentification : cookie de rafraîchissement, révocation, verrouillage."""
import math
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

# En-tête envoyé par les applications natives (Capacitor) qui ne peuvent pas utiliser le cookie :
# le jeton de rafraîchissement est alors renvoyé dans le corps de la réponse.
NATIVE_HEADER = 'HTTP_X_TOKEN_TRANSPORT'


def wants_body_token(request):
    return request.META.get(NATIVE_HEADER, '').lower() == 'body'


def issue_tokens(request, response, user):
    """Crée une paire de jetons : accès dans le corps, rafraîchissement dans un cookie HttpOnly."""
    refresh = RefreshToken.for_user(user)
    response.data['access'] = str(refresh.access_token)
    set_refresh_cookie(request, response, str(refresh))
    return response


def set_refresh_cookie(request, response, refresh):
    if wants_body_token(request):
        response.data['refresh'] = refresh
        return
    cfg = settings.REFRESH_COOKIE
    response.set_cookie(cfg['key'], refresh, max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
                        path=cfg['path'], httponly=cfg['httponly'], secure=cfg['secure'], samesite=cfg['samesite'])


def clear_refresh_cookie(response):
    cfg = settings.REFRESH_COOKIE
    response.delete_cookie(cfg['key'], path=cfg['path'], samesite=cfg['samesite'])


def read_refresh(request):
    return request.COOKIES.get(settings.REFRESH_COOKIE['key']) or (request.data.get('refresh') if hasattr(request, 'data') else None)


def revoke_all_tokens(user):
    """Révoque toutes les sessions ouvertes (changement ou réinitialisation de mot de passe, désactivation)."""
    for token in OutstandingToken.objects.filter(user=user).exclude(blacklistedtoken__isnull=False):
        BlacklistedToken.objects.get_or_create(token=token)


# --- Verrouillage du compte après échecs répétés -------------------------------------------------

def lock_remaining_minutes(user):
    if not user.is_locked:
        return 0
    return max(1, math.ceil((user.locked_until - timezone.now()).total_seconds() / 60))


def register_failure(user):
    """Incrémente le compteur d'échecs ; verrouille le compte au-delà du seuil. Retourne True si verrouillé."""
    user.failed_login_attempts += 1
    locked = user.failed_login_attempts >= settings.LOGIN_MAX_FAILURES
    if locked:
        user.locked_until = timezone.now() + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
        user.failed_login_attempts = 0
    user.save(update_fields=['failed_login_attempts', 'locked_until'])
    return locked


def register_success(user):
    if user.failed_login_attempts or user.locked_until:
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save(update_fields=['failed_login_attempts', 'locked_until'])
