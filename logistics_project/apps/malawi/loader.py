import os
import re
from django.db import transaction
from django.conf import settings
from rapidsms.contrib.locations.models import LocationType, Location
from logistics.models import SupplyPoint, SupplyPointType,\
    ProductReportType, ContactRole, Product, ProductType
from logistics.util import config
from logistics.shortcuts import supply_point_from_location
from logistics_project.loader.base import load_report_types, load_roles
import csv
from pytz import timezone
from datetime import datetime
import pytz
from scheduler.models import EventSchedule
from django.core.exceptions import ObjectDoesNotExist

class LoaderException(Exception):
    pass

def init_static_data(log_to_console=False, do_locations=False, do_products=True):
    """
    Initialize any data that should be static here
    """
    # These are annoyingly necessary to live in the DB, currently. 
    # Really this should be app logic, I think.
    load_report_types()
    load_roles()
    load_schedules()
    loc_file = getattr(settings, "STATIC_LOCATIONS")
    if do_locations and loc_file:
        load_locations_from_path(loc_file, log_to_console=log_to_console)
    product_file = getattr(settings, "STATIC_PRODUCTS")
    if do_products and product_file:
        load_products(product_file, log_to_console=log_to_console)
    
    
def clear_locations():
    Location.objects.all().delete()
    LocationType.objects.all().delete()
    
def clear_products():
    Product.objects.all().delete()
    ProductType.objects.all().delete()


def load_schedules():
    malawi_tz = timezone("Africa/Blantyre") 
    def _malawi_to_utc(hours):
        localized = malawi_tz.normalize(malawi_tz.localize(datetime(2011, 1, 1, hours, 0)))
        utced = localized.astimezone(pytz.utc)
        return (utced.hour)
    
    def _get_schedule(func):
        try:
            schedule = EventSchedule.objects.get(callback=func)
        except ObjectDoesNotExist:
            schedule = EventSchedule(callback=func)
        schedule.minutes = [0]
        return schedule
    
    warehouse = _get_schedule("warehouse.runner.update_warehouse")
    warehouse.hours = [0, 12]
    warehouse.save()
    
    eo = _get_schedule("logistics_project.apps.malawi.nag.send_district_eo_reminders")
    eo.hours = [_malawi_to_utc(9)]
    eo.days_of_week = [1] # tuesday
    eo.save()
    
    so = _get_schedule("logistics_project.apps.malawi.nag.send_district_so_reminders")
    so.hours = [_malawi_to_utc(9)]
    so.days_of_week = [3] # thursday
    so.save()
    
def load_products(file_path, log_to_console=True):
    if log_to_console: print "loading static products from %s" % file_path
    # give django some time to bootstrap itself
    if not os.path.exists(file_path):
        raise LoaderException("Invalid file path: %s." % file_path)
    
    def _int_or_nothing(val):
        try:
            return int(val)
        except ValueError:
            return None
        
    csv_file = open(file_path, 'r')
    try:
        count = 0
        for line in csv_file:
            # leave out first line
            if "product name" in line.lower():
                continue
            #Product Name,Code,Dose,AMC,Family,Formulation,EOP Quantity,# of patients a month,
            name, code, dose, monthly_consumption, typename, form, eop_quant, num_pats, min_pack_size = line.strip().split(",")
            #create/load type
            type = ProductType.objects.get_or_create(name=typename, code=typename.lower())[0]
            
            try:
                product = Product.objects.get(sms_code=code.lower())
            except Product.DoesNotExist:
                product = Product(sms_code=code.lower())
            product.name = name
            product.description = name # todo
            product.type = type
            product.average_monthly_consumption = _int_or_nothing(monthly_consumption)
            product.emergency_order_level = _int_or_nothing(eop_quant)
            product.save()
            
            count += 1
    
        if log_to_console: print "Successfully processed %s products." % count
    
    finally:
        csv_file.close()

