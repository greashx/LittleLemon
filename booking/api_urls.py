from django.urls import path
from . import views

urlpatterns = [
    path('bookings', views.bookings_json, name='bookings_json'),
    path('slots', views.available_slots_json, name='available_slots_json'),
    path('book', views.create_booking, name='create_booking'),
]
