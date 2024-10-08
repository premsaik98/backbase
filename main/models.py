import importlib

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=20, db_index=True)
    symbol = models.CharField(max_length=10)

    def __str__(self):
        return self.code


class CurrencyExchangeRate(models.Model):
    source_currency = models.ForeignKey(Currency, related_name='exchanges', on_delete=models.CASCADE)
    exchanged_currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    valuation_date = models.DateField(db_index=True)
    rate_value = models.DecimalField(max_digits=18, decimal_places=6, db_index=True)
    
    def __str__(self):
        return f"{self.source_currency} to {self.exchanged_currency} on {self.valuation_date}"


class Provider(models.Model):
    name = models.CharField(max_length=100)
    class_path = models.CharField(max_length=255, help_text="Full import path of the provider class (e.g., 'myapp.providers.CurrencyBeaconProvider')")
    priority = models.IntegerField(default=1)
    active = models.BooleanField(default=True)

    def clean(self):
        try:
            module_name, class_name = self.class_path.rsplit('.', 1)
            provider_module = importlib.import_module(module_name)
            provider_class = getattr(provider_module, class_name)
        except (ImportError, AttributeError):
            raise ValidationError({
                'class_path': _(f"Invalid provider class path: {self.class_path}. Ensure the class exists and is importable.")
            })

    def __str__(self):
        return f"{self.name} (Priority: {self.priority}, Active: {self.active})"
