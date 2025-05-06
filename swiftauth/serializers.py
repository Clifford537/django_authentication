from rest_framework import serializers
from .models import Account, Transaction, User
from decimal import Decimal

# -----------------------------------------------
#  PAYMENT SERIALIZER (Handles Transactions)
# -----------------------------------------------
class PaymentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    source = serializers.CharField()

    def validate(self, data):
        """Ensure recipient exists before processing the payment."""
        email = data.get("email")
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User not found.")
        return data

    def save(self):
        """Processes the transaction and updates balance."""
        email = self.validated_data["email"]
        amount = Decimal(self.validated_data["amount"])
        source = self.validated_data["source"]

        user = User.objects.get(email=email)  # Recipient
        account, created = Account.objects.get_or_create(user=user)

        # Update balance
        account.balance += amount
        account.save()

        # Create transaction
        transaction = Transaction.objects.create(
            sender=None,  # External deposit, so no sender
            recipient=user,
            transaction_type="deposit",
            amount=amount,
            source=source
        )

        return {
            "balance": account.balance,
            "source": source,
            "user": user,
            "amount": amount,
            "transaction": transaction,
        }

# -----------------------------------------------
#  USER SERIALIZER (Returns User Details)
# -----------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "phone", "country", "date_of_birth", "is_verified", "is_active", "balance"]

    def get_balance(self, obj):
        """Fetch the user's account balance."""
        account = Account.objects.filter(user=obj).first()
        return account.balance if account else Decimal("0.00")
