from django.db import models
from datetime import datetime
from django.contrib.auth.models import User

class Account(models.Model):
    account_id = models.CharField(max_length=100, unique=True)
    current_balance = models.FloatField()
    available_balance = models.FloatField(default=0.0)
    blocked_balance = models.FloatField(default=0.0)
    credit_amount = models.FloatField(default=0.0)
    currency = models.CharField(max_length=10)
    opened_date_time = models.DateTimeField()
    description = models.TextField()
    card_number = models.CharField(max_length=16, blank=True, null=True)
    card_expiry_date = models.DateField(blank=True, null=True)


    def __str__(self):
        return self.account_id

    def formatted_card_number(self):
        if self.card_number:
            return ' '.join(self.card_number[i:i+4] for i in range(0, len(self.card_number), 4))
        return None


class Transaction(models.Model):
    transaction_id = models.CharField(max_length=100, unique=True)
    account = models.ForeignKey(Account, related_name='transactions', on_delete=models.CASCADE)
    amount = models.FloatField()
    currency = models.CharField(max_length=10)
    status = models.CharField(max_length=20)
    credit_debit_indicator = models.CharField(max_length=10)
    description = models.TextField()
    booking_date_time = models.DateTimeField()
    type = models.CharField(max_length=20, default = 'PAYMENT')  # Добавляем поле для типа транзакции

    def __str__(self):
        return self.transaction_id

class Notification(models.Model):
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.message

class NotificationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by('-created_at')

class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=255)
    target_amount = models.FloatField()
    current_amount = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name