def load_locations_from_path(path, log_to_console=True):
    if log_to_console: print("Loading locations %s"  % (path))
    if not os.path.exists(path):
        raise LoaderException("Invalid file path: %s." % path)

    with open(path, 'r') as f:
        msgs = load_locations(f)
        if log_to_console and msgs:
            for msg in msgs:
                print msg


def get_facility_export(file_handle):
    """
    Gets an export of all the facilities in the system as a csv.
    """
    writer = csv.writer(file_handle)
    writer.writerow([
        'Zone Code',
        'Zone Name',
        'District Code',
        'District Name',
        'Facility Code',
        'Facility Name',
    ])

    facilities = SupplyPoint.objects.filter(
        active=True,
        type__code=config.SupplyPointCodes.FACILITY
    ).select_related(
        'supplied_by',
        'supplied_by__supplied_by'
    ).order_by("code")

    for facility in facilities:
        district = facility.supplied_by
        zone = district.supplied_by
        writer.writerow([
            zone.code,
            zone.name,
            district.code,
            district.name,
            facility.code,
            facility.name
        ])


class FacilityLoaderValidationError(Exception):
    validation_msg = None

    def __init__(self, validation_msg):
        super(FacilityLoaderValidationError, self).__init__(validation_msg)
        self.validation_msg = validation_msg


