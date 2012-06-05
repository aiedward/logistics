import json
from datetime import datetime
from logistics.decorators import place_in_request
from logistics.models import SupplyPoint, Product
from django.db.models.query_utils import Q
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown
from logistics_project.apps.tanzania.tables import SupervisionTable, RandRReportingHistoryTable, NotesTable, StockOnHandTable, ProductStockColumn, ProductMonthsOfStockColumn, RandRStatusTable, DeliveryStatusTable
from logistics_project.apps.tanzania.utils import chunks, get_user_location, soh_on_time_reporting, latest_status, randr_on_time_reporting, submitted_to_msd
from rapidsms.contrib.locations.models import Location
from logistics.tables import FullMessageTable
from models import DeliveryGroups
from logistics.views import MonthPager
from django.core.urlresolvers import reverse
from django.conf import settings
from logistics_project.apps.tanzania.decorators import gdata_required
import gdata.docs.client
import gdata.gauth
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from dimagi.utils.parsing import string_to_datetime
from django.views.decorators.http import require_POST
from django.views import i18n as i18n_views
from django.utils.translation import ugettext as _
from logistics_project.decorators import magic_token_required
from logistics_project.apps.tanzania.forms import AdHocReportForm
from logistics_project.apps.tanzania.models import AdHocReport, SupplyPointNote, SupplyPointStatusTypes
from rapidsms.contrib.messagelog.models import Message
from dimagi.utils.decorators.profile import profile

from logistics_project.apps.tanzania.reporting.models import *


PRODUCTS_PER_TABLE = 100 #7

def tz_location_url(location):
    try:
        sp = SupplyPoint.objects.get(location=location)
        if sp.type.code == "facility":
            return reverse("tz_facility_details", args=(sp.pk,))
    except SupplyPoint.DoesNotExist:
        pass
    return ""

def _is_district(location):
    return location and location.type.name == "DISTRICT"

def _is_region(location):
    return location and location.type.name == "REGION"

def _is_national(location):
    return location and location.type.name == "REGION"

def _are_not_related(location, user_loc):
    # if no user location is specified, then they're "related"
    if not user_loc:  return False
        
    # make sure the user_loc is a parent of the other, or vice versa
    def is_eventual_parent(loc, parent_candiate):
        while loc.parent is not None:
            if parent_candiate == loc.parent: return True
            loc = loc.parent
    
    return location != user_loc \
           and not is_eventual_parent(location, user_loc) \
           and not is_eventual_parent(user_loc, location)

def get_facilities_and_location(request):
    
    def _filter_facilities_by_location(facilities, location):
        if _is_region(location):
            return facilities.filter(Q(supplied_by__location__parent_id=location.id) | Q(supplied_by__location=location))
        elif _is_district(location):
            return facilities.filter(supplied_by__location=location)
        return facilities
    
    base_facilities = SupplyPoint.objects.filter(active=True, type__code="facility")
    
    user_loc = get_user_location(request.user)
    
    # filter initial list by location
    filtered_facilities = _filter_facilities_by_location(base_facilities, 
                                                         user_loc)
    
    if request.location:
        if _are_not_related(request.location, user_loc):
            messages.error(request, "You don't have permission to view that. Location reset.")
            location = user_loc
        else:    
            location = request.location
            filtered_facilities = _filter_facilities_by_location(filtered_facilities, request.location)
        
    elif user_loc:
        location = user_loc
    else:
        location = Location.objects.get(name="MOHSW")
    request.location = location
    return (filtered_facilities, location)

def _districts():
    return Location.objects.filter(type__name="DISTRICT")

def _regions():
    return Location.objects.filter(type__name="REGION")

def _user_districts(user):
    districts = _districts()
    location = get_user_location(user)
    if _is_district(location):
        return districts.filter(pk=location.pk)
    elif _is_region(location):
        return districts.filter(parent_id=location.pk)
    return districts

def _user_regions(user):
    regions = _regions()
    location = get_user_location(user)
    if _is_district(location):
        return regions.filter(pk=location.parent.pk)
    elif _is_region(location):
        return regions.filter(pk=location.pk)
    return regions

def district_supply_points_below(location, sps):
    if _is_district(location):
        return [SupplyPoint.objects.get(location=location)]
    elif _is_region(location):
        return sps.filter(location__parent_id=location.id, location__type__name="DISTRICT")
    else:
        return sps.filter(location__type__name="DISTRICT")
    
