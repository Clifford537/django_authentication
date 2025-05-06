from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Account, Transaction, Notification, PaymentActivation

admin.site.site_header = "SwiftPay Administration"  # Custom admin panel header
admin.site.site_title = "SwiftPay Admin Portal"  # Custom browser tab title
admin.site.index_title = "SwiftPay to TopSoftEdge Dashboard"

# -----------------------------------------------
# ✅ CUSTOM USER ADMIN (Manages Users)
# -----------------------------------------------
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "phone", "is_verified", "is_activated", "is_staff", "is_active")
    list_filter = ("is_verified", "is_activated", "is_staff", "is_active")
    search_fields = ("email", "phone")
    ordering = ("email",)
    fieldsets = (
        ("Personal Info", {"fields": ("email", "phone", "country", "date_of_birth")}),
        ("ID Verification", {"fields": ("national_id_front", "national_id_back")}),
        ("Status", {"fields": ("is_active", "is_verified", "is_activated", "is_staff", "is_superuser")}),
        ("Security", {"fields": ("password", "otp", "otp_expiry", "reset_token", "reset_token_expiry")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "phone", "password1", "password2", "is_verified", "is_activated"),
        }),
    )

# -----------------------------------------------
# ✅ ACCOUNT ADMIN (Manages User Balances & Payment Methods)
# -----------------------------------------------
class AccountAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "has_payment_method")
    search_fields = ("user__email", "user__phone")

    def has_payment_method(self, obj):
        """Check if the user has either a credit card or bank account."""
        return bool(obj.credit_card_number or obj.account_number)
    has_payment_method.boolean = True  # Show as a boolean icon in admin panel

# -----------------------------------------------
# ✅ TRANSACTION ADMIN (Tracks All Transactions)
# -----------------------------------------------
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_type", "amount", "timestamp", "sender_display", "recipient", "source")
    list_filter = ("transaction_type", "timestamp", "source")
    search_fields = ("sender__email", "recipient__email", "source")

    def sender_display(self, obj):
        """Show sender email or 'External' if sender is None."""
        return obj.sender.email if obj.sender else "External Deposit"
    sender_display.admin_order_field = "sender"
    sender_display.short_description = "Sender"

# -----------------------------------------------
# ✅ NOTIFICATION ADMIN (Tracks User Notifications)
# -----------------------------------------------
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "notification_type", "is_read", "timestamp")
    list_filter = ("notification_type", "is_read", "timestamp")
    search_fields = ("user__email", "message")

class PaymentActivationAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_paid', 'payment_date')  # Show key fields
    list_filter = ('is_paid',)  # Add filter for paid/unpaid
    search_fields = ('user__email', 'user__phone')  # Allow search by email & phone
# -----------------------------------------------
# ✅ REGISTER MODELS
# -----------------------------------------------
admin.site.register(User, UserAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(PaymentActivation, PaymentActivationAdmin)
