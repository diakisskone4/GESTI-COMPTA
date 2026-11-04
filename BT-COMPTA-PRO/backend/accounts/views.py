from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from core.audit import log_action
from core.permissions import IsAdmin

from . import security
from .serializers import (AdminUserSerializer, ChangePasswordSerializer, LoginSerializer, PasswordResetConfirmSerializer,
                          PasswordResetRequestSerializer, ProRegisterSerializer, RegisterSerializer, ReviewSerializer,
                          UserSerializer, check_password_strength)

User = get_user_model()

INVALID_CREDENTIALS = 'Identifiants incorrects.'


class PublicAuthView(APIView):
    """Vue d'authentification publique : pas de session JWT requise, limitation de débit dédiée."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'


class RegisterView(PublicAuthView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log_action(request, 'user.register', user, user=user, role=user.role)
        response = Response({'user': UserSerializer(user).data}, status=status.HTTP_201_CREATED)
        return security.issue_tokens(request, response, user)


def notify(recipients, subject, body):
    """Envoi d'un e-mail sans bloquer l'action si le serveur de messagerie est indisponible."""
    if not isinstance(recipients, (list, tuple)):
        recipients = [recipients.email]
    try:
        send_mail(f'BT COMPTA PRO — {subject}', body, settings.DEFAULT_FROM_EMAIL, recipients)
    except Exception:  # pragma: no cover - dépend du serveur SMTP
        import logging
        logging.getLogger('btc.security').warning("Échec d'envoi d'e-mail : %s", subject)


class ProRegisterView(PublicAuthView):
    """Inscription professionnelle : technicien comptable (accès immédiat) ou enseignant (validation administrateur)."""

    def post(self, request):
        serializer = ProRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log_action(request, 'user.register_pro', user, user=None, role=user.role, status=user.approval_status)
        if user.approval_status == User.Approval.PENDING:
            admins = list(User.objects.filter(role=User.Role.ADMIN, is_active=True).values_list('email', flat=True))
            if admins:
                notify(admins, 'Nouvelle demande de compte enseignant',
                       f"{user.get_full_name()} ({user.email}) demande un compte enseignant.\n"
                       f"Établissement : {user.establishment}\nMatières : {user.speciality}\n\n{user.motivation}\n\n"
                       "Validez ou refusez la demande dans Administration > Demandes de comptes.")
            notify(user, 'Demande de compte enseignant reçue',
                   f"Bonjour {user.first_name},\n\nVotre demande de compte enseignant a bien été reçue. "
                   "Un administrateur va la vérifier ; vous recevrez un e-mail dès sa validation.\n\nL'équipe BT COMPTA PRO")
            return Response({'pending': True, 'detail': 'Demande envoyée. Votre compte enseignant sera activé après validation '
                                                        'par un administrateur ; vous serez prévenu par e-mail.'},
                            status=status.HTTP_202_ACCEPTED)
        response = Response({'user': UserSerializer(user).data}, status=status.HTTP_201_CREATED)
        return security.issue_tokens(request, response, user)


class LoginView(PublicAuthView):
    """Connexion par nom d'utilisateur ou e-mail.

    Protections : limitation par IP (THROTTLE_LOGIN) et verrouillage du compte après
    LOGIN_MAX_FAILURES échecs consécutifs pendant LOGIN_LOCK_MINUTES minutes.
    """

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data['identifier'].strip()
        password = serializer.validated_data['password']
        lookup = Q(email__iexact=identifier) if '@' in identifier else Q(username=identifier)
        account = User.objects.filter(lookup).first()

        if account and account.is_locked:
            minutes = security.lock_remaining_minutes(account)
            log_action(request, 'auth.login_blocked', account, user=account)
            return Response({'detail': f'Compte temporairement verrouillé après plusieurs échecs. Réessayez dans {minutes} minute(s) '
                                       'ou réinitialisez votre mot de passe.'}, status=status.HTTP_403_FORBIDDEN)

        # Compte professionnel non validé : message explicite, seulement si le mot de passe est correct.
        if account and account.approval_status != User.Approval.APPROVED and account.check_password(password):
            if account.approval_status == User.Approval.PENDING:
                detail = 'Votre demande de compte est en cours de validation par un administrateur. Vous serez prévenu par e-mail.'
            else:
                detail = 'Votre demande de compte a été refusée.' + (f' Motif : {account.review_note}' if account.review_note else '')
            return Response({'detail': detail, 'approval': account.approval_status}, status=status.HTTP_403_FORBIDDEN)

        user = authenticate(request, username=account.username if account else identifier, password=password)
        if user is None:
            if account and account.is_active:
                with transaction.atomic():
                    locked = security.register_failure(User.objects.select_for_update().get(pk=account.pk))
                log_action(request, 'auth.account_locked' if locked else 'auth.login_failed', account, user=account)
            else:
                log_action(request, 'auth.login_failed', identifier=identifier[:150])
            return Response({'detail': INVALID_CREDENTIALS}, status=status.HTTP_400_BAD_REQUEST)

        security.register_success(user)
        update_last_login(None, user)
        log_action(request, 'auth.login', user, user=user)
        return security.issue_tokens(request, Response({'user': UserSerializer(user).data}), user)


class RefreshView(PublicAuthView):
    """Renouvelle le jeton d'accès à partir du cookie HttpOnly (rotation + révocation de l'ancien)."""

    throttle_scope = None
    throttle_classes = []

    def post(self, request):
        refresh = security.read_refresh(request)
        if not refresh:
            return Response({'detail': 'Session expirée.'}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = TokenRefreshSerializer(data={'refresh': refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, ValidationError, Exception):
            response = Response({'detail': 'Session expirée. Veuillez vous reconnecter.'}, status=status.HTTP_401_UNAUTHORIZED)
            security.clear_refresh_cookie(response)
            return response
        data = serializer.validated_data
        user = User.objects.filter(pk=RefreshToken(data['refresh']).payload.get('user_id'), is_active=True).first()
        if user is None:
            response = Response({'detail': 'Compte désactivé.'}, status=status.HTTP_401_UNAUTHORIZED)
            security.clear_refresh_cookie(response)
            return response
        response = Response({'access': data['access'], 'user': UserSerializer(user).data})
        security.set_refresh_cookie(request, response, data['refresh'])
        return response


class LogoutView(PublicAuthView):
    throttle_scope = None
    throttle_classes = []

    def post(self, request):
        refresh = security.read_refresh(request)
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
                user = User.objects.filter(pk=token.payload.get('user_id')).first()
                log_action(request, 'auth.logout', user, user=user)
            except TokenError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        security.clear_refresh_cookie(response)
        return response


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.password_changed_at = timezone.now()
        user.save()
        security.revoke_all_tokens(user)  # déconnecte les autres appareils
        log_action(request, 'auth.password_changed', user)
        response = Response({'detail': 'Mot de passe modifié. Vos autres sessions ont été fermées.'})
        return security.issue_tokens(request, response, user)


class PasswordResetRequestView(PublicAuthView):
    """Envoie un lien de réinitialisation. Réponse identique que l'e-mail existe ou non (pas d'énumération)."""

    throttle_scope = 'password_reset'

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f'{settings.FRONTEND_URL}/reinitialiser-mot-de-passe?uid={uid}&token={token}'
            minutes = settings.PASSWORD_RESET_TIMEOUT // 60
            send_mail(
                'BT COMPTA PRO — Réinitialisation de votre mot de passe',
                f'Bonjour {user.first_name or user.username},\n\n'
                f'Une demande de réinitialisation du mot de passe a été faite pour votre compte.\n'
                f'Pour choisir un nouveau mot de passe, ouvrez ce lien (valable {minutes} minutes, utilisable une seule fois) :\n\n'
                f'{link}\n\n'
                'Si vous n\'êtes pas à l\'origine de cette demande, ignorez ce message : votre mot de passe reste inchangé.\n\n'
                'L\'équipe BT COMPTA PRO',
                settings.DEFAULT_FROM_EMAIL, [user.email])
            log_action(request, 'auth.password_reset_requested', user, user=user)
        return Response({'detail': 'Si un compte correspond à cette adresse, un e-mail de réinitialisation vient d\'être envoyé.'})


class PasswordResetConfirmView(PublicAuthView):
    throttle_scope = 'password_reset'

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(data['uid'])), is_active=True)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            user = None
        # Le jeton dépend du mot de passe actuel et de la dernière connexion : il devient invalide après usage.
        if user is None or not default_token_generator.check_token(user, data['token']):
            return Response({'detail': 'Lien invalide ou expiré. Faites une nouvelle demande.'}, status=status.HTTP_400_BAD_REQUEST)
        check_password_strength(data['new_password'], user, 'new_password')
        user.set_password(data['new_password'])
        user.password_changed_at = timezone.now()
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save()
        security.revoke_all_tokens(user)
        log_action(request, 'auth.password_reset_done', user, user=user)
        return Response({'detail': 'Mot de passe réinitialisé. Vous pouvez vous connecter.'})


class UserAdminViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                       viewsets.GenericViewSet):
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = User.objects.order_by('-date_joined')
        role = self.request.query_params.get('role')
        approval = self.request.query_params.get('approval')
        if approval in User.Approval.values:
            qs = qs.filter(approval_status=approval)
        search = self.request.query_params.get('search', '')[:100]
        if role:
            qs = qs.filter(role=role)
        if search:
            qs = qs.filter(Q(username__icontains=search) | Q(email__icontains=search) |
                           Q(first_name__icontains=search) | Q(last_name__icontains=search))
        return qs

    def perform_update(self, serializer):
        target = serializer.instance
        before = {'role': target.role, 'is_active': target.is_active}
        new_role = serializer.validated_data.get('role', target.role)
        new_active = serializer.validated_data.get('is_active', target.is_active)
        if target.pk == self.request.user.pk and (new_role != target.role or not new_active):
            raise ValidationError('Vous ne pouvez pas modifier votre propre rôle ni désactiver votre propre compte.')
        removes_admin = target.role == User.Role.ADMIN and target.is_active and (new_role != User.Role.ADMIN or not new_active)
        if removes_admin and not User.objects.filter(role=User.Role.ADMIN, is_active=True).exclude(pk=target.pk).exists():
            raise ValidationError('Impossible : la plateforme doit conserver au moins un administrateur actif.')
        user = serializer.save()
        if user.is_active and user.approval_status == User.Approval.PENDING:
            user.approval_status = User.Approval.APPROVED  # activation manuelle = validation
            user.reviewed_by, user.reviewed_at = self.request.user, timezone.now()
            user.save(update_fields=['approval_status', 'reviewed_by', 'reviewed_at'])
        if before['is_active'] and not user.is_active:
            security.revoke_all_tokens(user)
        log_action(self.request, 'user.updated_by_admin', user, before=before,
                   after={'role': user.role, 'is_active': user.is_active})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        user = self.get_object()
        if user.approval_status == User.Approval.APPROVED and user.is_active:
            raise ValidationError('Ce compte est déjà validé.')
        note = ReviewSerializer(data=request.data)
        note.is_valid(raise_exception=True)
        user.approval_status = User.Approval.APPROVED
        user.is_active = True
        user.reviewed_by, user.reviewed_at = request.user, timezone.now()
        user.review_note = note.validated_data.get('note', '')
        user.save()
        log_action(request, 'user.approved', user, role=user.role)
        notify(user, 'Votre compte est activé',
               f"Bonjour {user.first_name},\n\nVotre compte {user.get_role_display().lower()} a été validé. "
               f"Vous pouvez vous connecter : {settings.FRONTEND_URL}/connexion\n\nL'équipe BT COMPTA PRO")
        return Response(AdminUserSerializer(user).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        user = self.get_object()
        if user.pk == request.user.pk:
            raise ValidationError('Action impossible sur votre propre compte.')
        note = ReviewSerializer(data=request.data)
        note.is_valid(raise_exception=True)
        user.approval_status = User.Approval.REJECTED
        user.is_active = False
        user.reviewed_by, user.reviewed_at = request.user, timezone.now()
        user.review_note = note.validated_data.get('note', '')
        user.save()
        security.revoke_all_tokens(user)
        log_action(request, 'user.rejected', user, note=user.review_note)
        notify(user, 'Votre demande de compte',
               f"Bonjour {user.first_name},\n\nVotre demande de compte n'a pas pu être acceptée."
               + (f"\nMotif : {user.review_note}" if user.review_note else '')
               + "\n\nVous pouvez utiliser BT COMPTA PRO avec un compte apprenant.\n\nL'équipe BT COMPTA PRO")
        return Response(AdminUserSerializer(user).data)

    @action(detail=True, methods=['post'])
    def unlock(self, request, pk=None):
        user = self.get_object()
        security.register_success(user)
        log_action(request, 'user.unlocked_by_admin', user)
        return Response(AdminUserSerializer(user).data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def ping(request):
    return Response({'message': 'BT COMPTA PRO API OK'})
