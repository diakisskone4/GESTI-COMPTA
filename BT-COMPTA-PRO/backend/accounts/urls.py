from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (ChangePasswordView, ProRegisterView, LoginView, LogoutView, MeView, PasswordResetConfirmView, PasswordResetRequestView,
                    RefreshView, RegisterView, UserAdminViewSet, ping)

router = DefaultRouter()
router.register('users', UserAdminViewSet, basename='users')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('register/pro/', ProRegisterView.as_view(), name='register_pro'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('ping/', ping, name='ping'),
    path('', include(router.urls)),
]
