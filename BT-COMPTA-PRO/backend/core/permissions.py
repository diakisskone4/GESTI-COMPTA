from rest_framework.permissions import SAFE_METHODS, BasePermission


def has_role(user, *roles):
    return bool(user and user.is_authenticated and (user.is_superuser or user.role in roles))


class IsAdmin(BasePermission):
    message = 'Réservé aux administrateurs.'

    def has_permission(self, request, view):
        return has_role(request.user, 'admin')


class IsTeacherOrAdmin(BasePermission):
    message = 'Réservé aux enseignants et administrateurs.'

    def has_permission(self, request, view):
        return has_role(request.user, 'admin', 'teacher')


class ReadOnlyOrTeacher(BasePermission):
    """Lecture pour tout utilisateur connecté, écriture pour enseignants / administrateurs."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return has_role(request.user, 'admin', 'teacher')


class CanDoAccounting(BasePermission):
    """La gestion comptable est ouverte à tous les rôles (les apprenants s'entraînent sur leurs propres dossiers)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
