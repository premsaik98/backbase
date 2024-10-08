import importlib
from main.models import Provider

class ProviderManager:

    def __init__(self):
        self.providers = self.load_providers_from_db()

    def load_providers_from_db(self):
        provider_entries = Provider.objects.filter(active=True).order_by('priority')
        provider_instances = []

        for entry in provider_entries:
            try:
                module_name, class_name = entry.class_path.rsplit('.', 1)
                provider_module = importlib.import_module(module_name)
                provider_class = getattr(provider_module, class_name)
                
                provider_instance = provider_class()
                provider_instances.append({
                    "provider": provider_instance,
                    "priority": entry.priority
                })
            except (ImportError, AttributeError) as e:
                print(f"Error loading provider {entry.class_path}: {e}")
                continue

        return provider_instances


    def get_exchange_rate_data(self, source_currency, exchanged_currency, valuation_date=None):
        for provider_entry in self.providers:
            try:
                rate = provider_entry["provider"].get_exchange_rate_data(source_currency, exchanged_currency, valuation_date)
                if rate is not None:
                    return rate
            except Exception as e:
                print(f"Provider {provider_entry['provider']} failed: {e}")
        return None
