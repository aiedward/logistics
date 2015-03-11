from logistics.exceptions import TooMuchStockError
from logistics.models import ProductStock
from rapidsms.conf import settings


def check_max_levels_malawi(stock_report):
    """
    checks a stock report against maximum allowable levels. if more than the
    allowable threshold of stock is being reported it throws a validation error
    """
    hard_coded_max_thresholds = {
        "cl": 100,
        "cf": 1000,
        "cm": 1000,
        "co": 2000,
        "cw": 1000,
        "de": 300,
        "dm": 300,
        "gl": 300,
        "la": 2000,
        "lb": 2000,
        "lc": 300,
        "or": 500,
        "pa": 2000,
        "pb": 1000,
        "po": 100,
        "ss": 100,
        "te": 100,
        "un": 100,
        "zi": 2000,
    }
    MAX_REPORT_LEVEL_FACTOR = 3
    def _over_static_threshold(product_code, stock):
        return (
            not product_code or   # unknown, consider over
            product_code.lower() not in hard_coded_max_thresholds or  # not found, consider over
            stock > hard_coded_max_thresholds[product_code.lower()]  # actually over
        )
    for product_code, stock in stock_report.product_stock.items():
        if _over_static_threshold(product_code, stock):
            product = stock_report.get_product(product_code)
            try:
                current_stock = ProductStock.objects.get(supply_point=stock_report.supply_point,
                                                         product=product)
                max = current_stock.maximum_level * MAX_REPORT_LEVEL_FACTOR
                if stock > max:
                    raise TooMuchStockError(product=product, amount=stock, max=max)
            except ProductStock.DoesNotExist:
                pass