from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from applications.bilets.serializers import *
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import authentication_classes
from applications.bilets.models import *
from applications.bilets.paginations import *
from applications.bilets.permissions import *
from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework import generics
import logging
from io import BytesIO
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Order
import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.conf import settings
import os


class TicketAPIView(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    pagination_class = LargeResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['owner', 'title']
    search_fields = ['title']
    ordering_fields = ['id']

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        instance.count_views += 1
        instance.save(update_fields=['count_views'])
        return Response(serializer.data)

    @action(methods=['POST'], detail=True)
    def like(self, request, pk, *args, **kwargs):
        user = request.user
        like_obj, _ = Like.objects.get_or_create(owner=user, post_id=pk)
        like_obj.is_like = not like_obj.is_like
        like_obj.save()
        like_status = 'liked'
        if not like_obj.is_like:
            like_status = 'unliked'

        return Response({'status': like_status})

    @action(methods=['POST'], detail=True)
    def favorite(self, request, pk, *args, **kwargs):
        logger = logging.getLogger(__name__)
        user = request.user
        if user.is_anonymous:
            return Response({'error': 'Только аутентифицированные пользователи могут выполнять это действие'},
                            status=http_status.HTTP_401_UNAUTHORIZED)

        favorite_obj, _ = Favorite.objects.get_or_create(owner=user, post_id=pk)
        favorite_obj.is_favorite = not favorite_obj.is_favorite
        favorite_obj.save()
        status = 'favorites'
        if not favorite_obj.is_favorite:
            status = 'not favorite'

        logger.info(f"User {user.username} marked ticket {pk} as {status}")

        return Response({'status': status})

    @action(methods=['POST'], detail=True)
    def rating(self, request, pk, *args, **kwargs):
        user = request.user
        serializer = RatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rating_obj, _ = Rating.objects.get_or_create(owner=request.user, post_id=pk)
        rating_obj.rating = serializer.data['rating']
        rating_obj.save()
        return Response(serializer.data)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        elif self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CommentModelViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(user=self.request.user)

        return Response('Заказ успешно создан, но требует подтверждения.', status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def confirm_order(self, activation_code):
        order = get_object_or_404(Order, activation_code=activation_code)
        if not order.is_active:
            order.is_active = True
            order.activation_code = ''
            order.save(update_fields=['is_active', 'activation_code'])

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            data = f"Order ID: {order.id}\nTicket: {order.ticket.title}\nOwner: {order.user.username}"
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            img_path = os.path.join(settings.MEDIA_ROOT, f'qrcodes/order_{order.id}.png')
            img.save(img_path, format="PNG")

            email = order.user.email
            code = order.activation_code
            name = order.user.username
            send_order_email(email, code, name, img_path)

            return Response('Заказ успешно подтвержден и QR-код отправлен на вашу почту', status=status.HTTP_200_OK)
        else:
            return Response('Заказ уже был подтвержден', status=status.HTTP_400_BAD_REQUEST)


class OrderActivationAPIView(APIView):
    def get(self, request, activation_code):
        order = Order.objects.filter(activation_code=activation_code).first()

        if not order:
            return Response('Заказ не найден', status=status.HTTP_404_NOT_FOUND)

        if order.is_active:
            img_url = os.path.join(settings.MEDIA_URL, f'qrcodes/order_{order.id}.png')

            full_img_url = f'http://localhost:8000{img_url}'
            return Response({'message': 'Заказ уже был подтвержден', 'qr_code_image_url': full_img_url}, status=status.HTTP_400_BAD_REQUEST)

        if order.user == request.user:
            return Response('Вы уже активировали этот заказ')

        order.is_active = True
        order.save(update_fields=['is_active'])

        order.ticket.decrease_total_ticket()


        ticket_id = order.ticket.id
        ticket_title = order.ticket.title
        location = order.ticket.location
        date = order.ticket.date
        owner_name = order.user
        phone_number = "0507812318"
        message = "Для связи с нами"
        data = (f"Ticket ID: {ticket_id}"
                f"\nTicket: {ticket_title}"
                f"\nLocation: {location}"
                f"\nDate: {date}"
                f"\nOwner: {owner_name}"
                f"\nPhone: {phone_number}\n"
                f"Message: {message}")

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        img_path = os.path.join(settings.MEDIA_ROOT, f'qrcodes/order_{order.id}.png')
        img.save(img_path, format="PNG")

        img_url = os.path.join(settings.MEDIA_URL, f'qrcodes/order_{order.id}.png')

        full_img_url = f'http://localhost:8000{img_url}'

        response_data = {
            'message': 'Успешно, Вы подтвердили покупку',
            'qr_code_image_url': full_img_url
        }

        qr_code_image_url = os.path.join(settings.MEDIA_URL[1:], f'qrcodes/order_{order.id}.png')

        return Response({'message': 'Заказ успешно подтвержден и QR-код отправлен на вашу почту',
                     'qr_code_image_url': full_img_url}, status=status.HTTP_200_OK)


class OrderQRCodeAPIView(generics.RetrieveAPIView):
    queryset = Order.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if not instance.is_active:
            return Response('Заказ не был подтвержден', status=status.HTTP_400_BAD_REQUEST)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        data = f"Order ID: {instance.id}\nTicket: {instance.ticket.title}\nOwner: {instance.user.username}"
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        media_root = settings.MEDIA_ROOT
        img_path = os.path.join(media_root, f'qr_codes/order_{instance.id}.png')
        img.save(img_path, format="PNG")

        img_url = os.path.join(settings.MEDIA_URL[1:], f'qr_codes/order_{instance.id}.png')

        return Response({'qr_code_image_url': img_url})


class UserOrderHistoryAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

# class AllCommentsAPIView(viewsets.ReadOnlyModelViewSet):
#     queryset = Comment.objects.all().order_by('-id')
#     serializer_class = CommentSerializer
#     permission_classes = []


class UserActionHistoryAPIView(APIView):
    def get(self, request, name):
        if name == "like":
            likes = Like.objects.filter(owner=request.user)

            liked_posts = []

            for like in likes:
                post = like.ticket

                post_data = {
                    "id": post.id,
                    "title": post.title,
                    "liked_at": like.created_at,
                }
                liked_posts.append(post_data)

            return Response({"liked_posts": liked_posts})

        elif name == "favorite":
            favorites = Favorite.objects.filter(owner=request.user)

            favorite_posts = []

            for favorite in favorites:
                post = favorite.ticket

                post_data = {
                    "id": post.id,
                    "title": post.title,
                    "favorited_at": favorite.created_at,
                }
                favorite_posts.append(post_data)

            return Response({"favorite_posts": favorite_posts})

        elif name == "rating":

            ratings = Rating.objects.filter(owner=request.user)

            rated_posts = []

            for rating in ratings:
                post = rating.post

                post_data = {
                    "id": post.id,
                    "title": post.title,
                    "rating": rating.rating,
                    "rated_at": rating.created_at,
                }
                rated_posts.append(post_data)

            return Response({"rated_posts": rated_posts})

        elif name == "comment":

            comments = Comment.objects.filter(owner=request.user)

            commented_posts = []

            for comment in comments:
                post = comment.post
                post_data = {
                    "id": post.id,
                    "title": post.title,
                    "commented_at": comment.created_at,
                }
                commented_posts.append(post_data)

            return Response({"commented_posts": commented_posts})

        return Response("Invalid action name", status=status.HTTP_400_BAD_REQUEST)