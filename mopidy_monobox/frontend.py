#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import serial
import pykka

from mopidy import core, audio
import smc
import feedbackplayer

STATE_POWER_STANDBY = 'STATE_POWER_STANDBY'
STATE_POWER_ON = 'STATE_POWER_ON'
STATE_POWER_PENDING_ON = 'STATE_POWER_PENDING_ON'

STATE_TRACK_PLAYBACK_IDLE = 'STATE_TRACK_PLAYBACK_IDLE'
STATE_TRACK_PLAYBACK_PENDING = 'STATE_TRACK_PLAYBACK_PENDING'
STATE_TRACK_PLAYBACK_PLAYING = 'STATE_TRACK_PLAYBACK_PLAYING'



logger = logging.getLogger(__name__)

class MonoboxFrontend(pykka.ThreadingActor, core.CoreListener, audio.AudioListener):
    def __init__(self, config, core):
        super(MonoboxFrontend, self).__init__()
        self.core = core
        self.config = config
        self.radios_ready = False
        self.power_state = STATE_POWER_STANDBY
        self.track_state = STATE_TRACK_PLAYBACK_IDLE

        self.smc = smc.SerialMonoboxController.start(self,
                config['monobox']['serial_port'],
                config['monobox']['serial_bps'])
    
        self.feedbacks = {
                'poweron': feedbackplayer.FeedbackPlayer('fav_set.wav'),
                'click': feedbackplayer.FeedbackPlayer('click.wav'),
                'error': feedbackplayer.FeedbackPlayer('error.wav'),
                'next': feedbackplayer.FeedbackPlayer('next.wav'),
        }
        self.browse_radios()
    
    def on_stop(self):
        self.smc.stop()

    def state_changed(self, old_state, new_state, target_state):
        if old_state == 'stopped' and new_state == 'paused' and target_state == 'playing':
            self.feedbacks['next'].play(loop=True)
        elif old_state == 'paused' and new_state == 'playing':
            self.feedbacks['next'].fadeout()

        print 'AUDIO STATE:', old_state, new_state, target_state

    def track_playback_started(self, tl_track):
        logger.info('track_playback_started: %s' % tl_track)
        self.encoder_abspos = 0
        self.track_state = STATE_TRACK_PLAYBACK_PLAYING

    def browse_radios(self):
        self.core.tracklist.clear()
        for radio in self.core.library.browse(uri='tunein:category:local').get():
            self.core.tracklist.add(uri=radio.uri)
            logger.debug('Added radio %s' % str(radio))

        self.radios_ready = True
        if self.power_state == STATE_POWER_PENDING_ON:
            self.power_on()

    def set_volume(self, volume):
        return
        self.core.playback.set_volume(volume)

    def set_power_control(self, wanted_state):
        logger.info('set_power_control wanted_state=%d' % wanted_state)
        if wanted_state == 1:
            if self.radios_ready:
                self.power_on()
            else:
                logger.warning('Delaying power on')
                self.power_state = STATE_POWER_PENDING_ON
        else:
            self.standby()

    def power_on(self):
        self.feedbacks['poweron'].play()
        self.core.playback.play()
        self.power_state = STATE_POWER_ON

    def standby(self):
        self.power_state = STATE_POWER_STANDBY
        if self.core.playback.state.get() == core.PlaybackState.PLAYING:
            self.track_state = STATE_TRACK_PLAYBACK_IDLE
            self.core.playback.stop()

    def play_next(self):
        logger.info('play_next')
        self.track_state = STATE_TRACK_PLAYBACK_PENDING
        self.core.playback.next()

    def play_previous(self):
        logger.info('play_previous')
        self.track_state = STATE_TRACK_PLAYBACK_PENDING
        self.core.playback.previous()

    def next_button_pressed(self):
        if (self.track_state == STATE_TRACK_PLAYBACK_PENDING or
                self.core.playback.state.get() != core.PlaybackState.PLAYING):
            self.feedbacks['error'].play()
            logger.warning('Skipping next button request')
            return
        else:
            self.feedbacks['click'].play()
            self.play_next()
