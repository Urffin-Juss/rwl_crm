from apps.stock.models import StockLocation
from django.conf import settings

def get_tech_stock_location():

    return StockLocation.objects.get(name=settings.DEFAULT_TECH_STOCK_LOCATION_NAME)


