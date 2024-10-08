from rest_framework import serializers
from .models import Currency, CurrencyExchangeRate


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['code', 'name', 'symbol']


class CurrencyExchangeRateSerializer(serializers.ModelSerializer):
    source_currency = CurrencySerializer()
    exchanged_currency = CurrencySerializer()

    class Meta:
        model = CurrencyExchangeRate
        fields = ['source_currency', 'exchanged_currency', 'rate_value', 'valuation_date']


class CurrencyExchangeRateCreateSerializer(serializers.ModelSerializer):
    source_currency = serializers.SlugRelatedField(slug_field='code', queryset=Currency.objects.all())
    exchanged_currency = serializers.SlugRelatedField(slug_field='code', queryset=Currency.objects.all())

    class Meta:
        model = CurrencyExchangeRate
        fields = ['source_currency', 'exchanged_currency', 'rate_value', 'valuation_date']

    def create(self, validated_data):
        return CurrencyExchangeRate.objects.create(**validated_data)
