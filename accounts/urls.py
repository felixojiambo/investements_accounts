from django.urls import path, include

urlpatterns = [
    path('auth/', include('accounts.urls.authentication_urls')),
    path('user-accounts/', include('accounts.urls.user_account_urls')),
    path('investment-accounts/', include('accounts.urls.investment_account_urls')),
    path('transactions/', include('accounts.urls.transaction_urls')),
]
