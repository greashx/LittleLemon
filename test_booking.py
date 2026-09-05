"""End-to-end test for the booking system, all 5 criteria."""
import os, django, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LittleLemon.settings")
django.setup()

from django.test import Client
from booking.models import Booking

c = Client()

# Clear data
Booking.objects.all().delete()

def step(n, desc):
    print(f"\n--- {n}. {desc} ---")

def assert_eq(actual, expected, label):
    ok = actual == expected
    print(f"  [{'OK' if ok else 'FAIL'}] {label}: got {actual!r} expected {expected!r}")
    if not ok:
        raise SystemExit(1)

# 1. App registration and DB
step(1, "App + DB configured")
from django.conf import settings
print(f"  booking in INSTALLED_APPS: {'booking' in settings.INSTALLED_APPS}")
print(f"  DATABASES engine: {settings.DATABASES['default']['ENGINE']}")
print(f"  Booking table exists: {Booking._meta.db_table}")

# 2. Frontend UI loaded
step(2, "Home page loads with date picker and today pre-filled")
r = c.get('/')
assert_eq(r.status_code, 200, "GET / (landing)")
body = r.content.decode()
import re
assert_eq('Little Lemon' in body, True, "landing page contains title")
assert_eq('{% static' not in body, True, "template rendered (no raw template tags)")

# Booking form at /book
r = c.get('/book')
assert_eq(r.status_code, 200, "GET /book (booking form)")
form_body = r.content.decode()
m_date = re.search(r'type="date"', form_body)
assert_eq(bool(m_date), True, "date input has type='date' in booking form")
assert_eq('id="first_name"' in form_body, True, "first_name present in booking form")
assert_eq('id="reservation_slot"' in form_body, True, "reservation_slot present in booking form")
assert_eq('required' in form_body.split('id="reservation_date"')[1][:200], True, "date is required in booking form")

# Check the JS auto-pre-selects today
js_check = c.get('/static/booking/app.js')
assert_eq(js_check.status_code, 200, "static JS served")
js_text = b''.join(js_check.streaming_content).decode() if hasattr(js_check, 'streaming_content') and not hasattr(js_check, 'content') else js_check.content.decode()
assert_eq('todayISO' in js_text and '$date.value = todayISO()' in js_text, True, "JS auto-selects today's date")

# 4. JSON API
step(4, "JSON API: /api/bookings?date=...")
r = c.get('/api/bookings')
assert_eq(r.status_code, 200, "GET /api/bookings")
r = c.get('/api/bookings?date=2026-12-25')
assert_eq(r.status_code, 200, "GET /api/bookings?date=2026-12-25")
assert_eq(r.json(), [], "no bookings yet -> empty list")

# 5. Duplicate prevention (backend)
step(5, "Duplicate booking prevention (backend)")
payload = {"first_name": "Alice", "reservation_date": "2026-12-25", "reservation_slot": 11}
r = c.post('/api/book', data=json.dumps(payload), content_type='application/json')
print(f"  first POST status: {r.status_code} body: {r.content[:200]}")
assert_eq(r.status_code, 201, "first POST succeeds")
# Duplicate
r = c.post('/api/book', data=json.dumps(payload), content_type='application/json')
print(f"  duplicate POST status: {r.status_code} body: {r.content[:200]}")
assert_eq(r.status_code, 409, "duplicate POST rejected with 409")

# 4. JSON returns the booking
r = c.get('/api/bookings?date=2026-12-25')
data = r.json()
assert_eq(len(data), 1, "1 booking for 2026-12-25")
assert_eq(data[0]['first_name'], 'Alice', "first_name matches")
assert_eq(data[0]['reservation_slot'], 11, "slot matches")

# Slots endpoint excludes booked
r = c.get('/api/slots?date=2026-12-25')
data = r.json()
assert_eq(11 in data['booked'], True, "slot 11 reported as booked")
available = [s for s in data['slots'] if s not in data['booked']]
assert_eq(11 not in available, True, "slot 11 hidden from available")
assert_eq(12 not in available, False, "slot 12 still available")

# Different slot works
payload2 = {"first_name": "Bob", "reservation_date": "2026-12-25", "reservation_slot": 12}
r = c.post('/api/book', data=json.dumps(payload2), content_type='application/json')
assert_eq(r.status_code, 201, "different slot is allowed")

# Different date same slot
payload3 = {"first_name": "Alice", "reservation_date": "2026-12-26", "reservation_slot": 11}
r = c.post('/api/book', data=json.dumps(payload3), content_type='application/json')
assert_eq(r.status_code, 201, "same slot on different date is allowed")

# 3. fetch usage verified
step(3, "fetch() API usage in frontend")
assert_eq("fetch(" in js_text, True, "JS uses fetch() API")
assert_eq("method: 'POST'" in js_text or '"POST"' in js_text, True, "POST via fetch")
# Date change triggers refresh
assert_eq("addEventListener('change'" in js_text, True, "date change triggers fetch refresh")
# No-bookings message in booking form
assert_eq('No Bookings' in form_body, True, "UI shows 'No Bookings' when empty")

# 4. No bookings UI handling
r = c.get('/api/bookings?date=2099-01-01')
assert_eq(r.json(), [], "no bookings for far future date")

print("\nALL BOOKING CRITERIA PASSED")
