'''
New views for the upgraded reports of the system.
'''
import json
from random import random
from datetime import datetime, timedelta
from collections import defaultdict

from django.conf import settings
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect
from django.utils.datastructures import SortedDict

from dimagi.utils.decorators.datespan import datespan_in_request
from dimagi.utils.dates import months_between

from rapidsms.contrib.locations.models import Location

from logistics.models import Product, SupplyPoint
from logistics.decorators import place_in_request

from logistics_project.apps.malawi.util import get_facilities, get_districts,\
    get_country_sp
from logistics.util import config
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData,\
    ProductAvailabilityDataSummary, ReportingRate, OrderRequest


REPORT_LIST = SortedDict([
    ("Dashboard", "dashboard"),
    ("Reporting Rate", "reporting-rate"),
    ("Stock Status", "stock-status"),
    ("Consumption Profiles", "consumption-profiles"),
    ("Alert Summary", "alert-summary"),
    ("Re-supply Qts Required", "re-supply-qts-required"),
    ("Lead Times", "lead-times"),
    ("Order Fill Rate", "order-fill-rate"),
    ("Emergency Orders", "emergency-orders"),
])

to_stub = lambda x: {"name": x, "slug": REPORT_LIST[x]}

stub_reports = [to_stub(r) for r in REPORT_LIST.keys()]

def home(request):
    return redirect("/malawi/r/dashboard/")
    
@place_in_request()
@datespan_in_request(format_string='%B %Y')
def get_report(request, slug=''):
    context = shared_context(request)
    context.update({"report_list": stub_reports,
                    "slug": slug})
    
    context.update(get_more_context(request, slug))
    return render_to_response("malawi/new/%s.html" % slug, 
                              context,
                              context_instance=RequestContext(request))


def get_more_context(request, slug=None):
    func_map = {
        'dashboard': dashboard_context,
        'emergency-orders': eo_context,
        'order-fill-rate': ofr_context,
        're-supply-qts-required': rsqr_context,
        'alert-summary': as_context,
        'consumption-profiles': cp_context,
        'stock-status': ss_context,
        'lead-times': lt_context,
        'reporting-rate': rr_context,
    }
    if slug in func_map:
        return func_map[slug](request)
    else:
        return {}

    context = func_map[slug](request) if slug in func_map else {}
    context["slug"] = slug
    return context 

def shared_context(request):
    products = Product.objects.all().order_by('sms_code')
    country = get_country_sp()
    window_date = _get_window_date(request)
    
    # national stockout percentages by product
    stockout_pcts = SortedDict()
    for p in products:
        availability = ProductAvailabilityData.objects.get(supply_point=country,
                                                           date=window_date,
                                                           product=p)
        stockout_pcts[p] = _pct(availability.managed_and_without_stock,
                                availability.managed)
    
    return { "settings": settings,
             "report_list": stub_reports,
             "location": request.location or get_country_sp(),
             "districts": get_districts(),
             "facilities": get_facilities(),
             "hsas": 643,
             "reporting_rate": "93.3",
             "products": products,
             "product_stockout_pcts": stockout_pcts,
    }

def timechart(labels):
    summary = {
        "xlabels": [],
        "legenddiv": "legend-div",
        "div": "chart-div",
        "max_value": 3,
        # "width": "730px",
        "width": "100%",
        "height": "200px",
        "data": [],
        "xaxistitle": "month",
        "yaxistitle": "rate"
    }
    count = 0
    summary['xlabels'] = _month_labels(datetime.now() - timedelta(days=61), datetime.now())
    summary['data'] = barseries(labels, len(summary['xlabels']))
    return summary


def barseries(labels, num_points):
    return [{"label": l, "data": bardata(num_points)} for l in labels]
    
def bardata(num_points):
    return [[i + 1, random()] for i in range(num_points)]

def _month_labels(start_date, end_date):
    return [[i + 1, '<span>%s</span>' % datetime(year, month, 1).strftime("%b")] \
            for i, (year, month) in enumerate(months_between(start_date, end_date))]
    
