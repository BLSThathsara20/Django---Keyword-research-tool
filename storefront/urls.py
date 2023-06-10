from django.contrib import admin
from django.urls import path, include
from playground.views import analyze_website, download_keywords, subpage_analysis_result

urlpatterns = [
    path('admin/', admin.site.urls),
    path('playground/', include('playground.urls')),
    path('analyze-website/', analyze_website, name='analyze_website'),
    path('download/', download_keywords, name='download_keywords'),
    path('subpage-analysis-result/', subpage_analysis_result, name='subpage_analysis_result'),
]
