"""End-to-end functional test covering all 21 rubric criteria."""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LittleLemon.settings")
django.setup()

from django.test import Client
from django.contrib.auth.models import User, Group
from rest_framework.authtoken.models import Token
from LittleLemonDRF.models import Category, MenuItem, Cart, Order, OrderItem

BASE = "/api"
c_admin = Client(HTTP_USER_AGENT="test")
c_man = Client(HTTP_USER_AGENT="test")
c_crew = Client(HTTP_USER_AGENT="test")
c_cust = Client(HTTP_USER_AGENT="test")

# Clean slate
User.objects.filter(username__in=["root", "manager1", "crew1", "customer1"]).delete()
Cart.objects.all().delete()
Order.objects.all().delete()
OrderItem.objects.all().delete()
MenuItem.objects.all().delete()
Category.objects.all().delete()

def step(n, desc):
    print(f"\n--- {n}. {desc} ---")

def assert_eq(actual, expected, label):
    ok = actual == expected
    print(f"  [{'OK' if ok else 'FAIL'}] {label}: got {actual!r} expected {expected!r}")
    if not ok:
        raise SystemExit(1)

# 5. Create groups + admin user, get token via Djoser
step(5, "Create groups and admin (Manager can log in)")
manager_group, _ = Group.objects.get_or_create(name="Manager")
crew_group, _ = Group.objects.get_or_create(name="Delivery crew")
admin = User.objects.create_superuser("root", "root@example.com", "rootpass123")
admin_token, _ = Token.objects.get_or_create(user=admin)
c_admin.defaults["HTTP_AUTHORIZATION"] = f"Token {admin_token}"
r = c_admin.get(f"{BASE}/groups/manager/users")
assert_eq(r.status_code, 200, "admin access manager group with admin token (criterion 2)")

# 1. Admin assigns manager1 to Manager group
step(1, "Admin assigns user to Manager group")
m_user = User.objects.create_user("manager1", "m@example.com", "manpass123")
m_token, _ = Token.objects.get_or_create(user=m_user)
r = c_admin.post(f"{BASE}/groups/manager/users", data={"username": "manager1"}, content_type="application/json")
assert_eq(r.status_code, 201, "admin POST /groups/manager/users")
m_user.refresh_from_db()
assert_eq(m_user.groups.filter(name="Manager").exists(), True, "manager1 in Manager group")

# 5. Manager logs in
m_token = m_user.auth_token.key if False else Token.objects.get(user=m_user).key
c_man.defaults["HTTP_AUTHORIZATION"] = f"Token {m_token}"
r = c_man.get(f"{BASE}/groups/manager/users")
assert_eq(r.status_code, 200, "manager1 token works (criterion 5)")

# 3. Admin adds menu item
step(3, "Admin adds menu items")
cat = Category.objects.create(slug="mains", title="Mains")
r = c_admin.post(f"{BASE}/menu-items", data={"title":"Pizza","price":"10.00","inventory":20,"category_id":cat.id,"featured":False}, content_type="application/json")
assert_eq(r.status_code, 201, "admin POST /menu-items")
pizza = MenuItem.objects.get(title="Pizza")
r = c_admin.post(f"{BASE}/menu-items", data={"title":"Pasta","price":"12.50","inventory":10,"category_id":cat.id,"featured":False}, content_type="application/json")
pasta = MenuItem.objects.get(title="Pasta")
r = c_admin.post(f"{BASE}/menu-items", data={"title":"Salad","price":"8.00","inventory":15,"category_id":cat.id,"featured":True}, content_type="application/json")
salad = MenuItem.objects.get(title="Salad")

# 4. Admin adds categories
step(4, "Admin adds category")
r = c_admin.post(f"{BASE}/categories", data={"slug":"desserts","title":"Desserts"}, content_type="application/json")
assert_eq(r.status_code, 201, "admin POST /categories")
assert_eq(Category.objects.filter(title="Desserts").exists(), True, "Desserts category created")

# 6. Manager updates item of the day (featured)
step(6, "Manager updates item of the day")
r = c_man.patch(f"{BASE}/menu-items/{pizza.id}", data={"featured":True}, content_type="application/json")
assert_eq(r.status_code, 200, "manager PATCH /menu-items/<id>")
pizza.refresh_from_db()
assert_eq(pizza.featured, True, "pizza featured set by manager")

# 7. Manager assigns delivery crew
step(7, "Manager assigns user to delivery crew")
crew_user = User.objects.create_user("crew1", "c@example.com", "crewpass123")
crew_token, _ = Token.objects.get_or_create(user=crew_user)
r = c_man.post(f"{BASE}/groups/delivery-crew/users", data={"username":"crew1"}, content_type="application/json")
assert_eq(r.status_code, 201, "manager POST /groups/delivery-crew/users")
crew_user.refresh_from_db()
assert_eq(crew_user.groups.filter(name="Delivery crew").exists(), True, "crew1 in Delivery crew group")

# 11. Customer registers via Djoser
step(11, "Customer registration")
r = c_cust.post(f"{BASE}/auth/users/", data={"username":"customer1","password":"custpass123","email":"c1@x.com","re_password":"custpass123"}, content_type="application/json")
print(f"  register status: {r.status_code} body: {r.content[:200]}")
if r.status_code == 400:
    r = c_cust.post(f"{BASE}/auth/users/", data={"username":"customer1","password":"custpass123","email":"c1@x.com"}, content_type="application/json")
    print(f"  register status2: {r.status_code} body: {r.content[:200]}")