def lt_context(request):
    month_table = {
        "title": "",
        "header": ['Month', 'Ord-Ord Ready (days)', 'Ord-Ord Received(days)', 'Total Lead Time (days)'],
        "data": [['Jan', 3, 14, 7], ['Feb', 12, 7, 4], ['Mar', 14, 6, 4]],
    }

    lt_table = {
        "title": "Average Lead Times by Facility",
        "header": ['Facility', 'Period (# Months)', 'Ord-Ord Ready (days)', 'Ord-Ord Received(days)', 'Total Lead Time (days)'],
        "data": [['BULA', 6, 31, 42, 37], ['Chesamu', 6, 212, 27, 14], ['Chikwina', 6, 143, 61, 14]],
    }    
    return {"summary": timechart(['Ord-Ord Ready', 'Ord-Ord Received']),
            "month_table": month_table,
            "lt_table": lt_table}

def dashboard_context(request):
    window_date = _get_window_date(request)

    # reporting rates + stockout summary
    districts = get_districts().order_by('name')
    summary_data = SortedDict()
    for d in districts:
        avail_sum = ProductAvailabilityDataSummary.objects.get(supply_point=d, date=window_date)
        stockout_pct = _pct(avail_sum.with_any_stockout,
                             avail_sum.manages_anything) 
        rr = ReportingRate.objects.get(supply_point=d, date=window_date)
        reporting_rate = _pct(rr.reported, rr.total)
        summary_data[d] = {"stockout_pct": stockout_pct,
                           "reporting_rate": reporting_rate}
    
    # report chart
    start_date = request.datespan.startdate
    report_chart = {
        "legenddiv": "summary-legend-div",
        "div": "summary-chart-div",
        "max_value": 100,
        "width": "100%",
        "height": "200px",
        "xaxistitle": "month",
    }
    data = defaultdict(lambda: defaultdict(lambda: 0)) # turtles!
    dates = []
    country = get_country_sp()
    for year, month in months_between(start_date, window_date):
        dt = datetime(year, month, 1)
        dates.append(dt)
        rr = ReportingRate.objects.get(supply_point=country, date=dt)
        data["on time"][dt] = _pct(rr.on_time, rr.total)
        data["late"][dt] = _pct(rr.reported - rr.on_time, rr.total)
        data["missing"][dt] = _pct(rr.total - rr.reported, rr.total)
        data["complete"][dt] = _pct(rr.complete, rr.total)
    
    ret_data = [{'data': [[i + 1, data[k][dt]] for i, dt in enumerate(dates)],
                 'label': k, 'lines': {"show": False}, "bars": {"show": True},
                 'stack': 0} \
                 for k in ["on time", "late", "missing"]]
    
    ret_data.append({'data': [[i + 1, data["complete"][dt]] for i, dt in enumerate(dates)],
                     'label': 'complete', 'lines': {"show": True}, "bars": {"show": False},
                     'yaxis': 2})
    
    report_chart['xlabels'] = [[i + 1, '%s' % dt.strftime("%b")] for i, dt in enumerate(dates)]
    report_chart['data'] = json.dumps(ret_data)
    return {"summary_data": summary_data,
            "graphdata": report_chart,
            "pa_width": 530 if settings.STYLE=='both' else 730 }

