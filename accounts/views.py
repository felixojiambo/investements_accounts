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

class InvestmentAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InvestmentAccount.objects.all()
    serializer_class = InvestmentAccountSerializer
    permission_classes = [IsAuthenticated, IsAccountFullAccess]

class TransactionCreateView(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsAccountPostOnly]

class AdminTransactionView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        user = self.request.user
        transactions = Transaction.objects.filter(account__userinvestmentaccount__user=user)

        # Apply date filter if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            transactions = transactions.filter(created_at__range=[start_date, end_date])

        return transactions

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        total_balance = self.get_queryset().aggregate(Sum('account__balance'))['account__balance__sum']
        response.data = {'transactions': response.data, 'total_balance': total_balance}
        return response
