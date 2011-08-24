from logistics.decorators import place_in_request
from logistics.models import SupplyPoint, Product
from logistics.views import get_facilities
from logistics.reports import ReportingBreakdown
from dimagi.utils.dates import DateSpan
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils import translation
from logistics_project.apps.malawi.util import facility_supply_points_below
from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown
from logistics_project.apps.tanzania.tables import OrderingStatusTable
from logistics_project.apps.tanzania.utils import chunks
from rapidsms.contrib.locations.models import Location
from dimagi.utils.decorators.datespan import datespan_in_request
from models import DeliveryGroups
from logistics.views import MonthPager

def _get_facilities_and_location(request):
    base_facilities = SupplyPoint.objects.filter(active=True, type__code="facility")

    # district filter
    if request.location and not request.location.name.startswith("MOHSW"):
        location = request.location
        base_facilities = base_facilities.filter(supplied_by__location=location)
    else:
        location = Location.objects.get(name="MOHSW")
    return base_facilities, location

def _districts():
    return Location.objects.filter(supplypoint__type__code="district")

@place_in_request()
def dashboard(request):
    translation.activate("en")
    mp = MonthPager(request)
    base_facilities, location = _get_facilities_and_location(request)

    dg = DeliveryGroups(mp.month, facs=base_facilities)
    sub_data = SupplyPointStatusBreakdown(base_facilities, month=mp.month, year=mp.year)
    return render_to_response("tanzania/dashboard.html",
                              {
                               "sub_data": sub_data,
                               "graph_width": 300,
                               "graph_height": 300,
                               "dg": dg,
                               "month_pager": mp,
                               "facs": list(base_facilities), # Not named 'facilities' so it won't trigger the selector
                               "districts": _districts(),
                               "location": location},
                               
                              context_instance=RequestContext(request))
PRODUCTS_PER_TABLE = 6

#@login_required
@place_in_request()
def facilities_detail(request, view_type="inventory"):
    facs, location = _get_facilities_and_location(request)
    mp = MonthPager(reqyest)
    products = Product.objects.all().order_by('name')
    products = chunks(products, PRODUCTS_PER_TABLE)
    return render_to_response("tanzania/facilities_list.html",
                              {'facs': facs,
                               'product_sets': products,
                               'month_pager': mp,
                               'districts': _districts(),
                               'location': location}, context_instance=RequestContext(request))

def datespan_to_month(datespan):
    return datespan.startdate.month

#@login_required
@place_in_request()
def facilities_index(request, view_type="inventory"):
    # TODO Needs ability to view stock as of a given month.
    facs, location = _get_facilities_and_location(request)
    mp = MonthPager(request)
    products = Product.objects.all().order_by('name')
    products = chunks(products, PRODUCTS_PER_TABLE)
    return render_to_response("tanzania/facilities_list.html",
                              {'facs': facs,
                               'product_set': products,
                               'location': location,
                               'month_pager': mp,
                               'districts': _districts(),
                               }, context_instance=RequestContext(request))
@place_in_request()
def facilities_ordering(request):
    facs, location = _get_facilities_and_location(request)
    mp = MonthPager(request)
    return render_to_response(
        "tanzania/facilities_ordering.html",
        {
            "month_pager": mp,
            "districts": _districts(),
            "location": location,
            "table": OrderingStatusTable(object_list=facs, request=request, month=mp.month, year=mp.year)
        },
        context_instance=RequestContext(request))

