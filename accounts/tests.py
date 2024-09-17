from datetime import datetime, timedelta
from decimal import Decimal
import json
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now, make_aware
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from .models import InvestmentAccount, UserAccount, Transaction


class JWTAuthMixin:
    def authenticate(self, username='testuser', password='12345'):
        """Authenticate the user and set the access token in the client."""
        # Check if the user already exists
        try:
            self.user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise ValueError("User does not exist. Please ensure the user is created.")

        # Attempt to obtain the JWT token for the existing user
        response = self.client.post(reverse('authentication:token_obtain_pair'), {
            'username': username,
            'password': password
        })

        # Ensure the token was successfully obtained
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Set the Authorization header with the obtained access token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['access'])


class InvestmentAccountCreateViewTests(JWTAuthMixin,APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@gmail.com')
        self.authenticate('admin', 'adminpass')
        self.url = reverse('investment_accounts:create-investment-account')

    def test_create_investment_account(self):
        data = {'name': 'New Investment Account', 'permission_level': 'full_access'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InvestmentAccount.objects.count(), 1)
        self.assertEqual(InvestmentAccount.objects.get().name, 'New Investment Account')

    def test_create_investment_account_invalid_data(self):
        data = {'name': '', 'permission_level': 'invalid_level'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('permission_level', response.data)

class UserAccountCreateViewTests(JWTAuthMixin,APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass')
        self.authenticate('admin', 'adminpass')
        self.account_type = InvestmentAccount.objects.create(
            name='Investment Account 2',
            permission_level=InvestmentAccount.FULL_ACCESS
        )
        self.url = reverse('user_accounts:user-account-create')

    def test_create_user_account(self):
        data = {'account_type': self.account_type.id, 'user': self.admin_user.id}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserAccount.objects.count(), 1)

    def test_create_user_account_invalid_data(self):
        data = {'account_type': self.account_type.id}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserCreateViewTests(JWTAuthMixin, APITestCase):
    def setUp(self):
        self.url = reverse('authentication:user-register')

    def test_create_user(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'newuser')
        self.assertEqual(User.objects.get().email, 'newuser@example.com')

    def test_create_user_without_email(self):
        data = {
            'username': 'newuser',
            'password': 'newpass'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

class UserAccountListViewTests(JWTAuthMixin, APITestCase):
    def setUp(self):
        # Clear UserAccount objects to ensure test isolation
        UserAccount.objects.all().delete()

        self.user = User.objects.create_user(username='testuser', password='12345', email='newuser@example.com')

        # Authenticate the user using JWTAuthMixin
        self.authenticate()

        self.account_type = InvestmentAccount.objects.create(
            name='Investment Account 2',
            permission_level=InvestmentAccount.FULL_ACCESS
        )
        self.user_account = UserAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            balance=Decimal('1000.00')
        )
        self.url = reverse('user_accounts:user-account-list')

    def test_list_user_accounts(self):
        response = self.client.get(self.url)
        print("Response Data:", response.data)  # You can remove this print if no longer needed
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Access the 'results' key in the paginated response and check its length
        self.assertEqual(len(response.data['results']), 1)  # Ensure only one account is returned
        self.assertEqual(response.data['results'][0]['balance'], '1000.00')

class UserAccountDetailViewTests(JWTAuthMixin, APITestCase):
    def setUp(self):
        # Create the user explicitly
        self.user = User.objects.create_user(username='testuser', password='12345',email='newuser@example.com')

        # Authenticate the user using JWTAuthMixin
        self.authenticate()  # This will handle token-based authentication

        self.account_type = InvestmentAccount.objects.create(
            name='Investment Account 2',
            permission_level=InvestmentAccount.FULL_ACCESS
        )
        self.user_account = UserAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            balance=Decimal('1000.00')
        )
        self.url = reverse('user_accounts:user-account-detail', kwargs={'pk': self.user_account.id})

    def test_retrieve_user_account(self):
        response = self.client.get(self.url)  # Authenticated request
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], '1000.00')

    def test_update_user_account(self):
        data = {'balance': '1500.00'}
        response = self.client.patch(self.url, data, format='json')  # Authenticated request
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(UserAccount.objects.get().balance, Decimal('1500.00'))

    def test_delete_user_account(self):
        response = self.client.delete(self.url)  # Authenticated request
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserAccount.objects.count(), 0)


class TransactionListViewTests(JWTAuthMixin, APITestCase):
    def setUp(self):
        # Create the user explicitly
        self.user = User.objects.create_user(username='testuser', password='12345', email='newuser@example.com')

        # Authenticate the user using JWTAuthMixin
        self.authenticate()  # This will handle token-based authentication

        self.account_type = InvestmentAccount.objects.create(
            name='Investment Account 2',
            permission_level=InvestmentAccount.FULL_ACCESS
        )
        self.user_account = UserAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            balance=Decimal('1000.00')
        )
        self.transaction = Transaction.objects.create(
            user_account=self.user_account,
            amount=Decimal('200.00'),
            transaction_type=Transaction.CREDIT
        )
        self.url = reverse('transactions:transaction-list')

    def test_list_transactions(self):
        """Test if transactions are listed successfully for a valid account_id."""
        response = self.client.get(self.url, {'account_id': self.user_account.id})  # Authenticated request
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['amount'], '200.00')

    def test_list_transactions_no_account(self):
        """Test error when account_id is not provided."""
        response = self.client.get(self.url)  # Authenticated request without account_id
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # Expecting 403 instead of 400
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'You do not have permission to perform this action.')

    def test_list_transactions_wrong_account(self):
        """Test error when the account does not belong to the user."""
        # Create a different user and account
        another_user = User.objects.create_user(username='otheruser', password='password', email='other@example.com')
        another_account = UserAccount.objects.create(
            user=another_user,
            account_type=self.account_type,
            balance=Decimal('500.00')
        )
        response = self.client.get(self.url,
                                   {'account_id': another_account.id})  # Request with another user's account_id
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)  # Check for 'detail', not 'error'
        self.assertEqual(response.data['detail'], 'You do not have permission to perform this action.')

class CreateTransactionViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345', email='test@example.com')
        self.investment_account = InvestmentAccount.objects.create(name="Investment Account", permission_level=InvestmentAccount.FULL_ACCESS)
        self.user_account = UserAccount.objects.create(user=self.user, account_type=self.investment_account, balance=Decimal('1000.00'))
        self.url = reverse('transactions:transaction-create')  # Assuming 'create-transaction' is the URL name

        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_create_credit_transaction(self):
        """Test creating a credit transaction."""
        data = {
            'account_id': self.user_account.id,
            'amount': '200.00',
            'transaction_type': Transaction.CREDIT
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '200.00')

    def test_create_debit_transaction_success(self):
        """Test creating a debit transaction with sufficient funds."""
        data = {
            'account_id': self.user_account.id,
            'amount': '500.00',
            'transaction_type': Transaction.DEBIT
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '500.00')

    def test_create_debit_transaction_insufficient_funds(self):
        """Test creating a debit transaction with insufficient funds."""
        data = {
            'account_id': self.user_account.id,
            'amount': '1500.00',  # More than available balance
            'transaction_type': Transaction.DEBIT
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient funds for this transaction.', response.data['non_field_errors'])


class TransactionDetailViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create an InvestmentAccount instance with FULL_ACCESS permission
        self.investment_account = InvestmentAccount.objects.create(
            name='Test Account',
            permission_level=InvestmentAccount.FULL_ACCESS
        )

        # Create a UserAccount instance
        self.account = UserAccount.objects.create(
            user=self.user,
            account_type=self.investment_account,
            balance=1000
        )

        # Create a Transaction instance
        self.transaction = Transaction.objects.create(
            user_account=self.account,
            amount=100,
            transaction_type='debit'
        )

    def test_get_transaction_detail(self):
        url = reverse('transactions:transaction-detail', kwargs={'transaction_id': self.transaction.id})
        response = self.client.get(url, {'account_id': self.account.id})
        print(f"GET transaction detail response: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.transaction.id)

    def test_update_transaction(self):
        url = reverse('transactions:transaction-detail', kwargs={'transaction_id': self.transaction.id})
        data = {
            'amount': 150,
            'account_id': self.account.id,
            'user_account': self.account.id,
            'transaction_type': self.transaction.transaction_type
        }
        response = self.client.put(url, data)
        print(f"PUT transaction update response: {response.status_code}")
        print(f"Response content: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.amount, 150)

    def test_delete_transaction(self):
        url = reverse('transactions:transaction-detail', kwargs={'transaction_id': self.transaction.id})
        response = self.client.delete(url, {'account_id': self.account.id})
        print(f"DELETE transaction response: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Transaction.objects.filter(id=self.transaction.id).exists())


class AdminUserTransactionsViewTests(APITestCase):

    def setUp(self):
        # Create a user and an admin user
        self.user = User.objects.create_user(username='user', password='password')
        self.admin_user = User.objects.create_superuser(username='admin', password='password')

        # Create an investment account
        self.investment_account = InvestmentAccount.objects.create(
            name='Test Account',
            permission_level=InvestmentAccount.FULL_ACCESS
        )

        # Create a user account
        self.user_account = UserAccount.objects.create(
            user=self.user,
            account_type=self.investment_account,
            account_number='1234567890',
            balance=1000.00
        )

        # Create transactions
        self.transaction1 = Transaction.objects.create(
            user_account=self.user_account,
            amount=100.00,
            transaction_type=Transaction.CREDIT,
            created_at=make_aware(datetime.now() - timedelta(days=2))
        )
        self.transaction2 = Transaction.objects.create(
            user_account=self.user_account,
            amount=50.00,
            transaction_type=Transaction.DEBIT,
            created_at=make_aware(datetime.now() - timedelta(days=1))
        )

        # Generate JWT tokens for admin user
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_admin_can_retrieve_transactions(self):
        url = reverse('transactions:admin-user-transactions')
        response = self.client.get(url, {
            'user_id': self.user.id,
            'start_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['transactions']), 2)
        self.assertEqual(response.data['total_balance'], 150.00)

    def test_non_admin_cannot_retrieve_transactions(self):
        # Generate JWT tokens for non-admin user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        url = reverse('transactions:admin-user-transactions')
        response = self.client.get(url, {
            'user_id': self.user.id,
            'start_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_user_id(self):
        url = reverse('transactions:admin-user-transactions')
        response = self.client.get(url, {
            'start_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'User ID is required.')

    def test_missing_dates(self):
        url = reverse('transactions:admin-user-transactions')
        response = self.client.get(url, {
            'user_id': self.user.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Both start_date and end_date are required.')

    def test_invalid_date_format(self):
        url = reverse('transactions:admin-user-transactions')
        response = self.client.get(url, {
            'user_id': self.user.id,
            'start_date': 'invalid-date',
            'end_date': datetime.now().strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Dates must be in the format YYYY-MM-DD.')

    def test_start_date_after_end_date(self):
        url = reverse('transactions:admin-user-transactions')
        response = self.client.get(url, {
            'user_id': self.user.id,
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'end_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Start date must be before end date.')