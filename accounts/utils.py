from rest_framework.exceptions import ValidationError


def validate_account_id(request):
    """
    Retrieve and validate `account_id` from request parameters or data.

    Raises:
        ValidationError: If `account_id` is missing.

    Returns:
        str: The validated account ID.
    """
    account_id = request.query_params.get('account_id') or request.data.get('account_id')
    if not account_id:
        raise ValidationError({"error": "Account ID is required."})
    return account_id