class FacilityLoader(object):
    """
    This utility allows you to create/edit districts and facilities in bulk.
    To use it, pass in a file object and run it. Example:

        with open('filename.csv', 'r') as f:
            FacilityLoader(f).run()

    ** Expected Format **
    The file should be a csv file with 6 columns, in the order below:
        zone code
        zone name
        district code
        district name
        facility code
        facility name

    Using a header is optional, but if a header is used, the columns should have
    the names above.

    ** Facility Usage **
    Facilities are looked up by code. If the facility does not exist, it is
    created. If the facility exists, all of its information is updated.

    ** District Usage **
    Districts are lookuped by code. If the district does not exist, it is
    created. If the district exists, only its zone is updated.

    ** Zone / HSA Usage **
    Zones and HSAs cannot be created or updated with this utility.

    ** Errors **
    If an error occurs, a FacilityLoaderValidationError is raised describing the
    error and the row that had the error. If any exception is raised, no changes
    are applied to the database.
    """

    file_obj = None
    data = None
    valid_zone_codes = None
    district_zone_map = None

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.data = []
        self.valid_zone_codes = list(
            SupplyPoint.objects.filter(type__code=config.SupplyPointCodes.ZONE).values_list('code', flat=True)
        )
        self.district_zone_map = {}

    def validate_column_data(self, line_num, value):
        data = [column.strip() for column in value.split(",")]
        if len(data) != 6:
            raise FacilityLoaderValidationError("Error with row %s. Expected 6 columns of data." % line_num)

        if any([not column for column in data]):
            raise FacilityLoaderValidationError("Error with row %s. Expected a value for every column." % line_num)

        return data

    def validate_zone_code(self, line_num, value):
        if value not in self.valid_zone_codes:
            raise FacilityLoaderValidationError("Error with row %s. Expected zone code to be one of: %s"
                % (line_num, ', '.join(self.valid_zone_codes)))

        return value

    def validate_district_code(self, line_num, value):
        value = value.zfill(2)
        if not re.match("^\d\d$", value):
            raise FacilityLoaderValidationError("Error with row %s. Expected district code to consist of "
                "at most 2 digits." % line_num)

        return value

    def validate_facility_code(self, line_num, value):
        value = value.zfill(4)
        if not re.match("^\d\d\d\d$", value):
            raise FacilityLoaderValidationError("Error with row %s. Expected facility code to consist of "
                "at most 4 digits." % line_num)

        return value

    def validate_district_zone_mapping(self, zone_code, district_code):
        if district_code not in self.district_zone_map:
            self.district_zone_map[district_code] = zone_code
        else:
            if self.district_zone_map[district_code] != zone_code:
                raise FacilityLoaderValidationError("Error with row %s. The zone assigned to district %s "
                    "differs across multiple rows. Please check zone for all rows with district %s."
                    % (line_num, district_code, district_code))

    def parse_data(self):
        line_num = 1
        for line in self.file_obj:
            # Ignore headers
            if line_num == 1 and "district code" in line.lower():
                continue

            column_data = self.validate_column_data(line_num, line)
            zone_code, zone_name, district_code, district_name, facility_code, facility_name = column_data

            zone_code = self.validate_zone_code(line_num, zone_code)
            district_code = self.validate_district_code(line_num, district_code)
            facility_code = self.validate_facility_code(line_num, facility_code)

            self.validate_district_zone_mapping(zone_code, district_code)
            self.data.append({
                'line_num': line_num,
                'zone_code': zone_code,
                'zone_name': column_data[1],
                'district_code': district_code,
                'district_name': column_data[3],
                'facility_code': facility_code,
                'facility_name': column_data[5],
            })

            line_num += 1

    def get_or_create_district_location(self, row, zone_location):
        try:
            district_location = Location.objects.get(code=row['district_code'])
            if district_location.type_id != config.LocationCodes.DISTRICT:
                raise FacilityLoaderValidationError("Error with row %s. District code %s does not reference "
                    "a district." % (row['line_num'], row['district_code']))

            if district_location.parent_id != zone_location.pk:
                district_location.parent = zone_location
                district_location.save()
        except Location.DoesNotExist:
            district_location = Location.objects.create(
                code=row['district_code'],
                name=row['district_name'],
                type_id=config.LocationCodes.DISTRICT,
                parent=zone_location
            )

        return district_location

    def get_or_create_facility_location(self, row, district_location):
        try:
            facility_location = Location.objects.get(code=row['facility_code'])
            if facility_location.type_id != config.LocationCodes.FACILITY:
                raise FacilityLoaderValidationError("Error with row %s. Facility code %s does not reference "
                    "a facility." % (row['line_num'], row['facility_code']))
        except Location.DoesNotExist:
            facility_location = Location(code=row['facility_code'])

        facility_location.name = row['facility_name']
        facility_location.type_id = config.LocationCodes.FACILITY
        facility_location.parent = district_location
        facility_location.save()
        return facility_location

    def get_or_create_district_supply_point(self, row, district_location, zone_supply_point):
        try:
            supply_point = SupplyPoint.objects.get(code=district_location.code)
            if supply_point.type_id != config.SupplyPointCodes.DISTRICT:
                raise FacilityLoaderValidationError("Error with row %s. District code %s does not reference "
                    "a district." % (row['line_num'], district_location.code))

            supply_point.name = district_location.name
            supply_point.location = district_location
            supply_point.supplied_by = zone_supply_point
            supply_point.save()
        except SupplyPoint.DoesNotExist:
            supply_point = SupplyPoint.objects.create(
                code=district_location.code,
                type_id=config.SupplyPointCodes.DISTRICT,
                name=district_location.name,
                location=district_location,
                supplied_by=zone_supply_point
            )

        return supply_point

    def get_or_create_facility_supply_point(self, row, facility_location, district_supply_point):
        try:
            supply_point = SupplyPoint.objects.get(code=facility_location.code)
            if supply_point.type_id != config.SupplyPointCodes.FACILITY:
                raise FacilityLoaderValidationError("Error with row %s. Facility code %s does not reference "
                    "a facility." % (row['line_num'], facility_location.code))

            supply_point.name = facility_location.name
            supply_point.location = facility_location
            supply_point.supplied_by = district_supply_point
            supply_point.save()
        except SupplyPoint.DoesNotExist:
            supply_point = SupplyPoint.objects.create(
                code=facility_location.code,
                type_id=config.SupplyPointCodes.FACILITY,
                name=facility_location.name,
                location=facility_location,
                supplied_by=district_supply_point
            )

        return supply_point

    def load_data(self):
        for row in self.data:
            zone_location = Location.objects.get(code=row['zone_code'])
            zone_supply_point = SupplyPoint.objects.get(code=row['zone_code'])
            district_location = self.get_or_create_district_location(row, zone_location)
            facility_location = self.get_or_create_facility_location(row, district_location)
            district_supply_point = self.get_or_create_district_supply_point(row, district_location, zone_supply_point)
            self.get_or_create_facility_supply_point(row, facility_location, district_supply_point)

    def run(self):
        """
        Returns the number of records processed on success, otherwise raises
        a FacilityLoaderValidationError.
        """
        self.parse_data()
        with transaction.commit_on_success():
            self.load_data()

        return len(self.data)


