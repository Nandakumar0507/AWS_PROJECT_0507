from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Role

User = get_user_model()


class AuthTests(TestCase):
    def test_user_creation_with_role(self):
        user = User.objects.create_user(
            email="patient@example.com",
            username="patient1",
            password="StrongPass123!",
            role=Role.PATIENT,
        )
        self.assertEqual(user.role, Role.PATIENT)
