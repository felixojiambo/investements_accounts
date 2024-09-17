from django.contrib import admin
from .models import InvestmentAccount, UserAccount, Transaction

@admin.register(InvestmentAccount)
class InvestmentAccountAdmin(admin.ModelAdmin):
    """
    Admin configuration for InvestmentAccount.
    """
    list_display = ('name', 'permission_level', 'created_at')
    list_filter = ('permission_level', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('created_at',)
    readonly_fields = ('created_at',)

@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserAccount.
    """
    list_display = ('user', 'account_type', 'account_number','balance', 'created_at')
    list_filter = ('account_type', 'created_at')
    search_fields = ('user__username', 'account_type__name')
    ordering = ('created_at',)
    readonly_fields = ('created_at','account_number')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Transaction.
    """
    list_display = ('user_account', 'amount', 'transaction_type', 'created_at')
    list_filter = ('transaction_type', 'created_at', 'user_account__account_type')
    search_fields = ('user_account__user__username', 'amount')
    ordering = ('created_at',)
    readonly_fields = ('created_at',)
    list_select_related = ('user_account', 'user_account__user', 'user_account__account_type')
