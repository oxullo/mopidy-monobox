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
        self.playlists_ready = False
        self.pending_power = False

        self.smc = SerialMonoboxController(self, config['monobox']['serial_port'])

    def playlists_loaded(self):
        self.playlists_ready = True
        if self.pending_power:
            self.power_on()
            self.pending_power = None

    def set_power_control(self, wanted_state):
        logger.info('set_power_control wanted_state=%d' % wanted_state)
        if wanted_state == 1:
            if self.playlists_ready:
                self.power_on()
            else:
                logger.debug('Delaying power on')
                self.pending_power = True
        else:
            self.standby()

    def power_on(self):
        self.core.tracklist.clear()
        playlists = self.core.playlists.playlists.get()
        for playlist in playlists:
            self.core.tracklist.add(uri=playlist.uri)
        self.core.playback.play()

    def standby(self):
        if self.core.playback.state.get() == core.PlaybackState.PLAYING:
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
