from django.urls import path
from . import views

urlpatterns = [
    path('categories', views.CategoriesView.as_view()),
    path('menu-items', views.MenuItemsView.as_view()),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()),

    path('groups/manager/users', views.ManagerGroupView.as_view()),
    path('groups/manager/users/<int:userId>', views.ManagerGroupRemoveView.as_view()),
    path('groups/delivery-crew/users', views.DeliveryCrewGroupView.as_view()),
    path('groups/delivery-crew/users/<int:userId>', views.DeliveryCrewGroupRemoveView.as_view()),

    path('cart/menu-items', views.CartView.as_view()),
    path('orders', views.OrderView.as_view()),
    path('orders/<int:pk>', views.SingleOrderView.as_view()),
]
