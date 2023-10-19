from django.test import TestCase
from applications.account.models import *
from django.test import TestCase
from django.core.cache import cache
from django.test import TestCase
import requests


class CustomUserModelTestCase(TestCase):
    """
        Тесты для модели CustomUser.
    """

    def setUp(self):
        """
            Настройка тестовых данных.
        """
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="testpassword",
            name="John",
            surname="Doe",
            phone_number="1234567890"
        )

    def test_create_user(self):
        """
            Проверка создания обычного пользователя.
        """
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.name, "John")
        self.assertEqual(self.user.surname, "Doe")
        self.assertEqual(self.user.phone_number, "1234567890")

#
class MyCacheTestCase(TestCase):
    """
        Тесты для кэша.
    """

    def test_caching(self):
        """
            Проверка кэширования значения.
        """
        cache.set('my_key', 'my_value', 60)

        cached_value = cache.get('my_key')
        self.assertEqual(cached_value, 'my_value')

    def test_cache_timeout(self):
        """
            Проверка срока действия кэша.
        """
        cache.set('my_key', 'my_value', 1)

        import time
        time.sleep(2)

        cached_value = cache.get('my_key')
        self.assertIsNone(cached_value)


