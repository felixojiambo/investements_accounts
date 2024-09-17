from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now, make_aware
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from .models import InvestmentAccount, UserAccount, Transaction


class JWTAuthMixin:
    """
    Mixin to handle JWT authentication in test cases.
    """

    def authenticate(self, username='testuser', password='12345'):
        """
        Authenticate user and set access token in the client.

        Args:
            username (str): The username for authentication. Defaults to 'testuser'.
            password (str): The password for authentication. Defaults to '12345'.

        Raises:
            ValueError: If the user does not exist.
        """
        try:
            self.user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise ValueError("User does not exist.")

        response = self.client.post(reverse('authentication:token_obtain_pair'), {
            'username': username,
            'password': password
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['access'])


class InvestmentAccountCreateViewTests(JWTAuthMixin, APITestCase):
    """
    Tests for creating InvestmentAccount instances.
    """

    def setUp(self):
        """
        Set up test environment with an admin user and authentication.
        """
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@gmail.com')
        self.authenticate('admin', 'adminpass')
        self.url = reverse('investment_accounts:create-investment-account')

    def test_create_investment_account(self):
        """
        Test creating an investment account with valid data.
        """
        data = {'name': 'New Investment Account', 'permission_level': 'full_access'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InvestmentAccount.objects.count(), 1)
        self.assertEqual(InvestmentAccount.objects.get().name, 'New Investment Account')

    def test_create_investment_account_invalid_data(self):
        """
        Test creating an investment account with invalid data.
        """
        data = {'name': '', 'permission_level': 'invalid_level'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('permission_level', response.data)


class UserAccountCreateViewTests(JWTAuthMixin, APITestCase):
    """
    Tests for creating UserAccount instances.
    """

    def setUp(self):
        """
        Set up test environment with an admin user and authentication.
        """
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass')
        self.authenticate('admin', 'adminpass')
        self.account_type = InvestmentAccount.objects.create(
            name='Investment Account 2',
            permission_level=InvestmentAccount.FULL_ACCESS
        )
        self.url = reverse('user_accounts:user-account-create')

    def test_create_user_account(self):
        """
        Test creating a user account with valid data.
        """
        data = {'account_type': self.account_type.id, 'user': self.admin_user.id}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserAccount.objects.count(), 1)

    def test_create_user_account_invalid_data(self):
        """
        Test creating a user account with missing data.
        """
        data = {'account_type': self.account_type.id}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserCreateViewTests(JWTAuthMixin, APITestCase):
    """
    Test cases for user creation via the UserCreateView.
    """

    def setUp(self):
        """
        Set up test environment with the URL for user registration.
        """
        self.url = reverse('authentication:user-register')

    def test_create_user(self):
        """
        Test creating a user with valid data.

        Verifies that a new user is created successfully and that the user's details are stored correctly.
        """
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
        """
        Test creating a user without providing an email.

        Verifies that a 400 Bad Request status is returned and that the response includes an error about the missing email.
        """
        data = {
            'username': 'newuser',
            'password': 'newpass'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


class UserAccountListViewTests(JWTAuthMixin, APITestCase):
    """
    Test cases for listing UserAccount instances.
    """

    def setUp(self):
        """
        Set up test environment with a user, user account, and authentication.

        Clears existing UserAccount objects to ensure test isolation.
        """
        UserAccount.objects.all().delete()

        self.user = User.objects.create_user(username='testuser', password='12345', email='newuser@example.com')
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
        """
        Test listing user accounts.

        Verifies that the user account is listed correctly and includes the expected balance.
        """
        response = self.client.get(self.url)
        print("Response Data:", response.data)  # Optional debug print
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['balance'], '1000.00')


class UserAccountDetailViewTests(JWTAuthMixin, APITestCase):
    """
    Test cases for retrieving, updating, and deleting UserAccount instances.
    """

    def setUp(self):
        """
        Set up test environment with a user account and authentication.
        """
        self.user = User.objects.create_user(username='testuser', password='12345', email='newuser@example.com')
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
        self.url = reverse('user_accounts:user-account-detail', kwargs={'pk': self.user_account.id})

    def test_retrieve_user_account(self):
        """
        Test retrieving a user account.

        Verifies that the details of the user account are returned correctly.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], '1000.00')

    def test_update_user_account(self):
        """
        Test updating a user account balance.

        Verifies that the balance is updated successfully and the new balance is correctly reflected.
        """
        data = {'balance': '1500.00'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(UserAccount.objects.get().balance, Decimal('1500.00'))

    def test_delete_user_account(self):
        """
        Test deleting a user account.

        Verifies that the user account is deleted and no longer exists in the database.
        """
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserAccount.objects.count(), 0)


class TransactionListViewTests(JWTAuthMixin, APITestCase):
    """
    Test cases for listing Transaction instances.
    """

    def setUp(self):
        """
        Set up test environment with a user, user account, transaction, and authentication.
        """
        self.user = User.objects.create_user(username='testuser', password='12345', email='newuser@example.com')
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
        self.transaction = Transaction.objects.create(
            user_account=self.user_account,
            amount=Decimal('200.00'),
            transaction_type=Transaction.CREDIT
        )
        self.url = reverse('transactions:transaction-list')

    def test_list_transactions(self):
        """
        Test listing transactions for a valid account ID.

        Verifies that transactions are listed correctly for the authenticated user's account.
        """
        response = self.client.get(self.url, {'account_id': self.user_account.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['amount'], '200.00')

    def test_list_transactions_no_account(self):
        """
        Test error handling when no account ID is provided.

        Verifies that a 403 Forbidden status is returned when the account ID is missing.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'You do not have permission to perform this action.')

    def test_list_transactions_wrong_account(self):
        """
        Test error handling when the account does not belong to the user.

        Verifies that a 403 Forbidden status is returned when accessing transactions for an account not owned by the user.
        """
        another_user = User.objects.create_user(username='otheruser', password='password', email='other@example.com')
        another_account = UserAccount.objects.create(
            user=another_user,
            account_type=self.account_type,
            balance=Decimal('500.00')
        )
        response = self.client.get(self.url, {'account_id': another_account.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'You do not have permission to perform this action.')
class CreateTransactionViewTests(APITestCase):
    """
    Test cases for creating transactions via the CreateTransactionView.
    """

    def setUp(self):
        """
        Set up test environment with a user, investment account, and user account.

        Authenticates the user with a JWT token.
        """
        self.user = User.objects.create_user(username='testuser', password='12345', email='test@example.com')
        self.investment_account = InvestmentAccount.objects.create(name="Investment Account", permission_level=InvestmentAccount.FULL_ACCESS)
        self.user_account = UserAccount.objects.create(user=self.user, account_type=self.investment_account, balance=Decimal('1000.00'))
        self.url = reverse('transactions:transaction-create')  # Assuming 'create-transaction' is the URL name

        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_create_credit_transaction(self):
        """
        Test creating a credit transaction.

        Verifies that a credit transaction is created successfully and the amount is correctly recorded.
        """
        data = {
            'account_id': self.user_account.id,
            'amount': '200.00',
            'transaction_type': Transaction.CREDIT
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '200.00')

    def test_create_debit_transaction_success(self):
        """
        Test creating a debit transaction with sufficient funds.

        Verifies that a debit transaction is created successfully when there are sufficient funds in the account.
        """
        data = {
            'account_id': self.user_account.id,
            'amount': '500.00',
            'transaction_type': Transaction.DEBIT
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '500.00')

    def test_create_debit_transaction_insufficient_funds(self):
        """
        Test creating a debit transaction with insufficient funds.

        Verifies that a 400 Bad Request status is returned and the response contains an error message when there are insufficient funds.
        """
        data = {
            'account_id': self.user_account.id,
            'amount': '1500.00',  # More than available balance
            'transaction_type': Transaction.DEBIT
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient funds for this transaction.', response.data['non_field_errors'])


class TransactionDetailViewTests(APITestCase):
    """
    Test cases for retrieving, updating, and deleting transactions via the TransactionDetailView.
    """

    def setUp(self):
        """
        Set up test environment with a user, investment account, user account, and transaction.

        Authenticates the user.
        """
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
        """
        Test retrieving transaction details.

        Verifies that transaction details are returned correctly for a valid transaction ID and account ID.
        """
        url = reverse('transactions:transaction-detail', kwargs={'transaction_id': self.transaction.id})
        response = self.client.get(url, {'account_id': self.account.id})
        print(f"GET transaction detail response: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.transaction.id)

    def test_update_transaction(self):
        """
        Test updating a transaction.

        Verifies that a transaction is updated successfully and the changes are reflected in the database.
        """
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
        """
        Test deleting a transaction.

        Verifies that a transaction is deleted successfully and no longer exists in the database.
        """
        url = reverse('transactions:transaction-detail', kwargs={'transaction_id': self.transaction.id})
        response = self.client.delete(url, {'account_id': self.account.id})
        print(f"DELETE transaction response: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Transaction.objects.filter(id=self.transaction.id).exists())
class AdminUserTransactionsViewTests(APITestCase):
    """
    Test cases for retrieving user transactions via the AdminUserTransactionsView.
    """

    def setUp(self):
        """
        Set up test environment with a regular user, an admin user, an investment account, a user account,
        and transactions.

        Authenticates the client with the admin user's JWT token.
        """
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
        """
        Test that an admin can retrieve transactions for a user within a date range.

        Verifies that an admin user can successfully retrieve transactions for a specific user and date range,
        including the correct count of transactions and total balance.
        """
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
        """
        Test that a non-admin user cannot retrieve transactions.

        Verifies that a regular user cannot access the endpoint meant for admins and receives a forbidden status.
        """
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
        """
        Test that missing user ID in request results in a bad request.

        Verifies that a 400 Bad Request status is returned when the user ID parameter is missing.
        """
        url = reverse('transactions:admin-user-transactions')
        response = self.client.get(url, {
            'start_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'User ID is required.')

    def test_missing_dates(self):
        """
        Test that missing date parameters in request results in a bad request.

        Verifies that a 400 Bad Request status is returned when either start_date or end_date is missing.
        """
        url = reverse('transactions:admin-user-transactions')
        response = self.client.get(url, {
            'user_id': self.user.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Both start_date and end_date are required.')

    def test_invalid_date_format(self):
        """
        Test that an invalid date format results in a bad request.

        Verifies that a 400 Bad Request status is returned when the date format is incorrect.
        """
        url = reverse('transactions:admin-user-transactions')
        response = self.client.get(url, {
            'user_id': self.user.id,
            'start_date': 'invalid-date',
            'end_date': datetime.now().strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Dates must be in the format YYYY-MM-DD.')

    def test_start_date_after_end_date(self):
        """
        Test that a start date after the end date results in a bad request.

        Verifies that a 400 Bad Request status is returned when the start_date is after the end_date.
        """
        url = reverse('transactions:admin-user-transactions')
        response = self.client.get(url, {
            'user_id': self.user.id,
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'end_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Start date must be before end date.')
