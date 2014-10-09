from django.conf import settings
from django.utils.datastructures import SortedDict

from logistics.models import Product, SupplyPoint
from logistics.reports import ReportView
from logistics.util import config

from logistics_project.apps.malawi.util import get_facilities, get_districts,\
    get_country_sp, pct, get_default_supply_point, get_visible_districts,\
    get_visible_facilities, get_all_visible_locations, get_view_level, get_visible_hsas
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData, ReportingRate
from logistics_project.apps.malawi.warehouse.report_utils import current_report_period


class MalawiWarehouseView(ReportView):
    
    show_report_nav = True # override to hide
    
    @property
    def template_name(self):
        return "%s/%s.html" % (settings.REPORT_FOLDER, self.slug)
        
    def shared_context(self, request):
        base_context = super(MalawiWarehouseView, self).shared_context(request)

        country = get_country_sp()
        products = Product.objects.filter(is_active=True).order_by('sms_code')
        date = current_report_period()
        
        # national stockout percentages by product
        stockout_pcts = SortedDict()
        for p in products:
            try:
                availability = ProductAvailabilityData.objects.get(
                    supply_point=country,
                    date=date,
                    product=p
                )
                stockout_pcts[p] = (pct(availability.managed_and_without_stock,
                                        availability.managed),
                                    availability.managed)
            except ProductAvailabilityData.DoesNotExist:
                stockout_pcts[p] = ('?', '?')

        pct_reported = '?'
        try:
            current_rr = ReportingRate.objects.get(date=date, supply_point=country)
            pct_reported = current_rr.pct_reported
        except ReportingRate.DoesNotExist:
            pass

        default_sp = get_default_supply_point(request.user)
        visible_facilities = get_visible_facilities(request.user).order_by('parent_id')
        visible_hsas = get_visible_hsas(request.user)

        querystring = '?'
        for key in request.GET.keys():
            querystring += '%s=%s&' % (key, request.GET[key])

        districts = get_districts(request.user.is_superuser)
        base_context.update({
            "default_chart_width": 530 if settings.STYLE=='both' else 730,
            "country": country,
            "districts": districts,
            "district_count": districts.count(),
            "facilities": visible_facilities,
            "facility_count": SupplyPoint.objects.filter(active=True, 
                                                         type__code=config.SupplyPointCodes.FACILITY).count(),
            "visible_hsas": visible_hsas,
            "hsas": SupplyPoint.objects.filter(active=True, type__code="hsa").count(),
            "reporting_rate": pct_reported,
            "products": products,
            "product_stockout_pcts": stockout_pcts,
            "location": request.location or default_sp.location,
            "querystring": querystring,
            "show_report_nav": self.show_report_nav,
            "window_date": current_report_period(),
        })
        return base_context

class DashboardView(MalawiWarehouseView):
    """
    Reports that are only available to people whose location is set to 
    a district (or higher). The use case is: I should be able to see this
    report for my district, facilities in my district, or nationally, but 
    not for any other district.
    """
    def can_view(self, request):
        if request.user.is_superuser: return True
        else:
            return request.location in get_all_visible_locations(request.user)\
                if request.location else True

    def shared_context(self, request):
        base_context = super(DashboardView, self).shared_context(request)
        view_level = get_view_level(request.user)
        base_context["national_view_level"] = view_level
        return base_context

class DistrictOnlyView(MalawiWarehouseView):
    """
    Reports that are only available to people whose location is set to 
    a district (or higher). The use case is: I should be able to see this
    report for my district, facilities in my district, or nationally, but 
    not for any other district.
    """
    def can_view(self, request):
        if request.user.is_superuser: return True
        else:
            return request.location in get_all_visible_locations(request.user)\
                if request.location else True

    def shared_context(self, request):
        base_context = super(DistrictOnlyView, self).shared_context(request)
        visible_districts = get_visible_districts(request.user)
        view_level = get_view_level(request.user)
        base_context["districts"] = visible_districts
        base_context["national_view_level"] = view_level == 'national'
        return base_context