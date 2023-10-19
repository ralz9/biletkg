from rest_framework.test import APIClient, APITestCase
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from .models import Ticket, Comment, Order
from .serializers import TicketSerializer, CommentSerializer, OrderSerializer
import requests


User = get_user_model()

class RecommendationTest(TestCase):
    """
        Тесты для рекомендаций.
    """

    def test_recommendations(self):
        """
            Проверка получения рекомендаций.
        """
        url = 'http://localhost:8000/api/bilets/ticket-recommendations/'
        response = requests.get(url)

        self.assertEqual(response.status_code, 200)
        recommendations = response.json()
        self.assertIsNotNone(recommendations)

############
# Model
###########
class TicketModelTestCase(TestCase):

    def test_decrease_total_ticket(self):
        user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword"
        )
        ticket = Ticket.objects.create(
            owner=user,
            title="Test Ticket",
            location="Test Location",
            price=10.0,
            total_ticket=10,
            date="2023-09-30T12:00:00Z",
            description="Test Description"
        )
        #
        initial_total_ticket = ticket.total_ticket
        ticket.decrease_total_ticket()
        updated_ticket = Ticket.objects.get(pk=ticket.pk)

        self.assertEqual(updated_ticket.total_ticket, initial_total_ticket - 1)

###########
# Ticket ApiView
###########
class TicketAPIViewTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword"
        )
        self.ticket = Ticket.objects.create(
            title="Test Ticket",
            location="Test Location",
            price=10.0,
            total_ticket=10,
            date="2023-09-30T12:00:00Z",
            description="Test Description"
        )

    def test_list_tickets(self):
        url = reverse("ticket-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_ticket(self):
        url = reverse("ticket-detail", args=[self.ticket.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_ticket(self):
        url = reverse("ticket-list")
        data = {
            "title": "New Ticket",
            "location": "New Location",
            "price": 20.0,
            "total_ticket": 5,
            "date": "2023-10-15T14:00:00Z",
            "description": "New Description"
        }
#
class CommentModelTestCase(TestCase):

    def test_comment_creation(self):
        user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword"
        )
        ticket = Ticket.objects.create(
            owner=user,
            title="Test Ticket",
            location="Test Location",
            price=10.0,
            total_ticket=10,
            date="2023-09-30T12:00:00Z",
            description="Test Description"
        )
        comment = Comment.objects.create(
            owner=user,
            post=ticket,
            body="Test Comment"
        )

        self.assertEqual(comment.owner, user)
        self.assertEqual(comment.post, ticket)
        self.assertEqual(comment.body, "Test Comment")

class OrderModelTestCase(TestCase):

    def test_create_activation_code(self):
        user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword"
        )
        ticket = Ticket.objects.create(
            owner=user,
            title="Test Ticket",
            location="Test Location",
            price=10.0,
            total_ticket=10,
            date="2023-09-30T12:00:00Z",
            description="Test Description"
        )
        order = Order.objects.create(
            user=user,
            ticket=ticket,
            name="Test Order",
            phone_number="1234567890"
        )

        self.assertFalse(order.activation_code)
        order.create_activation_code()
        self.assertTrue(order.activation_code)

#####################
# APIview
###############################
class TicketAPIViewTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword"
        )
        self.ticket = Ticket.objects.create(
            owner=self.user,
            title="Test Ticket",
            location="Test Location",
            price=10.0,
            total_ticket=10,
            date="2023-09-30T12:00:00Z",
            description="Test Description"
        )

    def test_list_tickets(self):
        url = reverse("ticket-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_ticket(self):
        url = reverse("ticket-detail", args=[self.ticket.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_ticket(self):
        url = reverse("ticket-list")
        data = {
            "title": "New Ticket",
            "location": "New Location",
            "price": 20.0,
            "total_ticket": 5,
            "date": "2023-10-15T14:00:00Z",
            "description": "New Description"
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#
# #########################
# # Comment View
# ############################
class CommentModelViewSetTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword"
        )
        self.ticket = Ticket.objects.create(
            owner=self.user,
            title="Test Ticket",
            location="Test Location",
            price=10.0,
            total_ticket=10,
            date="2023-09-30T12:00:00Z",
            description="Test Description"
        )
        self.comment = Comment.objects.create(
            owner=self.user,
            post=self.ticket,
            body="Test Comment"
        )

    def test_list_comments(self):
        url = reverse("comment-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_comment(self):
        url = reverse("comment-detail", args=[self.comment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_comment(self):
        url = reverse("comment-list")
        data = {
            "post": self.ticket.id,
            "body": "New Comment"
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
# ##########################
# # Order View
# ##########################
class OrderViewSetTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword"
        )
        self.ticket = Ticket.objects.create(
            owner=self.user,
            title="Test Ticket",
            location="Test Location",
            price=10.0,
            total_ticket=10,
            date="2023-09-30T12:00:00Z",
            description="Test Description"
        )
        self.order = Order.objects.create(
            user=self.user,
            ticket=self.ticket,
            name="Test Order",
            phone_number="1234567890",
            activation_code="testcode"
        )

    def test_list_orders(self):
        url = reverse("order-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_order(self):
        url = reverse("order-detail", args=[self.order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_order(self):
        url = reverse("order-list")
        data = {
            "ticket": self.ticket.id,
            "name": "New Order",
            "phone_number": "9876543210"
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class OrderActivationAPIViewTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword"
        )
        self.ticket = Ticket.objects.create(
            owner=self.user,
            title="Test Ticket",
            location="Test Location",
            price=10.0,
            total_ticket=10,
            date="2023-09-30T12:00:00Z",
            description="Test Description"
        )
        self.order = Order.objects.create(
            user=self.user,
            ticket=self.ticket,
            name="Test Order",
            phone_number="1234567890",
            activation_code='shortcode'
        )
        self.client.force_authenticate(user=self.user)

    def test_already_activated_order(self):
        self.order.is_active = True
        self.order.save()

        url = reverse("order-activation", kwargs={"activation_code": self.order.activation_code})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_activation_code(self):
        invalid_code = "invalidcode"
        url = reverse("order-activation", kwargs={"activation_code": invalid_code})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
# #
# #
#
# ####################################
# # Order History
####################################
class UserOrderHistoryAPIViewTestCase(APITestCase):
    def setUp(self):

        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword"
        )

        self.ticket1 = Ticket.objects.create(
            owner=self.user,
            title="Ticket 1",
            location="Location 1",
            price=10.0,
            total_ticket=10,
            date="2023-09-30T12:00:00Z",
            description="Description 1"
        )
        self.ticket2 = Ticket.objects.create(
            owner=self.user,
            title="Ticket 2",
            location="Location 2",
            price=15.0,
            total_ticket=5,
            date="2023-10-15T14:00:00Z",
            description="Description 2"
        )

        self.order1 = Order.objects.create(
            user=self.user,
            ticket=self.ticket1,
            name="Order 1",
            phone_number="1234567890"
        )
        self.order2 = Order.objects.create(
            user=self.user,
            ticket=self.ticket2,
            name="Order 2",
            phone_number="9876543210"
        )

        self.client.force_authenticate(user=self.user)

    def test_user_order_history(self):

        url = reverse("user-order-history")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = OrderSerializer([self.order2, self.order1], many=True).data
        self.assertEqual(response.data, expected_data)

    def test_user_order_history_unauthenticated(self):

        url = reverse("user-order-history")

        self.client.force_authenticate(user=None)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

