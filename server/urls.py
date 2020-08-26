from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


def docs(request):
    from django.shortcuts import render
    return render(request, 'docs.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('backend.urls')),
    path('docs/', docs),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
