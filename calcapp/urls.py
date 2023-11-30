from django.urls import path
from . import views

app_name = "calcapp"

urlpatterns = [
    path('', views.index, name='index'),
    path('send_query', views.send_query, name='send_query')
]
