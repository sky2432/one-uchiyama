from django.urls import path
from .views import top, detail, admin, search

urlpatterns = [
    path('admin/', admin, name='admin'),
    path('', top, name='top'),
    path('detail/<int:pk>', detail, name='detail'),
    path('search', search, name='search'),
]