# @profile("/Users/jpwagner/Desktop/")
@place_in_request()
def dashboard(request):

    mp = MonthPager(request)

    base_facilities, location = get_facilities_and_location(request)

    dg = DeliveryGroups(mp.month, facs=base_facilities)
    sub_data = SupplyPointStatusBreakdown(base_facilities, month=mp.month, year=mp.year)
    msd_sub_count = submitted_to_msd(district_supply_points_below(location, dg.processing()), mp.month, mp.year)
    return render_to_response("tanzania/dashboard.html",
                              {"sub_data": sub_data,
                               "graph_width": 300,
                               "graph_height": 300,
                               "dg": dg,
                               "month_pager": mp,
                               "msd_sub_count": msd_sub_count,
                               "facs": list(base_facilities), # Not named 'facilities' so it won't trigger the selector
                               "districts": _user_districts(request.user),
                               "regions": _user_regions(request.user),
                               "location": location,
                               "destination_url": "tz_dashboard"
                               },
                               
                              context_instance=RequestContext(request))

# @profile("/Users/jpwagner/Desktop/")
@place_in_request()
def dashboard2(request):
    mp = MonthPager(request)
    last_month = datetime(datetime.fromordinal(mp.begin_date.toordinal()-1).year, datetime.fromordinal(mp.begin_date.toordinal()-1).month,1)

    org = request.GET.get('place')
    if not org:
        # TODO: Get this from config
        org = 'MOHSW-MOHSW'

    org_summary = OrganizationSummary.objects.get(date__range=(mp.begin_date,mp.end_date),organization__code=org)

    soh_data = GroupData.objects.filter(group_summary__title='soh_submit',group_summary__org_summary__date__range=(mp.begin_date,mp.end_date),group_summary__org_summary__organization__code=org)
    rr_data = GroupData.objects.filter(group_summary__title='rr_submit',group_summary__org_summary__date__range=(mp.begin_date,mp.end_date),group_summary__org_summary__organization__code=org)
    delivery_data = GroupData.objects.filter(group_summary__title='deliver',group_summary__org_summary__date__range=(mp.begin_date,mp.end_date),group_summary__org_summary__organization__code=org)
    process_data = GroupData.objects.filter(group_summary__title='process',group_summary__org_summary__date__range=(mp.begin_date,mp.end_date),group_summary__org_summary__organization__code=request.location.code)

    soh_json, soh_total, soh_complete = convert_soh_data_to_pie_chart(soh_data, mp.begin_date)
    rr_json, submit_total, submit_complete, submitting_group = convert_rr_data_to_pie_chart(rr_data, mp.begin_date)
    delivery_json, delivery_total, delivery_complete, delivery_group = convert_delivery_data_to_pie_chart(delivery_data, mp.begin_date)
    processing_total, processing_complete, processing_group = prepare_processing_info(process_data)

    total = org_summary.total_orgs
    avg_lead_time = org_summary.average_lead_time_in_days

    # product_availability = ProductAvailabilityData.objects.filter(date__range=(mp.begin_date,mp.end_date), organization__code=request.location.code)
    # product_dashboard = ProductAvailabilityDashboardChart.objects.filter(date__range=(mp.begin_date,mp.end_date), organization__code=request.location.code)

    # product_json = convert_product_data_to_dashboard(product_availability, product_dashboard)

    location = Location.objects.get(code=org)
    #######

    # breakthis

    return render_to_response("tanzania/dashboard2.html",
                              {"month_pager": mp,
                               "last_month": last_month,
                               "soh_json": soh_json,
                               "rr_json": rr_json,
                               "delivery_json": delivery_json,
                               "processing_total": soh_total,
                               "processing_complete": soh_complete,
                               "submitting_total": submit_total,
                               "submitting_complete": submit_complete,
                               "delivery_total": delivery_total,
                               "delivery_complete": delivery_complete,
                               "delivery_group": delivery_group,
                               "submitting_group": submitting_group,
                               "processing_group": processing_group,
                               "total": total,
                               "avg_lead_time": avg_lead_time,

                               "graph_width": 300,
                               "graph_height": 300,
                               "location": location,
                               "destination_url": "tz_dashboard2"
                               },
                               
                              context_instance=RequestContext(request))

def prepare_processing_info(data):
    total = 0
    complete = 0
    for result in data:
        entry = {}
        number = int(result.number)
        total += number
        entry['value'] = number
        if result.complete:
            complete += number
    return total, complete, data[0].group_code

