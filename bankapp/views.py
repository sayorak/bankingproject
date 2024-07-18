import datetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
import requests
from django.db import models  # Import models
from django.utils.timezone import make_aware, now

from accounts.models import Profile
from django.views.decorators.csrf import csrf_exempt

from .models import Account, Transaction, Notification, Goal
from datetime import datetime
from django.utils.dateparse import parse_date
from django.db.models import Sum

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
    response = requests.get(url, headers=headers)   # Send GET request
    data = response.json()

    accounts = data.get('data', {}).get('accounts', [])   # Extract the list of accounts
    for account in accounts:     # Process each account
        account_obj, created = Account.objects.update_or_create(   # Update or create a record in the database
            account_id=account['accountId'],
            defaults={
                'current_balance': account['currentBalance'],
                'currency': account['currency'],  # Currency
                'opened_date_time': datetime.fromisoformat(account['openedDateTime'][:-1]),  # Account opening date
                'description': account['description']  # Description
            }
        )

        # Check and set card number and expiry date if they don't already exist
        if not account_obj.card_number:
            account_obj.card_number = generate_random_card_number()
        if not account_obj.card_expiry_date:
            account_obj.card_expiry_date = generate_random_expiry_date()

        account_obj.save()

        fetch_transactions(account_obj)    # Fetch transactions and balance
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

    # Check if data was received
    if data:
        account, created = Account.objects.get_or_create(account_id=account.account_id)  # Find in the database
        account.current_balance = data.get('currentBalance', 0)  # Update balance and currency
        account.available_balance = data.get('availableBalance', 0)
        account.blocked_balance = data.get('blockedBalance', 0)
        account.currency = data.get('currency', 'USD')

        # Update credit line if data is available
        credit_line = data.get('creditLine', [])
        included_credit = next((line for line in credit_line if line.get('included')), {})
        account.credit_amount = included_credit.get('amount', {}).get('amount', 0)

        # Generate random numbers only if card_number is not set
        if not account.card_number:
            account.card_number = generate_random_card_number()
        if not account.card_expiry_date:
            account.card_expiry_date = generate_random_expiry_date()

        account.save()

        # Return JSON response
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
    accounts = Account.objects.all()  # Fetch all accounts

    # Get the selected account from the request
    selected_account_id = request.GET.get('account')
    selected_account = accounts.first()  # Default to the first account if none is selected
    if selected_account_id:
        selected_account = Account.objects.get(account_id=selected_account_id)

    # Format card numbers
    for account in accounts:
        if account.card_number:
            account.formatted_card_number = f'*{account.card_number[-4:]}'
        else:
            account.formatted_card_number = account.account_id

    # Get all transactions for the selected account
    transactions = Transaction.objects.filter(account=selected_account).exclude(type='INCOME').order_by('-booking_date_time')

    # Translate categories to Russian
    category_translation = {
        'INCOME': 'Пополнение',
        'WITHDRAWAL': 'Снятие',
        'TRANSFER': 'Перевод',
        'PURCHASE': 'Покупка',
        'E_COMMERCE': 'Интернет покупка',
        'PAYMENT': 'Платеж',
        'BONUS': 'Бонус/кэшбек',
        'OTHER': 'Прочие операции'
    }

    # Aggregate expenses by category
    expense_types = ['WITHDRAWAL', 'TRANSFER', 'PURCHASE', 'E_COMMERCE', 'PAYMENT', 'BONUS', 'OTHER']
    expenses = transactions.filter(type__in=expense_types)

    categories = expenses.values('type').annotate(total_amount=models.Sum('amount')).order_by('-total_amount')
    total_expenses = sum(category['total_amount'] for category in categories)
    category_breakdown = [
        {
            'type': category_translation.get(category['type'], category['type']),
            'total_amount': category['total_amount'],
            'percentage': (category['total_amount'] / total_expenses) * 100 if total_expenses else 0
        }
        for category in categories
    ]

    # Prepare data for the pie chart
    labels = [category['type'] for category in category_breakdown]
    data = [category['total_amount'] for category in category_breakdown]

    # Translate transaction types for display
    for transaction in transactions:
        transaction.translated_type = category_translation.get(transaction.type, transaction.type)

    context = {
        'user_name': user.get_full_name() or user.username,
        'user_email': user.email,
        'accounts': accounts,
        'selected_account': selected_account,
        'category_breakdown': category_breakdown,
        'transactions': transactions,
        'chart_labels': labels,
        'chart_data': data
    }
    return render(request, 'bankapp/analytics_expenses.html', context)


