from logistics import settings
from rapidsms.tests.scripted import TestScript
from logistics.apps.malawi import loader
from rapidsms.contrib.messagelog.models import Message
import csv
import os

class OutputtingTestScript(TestScript):
    """
    Test class that saves all the test messages to a csv file 
    for documentation/auditing purposes
    """
    
    # this can be overridden in the subclass if desired
    output_directory = os.path.join(os.path.dirname(__file__), "testscripts")
    
    @property
    def output_filename(self):
        return os.path.join(self.output_directory, 
                            "%s_%s.csv" % (self.__class__.__name__, self._testMethodName)) 
    
    def tearDown(self):
        if not os.path.exists(self.output_directory):
            os.mkdir(self.output_directory)
        
        with open(self.output_filename, "wb") as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(["Phone Number", "Direction", "Message"])
            def csv_line(writer, msg):
                def direction(msg):
                    return ">>" if  msg.direction == "I" else "<<"
                return writer.writerow([msg.connection.identity, direction(msg), msg.text])
            for message in Message.objects.order_by("date"):
                csv_line(writer, message)
        super(OutputtingTestScript, self).tearDown()

    
class MalawiTestBase(OutputtingTestScript):
    """
    Base test class that prepopulates tests with malawi's static data
    """
    
    def setUp(self):
        super(MalawiTestBase, self).setUp()
        loader.init_static_data()
        settings.LOGISTICS_APPROVAL_REQUIRED = False
    