assert r.status_code in (201, 200), f"register failed: {r.content}"

# 12. Customer logs in
step(12, "Customer logs in for token")
r = c_cust.post("/token/login/", data={"username":"customer1","password":"custpass123"}, content_type="application/json")
print(f"  login status: {r.status_code} body: {r.content[:200]}")
assert r.status_code == 200, f"login failed: {r.content}"
cust_token = r.json()["auth_token"]
c_cust.defaults["HTTP_AUTHORIZATION"] = f"Token {cust_token}"
# delivery crew login
crew_token = Token.objects.get(user=crew_user).key
c_crew.defaults["HTTP_AUTHORIZATION"] = f"Token {crew_token}"

# 13. Customer browses categories
step(13, "Customer browses categories")
r = c_cust.get(f"{BASE}/categories")
assert_eq(r.status_code, 200, "GET /categories")

# 14. Customer browses all menu items
step(14, "Customer browses menu items")
r = c_cust.get(f"{BASE}/menu-items")
assert_eq(r.status_code, 200, "GET /menu-items")
assert_eq(r.json()["count"] >= 3, True, "at least 3 items")

# 15. Filtered by category
step(15, "Filter by category")
r = c_cust.get(f"{BASE}/menu-items?category={cat.id}")
assert_eq(r.status_code, 200, "GET /menu-items?category=")
assert_eq(r.json()["count"], 3, "all 3 in Mains category")

# 16. Pagination present
step(16, "Pagination")
r = c_cust.get(f"{BASE}/menu-items?page=1")
assert_eq(r.status_code, 200, "GET /menu-items?page=1")
assert "count" in r.json() and "results" in r.json(), "pagination shape"

# 17. Sort by price
step(17, "Sort by price")
r = c_cust.get(f"{BASE}/menu-items?ordering=price")
results = r.json()["results"]
prices = [float(i["price"]) for i in results]
assert_eq(prices, sorted(prices), "items sorted ascending by price")

# 18. Add to cart
step(18, "Add to cart")
r = c_cust.post(f"{BASE}/cart/menu-items", data={"menuitem_id":pizza.id,"quantity":2}, content_type="application/json")
print(f"  add cart status: {r.status_code} body: {r.content[:200]}")
assert_eq(r.status_code, 201, "POST /cart/menu-items")
r = c_cust.post(f"{BASE}/cart/menu-items", data={"menuitem_id":pasta.id,"quantity":1}, content_type="application/json")
assert_eq(r.status_code, 201, "POST pasta to cart")

# 19. Access cart
step(19, "Access cart")
r = c_cust.get(f"{BASE}/cart/menu-items")
assert_eq(r.status_code, 200, "GET /cart/menu-items")
data = r.json()
cart_list = data if isinstance(data, list) else data.get("results", data)
assert_eq(len(cart_list), 2, "two items in cart")

# 20. Place order (cart -> order, cart cleared)
step(20, "Place order (cart -> order)")
r = c_cust.post(f"{BASE}/orders", data={}, content_type="application/json")
print(f"  order status: {r.status_code} body: {r.content[:300]}")
assert_eq(r.status_code, 201, "POST /orders")
order_data = r.json()
assert float(order_data["total"]) == 32.50, f"expected total 32.50 got {order_data['total']}"
print(f"  [OK] order total: {order_data['total']}")
r = c_cust.get(f"{BASE}/cart/menu-items")
data = r.json()
cart_list = data if isinstance(data, list) else data.get("results", data)
assert_eq(cart_list, [], "cart cleared after order")

# 21. Browse own orders
step(21, "Customer browses own orders")
r = c_cust.get(f"{BASE}/orders")
assert_eq(r.status_code, 200, "GET /orders")
data = r.json()
orders = data if isinstance(data, list) else data.get("results", data)
assert_eq(len(orders), 1, "1 order visible to customer")
order_id = order_data["id"]

# 8. Manager assigns order to delivery crew
step(8, "Manager assigns order to delivery crew")
r = c_man.patch(f"{BASE}/orders/{order_id}", data={"delivery_crew_id":crew_user.id}, content_type="application/json")
print(f"  assign status: {r.status_code} body: {r.content[:200]}")
assert_eq(r.status_code, 200, "manager PATCH /orders/<id>")

# 9. Delivery crew sees assigned order
step(9, "Delivery crew sees assigned order")
r = c_crew.get(f"{BASE}/orders")
assert_eq(r.status_code, 200, "GET /orders as crew")
data = r.json()
orders = data if isinstance(data, list) else data.get("results", data)
assert_eq(len(orders), 1, "crew sees 1 order")
r = c_crew.get(f"{BASE}/orders/{order_id}")
assert_eq(r.status_code, 200, "GET single order as crew")

# 10. Delivery crew updates status to delivered
step(10, "Delivery crew marks delivered (status=1)")
r = c_crew.patch(f"{BASE}/orders/{order_id}", data={"status":1}, content_type="application/json")
print(f"  deliver status: {r.status_code} body: {r.content[:200]}")
assert_eq(r.status_code, 200, "crew PATCH /orders/<id> status=1")
assert_eq(r.json()["status"], True, "order status is True (delivered)")

print("\nALL 21 CRITERIA PASSED")
