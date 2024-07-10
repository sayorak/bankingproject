import datetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
import requests

from accounts.models import Profile
from django.views.decorators.csrf import csrf_exempt

from .models import Account, Transaction, Notification
from datetime import datetime

Bearer = 'eyJ4NXQjUzI1NiI6Img3RjhRR0ZnY1d3YngzaUJfQVIzT2V0Snczbmg2S2h5SW9RTWxtdXRVeVEiLCJraWQiOiJucGtfb2F1dGhfc3RhZ2UiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIwMzAyMTA1NTAzMjMiLCJhdWQiOiI5YTA4ZTc5MS0wZmFhLTQ4ODEtOTI3Zi0xMGY0MjA2ZjJlOGQiLCJuYmYiOjE3MjAxMTM4OTQsImF1dGhvcml6YXRpb25faWQiOiIzOTE0OWFiMS03OTc1LTQ3ZmYtODU4Yi05OGQ2M2ZmZGMzNTgiLCJzY29wZSI6WyJvcGVuaWQiLCJhY2NvdW50X3RyYW5zYWN0aW9ucy40NmQ4YTk2NC1mMmMzLTQ1YmUtYmExYS1kNTJjYmU0ZWQxMGQiLCJhY2NvdW50cy40NmQ4YTk2NC1mMmMzLTQ1YmUtYmExYS1kNTJjYmU0ZWQxMGQiLCJhY2NvdW50X2JhbGFuY2UuNDZkOGE5NjQtZjJjMy00NWJlLWJhMWEtZDUyY2JlNGVkMTBkIl0sImlzcyI6Imh0dHBzOi8vYXV0aC5zdGFnZS5raXNjLmt6IiwiZXhwIjoxNzIyNzA1ODk0LCJpYXQiOjE3MjAxMTM4OTQsInNpZCI6IjMyYTE0MWMzLWRlOTctNGVmNC05MWE1LWFhNDEwMmU3ZmU1NSJ9.dK0rbW6Sh9IoK1-pMyB-3INkiZZFDH_KX9nCggsGG45CPVNOBCJZXHpxuE4pmkoYFJ8qfL6wX7a9s2CEnaQNdI6BxtWBVwg7061Rn0K8I0n-DrNdb9gIc_ZzOYvKObtKTRYR6QcnaF-UASECaC_AbrzKwv7LgeUQd648S8muyN_cJ4hF7rgZWN79ssfAChs4Uhc7eGxq24NtjTSdofxCM7zZ6Eqp9hYVXafi7P4wnMTWINB7V9M3bPXqeV65Q2FxHzxvR7h-TsGaSIvn1Xm_okC_C-YYarGfH2YzVuaTlNqhR8DSBHfWAgDmJ5GPIdSYis4lyXscwJptnGT55Jxz9g'

NPKHeaders = {
        "Authorization": f"Bearer {Bearer}",
        "x-fapi-interaction-id": "29736bba-9f68-4efd-bd7a-7ebed80058ce",
        "x-provider-id": "46d8a964-f2c3-45be-ba1a-d52cbe4ed10d"
}

type_mapping = {
    "PAYMENT": "Платеж",
    "E_COMMERCE": "Электронная коммерция",
    "PURCHASE": "Покупка",
    "WITHDRAWAL": "Снятие",
    "INCOME": "Доход",
    "TRANSFER": "Перевод",
    "OTHER": "Прочее"
}   #словарь типов транзакций

#=================================ФУНКЦИИ КОТОРЫЕ ОТНОСЯТСЯ К ОБРАЩЕНИЮ К АПИ НПК===================
def fetch_accounts():
    url = "https://api.stage.kisc.kz/v1/accounts"
    headers = NPKHeaders
    response = requests.get(url, headers=headers)   #отправка гет запроса
    data = response.json()

    accounts = data.get('data', {}).get('accounts', [])   #извлечение списка аккаунтов
    for account in accounts:     #обработка каждого аккаунта
        card_number = generate_random_card_number()  # случайный номер
        expiry_date = generate_random_expiry_date() #дата истечения

        account_obj, created = Account.objects.update_or_create(   #обновление, создание записи в базе данных
            account_id=account['accountId'],
            defaults={
                'current_balance': account['currentBalance'],
                'currency': account['currency'],  #валюта
                'opened_date_time': datetime.fromisoformat(account['openedDateTime'][:-1]),  #дата открытия аккаунта
                'description': account['description'],  #описание
                'card_number': card_number,
                'card_expiry_date': expiry_date
            }
        )
        fetch_transactions(account_obj)    #получение транзакций и баланса
        fetch_balance(account_obj)

def fetch_transactions(account):
    url = f"https://api.stage.kisc.kz/v1/accounts/{account.account_id}/transactions"
    headers = NPKHeaders
    response = requests.get(url, headers=headers)
    data = response.json()

    transactions = data.get('data', {}).get('transactions', [])  #извлечение списка транзакций
    for transaction in transactions:   #обработка каждой транзакции
        amount = transaction['amount']['amount']  #извлечение суммы
        if transaction['type'] != 'INCOME':  #если тип не инком
            amount = -amount
        Transaction.objects.update_or_create(
            transaction_id=transaction['transactionId'],
            defaults={
                'account': account,   #связь с аккаунтом
                'amount': transaction['amount']['amount'],   #сумма транзакции
                'currency': transaction['amount']['currency'],  #валюта
                'status': transaction['status'],
                'credit_debit_indicator': transaction['creditDebitIndicator'],  #индикатор дебета или кредита
                'description': transaction['description'],
                'booking_date_time': datetime.fromisoformat(transaction['bookingDateTime'][:-1]),  #дата
                'type': transaction['type']    #тип транзакции
            }
        )

