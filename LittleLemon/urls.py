"""LittleLemon URL Configuration"""
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter
from Restaurant import views as restaurant_views

router = DefaultRouter()
router.register(r'tables', restaurant_views.BookingViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('LittleLemonDRF.urls')),
    path('api/', include('booking.api_urls')),
    path('', include('booking.urls')),
    path('restaurant/menu/', include('Restaurant.urls')),
    path('restaurant/booking/', include(router.urls)),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('', include('djoser.urls.authtoken')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) if settings.DEBUG else []