@login_required
def analytics_view(request):
    user = request.user
    accounts = Account.objects.all()  # Fetch all accounts

    # Get the selected account from the request
    selected_account_id = request.GET.get('account')
    selected_account = accounts.first()  # Default to the first account if none is selected
    if selected_account_id:
        selected_account = Account.objects.get(id=selected_account_id)

    # Format card numbers
    for account in accounts:
        if account.card_number:
            account.formatted_card_number = f'*{account.card_number[-4:]}'
        else:
            account.formatted_card_number = account.account_id

    # Get all transactions for the selected account
    transactions = Transaction.objects.filter(
        account=selected_account
    )

    # Aggregate transactions by year over the last 7 years
    current_year = datetime.now().year
    start_year = current_year - 6  # Last 7 years
    labels = [str(year) for year in range(start_year, current_year + 1)]
    data = []

    for year in range(start_year, current_year + 1):
        yearly_total = transactions.filter(
            booking_date_time__year=year
        ).aggregate(total_amount=models.Sum('amount'))['total_amount'] or 0
        data.append(yearly_total)

    # Calculate additional statistics
    total_transactions = transactions.count()

    if total_transactions > 0:
        earliest_transaction = transactions.earliest('booking_date_time').booking_date_time
        earliest_transaction = make_aware(earliest_transaction) if earliest_transaction.tzinfo is None else earliest_transaction
        total_days = (make_aware(datetime.now()) - earliest_transaction).days
    else:
        total_days = 1

    avg_per_day = sum(data) / total_days

    unique_transaction_types = transactions.values('type').distinct().count()
    change_percentage = ((data[-1] - data[-2]) / data[-2] * 100) if len(data) > 1 and data[-2] != 0 else 0

    context = {
        'user_name': user.get_full_name() or user.username,
        'user_email': user.email,
        'accounts': accounts,
        'selected_account': selected_account,
        'labels': labels,
        'data': data,
        'avg_per_day': avg_per_day,
        'total_transactions': total_transactions,
        'change_percentage': change_percentage,
        'unique_transaction_types': unique_transaction_types
    }
    return render(request, 'bankapp/analytics.html', context)

from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from datetime import timedelta
from .models import Transaction, Account

@login_required
def analytics_transaction_history_view(request):
    user = request.user
    accounts = Account.objects.all()
    selected_account_id = request.GET.get('account')
    filter_option = request.GET.get('filter')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Установка выбранного аккаунта
    selected_account = accounts.first()
    if selected_account_id:
        selected_account = Account.objects.get(account_id=selected_account_id)

    # Определяем период на основе выбранного фильтра
    if filter_option == 'week':
        start_date = now() - timedelta(weeks=1)
        end_date = now()
    elif filter_option == 'month':
        start_date = now() - timedelta(days=30)
        end_date = now()
    elif filter_option == 'three_months':
        start_date = now() - timedelta(days=90)
        end_date = now()
    elif filter_option == 'half_year':
        start_date = now() - timedelta(days=180)
        end_date = now()
    elif filter_option == 'year':
        start_date = now() - timedelta(days=365)
        end_date = now()
    elif filter_option == 'period' and start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        start_date = None
        end_date = None

    # Фильтрация транзакций по выбранному аккаунту и периоду
    if start_date and end_date:
        transactions = Transaction.objects.filter(
            account=selected_account,
            booking_date_time__range=[start_date, end_date]
        ).order_by('-booking_date_time')

        # Вычисляем начальный баланс
        income_before_start_date = Transaction.objects.filter(
            account=selected_account,
            booking_date_time__lt=start_date,
            type='INCOME'
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        expense_before_start_date = Transaction.objects.filter(
            account=selected_account,
            booking_date_time__lt=start_date
        ).exclude(type='INCOME').aggregate(Sum('amount'))['amount__sum'] or 0

        initial_balance = (income_before_start_date - expense_before_start_date)
    else:
        transactions = Transaction.objects.filter(account=selected_account).order_by('-booking_date_time')
        initial_balance = 0

    # Вычисление итоговых значений
    income_total = transactions.filter(type='INCOME').aggregate(Sum('amount'))['amount__sum'] or 0
    expense_total = transactions.exclude(type='INCOME').aggregate(Sum('amount'))['amount__sum'] or 0
    final_balance = initial_balance + income_total - expense_total

    # Перевод типов транзакций
    for transaction in transactions:
        transaction.translated_type = {
            'INCOME': 'Пополнение',
            'WITHDRAWAL': 'Снятие',
            'TRANSFER': 'Перевод',
            'PURCHASE': 'Покупка',
            'E_COMMERCE': 'Интернет покупка',
            'PAYMENT': 'Платеж',
            'BONUS': 'Бонус/кэшбек',
            'OTHER': 'Прочие операции'
        }.get(transaction.type, transaction.type)

    context = {
        'user_name': user.get_full_name() or user.username,
        'user_email': user.email,
        'accounts': accounts,
        'selected_account': selected_account,
        'transactions': transactions,
        'start_date': start_date,
        'end_date': end_date,
        'initial_balance': initial_balance,
        'income_total': income_total,
        'expense_total': expense_total,
        'final_balance': final_balance,
        'start_date': start_date,
        "end_date": end_date
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


@login_required
def goals_view(request):
    user = request.user
    if request.method == 'POST':
        account_id = request.POST.get('account')
        name = request.POST.get('name')
        target_amount = request.POST.get('target_amount')

        account = Account.objects.get(account_id=account_id)
        Goal.objects.create(user=request.user, account=account, name=name, target_amount=target_amount)
        return redirect('goals')

    goals = Goal.objects.filter(user=request.user)
    accounts = Account.objects.all()
    for goal in goals:
        if goal.target_amount > 0:
            goal.progress = (goal.current_amount / goal.target_amount) * 100
        else:
            goal.progress = 0
    context = {
        'goals': goals,
        'user_name': user.get_full_name() or user.username,  # Use full name if available, otherwise username
        'user_email': user.email,
        'accounts': accounts,
    }
    return render(request, 'bankapp/goals.html', context)

@login_required
def add_goal_view(request):
    goals = Goal.objects.filter(user=request.user)
    context = {
        'goals': goals
    }
    return render(request, 'bankapp/goals.html', context)

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
        account = Account.objects.get(account_id = account_id)
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

@csrf_exempt
def add_funds(request):
    if request.method == 'POST':
        goal_id = request.POST.get('goal_id')
        add_amount = float(request.POST.get('add_amount'))
        goal = Goal.objects.get(id=goal_id)
        goal.current_amount += add_amount
        goal.save()
        return redirect('goals')