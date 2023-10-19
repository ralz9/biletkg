from rest_framework import generics
from .models import Ticket
from .serializers import TicketSerializer


class TicketRecommendationsView(generics.ListAPIView):
    serializer_class = TicketSerializer

    def get_queryset(self):
        return Ticket.objects.all()
