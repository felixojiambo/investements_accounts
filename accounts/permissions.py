from rest_framework.permissions import BasePermission
from .models import UserAccount, InvestmentAccount


class BaseAccountPermission(BasePermission):
    """
    Base permission class for account-based permissions with common logic for fetching the user account.
    """

    def get_user_account(self, request):
        """
        Retrieve the UserAccount instance based on the provided account_id in the request.
        """
        account_id = request.query_params.get('account_id') or request.data.get('account_id')
        print(f"Account ID: {account_id}")  # Add logging here
        if not account_id:
            return None

        try:
            user_account = UserAccount.objects.get(user=request.user, id=account_id)
            print(f"Found user account: {user_account.id} with permission level {user_account.account_type.permission_level}")
            return user_account
        except UserAccount.DoesNotExist:
            print("User account does not exist.")
            return None


class IsViewOnlyForInvestmentAccount1(BaseAccountPermission):
    """
    Permission for view-only access (GET requests) for transactions linked to Investment Account 1.
    """
    def has_permission(self, request, view):
        """
        Allow GET, HEAD, OPTIONS methods for view-only accounts.
        """
        user_account = self.get_user_account(request)
        if user_account and user_account.account_type.permission_level == InvestmentAccount.VIEW_ONLY:
            return request.method in ['GET', 'HEAD', 'OPTIONS']
        return False


class IsFullAccessForInvestmentAccount2(BaseAccountPermission):
    """
    Permission for full CRUD (Create, Read, Update, Delete) access for transactions linked to Investment Account 2.
    """
    def has_permission(self, request, view):
        """
        Allow all methods (CRUD) for full access accounts.
        """
        user_account = self.get_user_account(request)
        if user_account and user_account.account_type.permission_level == InvestmentAccount.FULL_ACCESS:
            return request.method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        return False


class IsPostOnlyForInvestmentAccount3(BaseAccountPermission):
    """
    Permission for post-only (POST requests) access for transactions linked to Investment Account 3.
    """
    def has_permission(self, request, view):
        """
        Allow only POST method for post-only accounts.
        """
        user_account = self.get_user_account(request)
        if user_account and user_account.account_type.permission_level == InvestmentAccount.POST_ONLY:
            return request.method == 'POST'
        return False


class DynamicAccountPermission(BaseAccountPermission):
    """
    Dynamic permission that grants access based on the account's permission level.
    """
    def has_permission(self, request, view):
        """
        Grant access based on the account's permission level.
        """
        user_account = self.get_user_account(request)
        if not user_account:
            print("Permission denied: No user account found.")
            return False

        investment_account = user_account.account_type
        print(f"Checking permissions for account with permission level: {investment_account.permission_level}")

        if investment_account.permission_level == InvestmentAccount.VIEW_ONLY:
            allowed = request.method in ['GET']
            print(f"Permission {'granted' if allowed else 'denied'} for VIEW_ONLY")
            return allowed
        elif investment_account.permission_level == InvestmentAccount.FULL_ACCESS:
            print("Permission granted for FULL_ACCESS")
            return True
        elif investment_account.permission_level == InvestmentAccount.POST_ONLY:
            allowed = request.method == 'POST'
            print(f"Permission {'granted' if allowed else 'denied'} for POST_ONLY")
            return allowed
        print("Permission denied: Method not allowed for this permission level.")
        return False
