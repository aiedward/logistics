from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics.models import SupplyPoint
from logistics_project.apps.malawi.util import get_default_supply_point,\
    hsas_below, hsa_supply_points_below, fmt_pct, group_for_location
from static.malawi import config
from logistics_project.apps.malawi.warehouse.report_utils import previous_report_period,\
    get_lead_time_table_data, get_stock_status_table_data,\
    WarehouseProductAvailabilitySummary
from collections import defaultdict
from logistics_project.apps.malawi.warehouse.models import ReportingRate,\
    TIME_TRACKER_TYPES, TimeTracker
from datetime import datetime
from dimagi.utils.dates import months_between

class View(warehouse_view.DistrictOnlyView):

    show_report_nav = False
    
    def custom_context(self, request):
        sp = SupplyPoint.objects.get(location=request.location)\
            if request.location else get_default_supply_point(request.user)

        report_date = request.datespan.enddate
        current_date = previous_report_period()
        facility = None
        template = "malawi/new/printable_base.html" if "print" in request.GET else "malawi/new/base.html"
            
        if sp.type.code == config.SupplyPointCodes.FACILITY:
            facility = sp
            hsas = hsa_supply_points_below(sp.location).order_by("name")
            
            # stock status chart
            pas = WarehouseProductAvailabilitySummary(facility, current_date)
            pa_table = {
                "id": "pa-table",
                "is_datatable": False,
                "is_downloadable": False,
                "header": ["Product", "% HSA stocked out", "% HSA under", 
                           "% HSA adequate", "% HSA overstocked", 
                           "% HSA not reported"],
                "data": pas.table_data,
            }
            
            
            # reporting rates chart - put everyone into buckets
            data = defaultdict(lambda: [])
            attrs = {"on_time": "Reporting on time", 
                     "late": "Late reporting",
                     "missing": "Non reporting", 
                     "complete": "Complete reporting", 
                     "incomplete": "Incomplete reporting"}
                     
            count = hsas.count()
            reported = 0
            for hsa in hsas:
                rr = ReportingRate.objects.get(supply_point=hsa, 
                                               date=report_date)
                counted = 0
                if rr.reported: 
                    reported += 1
                for attr in attrs:
                    if getattr(rr, attr):
                        data[attr].append(hsa)
                        counted += 1
                
            rr_data = [[attrs[a], fmt_pct(len(data[a]), 
                                          count if a not in ['complete', 'incomplete'] else reported), 
                        ", ".join([hsa.name for hsa in data[a]])] \
                        for a in ["on_time", "late", "missing", 
                                  "complete", "incomplete"]]
            rr_table = {
                "id": "rr-table",
                "is_datatable": False,
                "is_downloadable": False,
                "header": ["", "%", "Names of HSAs"],
                "data": rr_data,
            }
            
            # lead times table
            lt_table = {
                "id": "average-lead-times-hsa",
                "is_datatable": False,
                "is_downloadable": False,
                "header": ['Facility', "Order to order ready (days)",
                           "Order ready to order received (days)", "Total lead time (days)"],
                "data": get_lead_time_table_data([sp],
                                                 request.datespan.startdate, 
                                                 request.datespan.enddate),
            }   
            
            # stock status table
            headings = ["Product", "Average monthly consumption (last 60 days)",
                            "TOTAL SOH (day of report)", "MOS (current period)",
                            "Stock status"]
            ss_data = get_stock_status_table_data(sp)
            ss_table = {
                "id": "ss-table",
                "is_datatable": False,
                "is_downloadable": False,
                "header": headings,
                "data": ss_data,
            }
            
            return {
                "em": group_for_location(facility.location) == config.Groups.EM,
                "facility": facility,
                "pa_table": pa_table,
                "rr_table": rr_table,
                "lt_table": lt_table,
                "ss_table": ss_table,
                "current_date": current_date,
                "warehouse_base_template": template,
                "show_single_date": True
            }
                        
        return {
            "facility": facility,
            "current_date": current_date,
            "warehouse_base_template": template,
            "show_single_date": True
        }