from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from main.models import Currency, CurrencyExchangeRate, Provider



class CurrencyAdmin(admin.ModelAdmin):
    model = Currency
    fields = ['name', 'code', 'symbol']
    list_display =  ['name', 'code', 'symbol']


class CurrencyExchangeRateAdmin(admin.ModelAdmin):
    change_list_template = 'admin/currencyexchangerate/change_list.html'

    model = CurrencyExchangeRate
    fields = ['source_currency', 'exchanged_currency', 'valuation_date', 'rate_value']
    list_display = ['source_currency', 'exchanged_currency', 'valuation_date', 'rate_value']

    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('converter/', self.admin_site.admin_view(self.converter_view), name='currency_converter'),
        ]
        return custom_urls + urls

    def converter_view(self, request):
        return HttpResponseRedirect(reverse('currency_converter'))


class ProviderAdmin(admin.ModelAdmin):
    model = Provider
    list_display = ['name', 'class_path', 'priority', 'active']
    list_editable = ['priority', 'active']
    search_fields = ['name', 'class_path']


admin.site.register(Currency, CurrencyAdmin)
admin.site.register(CurrencyExchangeRate, CurrencyExchangeRateAdmin)
admin.site.register(Provider, ProviderAdmin)
