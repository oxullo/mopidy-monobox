#!/usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals

import os
import pygame

pygame.mixer.init()

class FeedbackPlayer(object):
    def __init__(self, filename):
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                'assets', filename)
        self.sound = pygame.mixer.Sound(filename)

    def play(self, loop=False):
        self.sound.play(loops=-1 if loop else 0)

    def fadeout(self):
        self.sound.fadeout(1000)
