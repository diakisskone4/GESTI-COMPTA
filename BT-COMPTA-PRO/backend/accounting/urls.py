from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (AccountingRuleViewSet, AccountViewSet, CompanyViewSet, FiscalYearViewSet, JournalEntryViewSet,
                    JournalViewSet, TaxRateViewSet)

router = DefaultRouter()
router.register('accounts', AccountViewSet, basename='account')
router.register('tax-rates', TaxRateViewSet, basename='taxrate')
router.register('rules', AccountingRuleViewSet, basename='rule')
router.register('companies', CompanyViewSet, basename='company')
router.register('fiscal-years', FiscalYearViewSet, basename='fiscalyear')
router.register('journals', JournalViewSet, basename='journal')
router.register('entries', JournalEntryViewSet, basename='entry')

urlpatterns = [path('', include(router.urls))]
