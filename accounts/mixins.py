from rest_framework.exceptions import ValidationError
from .models import UserAccount

class UserAccountMixin:
    """
    Mixin to retrieve UserAccount based on account_id from the request.
    """
    def get_user_account(self):
        """
        Retrieve the UserAccount instance based on account_id from the request.
        Raises ValidationError if account_id is missing or the account does not exist.
        """
        if not hasattr(self, 'request'):
            raise AttributeError("UserAccountMixin requires a 'request' object in the view context.")

        account_id = self.request.query_params.get('account_id') or self.request.data.get('account_id')
        if not account_id:
            raise ValidationError({"error": "Account ID is required."})

        try:
            return UserAccount.objects.get(user=self.request.user, id=account_id)
        except UserAccount.DoesNotExist:
            raise ValidationError({"error": "User account not found."})
