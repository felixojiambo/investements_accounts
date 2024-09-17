from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import InvestmentAccount, UserAccount, Transaction
from .permissions import DynamicAccountPermission
from .serializers import (
    UserAccountSerializer, InvestmentAccountSerializer,
    CreateUserAccountSerializer, UserSerializer,
    CreateTransactionSerializer, TransactionSerializer,
    TransactionListSerializer
)


def validate_account_id(request):
    """
    Validate and retrieve account_id from request.
    Raises ValidationError if account_id is missing.
    """
    account_id = request.query_params.get('account_id') or request.data.get('account_id')
    if not account_id:
        raise ValidationError({"error": "Account ID is required."})
    return account_id


class InvestmentAccountCreateView(generics.CreateAPIView):
    """
    API view for creating new InvestmentAccount.
    """
    queryset = InvestmentAccount.objects.all()
    serializer_class = InvestmentAccountSerializer


class UserAccountCreateView(generics.CreateAPIView):
    """
    API view for creating new UserAccount with transaction atomicity.
    """
    serializer_class = CreateUserAccountSerializer
    authentication_classes = [JWTAuthentication]

    @transaction.atomic
    def perform_create(self, serializer):
        """Save UserAccount with atomic transaction."""
        serializer.save()


class UserCreateView(generics.CreateAPIView):
    """
    API view for creating a new user, accessible without authentication.
    """
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class UserAccountListView(generics.ListAPIView):
    """
    API view for listing UserAccounts of the authenticated user.
    """
    serializer_class = UserAccountSerializer
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        """Return UserAccounts ordered by creation date."""
        return UserAccount.objects.filter(user=self.request.user).order_by('-created_at')


class UserAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, or deleting a UserAccount.
    """
    serializer_class = UserAccountSerializer
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        """Retrieve UserAccount for the authenticated user."""
        return UserAccount.objects.filter(user=self.request.user)

    @transaction.atomic
    def perform_update(self, serializer):
        """Save updates to UserAccount with atomic transaction."""
        serializer.save()

    @transaction.atomic
    def perform_destroy(self, instance):
        """Delete UserAccount with atomic transaction."""
        instance.delete()


class TransactionListView(generics.ListAPIView):
    """
    API view for listing transactions for a specified account.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, DynamicAccountPermission]
    serializer_class = TransactionListSerializer
    pagination_class = PageNumberPagination

    @extend_schema(
        parameters=[
            OpenApiParameter(name='account_id', type=int, required=True,
                             description='The ID of the account to list transactions for.'),
            OpenApiParameter(name='page', type=int, description='Page number for paginated results.')
        ],
        responses={
            200: TransactionListSerializer(many=True),
            400: OpenApiResponse(description='Bad Request'),
            403: OpenApiResponse(description='Forbidden - Account not accessible')
        },
        operation_id='listTransactions',
        description='Retrieve transactions for a specified account ordered by creation date.'
    )
    def get(self, request, *args, **kwargs):
        """
        List transactions for a given account, ordered by creation date.
        """
        account_id = request.query_params.get('account_id')

        if not account_id:
            return Response({"error": "account_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = UserAccount.objects.get(id=account_id, user=request.user)
        except UserAccount.DoesNotExist:
            return Response({"error": "Account not found or not accessible"}, status=status.HTTP_403_FORBIDDEN)

        transactions = Transaction.objects.filter(user_account=account).order_by('-created_at')

        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateTransactionView(generics.CreateAPIView):
    """
    API view for creating a new transaction.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, DynamicAccountPermission]
    serializer_class = CreateTransactionSerializer

    def post(self, request, *args, **kwargs):
        """
        Create a new transaction.
        """
        account_id = validate_account_id(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TransactionDetailView(generics.GenericAPIView):
    """
    API view for retrieving, updating, partially updating, or deleting a transaction.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, DynamicAccountPermission]

    def get_serializer_class(self):
        """
        Return the serializer class based on the request method.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return TransactionSerializer
        return TransactionSerializer

    def get_object(self):
        """
        Retrieve the Transaction object based on transaction_id.
        """
        transaction_id = self.kwargs.get('transaction_id')
        return get_object_or_404(Transaction, id=transaction_id)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='transaction_id', type=int, location=OpenApiParameter.PATH, required=True)
        ],
        responses={
            200: TransactionSerializer
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a transaction detail.
        """
        transaction = self.get_object()
        serializer = self.get_serializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='transaction_id', type=int, location=OpenApiParameter.PATH, required=True)
        ],
        request=TransactionSerializer,
        responses={
            200: TransactionSerializer
        }
    )
    def put(self, request, *args, **kwargs):
        """
        Update a transaction.
        """
        transaction = self.get_object()
        serializer = self.get_serializer(transaction, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='transaction_id', type=int, location=OpenApiParameter.PATH, required=True)
        ],
        request=TransactionSerializer,
        responses={
            200: TransactionSerializer
        }
    )
    def patch(self, request, *args, **kwargs):
        """
        Partially update a transaction.
        """
        transaction = self.get_object()
        serializer = self.get_serializer(transaction, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='transaction_id', type=int, location=OpenApiParameter.PATH, required=True)
        ],
        responses={
            204: None
        }
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete a transaction.
        """
        transaction = self.get_object()
        self.perform_destroy(transaction)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_update(self, serializer):
        """Save the updated transaction."""
        serializer.save()

    def perform_destroy(self, instance):
        """Delete the transaction."""
        instance.delete()


from django.utils.timezone import make_aware
from datetime import datetime, time

class AdminUserTransactionsView(generics.ListAPIView):
    """
    API view for listing transactions for a specific user within a date range.
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None  # Disable pagination for simplicity

    def get(self, request, *args, **kwargs):
        """
        Retrieve transactions for a user within a specified date range.
        """
        user_id = request.query_params.get('user_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not user_id:
            return Response({'error': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not start_date or not end_date:
            return Response({'error': 'Both start_date and end_date are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date_parsed = make_aware(datetime.combine(parse_date(start_date), time.min))
            end_date_parsed = make_aware(datetime.combine(parse_date(end_date), time.max))
        except Exception:
            return Response({'error': 'Dates must be in the format YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if start_date_parsed > end_date_parsed:
            return Response({'error': 'Start date must be before end date.'}, status=status.HTTP_400_BAD_REQUEST)

        transactions = Transaction.objects.filter(
            user_account__user=user,
            created_at__range=[start_date_parsed, end_date_parsed]
        ).order_by('-created_at')

        total_balance = transactions.aggregate(Sum('amount'))['amount__sum'] or 0

        serializer = self.get_serializer(transactions, many=True)
        return Response({
            'transactions': serializer.data,
            'total_balance': total_balance
        }, status=status.HTTP_200_OK)
