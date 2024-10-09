from datetime import datetime
from django.db import DatabaseError
import requests
from decimal import Decimal, ROUND_DOWN
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from main.forms import CurrencyConverterForm
from main.models import CurrencyExchangeRate, Currency
from main.providers.currency_beacon import CurrencyBeaconProvider
from main.providers.provider_manager import ProviderManager
from main.serializers import CurrencyExchangeRateSerializer, CurrencyExchangeRateCreateSerializer, CurrencySerializer
from main.utils import transform_data
\

class CurrencyAPIView(APIView):
    """
    Handle all CRUD operations for Currency using APIView.
    """

    def get(self, request, code=None):
        try:
            if code:
                currency = get_object_or_404(Currency, code=code)
                serializer = CurrencySerializer(currency)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                currencies = Currency.objects.all()
                serializer = CurrencySerializer(currencies, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Currency.DoesNotExist:
            return Response({"status":"failed", "error": "Currency not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status":"failed", "error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    def post(self, request):
        try:
            serializer = CurrencySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as db_err:
            return Response({"status":"failed", "error": f"Database error: {str(db_err)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status":"failed", "error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def patch(self, request, code):
        try:
            currency = get_object_or_404(Currency, code=code.upper())
            serializer = CurrencySerializer(currency, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Currency.DoesNotExist:
            return Response({"status":"failed", "error": "Currency not found"}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError as db_err:
            return Response({"status":"failed", "error": f"Database error: {str(db_err)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status":"failed", "error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, code):
        try:
            currency = get_object_or_404(Currency, code=code)
            currency.delete()
            return Response({"message": "Currency deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Currency.DoesNotExist:
            return Response({"status":"failed", "error": "Currency not found"}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError as db_err:
            return Response({"status":"failed", "error": f"Database error: {str(db_err)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status":"failed", "error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ExchangeRateView(APIView):
    
    def get(self, request, source_currency, exchanged_currency, valuation_date=None):

        source_currency_obj, created = Currency.objects.get_or_create(code=source_currency.upper(), defaults={'name': source_currency.upper()})
        exchanged_currency_obj, created = Currency.objects.get_or_create(code=exchanged_currency.upper(), defaults={'name': exchanged_currency.upper()})

        if valuation_date:
            valuation_date = parse_date(valuation_date)
        else:
            valuation_date = timezone.now().date()

        existing_rate = CurrencyExchangeRate.objects.filter(
            source_currency=source_currency_obj,
            exchanged_currency=exchanged_currency_obj,
            valuation_date=valuation_date
        ).first()

        if existing_rate:
            serializer = CurrencyExchangeRateSerializer(existing_rate)
            return Response(serializer.data)

        provider_manager = ProviderManager()
        rate = provider_manager.get_exchange_rate_data(source_currency, exchanged_currency, valuation_date)

        if rate:
            rounded_rate = Decimal(rate).quantize(Decimal('1.000000'), rounding=ROUND_DOWN)


            create_data = {
                'source_currency': source_currency_obj.code,
                'exchanged_currency': exchanged_currency_obj.code,
                'rate_value': rounded_rate,
                'valuation_date': valuation_date
            }


            create_serializer = CurrencyExchangeRateCreateSerializer(data=create_data)
            if create_serializer.is_valid():
                create_serializer.save()
                return Response(create_serializer.data, status=201)
            else:
                return Response(create_serializer.errors, status=400)

        return Response({"error": "Unable to fetch exchange rate"}, status=400)


def fetch_exchange_rate_from_api(request, source_currency_code, target_currency_code):

    try:
        relative_url = reverse('exchange_rate', kwargs={
            'source_currency': source_currency_code,
            'exchanged_currency': target_currency_code
        })
        
        api_url = request.build_absolute_uri(relative_url)
        
        response = requests.get(api_url)
        if response.status_code == 201:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error calling ExchangeRateView API: {e}")
        return None



class CurrencyConverterAPIView(APIView):
    def get(self, request):
        form = CurrencyConverterForm()
        return render(request, 'admin/converter.html', {'form': form})

    def post(self, request):
        if request.content_type == 'application/json':
            source_currency_code = request.data.get('source_currency', "").upper()
            target_currency_codes = request.data.get('target_currencies', [])

            try:
                source_currency = Currency.objects.get(code=source_currency_code)
            except Currency.DoesNotExist:
                return Response(
                    {"source_currency": [f"Currency with code '{source_currency_code}' does not exist."]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            target_currencies = []
            for code in target_currency_codes:
                code_upper = code.strip().upper()
                try:
                    target_currency = Currency.objects.get(code=code_upper)
                    target_currencies.append(target_currency.pk)
                except Currency.DoesNotExist:
                    return Response(
                        {"target_currencies": [f"Currency with code '{code_upper}' does not exist."]}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            form_data = {
                'source_currency': source_currency.pk,
                'target_currencies': target_currencies,
                'amount': request.data.get('amount')
            }
            
            form = CurrencyConverterForm(data=form_data)

            if form.is_valid():
                conversion_results = self.process_conversion(form)
                return Response({'conversion_results': conversion_results}, status=status.HTTP_200_OK)
            else:
                return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            form = CurrencyConverterForm(request.POST)
            if form.is_valid():
                conversion_results = self.process_conversion(form)
                return render(request, 'admin/converter.html', {'form': form, 'conversion_results': conversion_results})
            
            return render(request, 'admin/converter.html', {'form': form})


    def process_conversion(self, form):
        source_currency = form.cleaned_data['source_currency']
        target_currencies = form.cleaned_data['target_currencies']
        amount = form.cleaned_data['amount']

        conversion_results = []

        def get_exchange_rate_and_convert(target_currency, rate):
            converted_amount = round(Decimal(str(amount)) * rate, 2)
            conversion_results.append({
                'target_currency': target_currency.name,
                'converted_amount': str(converted_amount),
                'rate_value': str(round(rate, 6)),
                'symbol': target_currency.symbol
            })

        def fetch_exchange_rate_from_provider(target_currency):
            provider_manager = ProviderManager()
            rate = provider_manager.get_exchange_rate_data(source_currency.code, target_currency.code)

            if rate:
                rounded_rate = Decimal(rate).quantize(Decimal('1.000000'), rounding=ROUND_DOWN)

                create_data = {
                    'source_currency': source_currency.code,
                    'exchanged_currency': target_currency.code,
                    'rate_value': rounded_rate,
                    'valuation_date': timezone.now().date()
                }

                create_serializer = CurrencyExchangeRateCreateSerializer(data=create_data)
                if create_serializer.is_valid():
                    create_serializer.save()

                get_exchange_rate_and_convert(target_currency, rate)
            else:
                conversion_results.append({
                    'target_currency': target_currency.name,
                    'converted_amount': "N/A",
                    'rate_value': "N/A",
                    'symbol': target_currency.symbol
                })

        for target_currency in target_currencies:
            exchange_rate = CurrencyExchangeRate.objects.filter(
                source_currency=source_currency,
                exchanged_currency=target_currency
            ).order_by('-valuation_date').first()

            if exchange_rate:
                get_exchange_rate_and_convert(target_currency, exchange_rate.rate_value)
            else:
                fetch_exchange_rate_from_provider(target_currency)

        return conversion_results



def get_target_currencies(request):
    source_currency_id = request.GET.get('source_currency')
    if source_currency_id:
        target_currencies = Currency.objects.exclude(id=source_currency_id)
        data = [{'id': currency.id, 'name': currency.name} for currency in target_currencies]
        return JsonResponse({'target_currencies': data})
    return JsonResponse({'target_currencies': []})


class HistoricalCurrencyRate(APIView):

    def get(self, request, *args, **kwargs):
        try:
            source_currency = request.data.get('source_currency')
            from_date = request.data.get('from_date')
            symbols = request.data.get('symbols')

            if not (source_currency or from_date or symbols):
                return Response({'status':'failed', 'error': 'Invalid input parameters.'}, status.HTTP_400_BAD_REQUEST)
            
            try:
                from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            except ValueError:
                return Response({'status':'failed', 'error': 'Invalid date format'}, status.HTTP_400_BAD_REQUEST)

            cbp = CurrencyBeaconProvider()
            result, code = cbp.get_historical_exchange_rate(source_currency, from_date, symbols)

            if not code == 200:
                raise
            return Response(result, status.HTTP_200_OK)
        except Exception as ex:
            print(str(ex))
            return Response({'status': 'failed', 'error': 'An error occurred.'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        




class TimeseriesCurrencyRate(APIView):

    def get(self, request, *args, **kwargs):
        try:
            source_currency = request.data.get('source_currency')
            from_date = request.data.get('from_date')
            to_date = request.data.get('to_date')
            symbols = request.data.get('symbols')

            if not (from_date or to_date or symbols):
                return Response({'status':'failed', 'error': 'Invalid input parameters.'}, status.HTTP_400_BAD_REQUEST)
            
            try:
                from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
                to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
            except ValueError:
                return Response({'status':'failed', 'error': 'Invalid date format'}, status.HTTP_400_BAD_REQUEST)

            cbp = CurrencyBeaconProvider()
            data, code = cbp.get_timeseries_exchange_rate(source_currency, from_date, to_date, symbols)

            result = transform_data(data, source_currency)

            if not code == 200:
                raise
            return Response(result, status.HTTP_200_OK)
        except Exception as ex:
            print(str(ex))
            return Response({'status': 'failed', 'error': f'An error occurred'}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        