def load_locations(file):
    # create/load static types    
    country_type = LocationType.objects.get_or_create(slug=config.LocationCodes.COUNTRY, name=config.LocationCodes.COUNTRY)[0]
    district_type = LocationType.objects.get_or_create(slug=config.LocationCodes.DISTRICT, name=config.LocationCodes.DISTRICT)[0]
    facility_type = LocationType.objects.get_or_create(slug=config.LocationCodes.FACILITY, name=config.LocationCodes.FACILITY)[0]
    hsa_type = LocationType.objects.get_or_create(slug=config.LocationCodes.HSA, name=config.LocationCodes.HSA)[0]
    country = Location.objects.get_or_create(name=settings.COUNTRY[0].upper()+settings.COUNTRY[1:], type=country_type, code=settings.COUNTRY)[0]
    
    country_sp_type = SupplyPointType.objects.get_or_create(name="country", code=config.SupplyPointCodes.COUNTRY)[0]
    country_sp = supply_point_from_location(country, type=country_sp_type)
    district_sp_type = SupplyPointType.objects.get_or_create(name="district", code=config.SupplyPointCodes.DISTRICT)[0]
    fac_sp_type = SupplyPointType.objects.get_or_create(name="health facility", code=config.SupplyPointCodes.FACILITY)[0]
    # we don't use this anywhere in the loader, but make sure to create it
    hsa_sp_type = SupplyPointType.objects.get_or_create(name="health surveillance assistant", code=config.SupplyPointCodes.HSA)[0]
    
    count = 0
    for line in file:
        #leave out first line
        if "district code" in line.lower():
            continue
        district_code, district_name, facility_code, facility_name = \
            [token.strip() for token in line.split(",")]
        
        #create/load district
        def _pad_to(val, target_len):
            if len(val) < target_len:
                val = "%s%s" % ("0" * (target_len - len(val)), val)
            assert len(val) == target_len
            return val 
        
        district_code = _pad_to(district_code, 2)
        facility_code = _pad_to(facility_code, 4)
        
        try:
            district = Location.objects.get(code__iexact=district_code)
        except Location.DoesNotExist:
            district = Location.objects.create(name=district_name.strip(), type=district_type, 
                                               code=district_code, parent=country)
        # create/load district supply point info
        dist_sp = supply_point_from_location(district, type=district_sp_type, parent=country_sp)
        
        #create/load location info
        if not facility_code:
            facility_code = "temp%s" % count
        try:
            fac_loc = Location.objects.get(code=facility_code)
        except Location.DoesNotExist:
            fac_loc = Location(code=facility_code)
        fac_loc.name = facility_name.strip()
        fac_loc.parent = district
        fac_loc.type = facility_type
        fac_loc.save()
        
        # create/load supply point info
        fac_sp = supply_point_from_location(fac_loc, type=fac_sp_type, parent=dist_sp)
        
        count += 1

    return ["Successfully processed %s locations." % count]

def _clean(location_name):
    return location_name.lower().strip().replace(" ", "_")[:30]
