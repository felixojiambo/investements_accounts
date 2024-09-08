from rest_framework.permissions import BasePermission

from accounts.models import UserInvestmentAccount


class IsAccountViewOnly(BasePermission):
    def has_permission(self, request, view):
        account_id = view.kwargs['account_id']
        user_account = UserInvestmentAccount.objects.filter(user=request.user, account_id=account_id).first()
        return user_account and user_account.permission_level == UserInvestmentAccount.VIEW_ONLY

class IsAccountFullAccess(BasePermission):
    def has_permission(self, request, view):
        account_id = view.kwargs['account_id']
        user_account = UserInvestmentAccount.objects.filter(user=request.user, account_id=account_id).first()
        return user_account and user_account.permission_level == UserInvestmentAccount.FULL_ACCESS

class IsAccountPostOnly(BasePermission):
    def has_permission(self, request, view):
        account_id = view.kwargs['account_id']
        user_account = UserInvestmentAccount.objects.filter(user=request.user, account_id=account_id).first()
        return user_account and user_account.permission_level == UserInvestmentAccount.POST_ONLY

    def has_object_permission(self, request, view, obj):
        # Only allow POST requests
        return request.method == 'POST'
