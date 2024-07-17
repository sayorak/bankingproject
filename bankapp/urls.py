from django.urls import path
from .views import add_goal_view, goals_view, get_account_data, get_transactions, wallets_view, profile_view, analytics_view, analytics_transaction_history_view, analytics_expenses_view

urlpatterns = [
    path('', wallets_view, name='wallets'),
    path('profile/', profile_view, name='profile'),
    path('goals/', goals_view, name='goals'),
    path('goals/add/', add_goal_view, name='add_goal'),
    path('analytics/', analytics_view, name='analytics'),
    path('analytics-expenses/', analytics_expenses_view, name='analytics-expenses'),
    path('analytics-transaction-history/', analytics_transaction_history_view, name='analytics-transaction-history'),
    path('get_account_data/<str:account_id>/', get_account_data, name='get_account_data'),
    path('get_transactions/<str:account_id>/', get_transactions, name='get_transactions'),
]
