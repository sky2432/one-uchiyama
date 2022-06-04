from django.urls import path
from .views import top

urlpatterns = [
    path('', top, name='top'),
]
