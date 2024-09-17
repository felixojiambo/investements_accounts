from django.urls import path

from accounts.views import UserAccountListView, UserAccountCreateView, UserAccountDetailView

app_name = 'user_accounts'

urlpatterns = [
    path('', UserAccountListView.as_view(), name='user-account-list'),
    path('create/', UserAccountCreateView.as_view(), name='user-account-create'),
    path('<int:pk>/', UserAccountDetailView.as_view(), name='user-account-detail'),
]
