from django.urls import path
from . import views

urlpatterns = [
    path('', views.room_grid, name='room_grid'),
    path('set-timer/<int:room_id>/', views.set_room_timer, name='set_room_timer'),
    path('observers/', views.observer_dashboard, name='observer_dashboard'),
    path('observer-status-api/', views.observer_status_api, name='observer_status_api'),
    path('notifications/', views.notifications_dashboard, name='notifications_dashboard'),
]
