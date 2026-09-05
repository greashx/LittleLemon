from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from Restaurant.models import Menu
from Restaurant.serializers import MenuItemSerializer


class MenuViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pw")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.item1 = Menu.objects.create(Title="Pizza", Price=12, Inventory=50)
        self.item2 = Menu.objects.create(Title="Burger", Price=8, Inventory=30)

    def test_getall(self):
        response = self.client.get('/restaurant/menu/menu-items/', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=str(response.content))
        items = Menu.objects.all()
        serializer = MenuItemSerializer(items, many=True)
        self.assertEqual(response.data['results'], serializer.data)