def eo_context(request):
    sp_code = request.GET.get('place') or get_country_sp().code
    window_range = _get_window_range(request)

    oreqs = OrderRequest.objects.filter(supply_point__code=sp_code, date__range=window_range)
    eo_map = {}
    eos = 0
    total = 0
    for oreq in oreqs:
        eo_map[oreq.product] = (eos + oreq.emergency , total + oreq.total)

    ret_obj = {}
    summary = {
        "product_codes": [],
        "xlabels": [],
        "legenddiv": "legend-div",
        "div": "chart-div",
        "max_value": 3,
        "width": "100%",
        "height": "200px",
        "data": [],
        "xaxistitle": "products",
        "yaxistitle": "amount"
    }
    
    count = 0
    for eo in eo_map.keys():
        count += 1
        summary['product_codes'].append([count, '<span>%s</span>' % (str(eo.code.lower()))])

    summary['xlabels'] = summary['product_codes']
    summary['data'] = barseries(['emergency','total','c'], 10)

    table = {
        "title": "%HSA with Emergency Order by Product",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 35, 41, 53, 34], ['dt', 26, 26, 44, 21], ['sr', 84, 24, 54, 36]],
        "cell_width": "135px",
    }

    line_chart = {
        "height": "350px",
        "width": "100%", # "300px",
        "series": [],
    }
    for j in ['LA 1x6', 'LA 2x6']:
        temp = []
        for i in range(0,5):
            temp.append([random(),random()])
        line_chart["series"].append({"title": j, "data": sorted(temp)})

    ret_obj['summary'] = summary
    ret_obj['table'] = table
    ret_obj['line'] = line_chart
    return ret_obj


def ofr_context(request):
    ret_obj = {}

    table1 = {
        "title": "Monthly Average OFR by Product (%)",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 32, 41, 54, 35], ['dt', 23, 22, 41, 16], ['sr', 45, 44, 74, 26]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "OFR for Selected Time Period by Facility and Product (%)",
        "header": ["Facility", "bi", "cl", "cf", "cm"],
        "data": [[3, 3, 4, 5, 3], [2, 2, 2, 4, 1], [4, 4, 4, 4, 6]],
        "cell_width": "135px",
    }

    line_chart = {
        "height": "350px",
        "width": "100%", # "300px",
        "series": [],
    }
    for j in ['LA 1x6', 'LA 2x6']:
        temp = []
        for i in range(0,5):
            temp.append([random(),random()])
        line_chart["series"].append({"title": j, "data": sorted(temp)})

    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
    ret_obj['line'] = line_chart
    return ret_obj

def rsqr_context(request):
    ret_obj = {}

    table = {
        "title": "All Products (Aggregated Quantity required to ensure that HC can resupply",
        "header": ["Facility Name", "%HSA with Stockout", "LA 1x6", "LA 2x6", "Zinc"],
        "data": [['BULA', 32, 4123, 512, 3123], ['Chesamu', 22, 2123, 423, 123], ['Chikwina', 45, 4123, 423, 612]],
        "cell_width": "135px",
    }

    ret_obj['table'] = table
    return ret_obj

def as_context(request):
    ret_obj = {}

    table = {
        "title": "Current Alert Summary",
        "header": ["Facility", "# HSA", "%HSA stocked out", "%HSA with EO", "%HSA with no Products"],
        "data": [['BULA', 332, 42, 53, 35], ['Chesamu', 232, 25, 41, 11], ['Chikwina', 443, 41, 41, 46]],
        "cell_width": "135px",
    }
    
    ret_obj['table'] = table
    return ret_obj

