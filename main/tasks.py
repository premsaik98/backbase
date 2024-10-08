from backbase.celery_app import app
from main.providers.currency_beacon import CurrencyBeaconProvider
from main.utils import save_exchange_rates


@app.task(name='Save Historical Data')
def fetch_and_save_historical_exchange_rate(self, source_currency, exchanged_currency, date):
    provider = CurrencyBeaconProvider()
    result = provider.get_historical_exchange_rate(source_currency, exchanged_currency, date)
    
    if result:
        save_exchange_rates(result)
    else:
        self.retry(countdown=60, max_retries=3)

