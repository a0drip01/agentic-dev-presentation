from django.urls import path
from . import views

urlpatterns = [
    path('', views.room_grid, name='room_grid'),
    path('set-timer/<int:room_id>/', views.set_room_timer, name='set_room_timer'),
]
