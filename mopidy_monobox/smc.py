#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import threading
import logging
import serial

logger = logging.getLogger(__name__)

class SerialMonoboxController(threading.Thread):
    def __init__(self, frontend, serial_port):
        super(SerialMonoboxController, self).__init__()
        self.s = serial.Serial(serial_port, 115200, timeout=0.5)
        self.frontend = frontend
        self.setDaemon(True)
        self.start()

    def process(self, typ, value):
        if typ == 'P':
            self.frontend.set_power_control(value)
        elif typ == 'E':
            self.frontend.update_encoder(value)

    def run(self):
        while True:
            line = self.s.readline().strip()

            if line:
                res = re.search(r'^([EBP]):(\-?\d+)$', line)
                if res:
                    typ, value = res.groups()
                    try:
                        value = int(value)
                    except ValueError:
                        logger.warning('Cannot decode value %s (line=%s)' % (value, line))
                    else:
                        self.process(typ, value)
