from datetime import datetime
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.models import ProductReportsHelper , StockTransfer
from logistics.const import Reports
from logistics.decorators import logistics_contact_and_permission_required
from logistics.util import config

class TransferConfirmHandler(KeywordHandler):
    """
    HSA --> HSA transfer confirmation
    """

    keyword = "confirm"

    def help(self):
        self.handle("")

    @logistics_contact_and_permission_required(config.Operations.CONFIRM_TRANSFER)
    def handle(self, text):
        pending = StockTransfer.pending_transfers().filter\
            (receiver=self.msg.logistics_contact.supply_point).all()
        if len(pending) == 0:
            self.respond(config.Messages.NO_PENDING_TRANSFERS)
        else:
            # the easiest way to mark these in the database, 
            # is to make a fake stock report
            # of the pending transfers, considering them as receipts
            stock_report = ProductReportsHelper(self.msg.logistics_contact.supply_point, 
                                                Reports.REC)
            stock_report.parse(" ".join([p.sms_format() for p in pending]))
            stock_report.save()
            
            # close the pending transfers
            now = datetime.utcnow()
            for p in pending:
                p.confirm(now)
            self.respond(config.Messages.CONFIRM_RESPONSE, 
                         receiver=self.msg.logistics_contact.name,
                         products=", ".join([p.sms_format() for p in pending]))
