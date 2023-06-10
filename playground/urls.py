from django.urls import path
from . import views

app_name = 'playground'

urlpatterns = [
    path('analyze-website/', views.analyze_website, name='analyze_website'),
    path('subpage-analysis-result/', views.subpage_analysis_result, name='subpage_analysis_result'),
]
