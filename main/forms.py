from django import forms
from main.models import Currency

class CurrencyConverterForm(forms.Form):
    source_currency = forms.ModelChoiceField(queryset=Currency.objects.all(), label="Source Currency")
    target_currencies = forms.ModelMultipleChoiceField(queryset=Currency.objects.all(), label="Target Currencies")
    amount = forms.DecimalField(max_digits=12, decimal_places=2, label="Amount to Convert")

    def __init__(self, *args, **kwargs):
        super(CurrencyConverterForm, self).__init__(*args, **kwargs)
        if 'source_currency' in self.data:
            try:
                source_currency_id = int(self.data.get('source_currency'))
                self.fields['target_currencies'].queryset = Currency.objects.exclude(id=source_currency_id)
            except (ValueError, TypeError):
                pass
