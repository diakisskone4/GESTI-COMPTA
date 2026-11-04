from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()

# Inscription publique « Apprenant ». Les professionnels passent par ProRegisterSerializer :
# technicien comptable activé immédiatement, enseignant soumis à validation d'un administrateur.
# Le rôle Administrateur n'est jamais accessible par inscription.
SELF_REGISTER_ROLES = [User.Role.STUDENT]
PRO_REGISTER_ROLES = [User.Role.TEACHER, User.Role.ACCOUNTANT]


def check_password_strength(password, user=None, field='password'):
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError({field: list(exc.messages)})


class UserSerializer(serializers.ModelSerializer):
    role_label = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'role_label', 'level',
                  'phone', 'establishment', 'is_active', 'date_joined', 'last_login')
        read_only_fields = ('id', 'username', 'email', 'role', 'is_active', 'date_joined', 'last_login')
        extra_kwargs = {'first_name': {'max_length': 150}, 'phone': {'max_length': 20}}


class AdminUserSerializer(UserSerializer):
    is_locked = serializers.BooleanField(read_only=True)
    approval_label = serializers.CharField(source='get_approval_status_display', read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('is_locked', 'locked_until', 'approval_status', 'approval_label',
                                               'speciality', 'motivation', 'reviewed_at', 'review_note')
        read_only_fields = ('id', 'username', 'date_joined', 'last_login', 'locked_until', 'approval_status',
                            'speciality', 'motivation', 'reviewed_at', 'review_note')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=128, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=[(r.value, r.label) for r in SELF_REGISTER_ROLES], default=User.Role.STUDENT)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'level', 'phone', 'establishment', 'password')
        extra_kwargs = {'first_name': {'required': True}, 'last_name': {'required': True}}

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Cette adresse e-mail est déjà utilisée.')
        return value

    def validate(self, attrs):
        candidate = User(**{k: v for k, v in attrs.items() if k != 'password'})
        check_password_strength(attrs['password'], candidate)
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=254, help_text="Nom d'utilisateur ou e-mail")
    password = serializers.CharField(write_only=True, max_length=128)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, max_length=128)
    new_password = serializers.CharField(write_only=True, max_length=128)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({'old_password': 'Mot de passe actuel incorrect.'})
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({'new_password': 'Le nouveau mot de passe doit être différent de l\'actuel.'})
        check_password_strength(attrs['new_password'], user, 'new_password')
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)
    new_password = serializers.CharField(write_only=True, max_length=128)


class ProRegisterSerializer(RegisterSerializer):
    """Inscription des enseignants et techniciens comptables (informations professionnelles obligatoires)."""

    role = serializers.ChoiceField(choices=[(r.value, r.label) for r in PRO_REGISTER_ROLES])
    phone = serializers.CharField(max_length=20)
    establishment = serializers.CharField(max_length=150)
    speciality = serializers.CharField(max_length=150, required=False, allow_blank=True)
    motivation = serializers.CharField(max_length=1000, required=False, allow_blank=True)

    class Meta(RegisterSerializer.Meta):
        fields = RegisterSerializer.Meta.fields + ('speciality', 'motivation')

    def validate(self, attrs):
        if attrs['role'] == User.Role.TEACHER:
            if not attrs.get('speciality', '').strip():
                raise serializers.ValidationError({'speciality': 'Indiquez la ou les matières enseignées.'})
            if len(attrs.get('motivation', '').strip()) < 20:
                raise serializers.ValidationError({'motivation': 'Présentez votre demande (20 caractères minimum) : '
                                                                 'établissement, classes, fonctions…'})
        return super().validate(attrs)

    def create(self, validated_data):
        if validated_data['role'] == User.Role.TEACHER:
            validated_data['is_active'] = False
            validated_data['approval_status'] = User.Approval.PENDING
        return super().create(validated_data)


class ReviewSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=255, required=False, allow_blank=True)
