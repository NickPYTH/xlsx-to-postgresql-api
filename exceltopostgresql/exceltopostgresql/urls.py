from django.contrib import admin
from django.urls import path
from app.views import upload_xlsx_to_postgres

urlpatterns = [
    path('admin/', admin.site.urls),
    path('upload_xlsx_to_postgres/', upload_xlsx_to_postgres, name='upload_xlsx_to_postgres'),
]
