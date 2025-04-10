from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('about/', lambda request: render(request, 'users/about.html'), name='about'),
]
