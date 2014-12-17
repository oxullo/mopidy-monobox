#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import serial
import pykka

from mopidy import core
from smc import SerialMonoboxController

STATE_POWER_STANDBY = 'STATE_POWER_STANDBY'
STATE_POWER_ON = 'STATE_POWER_ON'
STATE_POWER_PENDING_ON = 'STATE_POWER_PENDING_ON'

STATE_TRACK_PLAYBACK_IDLE = 'STATE_TRACK_PLAYBACK_IDLE'
STATE_TRACK_PLAYBACK_PENDING = 'STATE_TRACK_PLAYBACK_PENDING'
STATE_TRACK_PLAYBACK_PLAYING = 'STATE_TRACK_PLAYBACK_PLAYING'

logger = logging.getLogger(__name__)

class MonoboxFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(MonoboxFrontend, self).__init__()
        self.core = core
        self.config = config
        self.encoder_abspos = 0
        self.playlists_ready = False
        self.power_state = STATE_POWER_STANDBY
        self.track_state = STATE_TRACK_PLAYBACK_IDLE

        self.smc = SerialMonoboxController.start(self, config['monobox']['serial_port'])

    def on_stop(self):
        self.smc.stop()

    def playlists_loaded(self):
        self.playlists_ready = True
        if self.power_state == STATE_POWER_PENDING_ON:
            self.power_on()

    def track_playback_started(self, tl_track):
        logger.info('track_playback_started: %s' % tl_track)
        self.encoder_abspos = 0
        self.track_state = STATE_TRACK_PLAYBACK_PLAYING

    def set_power_control(self, wanted_state):
        logger.info('set_power_control wanted_state=%d' % wanted_state)
        if wanted_state == 1:
            if self.playlists_ready:
                self.power_on()
            else:
                logger.debug('Delaying power on')
                self.power_state = STATE_POWER_PENDING_ON
        else:
            self.standby()

    def power_on(self):
        self.core.tracklist.clear()
        playlists = self.core.playlists.playlists.get()

        wanted_playlists = self.config['monobox']['only_playlists']
        for playlist in playlists:
            if ((wanted_playlists and playlist.name in wanted_playlists) or
                    not wanted_playlists):
                logger.info('Adding playlist %s' % playlist.name)
                self.core.tracklist.add(uri=playlist.uri)
            else:
                logger.info('Skipping playlist %s' % playlist.name)

        logger.info('Loaded %d tracks' % self.core.tracklist.length.get())
        if self.config['monobox']['shuffle']:
            logger.info('Shuffling')
            self.core.tracklist.shuffle()

        self.core.playback.play()
        self.power_state = STATE_POWER_ON

    def standby(self):
        if self.core.playback.state.get() == core.PlaybackState.PLAYING:
            self.track_state = STATE_TRACK_PLAYBACK_IDLE
            self.core.playback.pause()

    def update_encoder(self, delta):
        if (self.track_state == STATE_TRACK_PLAYBACK_PENDING or
                self.core.playback.state.get() != core.PlaybackState.PLAYING):
            return

        if self.config['monobox']['cue_feature']:
            self.cue(delta)
        else:
            self.encoder_abspos += delta
            if self.encoder_abspos > self.config['monobox']['pulses_trigger']:
                self.encoder_abspos = 0
                self.play_next()
            elif self.encoder_abspos < -self.config['monobox']['pulses_trigger']:
                self.encoder_abspos = 0
                self.play_previous()

    def recalculate_encoder_position(self):
        current_track = self.core.playback.current_track.get()
        norm_pos = float(self.core.playback.time_position.get()) / current_track.length
        new_encoder_pos = int(self.config['monobox']['pulses_trigger'] * norm_pos)
        self.encoder_abspos = new_encoder_pos

    def cue(self, delta):
        self.recalculate_encoder_position()

        self.encoder_abspos += delta

        if self.encoder_abspos >= self.config['monobox']['pulses_trigger']:
            self.play_next()
            self.encoder_abspos = 0
        elif self.encoder_abspos <= -self.config['monobox']['pulses_trigger']:
            self.play_previous()
            self.encoder_abspos = 0
        elif (self.encoder_abspos >= 0 and
                self.core.playback.state.get() == core.PlaybackState.PLAYING):
            norm_pos = float(self.encoder_abspos) / self.config['monobox']['pulses_trigger']
            current_track = self.core.playback.current_track.get()
            seek_ms = int(current_track.length * norm_pos)
            self.core.playback.seek(seek_ms)

    def play_next(self):
        logger.debug('play_next')
        self.track_state = STATE_TRACK_PLAYBACK_PENDING
        self.core.playback.next()

    def play_previous(self):
        logger.debug('play_previous')
        self.track_state = STATE_TRACK_PLAYBACK_PENDING
        self.core.playback.previous()
