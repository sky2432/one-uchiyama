from django.urls import path
from .views import top, detail, admin

urlpatterns = [
    path('', top, name='top'),
    path('detail/<int:pk>', detail, name='detail'),
    path('admin/', admin, name='admin'),
]
