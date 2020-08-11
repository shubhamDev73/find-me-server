from django.contrib import admin
from django.urls import path, include

def docs(request):
    from django.shortcuts import render
    return render(request, 'docs.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('backend.urls')),
    path('docs/', docs),
]
