from django.contrib.auth.models import User
from django.db import models


class InvestmentAccount(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

class UserInvestmentAccount(models.Model):
    VIEW_ONLY = 'view_only'
    FULL_ACCESS = 'full_access'
    POST_ONLY = 'post_only'

    PERMISSION_CHOICES = [
        (VIEW_ONLY, 'View Only'),
        (FULL_ACCESS, 'Full Access (CRUD)'),
        (POST_ONLY, 'Post Transactions Only'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(InvestmentAccount, on_delete=models.CASCADE)
    permission_level = models.CharField(max_length=20, choices=PERMISSION_CHOICES)

class Transaction(models.Model):
    account = models.ForeignKey(InvestmentAccount, related_name='transactions', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.amount} - {self.description}'