def convert_soh_data_to_pie_chart(data, date):
    ret_json = []
    total = 0
    complete = 0
    for result in data:
        entry = {}
        number = int(result.number)
        total += number
        entry['value'] = number
        if result.complete:
            complete += number
        if result.label=='not_responding':
            entry['color'] = '#8b198b'
            entry['description'] = "(%s) Didn't Respond (%s)" % (number, date.strftime("%b %Y"))
            entry['display'] = u'SOH Not Responding'
            ret_json.append(entry)
        elif result.label=='on_time':
            entry['color'] = 'green'
            entry['description'] = "(%s) SOH On Time (%s)" % (number, date.strftime("%b %Y"))
            entry['display'] = u'Stock Report On Time'
            ret_json.append(entry)
        elif result.label=='late':
            entry['color'] = 'orange'
            entry['description'] = "(%s) Submitted Late (%s)" % (number, date.strftime("%b %Y"))
            entry['display'] = u'Stock Report Late'
            ret_json.append(entry)
    return ret_json, total, complete

def convert_rr_data_to_pie_chart(data, date):
    ret_json = []
    total = 0
    complete = 0
    for result in data:
        entry = {}
        number = int(result.number)
        total += number
        entry['value'] = number
        if result.complete:
            complete += number
        if result.label=='not_responding':
            entry['color'] = '#8b198b'
            entry['description'] = "(%s) Didn't Respond (%s)" % (number, date.strftime("%b %Y"))
            entry['display'] = u"Didn't Respond"
            ret_json.append(entry)
        elif result.label=='not_submitted':
            entry['color'] = 'red'
            entry['description'] = "(%s) Haven't Submitted (%s)" % (number, date.strftime("%b %Y"))
            entry['display'] = u"Haven't Submitted"
            ret_json.append(entry)
        elif result.label=='on_time':
            entry['color'] = 'green'
            entry['description'] = "(%s) SOH On Time (%s)" % (number, date.strftime("%b %Y"))
            entry['display'] = u'Submitted On Time'
            ret_json.append(entry)
        elif result.label=='late':
            entry['color'] = 'orange'
            entry['description'] = "(%s) Submitted Late (%s)" % (result.number, date.strftime("%b %Y"))
            entry['display'] = u'Submitted Late'
            ret_json.append(entry)
    return ret_json, total, complete, data[0].group_code

def convert_delivery_data_to_pie_chart(data, date):
    ret_json = []
    total = 0
    complete = 0
    for result in data:
        entry = {}
        number = int(result.number)
        total += number
        entry['value'] = number
        if result.complete:
            complete += number
        if result.label=='not_responding':
            entry['color'] = '#8b198b'
            entry['description'] = "(%s) Didn't Respond (%s)" % (number, date.strftime("%b %Y"))
            entry['display'] = u"Didn't Respond"
            ret_json.append(entry)
        elif result.label=='received':
            entry['color'] = 'green'
            entry['description'] = "(%s) Delivery Received (%s)" % (number, date.strftime("%b %Y"))
            entry['display'] = u'Delivery Received'
            ret_json.append(entry)
        elif result.label=='not_received':
            entry['color'] = 'red'
            entry['description'] = "(%s) Delivery Not Received (%s)" % (number, date.strftime("%b %Y"))
            entry['display'] = u'Delivery Not Received'
            ret_json.append(entry)
    return ret_json, total, complete, data[0].group_code

def convert_product_data_to_dashboard(data, chart_info):
    ret_json = {}
    ret_json['ticks'] = []
    ret_json['data'] = []
    count = 0
    for product in data:
        count += 1
        ret_json['ticks'].append([count, '<span title=%s>%s</span' % (product.product.name, product.product.code)])
        for bar in chart_info:
            ret_json['data'].append({'color':bar.color, 'label':bar.label, 'data': 0}) # need to figure out better structure than one previously used
    return ret_json

def datespan_to_month(datespan):
    return datespan.startdate.month

