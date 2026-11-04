from django.urls import path

from .views import (CalculationHistoryDeleteView, CalculationHistoryView, CalculatorDetailView, CalculatorExportView,
                    CalculatorListView, CalculatorRunView)

urlpatterns = [
    path('', CalculatorListView.as_view(), name='calculators'),
    path('history/', CalculationHistoryView.as_view(), name='calc_history'),
    path('history/<int:pk>/', CalculationHistoryDeleteView.as_view(), name='calc_history_delete'),
    path('<slug:slug>/', CalculatorDetailView.as_view(), name='calculator_detail'),
    path('<slug:slug>/run/', CalculatorRunView.as_view(), name='calculator_run'),
    path('<slug:slug>/export/<str:fmt>/', CalculatorExportView.as_view(), name='calculator_export'),
]
