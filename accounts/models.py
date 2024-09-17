from datetime import datetime
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F


class InvestmentAccount(models.Model):
    """
    Model representing an investment account with varying permission levels.

    Attributes:
        name (str): The name of the investment account.
        description (str): An optional description of the investment account.
        permission_level (str): The permission level associated with the account,
            which can be 'view_only', 'full_access', or 'post_only'.
        created_at (datetime): The timestamp when the account was created.
    """
    VIEW_ONLY = 'view_only'
    FULL_ACCESS = 'full_access'
    POST_ONLY = 'post_only'

    PERMISSION_CHOICES = [
        (VIEW_ONLY, 'View Only'),
        (FULL_ACCESS, 'Full Access (CRUD)'),
        (POST_ONLY, 'Post Transactions Only'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    permission_level = models.CharField(max_length=20, choices=PERMISSION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['permission_level']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.permission_level})"


class UserAccount(models.Model):
    """
    Model representing a user's instance of an investment account type.

    Attributes:
        user (User): The user associated with this account.
        account_type (InvestmentAccount): The type of investment account.
        account_number (str): A unique identifier for the account.
        balance (Decimal): The current balance of the account.
        created_at (datetime): The timestamp when the account was created.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_type = models.ForeignKey(InvestmentAccount, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=50, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'account_type'], name='unique_user_account_type')
        ]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['account_type']),
            models.Index(fields=['account_number']),
        ]

    def __str__(self):
        return f"{self.user.username}'s {self.account_type.name} (Balance: {self.balance}, Account Number: {self.account_number})"

    def save(self, *args, **kwargs):
        """Generate and assign a unique account number if not already set."""
        if not self.account_number:
            self.account_number = self.generate_account_number()
        super().save(*args, **kwargs)

    def generate_account_number(self):
        """
        Generate a unique account number based on user ID, account type ID, year, and a sequential number.

        Returns:
            str: The generated account number.
        """
        existing_accounts = UserAccount.objects.filter(user=self.user, account_type=self.account_type)

        if existing_accounts.exists():
            last_account = existing_accounts.order_by('-account_number').first()
            last_sequential = int(last_account.account_number[-4:])
        else:
            last_sequential = 0

        formatted_sequential = f"{last_sequential + 1:04}"
        year = self.created_at.year if self.created_at else datetime.now().year

        return f"{self.user.id}{self.account_type.id}{year}{formatted_sequential}"


class Transaction(models.Model):
    """
    Model representing a financial transaction on a user's investment account.

    Attributes:
        user_account (UserAccount): The user's account affected by the transaction.
        amount (Decimal): The amount of the transaction.
        transaction_type (str): The type of transaction, either 'debit' or 'credit'.
        created_at (datetime): The timestamp when the transaction was created.
    """
    DEBIT = 'debit'
    CREDIT = 'credit'

    TRANSACTION_TYPE_CHOICES = [
        (DEBIT, 'Debit'),
        (CREDIT, 'Credit'),
    ]

    user_account = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user_account']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Transaction {self.transaction_type} of {self.amount} for {self.user_account.user.username}"

    def clean(self):
        """
        Validate the transaction to ensure positive amounts and prevent negative balances.

        Raises:
            ValidationError: If the transaction amount is not positive or if a debit
            transaction would result in a negative balance.
        """
        if self.amount <= 0:
            raise ValidationError("Transaction amount must be positive.")

        if self.transaction_type == self.DEBIT and self.user_account.balance < self.amount:
            raise ValidationError("Insufficient funds: this transaction would result in a negative balance.")

    def save(self, *args, **kwargs):
        """
        Process the transaction, adjusting the user's balance and saving the transaction.

        Locks the user account for update and ensures that the balance is updated correctly.
        """
        with transaction.atomic():
            self.clean()

            user_account = UserAccount.objects.select_for_update().get(id=self.user_account.id)

            if self.transaction_type == self.DEBIT:
                user_account.balance = F('balance') - self.amount
            elif self.transaction_type == self.CREDIT:
                user_account.balance = F('balance') + self.amount

            user_account.save(update_fields=['balance'])
            super().save(*args, **kwargs)
