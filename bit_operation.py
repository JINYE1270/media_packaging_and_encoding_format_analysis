#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import *

def exit(code=0):
    if os.name == 'nt':
        os.system('pause')

    sys.exit(code)


def mk_word(high_bits, low_bits):
    return (high_bits << 8) | low_bits


def mk_word24(bits1, bits2, bits3):
    return (bits1 << 16) | (bits2 << 8) | bits3


def mk_word32(bits1, bits2, bits3, bits4):
    return (bits1 << 24) | (bits2 << 16) | (bits3 << 8) | bits4


def mk_pcr(bits1, bits2, bits3, bits4, bits5):
    return bits1 << 25 | bits2 << 17 | bits3 << 9 | bits4 << 1 | bits5


def mk_pts_dts(bits1, bits2, bits3, bits4, bits5):
    return bits1 << 30 | bits2 << 22 | bits3 << 15 | bits4 << 7 | bits5


def ts2second(timestamp):
    return timestamp / 90000.0


