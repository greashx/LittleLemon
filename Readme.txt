LittleLemon REST API — Peer Review Guide
========================================

Base server URL
---------------
http://127.0.0.1:8000/


Project layout
--------------
LittleLemon/        Django project (settings.py, urls.py, wsgi.py)
  Restaurant/       DRF app — MenuItemSerializer + BookingViewSet (ModelViewSet)
  booking/          Static HTML frontend + booking JSON endpoints
  LittleLemonDRF/   DRF app — Categories, MenuItems, Cart, Orders, Groups
  tests/            Django TestCase unit tests (24 tests, all passing)

Run the server:
    python manage.py runserver

Run the test suite:
    python manage.py test tests --noinput


Authentication
--------------
All DRF endpoints require authentication. Two auth schemes are wired:

  1) DRF Token Authentication
       POST /api-token-auth/        { "username": "...", "password": "..." }
                                     -> { "token": "<40-char-token>" }
       Header for protected calls:
         Authorization: Token <token>

  2) Djoser Authentication
       POST /auth/users/            register a new user
       POST /auth/token/login/      exchange credentials for an auth_token
       POST /auth/token/logout/     invalidate the auth_token
       Header:
         Authorization: Token <auth_token>

JSON responses use Content-Type: application/json. Browsable API pages
(GET in a browser) are served at the same URLs and require the same auth.


Static HTML pages
-----------------
GET  /                       Little Lemon landing page (index.html)
GET  /book                   Booking form page (booking/home.html)
GET  /static/<path>           Static assets (CSS / JS / images)


Menu endpoints (Restaurant app)
-------------------------------
Full CRUD via DRF generic views. All require Token auth.

GET     /restaurant/menu/menu-items/                List menu items (paginated, supports ?ordering=)
POST    /restaurant/menu/menu-items/                Create a menu item
        Body: { "Title": "...", "Price": "...", "Inventory": 0 }

GET     /restaurant/menu/menu-items/<int:pk>        Retrieve a single menu item
PUT     /restaurant/menu/menu-items/<int:pk>        Replace a menu item
PATCH   /restaurant/menu/menu-items/<int:pk>        Partial update of a menu item
DELETE  /restaurant/menu/menu-items/<int:pk>        Delete a menu item


Booking / Table reservation endpoints
-------------------------------------
Two booking surfaces exist in the project:

A) Restaurant app — DRF ModelViewSet (requires Token auth):
   GET     /restaurant/booking/tables/               List bookings (paginated)
   POST    /restaurant/booking/tables/               Create a booking
           Body: { "Name": "...", "No_of_guests": 2, "BookingDate": "2026-12-25T19:00:00Z" }
   GET     /restaurant/booking/tables/<int:pk>/      Retrieve a booking
   PUT     /restaurant/booking/tables/<int:pk>/      Replace a booking
   PATCH   /restaurant/booking/tables/<int:pk>/      Partial update
   DELETE  /restaurant/booking/tables/<int:pk>/      Delete a booking

B) Public booking app (no auth, JSON, used by the static frontend):
   GET     /api/bookings?date=YYYY-MM-DD             List bookings for a date
   GET     /api/slots?date=YYYY-MM-DD                Available reservation slots
   POST    /api/book                                 Create a reservation (CSRF-exempt)
           Body: { "first_name": "...", "reservation_date": "YYYY-MM-DD", "reservation_slot": 12 }
           Returns 201 on success, 409 if slot already booked, 400 on invalid input.


LittleLemonDRF endpoints (extended catalog / ordering API)
-----------------------------------------------------------
GET     /api/categories                              List categories
POST    /api/categories                              Create a category
GET     /api/menu-items                              List DRF menu items (paginated, ?category=, ?ordering=)
POST    /api/menu-items                              Create a DRF menu item
GET     /api/menu-items/<int:pk>                     Retrieve
PUT/PATCH /api/menu-items/<int:pk>                   Update
DELETE  /api/menu-items/<int:pk>                     Delete
GET     /api/groups/manager/users                    List managers (admin/manager token)
POST    /api/groups/manager/users                    Assign user to Manager group
GET/DELETE /api/groups/manager/users/<int:userId>    Inspect / remove a manager
GET     /api/groups/delivery-crew/users              List delivery crew (admin/manager)
POST    /api/groups/delivery-crew/users              Assign user to Delivery crew
GET/DELETE /api/groups/delivery-crew/users/<int:userId>
GET/POST /api/cart/menu-items                        View / add to cart (customer)
DELETE  /api/cart/menu-items                         Clear cart
GET/POST /api/orders                                 View / place orders
GET/PUT/PATCH/DELETE /api/orders/<int:pk>            Inspect / update / cancel order
                                                     (manager can assign delivery_crew, crew can update status)


