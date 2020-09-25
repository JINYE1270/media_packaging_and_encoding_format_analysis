#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import ctypes

class H264NALUHdrFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('nal_unit_type', ctypes.c_uint8, 5),
        ('nal_ref_idc', ctypes.c_uint8, 2),
        ('forbidden_zero_bit', ctypes.c_uint8, 1),
    ]


class SEIMSGFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('last_payload_type_byte', ctypes.c_uint8, 8),
        ('last_payload_size_byte', ctypes.c_uint8, 8),
    ]
    IV = None


class CEI_DATAFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('reserved', ctypes.c_uint8, 5),
        ('next_key_id_flag', ctypes.c_uint8, 1),
        ('encryption_flag', ctypes.c_uint8, 1),
        # # if encryption_flag == 1
        # ('current_key_id', ctypes.c_uint16, 16),
        # # if next_key_id_flag == 1
        # ('next_key_id', ctypes.c_uint16, 16),
        # ('IV_length', ctypes.c_uint8, 8),
    ]
    current_key_id = None
    next_key_id = None
    IV_length = None
    IV = None