def _generate_soh_tables(request, facs, mp, products=None):
    show = request.GET.get('show', "")
    if not products: products = Product.objects.all().order_by('sms_code')
    product_set = chunks(products, PRODUCTS_PER_TABLE)
    tables = []
    iter = list(chunks(products, PRODUCTS_PER_TABLE))
    for prods in iter: # need a new generator
        # Need to create all the tables first.
        tables += [StockOnHandTable(object_list=facs.select_related(), request=request, prefix="soh_"+prods[0].sms_code, month=mp.month, year=mp.year, order_by=["D G", "Facility Name"])]

    for count in enumerate(iter):
        t = tables[count[0]]
        for prod in count[1]:
            if show == "months":
                pc = ProductMonthsOfStockColumn(prod, mp.month, mp.year)
            else:
                pc = ProductStockColumn(prod, mp.month, mp.year)
            t.add_column(pc, "pc_"+prod.sms_code)
    return tables, products, product_set, show

#@login_required
@place_in_request()
def facilities_index(request):
    facs, location = get_facilities_and_location(request)
    mp = MonthPager(request)
    
    # hack - don't show nationally scoped data because it's too slow
    if location.code == settings.COUNTRY:
        tables, products, product_set, show = [None, None, None, None]
    else:
        tables, products, product_set, show = _generate_soh_tables(request, facs, mp)

    return render_to_response("tanzania/facilities_list.html",
                              {'facs': facs,
                               'product_set': product_set,
                               'products': products,
                               'tables': tables,
                               'location': location,
                               'month_pager': mp,
                               'show': show,
                               'districts': _user_districts(request.user),
                               "regions": _user_regions(request.user),
                               "destination_url": "facilities_index"
                               }, context_instance=RequestContext(request))
@place_in_request()
def facilities_ordering(request):
    facs, location = get_facilities_and_location(request)
    mp = MonthPager(request)
    return render_to_response(
        "tanzania/facilities_ordering.html",
        {
            "month_pager": mp,
            "districts": _user_districts(request.user),
            "regions": _user_regions(request.user),
            "location": location,
#            "table": OrderingStatusTable(object_list=facs.select_related(), request=request, month=mp.month, year=mp.year),
            "destination_url": "ordering"
        },
        context_instance=RequestContext(request))

def facility_details(request, facility_id):
    facility = get_object_or_404(SupplyPoint, pk=facility_id)

    if request.method == "POST":
        text = request.POST.get('note_text')
        if text:
            note = SupplyPointNote(supply_point=facility,
                                   user=request.user,
                                   text=text)
            note.save()
            messages.success(request, "Note added!")

    return render_to_response(
        "tanzania/facility_details.html",
        {
            "facility": facility,
            "randr_status": latest_status(facility, SupplyPointStatusTypes.R_AND_R_FACILITY),
            "notes_table": NotesTable(object_list=SupplyPointNote.objects.filter(supply_point=facility).order_by("-date").select_related(), request=request),
            "report_types": ['Stock on Hand', 'Months of Stock']
        },
        context_instance=RequestContext(request))

def facility_messages(request, facility_id):
    facility = get_object_or_404(SupplyPoint, pk=facility_id)
    return render_to_response("tanzania/facility_messages.html",
        {
            "facility": facility,
            "table": FullMessageTable(object_list=Message.objects.filter(contact__in=facility.contact_set.all).order_by("-date"), request=request)
        },
                              context_instance=RequestContext(request)
    )

@gdata_required
def docdownload(request, facility_id):
    """
    Download google docs document
    """
    if 'token' in request.session:
        #should be able to make this global
        client = gdata.docs.client.DocsClient()
        client.ssl = True  # Force all API requests through HTTPS
        client.http_client.debug = False  # Set to True for debugging HTTP requests
        client.auth_token = gdata.gauth.AuthSubToken(request.session['token'])
        supply_point = get_object_or_404(SupplyPoint, pk=facility_id)
        query_string = '/feeds/default/private/full?title=%s&title-exact=false&max-results=100' % supply_point.code
        feed = client.GetDocList(uri=query_string)

        most_recent_doc = None

        if not feed.entry:
            messages.error(request, 'Sorry, there is no recent R&R for this facility.')
            return HttpResponseRedirect(reverse("tz_facility_details", args=[supply_point.pk]))
        else:
            for entry in feed.entry:
                if not most_recent_doc:
                    most_recent_doc = entry
                else:
                    new_date = string_to_datetime(entry.updated.text)
                    old_date = string_to_datetime(most_recent_doc.updated.text)
                    if new_date > old_date:
                        most_recent_doc = entry

        exportFormat = '&exportFormat=pdf'
        content = client.GetFileContent(uri=most_recent_doc.content.src + exportFormat)
    
    response = HttpResponse(content)
    response['content-Type'] = 'application/pdf'
    response['Content-Disposition'] = 'inline; filename=%s' % most_recent_doc.title.text
    return response

