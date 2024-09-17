from django.urls import path

from accounts.views import InvestmentAccountCreateView

app_name = 'investment_accounts'

urlpatterns = [
    path('', InvestmentAccountCreateView.as_view(), name='create-investment-account'),
]
