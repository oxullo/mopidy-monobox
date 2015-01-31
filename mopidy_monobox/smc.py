#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import threading
import re
import logging
import serial
import pykka

from mopidy import exceptions
from mopidy.utils import encoding

logger = logging.getLogger(__name__)


class SerialMonoboxController(pykka.ThreadingActor):
    def __init__(self, frontend, serial_port, serial_bps):
        super(SerialMonoboxController, self).__init__()
        try:
            self.s = serial.Serial(serial_port, serial_bps, timeout=0.5)
        except Exception as error:
            raise exceptions.FrontendError('SMC serial connection failed: %s' %
                    encoding.locale_decode(error))

        self.frontend = frontend
        self.buffer = ''

    def on_start(self):
        self.s.flushInput()
        thread = threading.Thread(target=self.thread_run)
        thread.start()

    def on_stop(self):
        self.running = False

    def thread_run(self):
        self.running = True
        while self.running:
            ch = self.s.read()
            if ch != '\r':
                self.buffer += ch

            # logger.debug('SMC buf: %s' % str([c for c in self.buffer]))

            while '\n' in self.buffer:
                self.process_line(self.buffer[0:self.buffer.find('\n')])
                self.buffer = self.buffer[self.buffer.find('\n') + 1:]

    def process_parsed(self, typ, value):
        if typ == 'P':
            self.frontend.set_power_control(value)
        elif typ == 'V':
            self.frontend.set_volume(value)
        elif typ == 'B' and value == 1:
            self.frontend.next_button_pressed()

    def process_line(self, line):
        logger.debug('SMC process line: %s' % line)
        res = re.search(r'^([BPV]):(\-?\d+)$', line)
        if res:
            typ, value = res.groups()
            try:
                value = int(value)
            except ValueError:
                logger.warning('Cannot decode value %s (line=%s)' % (value, line))
            else:
                self.process_parsed(typ, value)
