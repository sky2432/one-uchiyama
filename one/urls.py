from django.urls import path
from .views import top, detail, search

urlpatterns = [
    path('', top, name='top'),
    path('detail/<int:pk>', detail, name='detail'),
    path('search', search, name='search'),
]
