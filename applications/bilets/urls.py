from django.urls import path, include
from . import views
from applications.bilets.recommendations import TicketRecommendationsView
from applications.bilets.views import TicketAPIView, OrderActivationAPIView, UserOrderHistoryAPIView, OrderViewSet, \
    CommentModelViewSet, UserActionHistoryAPIView
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()

router.register('orders', OrderViewSet, basename='order')
router.register('comments', CommentModelViewSet)
router.register('', TicketAPIView, basename='ticket')

urlpatterns = [
    path('activate/<str:activation_code>/', OrderActivationAPIView.as_view(), name='order-activation'),
    path('qr-code/<int:pk>/', views.OrderQRCodeAPIView.as_view(), name='order-qr-code'),
    path('user-order-history/', UserOrderHistoryAPIView.as_view(), name='user-order-history'),
    path('ticket-recommendations/', TicketRecommendationsView.as_view(), name='ticket-recommendations'),
    path('get/<str:name>/', UserActionHistoryAPIView.as_view(), name='user-action-history'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += router.urls
