#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import threading
import logging
import serial

ENCODER_PULSES_THRESHOLD = 15

logger = logging.getLogger(__name__)

class SerialMonoboxController(threading.Thread):
    def __init__(self, frontend, serial_port):
        super(SerialMonoboxController, self).__init__()
        self.s = serial.Serial(serial_port, 115200, timeout=0.5)
        self.frontend = frontend
        self.encoder_abspos = 0
        self.setDaemon(True)
        self.start()

    def process(self, typ, value):
        if typ == 'P':
            self.frontend.set_power(value)
        elif typ == 'E':
            self.encoder_abspos += value

            if self.encoder_abspos >= ENCODER_PULSES_THRESHOLD:
                self.frontend.play_next()
                self.encoder_abspos = 0
            elif self.encoder_abspos <= -ENCODER_PULSES_THRESHOLD:
                self.frontend.play_previous()
                self.encoder_abspos = 0

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
