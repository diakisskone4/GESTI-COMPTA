from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from core.views import AuditLogView, DashboardView

admin.site.site_header = 'BT COMPTA PRO — Administration'
admin.site.site_title = 'BT COMPTA PRO'

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/audit-logs/', AuditLogView.as_view(), name='audit_logs'),
    path('api/pedagogy/', include('pedagogy.urls')),
    path('api/accounting/', include('accounting.urls')),
    path('api/calculations/', include('calculations.urls')),
    path('api/exams/', include('examinations.urls')),
]
