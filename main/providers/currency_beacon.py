import requests
from constance import config
from django.core.cache import cache
from requests.adapters import HTTPAdapter
from rest_framework import status
from rest_framework.response import Response
from urllib3 import Retry

class CurrencyBeaconProviderException(Exception):
    pass


class CurrencyBeaconProvider:

    def __init__(self, base_url=None, api_key=None, ):
        self.base_url = base_url or config.BEACON_BASE_URL
        self.api_key = api_key or config.CURRENCY_BEACON_API_KEY 
        self.session = requests.Session()
        retries = Retry(total=config.MAX_RETRIES, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def get_exchange_rate_data(self, source_currency, exchanged_currency):
        cache_key = f"{source_currency}_{exchanged_currency}_'latest'"
        cached_rate = cache.get(cache_key)

        if cached_rate:
            return cached_rate

        params = {
            'api_key': self.api_key,
            'base': source_currency,
            'symbols': exchanged_currency,
        }

        try:
            uri = self.base_url + "/latest"
            response = self.session.get(uri, params=params, timeout=config.API_REQUEST_TIMEOUT )
            if response.status_code == 200:
                rate = response.json()['response']['rates'].get(exchanged_currency)
                cache.set(cache_key, rate, timeout=config.CACHE_TIMEOUT)
                return rate
        except CurrencyBeaconProviderException as ex:
            print(f"Failed to get the exchange rate: {ex}")
            return None
    
    def get_historical_exchange_rate(self, source_currency, from_date, symbols=None):
        url = self.base_url + '/historical'
        params = {
            'api_key': self.api_key,
            'base': source_currency,
            'date': from_date,
            'symbols': symbols,
        }

        try:
            res = self.session.get(url, params=params)
            res.raise_for_status()
            code = res.json().get('meta').get('code') 
            if code == 200:
                data = res.json()['response']
                return data, code
            return {}, code
        except Exception as e:
            raise e
    

    def get_timeseries_exchange_rate(self, source_currency, from_date, to_date, symbols):
        url = self.base_url + '/timeseries'
        params = {
            'api_key': self.api_key,
            'base': source_currency,
            'start_date': from_date,
            'end_date': to_date,
            'symbols': symbols
        }

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            code = response.json().get('meta').get('code') 
            if code == 200:
                data = response.json()['response']
                return data, code
            return {}, code
        except Exception as e:
            raise e

    


