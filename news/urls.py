from django.urls import path
from . import views

app_name = "news"

urlpatterns = [
    path("", views.grab, name='grab')
]
