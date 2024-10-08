import json

from datetime import datetime
from main.models import Currency, CurrencyExchangeRate


def save_exchange_rates(response):
    base_currency_code = response['base']
    rates = response['rates']
    valuation_date = response['date']

    base_currency, _ = Currency.objects.get_or_create(code=base_currency_code)

    for target_currency_code, rate_value in rates.items():
        target_currency, _ = Currency.objects.get_or_create(code=target_currency_code)

        CurrencyExchangeRate.objects.update_or_create(
            source_currency=base_currency,
            exchanged_currency=target_currency,
            valuation_date=datetime.strptime(valuation_date, "%Y-%m-%d"),
            defaults={'rate_value': rate_value}
        )



def transform_data(data, source_currency):
    result = []
    for date, rates in data.items():
        for currency, rate in rates.items():
            result.append({
                "base": source_currency,
                "currency": currency,
                "date": date,
                "rate": rate
            })
    return result