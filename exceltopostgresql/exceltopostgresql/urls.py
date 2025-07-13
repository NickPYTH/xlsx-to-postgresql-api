from django.contrib import admin
from django.urls import path
from app.views import convert

urlpatterns = [
    path('admin/', admin.site.urls),
    path('convert/', convert, name='convert'),
]
