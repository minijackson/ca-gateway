#!/usr/bin/env python
import os
import unittest
import epics
import SIOCControl
import GatewayControl
import gwtests
import time

class DBEAlarmTest(unittest.TestCase):
    '''Test alarm updates (client using DBE_ALARM flag) through the Gateway'''

    def setUp(self):
        self.siocControl = SIOCControl.SIOCControl()
        self.gatewayControl = GatewayControl.GatewayControl()
        self.siocControl.startSIOCWithDefaultDB()
        self.gatewayControl.startGateway()
        os.environ["EPICS_CA_AUTO_ADDR_LIST"] = "NO"
        os.environ["EPICS_CA_ADDR_LIST"] = "localhost:{} localhost:{}".format(gwtests.iocPort,gwtests.gwPort)
        epics.ca.initialize_libca()
        self.eventsReceived = 0
        self.severityUnchanged = 0
        self.lastSeverity = 4

    def tearDown(self):
        epics.ca.finalize_libca()
        self.siocControl.stop()
        self.gatewayControl.stop()
        
    def onChange(self, pvname=None, **kws):
        self.eventsReceived += 1
        if gwtests.verbose:
            print pvname, " changed to ", kws['value'], kws['severity']
        if self.lastSeverity == kws['severity']:
            self.severityUnchanged += 1
        self.lastSeverity = kws['severity']
        
    def testAlarmLevel(self):
        '''DBE_ALARM monitor on an ai with two alarm levels - crossing the level generates updates'''
        # gateway:passiveALRM has HIGH=5 (MINOR) and HIHI=10 (MAJOR)
        pv = epics.PV("gateway:passiveALRM", auto_monitor=epics.dbr.DBE_ALARM)
        pv.add_callback(self.onChange)
        for val in [0,1,2,3,4,5,6,7,8,9,10,9,8,7,6,5,4,3,2,1,0]:
            pv.put(val)
            time.sleep(.001)
        time.sleep(.05)
        # We get 6 events: at connection (INVALID), at first write (NO_ALARM),
        # and at the level crossings MINOR-MAJOR-MINOR-NO_ALARM.
        self.assertTrue(self.eventsReceived == 6, 'events expected: 6; events received: ' + str(self.eventsReceived))
        # Any updates with unchanged severity are an error
        self.assertTrue(self.severityUnchanged == 0, str(self.severityUnchanged) + ' events with no severity changes received')
