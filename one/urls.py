from django.urls import path
from .views import top, search

urlpatterns = [
    path('', top, name='top'),
    path('search', search, name='search'),
]
