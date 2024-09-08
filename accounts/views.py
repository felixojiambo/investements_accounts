from django.db.models import Sum
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import InvestmentAccount, Transaction
from .permissions import IsAccountFullAccess, IsAccountPostOnly
from .serializers import InvestmentAccountSerializer, TransactionSerializer


class InvestmentAccountListCreateView(generics.ListCreateAPIView):
    queryset = InvestmentAccount.objects.all()
    serializer_class = InvestmentAccountSerializer
    permission_classes = [IsAuthenticated, IsAccountFullAccess]
