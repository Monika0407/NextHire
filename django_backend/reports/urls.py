from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('placed-export/', views.export_placed_students_csv, name='placed_export'),
]
