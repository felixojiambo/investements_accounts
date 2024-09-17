from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import UserAccount, InvestmentAccount, Transaction


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User creation and retrieval with unique email and username validation.
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        """
        Create a new User instance with hashed password.
        """
        user = User(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class InvestmentAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for InvestmentAccount model.
    """
    class Meta:
        model = InvestmentAccount
        fields = ['id', 'name', 'description', 'permission_level', 'created_at']


class CreateUserAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new UserAccount with custom validation for account type.
    """
    account_type = serializers.PrimaryKeyRelatedField(queryset=InvestmentAccount.objects.all())

    class Meta:
        model = UserAccount
        fields = ['user', 'account_type', 'account_number', 'created_at']
        read_only_fields = ['account_number', 'created_at']

    def validate(self, data):
        """
        Ensure user does not have multiple accounts of the same type.
        """
        user = self.context['request'].user
        account_type = data.get('account_type')

        if UserAccount.objects.filter(user=user, account_type=account_type).exists():
            raise serializers.ValidationError("User already has an account of this type.")

        return data

    def create(self, validated_data):
        """
        Create and return a new UserAccount instance.
        """
        user = validated_data['user']
        account_type = validated_data['account_type']

        user_account = UserAccount(user=user, account_type=account_type)
        user_account.save()  # Triggers save() method to generate account number

        return user_account


class UserAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for UserAccount model.
    """
    class Meta:
        model = UserAccount
        fields = ['id', 'user', 'balance', 'account_type']


class TransactionBaseSerializer(serializers.ModelSerializer):
    """
    Base serializer for transactions with common validation.
    """

    def validate_amount(self, value):
        """
        Ensure transaction amount is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Transaction amount must be positive.")
        return value

    def validate(self, attrs):
        """
        Ensure debit transactions do not result in negative balances.
        """
        user_account = attrs.get('user_account')
        transaction_type = attrs.get('transaction_type')
        amount = attrs.get('amount')

        if transaction_type == Transaction.DEBIT and user_account.balance < amount:
            raise serializers.ValidationError("Insufficient funds for this transaction.")

        return attrs


class TransactionSerializer(TransactionBaseSerializer):
    """
    Serializer for detailed transaction representation.
    """
    class Meta:
        model = Transaction
        fields = ['id', 'user_account', 'amount', 'transaction_type', 'created_at']


class CreateTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for creating transactions with account ID and positive amount validation.
    """
    account_id = serializers.IntegerField(write_only=True)  # Field for validation only

    class Meta:
        model = Transaction
        fields = ['account_id', 'amount', 'transaction_type']
        extra_kwargs = {
            'amount': {'validators': [MinValueValidator(0)]},  # Ensure positive amounts
        }

    def validate(self, attrs):
        """
        Validate transaction amount and ensure account exists.
        """
        account_id = attrs.get('account_id')
        if not account_id:
            raise serializers.ValidationError({"error": "Account ID is required."})

        try:
            user_account = UserAccount.objects.get(id=account_id)
        except UserAccount.DoesNotExist:
            raise serializers.ValidationError({"error": "User account not found."})

        amount = attrs['amount']
        transaction_type = attrs['transaction_type']
        if transaction_type == Transaction.DEBIT and user_account.balance < amount:
            raise serializers.ValidationError("Insufficient funds for this transaction.")

        attrs['user_account'] = user_account  # Set validated user account
        return attrs

    def create(self, validated_data):
        """
        Create a transaction and associate it with the user account.
        """
        validated_data.pop('account_id')  # Remove account_id from validated_data
        return super().create(validated_data)


class TransactionListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing transactions with filtering by account ID.
    """
    class Meta:
        model = Transaction
        fields = ['id', 'user_account', 'amount', 'transaction_type', 'created_at']

    def __init__(self, *args, **kwargs):
        self.account_id = kwargs.pop('account_id', None)
        super().__init__(*args, **kwargs)

    def validate(self, data):
        """
        Ensure account ID is provided and valid.
        """
        if not self.account_id:
            raise serializers.ValidationError({'account_id': 'This field is required.'})

        try:
            account = UserAccount.objects.get(id=self.account_id, user=self.context['request'].user)
        except UserAccount.DoesNotExist:
            raise serializers.ValidationError("User account not found.")

        return data

    def filter_transactions(self):
        """
        Filter transactions by account ID.
        """
        return Transaction.objects.filter(user_account_id=self.account_id)
