from django.test import TestCase
from Restaurant.models import Menu


class MenuItemTest(TestCase):
    def test_get_item(self):
        item = Menu.objects.create(Title="IceCream", Price=80, Inventory=100)
        self.assertEqual(str(item), "IceCream : 80")

    def test_str_includes_title_and_price(self):
        item = Menu.objects.create(Title="Soup", Price="5.50", Inventory=10)
        self.assertEqual(str(item), "Soup : 5.50")
