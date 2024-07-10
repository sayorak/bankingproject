from django.contrib import admin
from .models import Account, Transaction

class TransactionInline(admin.TabularInline):
    model = Transaction
    fields = ('transaction_id', 'amount', 'currency', 'status', 'credit_debit_indicator', 'description', 'booking_date_time')
    extra = 0

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        'account_id',
        'current_balance',
        'available_balance',  # Добавлено поле
        'currency',
        'opened_date_time',
        'description',
        'formatted_card_number',
        'card_expiry_date'
    )
    search_fields = ('account_id', 'description', 'card_number')
    list_filter = ('currency', 'opened_date_time')
    inlines = [TransactionInline]

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id',
        'account',
        'amount',
        'currency',
        'status',
        'credit_debit_indicator',
        'description',
        'booking_date_time',
        'type'
    )
    search_fields = ('transaction_id', 'description', 'account__account_id')
    list_filter = ('currency', 'status', 'credit_debit_indicator', 'booking_date_time', 'type')
