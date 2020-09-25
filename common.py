#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import ctypes as ctypes
import os
# from datetime import timedelta
# from optparse import OptionParser
from sm4 import *

sizeof = ctypes.sizeof

sm4_d = Sm4()

# 加密密钥
key_data = [0x61, 0x61, 0x6b, 0x36, 0x39, 0x33, 0x6a, 0x75,
            0x66, 0x76, 0x77, 0x32, 0x34, 0x37, 0x79, 0x30]
# 初始向量
iv_data = [0x64, 0x64, 0x30, 0x63, 0x6d, 0x75, 0x68, 0x38,
           0x68, 0x36, 0x70, 0x6b, 0x62, 0x78, 0x70, 0x39]

# SM4 CBC
# 待解析的加密 ts 流文件路径
file_path_enc_cbc_ts = "src_videos/test02_cbc_enc.ts"
# 解析出来的加密 h264 文件路径
file_path_enc_cbc_h264 = "test_videos2/test02_enc_cbc_parse.h264"
# 解密后的 h264 文件路径
file_path_dec_cbc_h264 = "test_videos2/test02_dec_cbc_parse.h264"
# file_path_dec_cbc_h264 = "test_videos_multi/multi_test02_dec_cbc_parse.h264"
# file_path_dec_cbc_h264 = "test_videos_multi/multi2_test02_dec_cbc_parse.h264"

# h264 视频帧起始码的位置，默认为0，即当前起始码开头位置为0
current_start_code_position = 0
