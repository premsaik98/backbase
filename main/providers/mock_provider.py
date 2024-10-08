import random

class MockProvider:
    def get_exchange_rate_data(self, source_currency, exchanged_currency, valuation_date=None):
        return round(random.uniform(0.5, 1.5), 6)
