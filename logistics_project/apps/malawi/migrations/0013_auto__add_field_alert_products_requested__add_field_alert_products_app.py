# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Alert.products_requested'
        db.add_column('malawi_alert', 'products_requested',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Alert.products_approved'
        db.add_column('malawi_alert', 'products_approved',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

    def backwards(self, orm):
        # Deleting field 'Alert.products_requested'
        db.delete_column('malawi_alert', 'products_requested')

        # Deleting field 'Alert.products_approved'
        db.delete_column('malawi_alert', 'products_approved')

    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'locations.location': {
            'Meta': {'ordering': "['name']", 'object_name': 'Location'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locations'", 'null': 'True', 'to': "orm['locations.LocationType']"})
        },
        'locations.locationtype': {
            'Meta': {'object_name': 'LocationType'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'primary_key': 'True'})
        },
        'locations.point': {
            'Meta': {'object_name': 'Point'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'})
        },
        'logistics.contactrole': {
            'Meta': {'object_name': 'ContactRole'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'responsibilities': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['logistics.Responsibility']", 'null': 'True', 'blank': 'True'})
        },
        'logistics.defaultmonthlyconsumption': {
            'Meta': {'unique_together': "(('supply_point_type', 'product'),)", 'object_name': 'DefaultMonthlyConsumption'},
            'default_monthly_consumption': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'supply_point_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPointType']"})
        },
        'logistics.product': {
            'Meta': {'ordering': "['name']", 'object_name': 'Product'},
            'average_monthly_consumption': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'emergency_order_level': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'equivalents': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'equivalents_rel_+'", 'null': 'True', 'to': "orm['logistics.Product']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'product_code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sms_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10', 'db_index': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.ProductType']"}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'logistics.producttype': {
            'Meta': {'object_name': 'ProductType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'logistics.responsibility': {
            'Meta': {'object_name': 'Responsibility'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'logistics.supplypoint': {
            'Meta': {'ordering': "['name']", 'object_name': 'SupplyPoint'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['logistics.SupplyPointGroup']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_reported': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'supplied_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPointType']"})
        },
        'logistics.supplypointgroup': {
            'Meta': {'object_name': 'SupplyPointGroup'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'logistics.supplypointtype': {
            'Meta': {'object_name': 'SupplyPointType'},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'primary_key': 'True'}),
            'default_monthly_consumptions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['logistics.Product']", 'null': 'True', 'through': "orm['logistics.DefaultMonthlyConsumption']", 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'malawi.alert': {
            'Meta': {'object_name': 'Alert'},
            'eo_total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'eo_with_resupply': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'eo_without_resupply': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'have_stockouts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_hsas': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'order_readys': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'products_approved': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'products_requested': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'reporting_receipts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total_requests': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'without_products_managed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'malawi.calculatedconsumption': {
            'Meta': {'object_name': 'CalculatedConsumption'},
            'calculated_consumption': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'time_needing_data': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'time_stocked_out': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'time_with_data': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.currentconsumption': {
            'Meta': {'object_name': 'CurrentConsumption'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'current_daily_consumption': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'stock_on_hand': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.historicalstock': {
            'Meta': {'object_name': 'HistoricalStock'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'stock': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.orderfulfillment': {
            'Meta': {'object_name': 'OrderFulfillment'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'quantity_received': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'quantity_requested': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.orderrequest': {
            'Meta': {'object_name': 'OrderRequest'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'emergency': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.organization': {
            'Meta': {'object_name': 'Organization'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'managed_supply_points': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['logistics.SupplyPoint']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'malawi.productavailabilitydata': {
            'Meta': {'object_name': 'ProductAvailabilityData'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'emergency_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'good_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'managed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_emergency_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_good_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_over_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_under_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_with_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_without_data': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_without_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'over_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'under_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {}),
            'with_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'without_data': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'without_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'malawi.productavailabilitydatasummary': {
            'Meta': {'object_name': 'ProductAvailabilityDataSummary'},
            'any_emergency_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_good_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_managed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_over_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_under_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_with_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_without_data': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_without_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.reportingrate': {
            'Meta': {'object_name': 'ReportingRate'},
            'complete': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'on_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'reported': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.timetracker': {
            'Meta': {'object_name': 'TimeTracker'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'time_in_seconds': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.userprofiledata': {
            'Meta': {'object_name': 'UserProfileData'},
            'contact_info': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'contacts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'facility_children': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'hsa_children': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'hsa_supervisors': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_charge': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'last_message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['messagelog.Message']", 'null': 'True'}),
            'products_managed': ('django.db.models.fields.TextField', [], {}),
            'supervisor_contacts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"})
        },
        'messagelog.message': {
            'Meta': {'object_name': 'Message'},
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']", 'null': 'True'}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'direction': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'rapidsms.backend': {
            'Meta': {'object_name': 'Backend'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'rapidsms.connection': {
            'Meta': {'unique_together': "(('backend', 'identity'),)", 'object_name': 'Connection'},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Backend']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'commodities': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'reported_by'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['logistics.Product']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'needs_reminders': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['malawi.Organization']", 'null': 'True', 'blank': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.ContactRole']", 'null': 'True', 'blank': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']", 'null': 'True', 'blank': 'True'})
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_items'", 'to': "orm['taggit.Tag']"})
        }
    }

    complete_apps = ['malawi']