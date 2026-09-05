from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from Restaurant.models import Booking, Menu
from Restaurant.serializers import BookingSerializer, MenuItemSerializer


def _auth(client):
    u = User.objects.create_user(username="tester", password="pw")
    client.force_authenticate(user=u)
    return u


class MenuItemTest(TestCase):
    def test_get_item(self):
        item = Menu.objects.create(Title="IceCream", Price=80, Inventory=100)
        self.assertEqual(str(item), "IceCream : 80")

    def test_menu_creation_validates_required_fields(self):
        with self.assertRaises(Exception):
            Menu.objects.create(Title="Bad")  # missing Price/Inventory


class MenuViewTest(TestCase):
    LIST_URL = "/restaurant/menu/menu-items/"
    DETAIL_URL_TPL = "/restaurant/menu/menu-items/{pk}"

    def setUp(self):
        self.client = APIClient()
        _auth(self.client)
        self.item1 = Menu.objects.create(Title="Pizza", Price=12, Inventory=50)
        self.item2 = Menu.objects.create(Title="Burger", Price=8, Inventory=30)

    def test_getall(self):
        r = self.client.get(self.LIST_URL, HTTP_ACCEPT="application/json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        items = Menu.objects.all()
        serializer = MenuItemSerializer(items, many=True)
        self.assertEqual(r.data["results"], serializer.data)

    def test_getall_requires_auth(self):
        anon = APIClient()
        r = anon.get(self.LIST_URL)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_item(self):
        payload = {"Title": "Salad", "Price": "9.50", "Inventory": 20}
        r = self.client.post(self.LIST_URL, payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, msg=str(r.content))
        self.assertEqual(Menu.objects.filter(Title="Salad").count(), 1)

    def test_retrieve_single_item(self):
        r = self.client.get(self.DETAIL_URL_TPL.format(pk=self.item1.id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["Title"], "Pizza")

    def test_update_item_put(self):
        r = self.client.put(
            self.DETAIL_URL_TPL.format(pk=self.item1.id),
            {"Title": "PizzaUpdated", "Price": "15.00", "Inventory": 40},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK, msg=str(r.content))
        self.item1.refresh_from_db()
        self.assertEqual(self.item1.Title, "PizzaUpdated")
        self.assertEqual(str(self.item1.Price), "15.00")

    def test_update_item_patch(self):
        r = self.client.patch(
            self.DETAIL_URL_TPL.format(pk=self.item1.id),
            {"Inventory": 99},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.item1.refresh_from_db()
        self.assertEqual(self.item1.Inventory, 99)

    def test_delete_item(self):
        r = self.client.delete(self.DETAIL_URL_TPL.format(pk=self.item2.id))
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Menu.objects.filter(pk=self.item2.id).exists())

    def test_404_on_missing(self):
        r = self.client.get(self.DETAIL_URL_TPL.format(pk=99999))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)


class BookingViewSetTest(TestCase):
    LIST_URL = "/restaurant/booking/tables/"
    DETAIL_URL_TPL = "/restaurant/booking/tables/{pk}/"

    def setUp(self):
        self.client = APIClient()
        _auth(self.client)
        self.booking = Booking.objects.create(
            Name="Alice", No_of_guests=2, BookingDate="2026-12-25T19:00:00Z"
        )

    def test_list_requires_auth(self):
        anon = APIClient()
        r = anon.get(self.LIST_URL)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_serialized(self):
        r = self.client.get(self.LIST_URL)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        qs = Booking.objects.all()
        serializer = BookingSerializer(qs, many=True)
        self.assertEqual(r.data["results"], serializer.data)

    def test_retrieve_booking(self):
        r = self.client.get(self.DETAIL_URL_TPL.format(pk=self.booking.id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["Name"], "Alice")

    def test_create_booking(self):
        payload = {"Name": "Bob", "No_of_guests": 4, "BookingDate": "2026-12-31T20:00:00Z"}
        r = self.client.post(self.LIST_URL, payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, msg=str(r.content))
        self.assertEqual(Booking.objects.filter(Name="Bob").count(), 1)

    def test_update_booking_put(self):
        payload = {"Name": "Alice2", "No_of_guests": 5, "BookingDate": "2026-12-25T20:00:00Z"}
        r = self.client.put(
            self.DETAIL_URL_TPL.format(pk=self.booking.id), payload, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK, msg=str(r.content))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.Name, "Alice2")
        self.assertEqual(self.booking.No_of_guests, 5)

    def test_update_booking_patch(self):
        r = self.client.patch(
            self.DETAIL_URL_TPL.format(pk=self.booking.id),
            {"No_of_guests": 6},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.No_of_guests, 6)

    def test_delete_booking(self):
        r = self.client.delete(self.DETAIL_URL_TPL.format(pk=self.booking.id))
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Booking.objects.filter(pk=self.booking.id).exists())

    def test_404_on_missing_booking(self):
        r = self.client.get(self.DETAIL_URL_TPL.format(pk=99999))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
