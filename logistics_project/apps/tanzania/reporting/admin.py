#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from logistics_project.apps.tanzania.reporting.models import *

class OrganizationSummaryAdmin(admin.ModelAdmin):
    model = OrganizationSummary
    list_display = ('supply_point', 'date', 'total_orgs', 'average_lead_time_in_days')
    list_filter = ('supply_point', 'date')

class GroupSummaryAdmin(admin.ModelAdmin):
    model = GroupSummary
    list_display = ('org_summary', 'title', 'total', 'responded', 'on_time', 'complete')
    list_filter = ('org_summary', 'title')
    
    
class ProductAvailabilityDataAdmin(admin.ModelAdmin):
    model = ProductAvailabilityData
    list_display = ('supply_point', 'date', 'product', 'total', 'with_stock', 
                    'without_stock', 'without_data')
    list_filter = ('supply_point', 'date', 'product')

class AlertAdmin(admin.ModelAdmin):
    model = Alert
    list_display = ('supply_point', 'date', 'type', 'expires', 'number', 'text')
    list_filter = ('supply_point', 'date', 'type', 'expires')

admin.site.register(OrganizationSummary, OrganizationSummaryAdmin)
admin.site.register(GroupSummary, GroupSummaryAdmin)
admin.site.register(ProductAvailabilityData, ProductAvailabilityDataAdmin)
admin.site.register(Alert, AlertAdmin)