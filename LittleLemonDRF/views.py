from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action

from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import (
    CategorySerializer,
    MenuItemSerializer,
    UserSerializer,
    CartSerializer,
    OrderSerializer,
    OrderItemSerializer,
)
from .permissions import IsAdminOrManager, IsManager, IsDeliveryCrew


class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrManager]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdminOrManager()]


class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminOrManager]

    ordering_fields = ['price', 'inventory']
    filterset_fields = ['price', 'inventory', 'category', 'featured']
    search_fields = ['title', 'category__title']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdminOrManager()]


class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminOrManager]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdminOrManager()]


def _group_users(group_name):
    return User.objects.filter(groups__name=group_name)


class ManagerGroupView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return _group_users('Manager')

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        if not username:
            return Response({'detail': 'username is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)
        managers = get_object_or_404(Group, name='Manager')
        managers.user_set.add(user)
        return Response({'message': f'{user.username} added to Manager group'}, status=status.HTTP_201_CREATED)


class ManagerGroupRemoveView(generics.DestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsManager]
    lookup_field = 'userId'

    def get_queryset(self):
        return _group_users('Manager')

    def perform_destroy(self, instance):
        managers = get_object_or_404(Group, name='Manager')
        managers.user_set.remove(instance)


class DeliveryCrewGroupView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return _group_users('Delivery crew')

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        if not username:
            return Response({'detail': 'username is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)
        crew = get_object_or_404(Group, name='Delivery crew')
        crew.user_set.add(user)
        return Response({'message': f'{user.username} added to Delivery crew group'}, status=status.HTTP_201_CREATED)


class DeliveryCrewGroupRemoveView(generics.DestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsManager]
    lookup_field = 'userId'

    def get_queryset(self):
        return _group_users('Delivery crew')

    def perform_destroy(self, instance):
        crew = get_object_or_404(Group, name='Delivery crew')
        crew.user_set.remove(instance)


class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        menuitem_id = request.data.get('menuitem_id') or request.data.get('menuitem')
        quantity = int(request.data.get('quantity', 1))
        if not menuitem_id:
            return Response({'detail': 'menuitem_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        menuitem = get_object_or_404(MenuItem, pk=menuitem_id)
        user = request.user
        cart_item, created = Cart.objects.get_or_create(
            user=user,
            menuitem=menuitem,
            defaults={'quantity': quantity, 'unit_price': menuitem.price, 'price': menuitem.price * quantity},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.price = cart_item.unit_price * cart_item.quantity
            cart_item.save()
        serializer = CartSerializer(cart_item, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        Cart.objects.filter(user=request.user).delete()
        return Response({'message': 'Cart emptied'}, status=status.HTTP_200_OK)


class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        if user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=user)
        return Order.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        user = request.user
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        total = sum(item.price for item in cart_items)
        order = Order.objects.create(user=user, total=total)
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=item.menuitem,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.price,
            )
        cart_items.delete()
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        if user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=user)
        return Order.objects.filter(user=user)

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        user = request.user
        data = request.data.copy()
        if user.is_staff or user.groups.filter(name='Manager').exists():
            delivery_crew_id = data.get('delivery_crew_id') or data.get('delivery_crew')
            if delivery_crew_id is not None:
                if delivery_crew_id in (None, '', '0'):
                    order.delivery_crew = None
                else:
                    order.delivery_crew = get_object_or_404(User, pk=delivery_crew_id)
            if 'status' in data:
                order.status = bool(int(data['status']))
            order.save()
        elif user.groups.filter(name='Delivery crew').exists() and order.delivery_crew == user:
            if 'status' in data:
                order.status = bool(int(data['status']))
                order.save()
            else:
                return Response({'detail': 'Delivery crew may only update status.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        return Response(OrderSerializer(order).data)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
