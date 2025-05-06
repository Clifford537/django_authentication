from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from .serializers import PaymentSerializer, UserSerializer
from .models import Notification


# ------------------------------------------------------
#  API VIEW TO RECEIVE PAYMENTS AND UPDATE BALANCE
# ------------------------------------------------------
@api_view(["POST"])
def receive_payment(request):
    """Handles incoming payments, updates balance, and notifies the recipient."""
    serializer = PaymentSerializer(data=request.data)

    if serializer.is_valid():
        result = serializer.save()
        user = result["user"]  # Recipient
        sender_name = result["source"]
        amount = result["amount"]

        if user:
            #  Create notification for the recipient
            Notification.objects.create(
                user=user,
                notification_type="success",
                message=f"You received a payment of ${amount} from {sender_name}.",
                is_read=False
            )

            #  Render email template
            email_html = render_to_string("emails/payment_received_email.html", {
                "user": user,
                "amount": amount,
                "sender_name": sender_name
            })

            #  Send email notification
            email = EmailMultiAlternatives(
                subject="Payment Received",
                body=f"You have received ${amount} from {sender_name}.",  # Fallback text
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(email_html, "text/html")  # Attach HTML version
            email.send()

        return Response(
            {
                "message": f"Payment received from {sender_name}",
                "new_balance": result["balance"],
                "transaction_id": result["transaction"].id
            },
            status=status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------------------------------
# API VIEW TO FETCH AUTHENTICATED USER DETAILS
# ------------------------------------------------------
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]  # Requires authentication

    def get(self, request, *args, **kwargs):
        """Fetch details of the authenticated user."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
