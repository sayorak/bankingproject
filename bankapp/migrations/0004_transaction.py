# Generated by Django 5.0.3 on 2024-07-08 14:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bankapp', '0003_account_card_expiry_date_account_card_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(max_length=100, unique=True)),
                ('amount', models.FloatField()),
                ('currency', models.CharField(max_length=10)),
                ('status', models.CharField(max_length=20)),
                ('credit_debit_indicator', models.CharField(max_length=10)),
                ('description', models.TextField()),
                ('booking_date_time', models.DateTimeField()),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='bankapp.account')),
            ],
        ),
    ]
