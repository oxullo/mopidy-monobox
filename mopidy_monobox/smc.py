#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
import logging
import serial
import gobject
import pykka

from mopidy import exceptions
from mopidy.utils import encoding

logger = logging.getLogger(__name__)


class SerialMonoboxController(pykka.ThreadingActor):
    def __init__(self, frontend, serial_port, serial_bps):
        super(SerialMonoboxController, self).__init__()
        try:
            self.s = serial.Serial(serial_port, serial_bps)
        except Exception as error:
            raise exceptions.FrontendError('SMC serial connection failed: %s' %
                    encoding.locale_decode(error))

        self.s.nonblocking()
        self.frontend_proxy = frontend.actor_ref.proxy()
        self.buffer = ''

    def on_start(self):
        self.s.flushInput()
        gobject.io_add_watch(self.s.fileno(),
                gobject.IO_IN | gobject.IO_ERR | gobject.IO_HUP,
                self.read_chunk)

    def process_parsed(self, typ, value):
        if typ == 'P':
            self.frontend_proxy.set_power_control(value)
        elif typ == 'E':
            self.frontend_proxy.update_encoder(value)
        elif typ == 'V':
            self.frontend_proxy.set_volume(value)

    def process_line(self, line):
        logger.debug('SMC process line: %s' % line)
        res = re.search(r'^([EBPV]):(\-?\d+)$', line)
        if res:
            typ, value = res.groups()
            try:
                value = int(value)
            except ValueError:
                logger.warning('Cannot decode value %s (line=%s)' % (value, line))
            else:
                self.process_parsed(typ, value)

    def read_chunk(self, fd, flags):
        logger.debug('SCM read_chunk fd=%d flags=%d' % (fd, flags))

        if flags & (gobject.IO_ERR | gobject.IO_HUP):
            self.stop('Bad client flags: %s' % flags)
            return True

        while self.s.inWaiting():
            ch = self.s.read()
            if ch != '\r':
                self.buffer += ch

        logger.debug('SMC buf: %s' % str([c for c in self.buffer]))

        while '\n' in self.buffer:
            self.process_line(self.buffer[0:self.buffer.find('\n')])
            self.buffer = self.buffer[self.buffer.find('\n') + 1:]

        return True