def change_language(request):
    return render_to_response('tanzania/change_language.html',
                              {'LANGUAGES': settings.LANGUAGES},
                              context_instance=RequestContext(request))

@require_POST
def change_language_real(request):
    messages.success(request, _("Language changed to %(lang)s") % \
                    {"lang": dict(settings.LANGUAGES)[request.POST.get("language")]})
    return i18n_views.set_language(request)

@place_in_request()
def reporting(request):
    facs, location = get_facilities_and_location(request)
    mp = MonthPager(request)
    dg = DeliveryGroups(mp.month, facs=facs)
    bd = SupplyPointStatusBreakdown(facs, mp.year, mp.month)
    ot = randr_on_time_reporting(dg.submitting(), mp.year, mp.month)

    tables, products, product_set, show = _generate_soh_tables(request, facs, mp)

    return render_to_response("tanzania/new-reports.html",
        {
          "location": location,
          "month_pager": mp,
          "districts": _user_districts(request.user),
          "regions": _user_regions(request.user),
          "facs": facs,
          "product_set": product_set,
          "products": products,
          "tables": tables,
          "show": show,
          "dg": dg,
          "bd": bd,
          "on_time": ot,
          "reporting_percentage": (float(len(bd.submitted)) / float(len(dg.submitting())) * 100) if len(dg.submitting()) else 0.0,
          "on_time_percentage": (float(len(ot)) / float(len(bd.submitted)) * 100) if len(bd.submitted) else 0.0,
          "supervision_table": SupervisionTable(object_list=dg.submitting().select_related(), request=request,
                                                month=mp.month, year=mp.year, prefix="supervision"),
          "randr_status_table": RandRStatusTable(object_list=dg.submitting().select_related(), request=request, month=mp.month, year=mp.year),
          "delivery_status_table": DeliveryStatusTable(object_list=dg.delivering().select_related(), request=request, month=mp.month, year=mp.year),
          "randr_history_table": RandRReportingHistoryTable(object_list=dg.submitting().select_related(), request=request,
                                                    month=mp.month, year=mp.year, prefix="randr_history"),
          "destination_url": "reports"
        },
        context_instance=RequestContext(request))

# TODO:
@place_in_request
def reporting2(request):
    facs, location = get_facilities_and_location(request)
    mp = MonthPager(request)
    dg = DeliveryGroups(mp.month, facs=facs)
    bd = SupplyPointStatusBreakdown(facs, mp.year, mp.month)
    ot = randr_on_time_reporting(dg.submitting(), mp.year, mp.month)

    tables, products, product_set, show = _generate_soh_tables(request, facs, mp)



@place_in_request()
@magic_token_required()
def reporting_pdf(request):
    return reporting(request)

@place_in_request()
def ad_hoc_reports(request):
    supply_point = None
    if request.location:
        try:
            supply_point = SupplyPoint.objects.get(location=request.location)
        except SupplyPoint.DoesNotExist:
            pass
    report = None
    if supply_point:
        try:
            report = AdHocReport.objects.get(supply_point=supply_point)
        except (AdHocReport.DoesNotExist, AdHocReport.MultipleObjectsReturned):
            pass
        
    if request.method == "POST":
        form = AdHocReportForm(request.POST)
        if form.is_valid():
            new_report = form.save(commit=False)
            if report is not None:
                assert(report.supply_point == new_report.supply_point)
                report.recipients = new_report.recipients
            else:
                report = new_report
            
            report.save()
            messages.success(request, "changes to ad hoc report saved")
            if request.POST["submit"] == "Send Test Messages":
                report.send()
                messages.success(request, "Test report sent to %s" % ", ".join(report.get_recipients()))
                
            else:
                return HttpResponseRedirect("%s?place=%s" % (reverse("reports"), 
                                                             report.supply_point.code))
    
    else:
        if report:
            form = AdHocReportForm(instance=report)
        elif supply_point:
            form = AdHocReportForm({"supply_point": supply_point.pk, "recipients": "Put email addresses here, separated by commas."})
        else:
            form = AdHocReportForm()
    return render_to_response("tanzania/edit_adhoc_report.html", {
        "form": form,
    }, context_instance=RequestContext(request))
    

