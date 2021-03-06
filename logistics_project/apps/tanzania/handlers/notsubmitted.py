from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.contrib.handlers.handlers.tagging import TaggingHandler
from django.utils.translation import ugettext_noop as _
from logistics.util import config
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues
from logistics.decorators import logistics_contact_required

class NotSubmitted(KeywordHandler,TaggingHandler):
    
    keyword = "sijatuma"

    def help(self):
        self.handle(text="")
        
    @logistics_contact_required()
    def handle(self, text):
        SupplyPointStatus.objects.create(status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                         status_value=SupplyPointStatusValues.NOT_SUBMITTED,
                                         supply_point=self.msg.logistics_contact.supply_point,
                                         status_date=self.msg.timestamp)
        self.respond(_(config.Messages.NOT_SUBMITTED_CONFIRM))