def fetch_balance(account):
    url = f"https://api.stage.kisc.kz/v1/accounts/{account.account_id}/balance"
    headers = NPKHeaders
    response = requests.get(url, headers=headers)
    data = response.json().get('data', {})
#проверяется получены ли были данные
    if data:
        account, created = Account.objects.get_or_create(account_id=account.account_id)   #поиск в бд
        account.current_balance = data.get('currentBalance', 0)   #обновление валюты и баланса
        account.available_balance = data.get('availableBalance', 0)
        account.blocked_balance = data.get('blockedBalance', 0)
        account.currency = data.get('currency', 'USD')
#обновление кредитной линии, если есть данные
        credit_line = data.get('creditLine', [])
        included_credit = next((line for line in credit_line if line.get('included')), {})
        account.credit_amount = included_credit.get('amount', {}).get('amount', 0)
#генерация случайных номеров
        account.card_number = account.card_number or generate_random_card_number()
        account.card_expiry_date = account.card_expiry_date or generate_random_expiry_date()

        account.save()
#возвращение джсон ответов
        return JsonResponse({"message": "Account balance updated successfully."})
    else:
        return JsonResponse({"error": "Failed to fetch account balance."}, status=400)
#==================================================================================================

#=========================ПРОГРУЗКА СТРАНИЦ=====================================
@login_required
def wallets_view(request):
    fetch_accounts()
    accounts = Account.objects.all()
    user = request.user
    context = {
        'accounts': accounts,
        'user_name': user.get_full_name() or user.username,  # Use full name if available, otherwise username
        'user_email': user.email
    }
    Notification.objects.create(user=request.user, message='Просмотрены счета из API НПК')
    return render(request, 'bankapp/wallets.html', context)


@login_required
def analytics_expenses_view(request):
    user = request.user
    context = {
        'user_name': user.get_full_name() or user.username,  # Use full name if available, otherwise username
        'user_email': user.email
    }
    return render(request, 'bankapp/analytics_expenses.html', context)

@login_required
def analytics_view(request):
    user = request.user
    context = {
        'user_name': user.get_full_name() or user.username,  # Use full name if available, otherwise username
        'user_email': user.email
    }
    return render(request, 'bankapp/analytics.html', context)

@login_required
def analytics_income_view(request):
    user = request.user
    context = {
        'user_name': user.get_full_name() or user.username,  # Use full name if available, otherwise username
        'user_email': user.email
    }
    return render(request, 'bankapp/analytics_income.html', context)

@login_required
def analytics_transaction_history_view(request):
    user = request.user
    context = {
        'user_name': user.get_full_name() or user.username,  # Use full name if available, otherwise username
        'user_email': user.email
    }
    return render(request, 'bankapp/analytics_transaction_history.html', context)


@login_required
def profile_view(request):
    profile = Profile.objects.get(user=request.user)
    user = request.user
    context = {
        'profile': profile,
        'user_name': user.get_full_name() or user.username,  # Use full name if available, otherwise username
        'user_email': user.email,
        'registration_date': profile.user.date_joined
    }
    Notification.objects.create(user=request.user, message='Посетил свою страницу профиля')
    return render(request, 'bankapp/profile.html', context)
#=========================ФУНКЦИИ ДЛЯ ПРОГРУЗКИ СТРАНИЦ=====================================

import random
from datetime import datetime, timedelta

def generate_random_card_number():    #номер карты
    return ''.join([str(random.randint(0, 9)) for _ in range(16)])

def generate_random_expiry_date():
    today = datetime.today()
    end_date = today + timedelta(days=5*365)
    random_date = today + (end_date - today) * random.random()
    return random_date.date()


#==================================ОБРАЩАЕМСЯ ЧЕРЕЗ GET ЗАПРОСЫ======================
@csrf_exempt
def get_transactions(request, account_id):
    categories = request.GET.get('categories', '').split(',')

    if categories and categories[0] != '':
        transactions = Transaction.objects.filter(account__account_id=account_id, type__in=categories).order_by('-booking_date_time')
    else:
        transactions = Transaction.objects.filter(account__account_id=account_id).order_by('-booking_date_time')

    transactions_data = [
        {
            "transaction_id": transaction.transaction_id,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "status": transaction.status,
            "credit_debit_indicator": transaction.credit_debit_indicator,
            "description": transaction.description,
            "booking_date_time": transaction.booking_date_time.strftime('%d.%m.%Y'),
            "type": transaction.type
        }
        for transaction in transactions
    ]

    return JsonResponse({"transactions": transactions_data})

@csrf_exempt
def get_account_data(request, account_id):
    try:
        account = Account.objects.get(account_id=account_id)
        data = {
            'current_balance': account.current_balance,
            'available_balance': account.available_balance,
            'blocked_balance': account.blocked_balance,
            'credit_amount': account.credit_amount,
            'currency': account.currency,
            'card_number': account.formatted_card_number(),
            'card_expiry_date': account.card_expiry_date.strftime('%m/%y') if account.card_expiry_date else None,
        }
        return JsonResponse({'data': data})
    except Account.DoesNotExist:
        return JsonResponse({'error': 'Account not found.'}, status=404)

