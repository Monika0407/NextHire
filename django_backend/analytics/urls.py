from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.general_placement_telemetry_view, name='dashboard'),
]