User registration & authentication endpoints
--------------------------------------------
Djoser — both prefixes expose identical endpoints:
   /auth/...   and   /api/auth/...

POST    /auth/users/                                 Register a new user
           Body: { "username": "...", "password": "...", "email": "..." }
GET     /auth/users/                                 List users (auth required)
GET     /auth/users/<username>/                      Retrieve a single user
DELETE  /auth/users/<username>/                      Delete a user
POST    /auth/users/activation/                      Activate account (if enabled)
POST    /auth/users/set_password/                    Change password
POST    /auth/users/reset_password/                  Request password reset
POST    /auth/users/reset_password_confirm/          Confirm password reset
POST    /auth/users/set_username/                    Change username
POST    /auth/users/reset_username/                  Request username reset
POST    /auth/users/reset_username_confirm/          Confirm username reset

Token-based sessions:
POST    /auth/token/login/                           { username, password } -> { auth_token }
POST    /auth/token/logout/                          Revoke the supplied auth_token

JWT (optional, also wired):
POST    /auth/jwt/create/                            { username, password } -> { access, refresh }
POST    /auth/jwt/refresh/                           { refresh } -> { access }
POST    /auth/jwt/verify/                            { token } -> {}

DRF obtain_auth_token (simple alternative):
POST    /api-token-auth/                             { username, password } -> { token }


How to test
-----------
Option A — Browser (browsable DRF UI)
  1. Start the server:  python manage.py runserver
  2. Get a token:        POST http://127.0.0.1:8000/api-token-auth/
                          with JSON body { "username": "root", "password": "rootpass123" }
  3. Open any endpoint in Chrome / Firefox, e.g.
       http://127.0.0.1:8000/restaurant/menu/menu-items/
  4. Click the green "Authorize" button (top-right) and paste:
       Token <your-token>
  5. Use the form to issue GET / POST / PUT / PATCH / DELETE.

Option B — Insomnia / Postman
  1. Import Insomnia_workspace.json (File -> Import -> From File).
     The workspace contains every endpoint pre-wired with auth templates.
  2. Set the Base environment variables:
       base_url = http://127.0.0.1:8000
       auth_token = <paste token from /api-token-auth/ or /auth/token/login/>
  3. Send requests. Authed calls automatically pick up the
     "Authorization: Token {{ auth_token }}" header.

Option C — curl
  TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api-token-auth/ \
           -H 'Content-Type: application/json' \
           -d '{"username":"root","password":"rootpass123"}' | python -c 'import sys,json;print(json.load(sys.stdin)["token"])')

  curl -H "Authorization: Token $TOKEN" http://127.0.0.1:8000/restaurant/menu/menu-items/

  curl -X POST -H "Authorization: Token $TOKEN" \
       -H 'Content-Type: application/json' \
       -d '{"Title":"Salad","Price":"9.50","Inventory":10}' \
       http://127.0.0.1:8000/restaurant/menu/menu-items/


Expected status codes
---------------------
200 OK              Successful GET / PATCH / PUT
201 Created         Successful POST
204 No Content      Successful DELETE
400 Bad Request     Validation failure
401 Unauthorized    Missing / invalid token
403 Forbidden       Authenticated but not permitted (role-based restrictions)
404 Not Found       Object does not exist


Notes for reviewers
-------------------
- Default admin: username=root, password=rootpass123 (created during local setup).
- Default roles: Manager, Delivery crew (assign via /api/groups/.../users).
- Pagination is enabled (PAGE_SIZE=2 in REST_FRAMEWORK). Use ?page=N or
  ?ordering=field,-otherfield to navigate.
- Anonymous access to any DRF endpoint returns 401 by design (settings.REST_FRAMEWORK
  DEFAULT_PERMISSION_CLASSES = (IsAuthenticated,)).
- The /api/bookings, /api/slots, /api/book endpoints (booking app) are public and
  used by the static HTML frontend at / and /book.


Files of interest
-----------------
LittleLemon/settings.py        Django + DRF + Djoser config
LittleLemon/urls.py            Project-level URL routing + DefaultRouter
Restaurant/views.py            MenuItemsView, SingleMenuItemView, BookingViewSet
Restaurant/serializers.py      MenuItemSerializer, BookingSerializer
booking/views.py               Public booking JSON + HTML views
LittleLemonDRF/views.py        Categories / menu-items / cart / orders / groups
tests/test_models.py           Menu model unit tests
tests/test_views.py            Menu + Booking CRUD unit tests
tests/test_auth.py             Djoser + DRF token auth flow tests
Insomnia_workspace.json        Pre-built Insomnia collection for peer testing
