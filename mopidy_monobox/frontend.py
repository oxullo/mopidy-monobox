#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import serial
import pykka

from mopidy import core
from smc import SerialMonoboxController

ENCODER_PULSES_THRESHOLD = 15

logger = logging.getLogger(__name__)

class MonoboxFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(MonoboxFrontend, self).__init__()
        self.core = core
        self.encoder_abspos = 0

        self.smc = SerialMonoboxController(self, config['monobox']['serial_port'])

    def set_power(self, state):
        logger.debug('set_power state=%d' % state)
        if state == 1:
            self.core.tracklist.clear()
            playlists = self.core.playlists.playlists.get()
            for playlist in playlists:
                self.core.tracklist.add(uri=playlist.uri)
            self.core.playback.play()
        else:
            self.core.playback.pause()

    def update_encoder(self, delta):
        self.encoder_abspos += delta

        if self.encoder_abspos >= ENCODER_PULSES_THRESHOLD:
            self.play_next()
            self.encoder_abspos = 0
        elif self.encoder_abspos <= -ENCODER_PULSES_THRESHOLD:
            self.play_previous()
            self.encoder_abspos = 0
        
    def play_next(self):
        logger.debug('play_next')
        self.core.playback.next()

    def play_previous(self):
        logger.debug('play_previous')
        self.core.playback.previous()
