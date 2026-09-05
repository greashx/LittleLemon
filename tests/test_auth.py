from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token


class AuthFlowTest(TestCase):
    """End-to-end Djoser + DRF token authentication flow."""

    def setUp(self):
        self.client = APIClient()

    def test_register_via_djoser(self):
        payload = {
            "username": "newuser",
            "password": "SuperSafe123!",
            "email": "newuser@example.com",
        }
        r = self.client.post("/auth/users/", payload, format="json")
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_201_CREATED))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_obtain_auth_token(self):
        User.objects.create_user(username="tokenuser", password="pw12345!")
        r = self.client.post(
            "/api-token-auth/",
            {"username": "tokenuser", "password": "pw12345!"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("token", r.json())
        self.assertEqual(len(r.json()["token"]), 40)

    def test_obtain_auth_token_invalid(self):
        User.objects.create_user(username="tokenuser", password="pw12345!")
        r = self.client.post(
            "/api-token-auth/",
            {"username": "tokenuser", "password": "WRONG"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_authenticates_protected_endpoint(self):
        user = User.objects.create_user(username="authuser", password="pw12345!")
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        r = self.client.get("/auth/users/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
