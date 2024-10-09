from django.urls import path
from main.views import ExchangeRateView, CurrencyConverterAPIView, get_target_currencies, HistoricalCurrencyRate, TimeseriesCurrencyRate, CurrencyAPIView


urlpatterns = [
    path('currencies/', CurrencyAPIView.as_view(), name='currency_list_create'),
    path('currencies/<str:code>/', CurrencyAPIView.as_view(), name='currency_detail'),
    path('converter/', CurrencyConverterAPIView.as_view(), name='currency_converter'),
    path('get-target-currencies/', get_target_currencies, name='get_target_currencies'),
    path('historical-rate/', HistoricalCurrencyRate.as_view(), name='historical_rate'),
    path('currency-rates-list/', TimeseriesCurrencyRate.as_view(), name='currency-rates-list'),
    path('exchange-rate/<str:source_currency>/<str:exchanged_currency>/', ExchangeRateView.as_view(), name='exchange_rate'),
    path('exchange-rate/<str:source_currency>/<str:exchanged_currency>/<str:valuation_date>/', ExchangeRateView.as_view(), name='exchange_rate_with_date'),
]
