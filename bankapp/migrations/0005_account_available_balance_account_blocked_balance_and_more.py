# Generated by Django 5.0.2 on 2024-07-08 17:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bankapp', '0004_transaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='available_balance',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='account',
            name='blocked_balance',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='account',
            name='credit_amount',
            field=models.FloatField(default=0.0),
        ),
    ]