def cp_context(request):
    ret_obj = {}

    table1 = {
        "title": "District Consumption Profiles",
        "header": ["Product", "Total Calc Cons", "Av Rep Rate", "AMC", "Total SOH"],
        "data": [['cc', 312, "47%", 5, 354], ['dt', 1322, "21%", 4, 121], ['sr', 4123, "14%", 4, 634]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "Facility Consumption Profiles",
        "header": ["Product", "Total Calc Cons", "Av Rep Rate", "AMC", "Total SOH"],
        "data": [['cc', 3234, "40%", 5, 345], ['dt', 2123, "52%", 4, 111], ['sr', 4132, "43%", 4, 634]],
        "cell_width": "135px",
    }

    line_chart = {
        "height": "350px",
        "width": "100%", # "300px",
        "series": [],
    }
    for j in ['Av Monthly Cons', 'Av Months of Stock']:
        temp = []
        for i in range(0,5):
            temp.append([random(),random()])
        line_chart["series"].append({"title": j, "data": sorted(temp)})

    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
    ret_obj['line'] = line_chart
    return ret_obj

def ss_context(request):
    ret_obj = {}
    summary = {
        "product_codes": [],
        "xlabels": [],
        "legenddiv": "legend-div",
        "div": "chart-div",
        "max_value": 3,
        "width": "100%",
        "height": "200px",
        "data": [],
        "xaxistitle": "products",
        "yaxistitle": "amount"
    }
    
    count = 0
    for product in Product.objects.all().order_by('sms_code')[0:10]:
        count += 1
        summary['product_codes'].append([count, '<span>%s</span>' % (str(product.code.lower()))])
        summary['xlabels'] = summary['product_codes']
    
    summary['data'] = barseries(['Stocked Out','Under Stock','Adequate'], 10)

    table1 = {
        "title": "",
        "header": ["Product", "HSA Stocked Out", "HSA Under", "HSA Adequate", "Overstock"],
        "data": [['cc', 34, 45, 52, 31], ['dt', 21, 25, 44, 17], ['sr', 43, 44, 41, 67]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "HSA Current Stock Status by District",
        "header": ["District", "HSA Stocked Out", "HSA Under", "HSA Adequate", "Overstock"],
        "data": [['cc', 33, 45, 52, 31], ['dt', 21, 29, 45, 13], ['sr', 43, 42, 42, 61]],
        "cell_width": "135px",
    }

    line_chart = {
        "height": "350px",
        "width": "100%", # "300px",
        "series": [],
    }
    for j in ['LA 1x6', 'LA 2x6']:
        temp = []
        for i in range(0,5):
            temp.append([random(),random()])
        line_chart["series"].append({"title": j, "data": sorted(temp)})

    ret_obj['summary'] = summary
    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
    ret_obj['line'] = line_chart
    return ret_obj

def rr_context(request):
    ret_obj = {}
    summary = {
        "product_codes": [],
        "xlabels": [],
        "legenddiv": "legend-div",
        "div": "chart-div",
        "max_value": 3,
        "width": "100%",
        "height": "200px",
        "data": [],
        "xaxistitle": "products",
        "yaxistitle": "amount"
    }
    
    count = 0
    xlabels = ['Jun', 'July', 'Aug']
    for xlabel in xlabels:
        count += 1
        summary['xlabels'].append([count, '<span>%s</span>' % str(xlabel)])
    
    summary['data'] = barseries(['on_time','late','not_reported'], len(xlabels))

    table1 = {
        "title": "",
        "header": ["Months", "%Reporting", "%Ontime", "%Late", "%None"],
        "data": [['June', 10, 47, 55, 31], ['July', 50, 24, 43, 15], ['Aug', 40, 47, 45, 61]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "Average Reporting Rate (Districts)",
        "header": ["Districts", "%Reporting", "%Ontime", "%Late", "%None"],
        "data": [['All', 32, 41, 54, 36], ['Nkatabay', 27, 27, 44, 11], ['Kasungu', 45, 44, 44, 67]],
        "cell_width": "135px",
    }

    table3 = {
        "title": "Average Reporting Rate (Facilities)",
        "header": ["Facilities", "%Reporting", "%Ontime", "%Late", "%None"],
        "data": [['All', 34, 45, 56, 38], ['Chesamu', 24, 22, 47, 18], ['Chikwina', 44, 44, 42, 65]],
        "cell_width": "135px",
    }

    ret_obj['summary'] = summary
    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
    ret_obj['table3'] = table3
    return ret_obj

def hsas(request):
    context = {}
    return render_to_response('malawi/new/hsas.html', context, context_instance=RequestContext(request))

def user_profiles(request):
    context = {}
    return render_to_response('malawi/new/user-profiles.html', context, context_instance=RequestContext(request))

def _get_window_date(request):
    # the window date is assumed to be the end date
    date = request.datespan.enddate
    assert date.day == 1
    return date

def _get_window_range(request):
    # the window date is assumed to be the end date
    date1 = request.datespan.startdate
    date1 = datetime(date1.year, (date1.month%12 - 2)%12 , 1)
    date2 = request.datespan.enddate
    assert date1.day == 1
    assert date2.day == 1
    return (date1, date2)

def _pct(num, denom):
    return float(num) / (float(denom) or 1) * 100

