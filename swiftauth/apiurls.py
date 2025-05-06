# from django.urls import include, path
# from rest_framework.routers import DefaultRouter
# from .apiviews import UserViewSet, AccountViewSet, TransactionViewSet, PaymentActivationViewSet, ExternalDepositView

# router = DefaultRouter()
# router.register(r'users', UserViewSet)
# router.register(r'accounts', AccountViewSet)
# router.register(r'transactions', TransactionViewSet)
# router.register(r'payment_activations', PaymentActivationViewSet)

# urlpatterns = [
#     path('', include(router.urls)),
#     # Manually map the ExternalDepositView
#     path('externalpayment/', ExternalDepositView.as_view(), name='external-deposit'),
    
# ]
