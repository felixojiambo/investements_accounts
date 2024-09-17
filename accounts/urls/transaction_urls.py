from django.urls import path

from accounts.views import  AdminUserTransactionsView, TransactionListView, \
    CreateTransactionView, TransactionDetailView

app_name = 'transactions'

urlpatterns = [
    path('list/', TransactionListView.as_view(), name='transaction-list'),
    path('create/', CreateTransactionView.as_view(), name='transaction-create'),
    path('<int:transaction_id>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('admin/user-transactions/', AdminUserTransactionsView.as_view(), name='admin-user-transactions'),
]
