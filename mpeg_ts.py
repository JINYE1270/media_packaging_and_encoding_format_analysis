#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import *

# TS头部固定字段
class TSHdrFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('sync_byte', ctypes.c_uint8, 8),
        ('pid12_8', ctypes.c_uint8, 5),
        ('transport_priority', ctypes.c_uint8, 1),
        ('payload_unit_start_indicator', ctypes.c_uint8, 1),
        ('transport_error_indicator', ctypes.c_uint8, 1),
        ('pid7_0', ctypes.c_uint8, 8),
        ('continuity_counter', ctypes.c_uint8, 4),
        ('adaptation_field_control', ctypes.c_uint8, 2),
        ('transport_scrambling_control', ctypes.c_uint8, 2),
    ]
    # Packet Header（包头）信息Demo 共4字节
    # #	标识	位数	说明
    # 0*	sync_byte	8 bits	固定是0x47
    # 1*	transport_error_indicator	1 bits	值为0，表示当前包没有发生传输错误。错误指示信息（1：该包至少有1bits传输错误）
    # 2*	payload_unit_start_indicator	1 bits	值为1，含义参考ISO13818-1标准文档。负载单元开始标志（packet不满188字节时需填充）
    # 3*	transport_priority	1 bits	值为0，表示当前包是低优先级。传输优先级标志（1：优先级高）
    # 4*	PID	13 bits	PID=0x0000,说明是PAT表。Packet ID号码，唯一的号码对应不同的包
    # 5*	transport_scrambling_control	2 bits	值为0x00，表示节目没有加密。加密标志（00：未加密；其他表示已加密）
    # 6*	adaptation_field_control	2 bits	值为0x01,具体含义请参考ISO13818-1。附加区域控制
    # 7*	continuity_counter	4 bits	值为0xC,表示当前传送的相同类型的包是第12个。包递增计数器


# 填充字段的头部
class AdaptFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('adaptation_field_length', ctypes.c_uint8, 8),
        ('adaptation_field_extension_flag', ctypes.c_uint8, 1),
        ('transport_private_data_flag', ctypes.c_uint8, 1),
        ('splicing_point_flag', ctypes.c_uint8, 1),
        ('OPCR_flag', ctypes.c_uint8, 1),
        ('PCR_flag', ctypes.c_uint8, 1),
        ('elementary_stream_priority_indicator', ctypes.c_uint8, 1),
        ('random_access_indicator', ctypes.c_uint8, 1),
        ('discontinuity_indicator', ctypes.c_uint8, 1),
    ]
    l_pcr_flag = []
    l_opcr_flag = []
    l_splicing_point_flag = []
    l_transport_private_data_flag = []
    l_adaptation_field_extension_flag = []
    l_ltw_flag = []
    l_piecewise_rate_flag = []
    l_seamless_splice_flag = []
    stuffing_byte = []


class PCR(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('base32_25', ctypes.c_uint8, 8),
        ('base24_17', ctypes.c_uint8, 8),
        ('base16_9', ctypes.c_uint8, 8),
        ('base8_1', ctypes.c_uint8, 8),
        ('extension8', ctypes.c_uint8, 1),
        ('reserved', ctypes.c_uint8, 6),
        ('base0', ctypes.c_uint8, 1),
        ('extension7_0', ctypes.c_uint8, 8),
    ]


# PES固定头部 6bytes
class PESHdrFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        # ('packet_start_code_prefix', ctypes.c_uint32, 24),
        ('packet_start_code_prefix_23_16', ctypes.c_uint8, 8),
        ('packet_start_code_prefix_15_8', ctypes.c_uint8, 8),
        ('packet_start_code_prefix_7_0', ctypes.c_uint8, 8),
        # ('stream_id', ctypes.c_uint32, 8),
        ('stream_id', ctypes.c_uint8, 8),
        # ('PES_packet_length', ctypes.c_uint16, 16),
        ('PES_packet_length_15_8', ctypes.c_uint8, 8),
        ('PES_packet_length_7_0', ctypes.c_uint8, 8),
    ]
    PES_packet_data_byte = None


# PES可选头部字段
class OptionPESHdrFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('original_or_copy', ctypes.c_uint8, 1),
        ('copyright', ctypes.c_uint8, 1),
        ('data_alignment_indicator', ctypes.c_uint8, 1),
        ('PES_priority', ctypes.c_uint8, 1),
        ('PES_scrambling_control', ctypes.c_uint8, 2),
        ('fix_10', ctypes.c_uint8, 2),
        ('PES_extension_flag', ctypes.c_uint8, 1),
        ('PES_CRC_flag', ctypes.c_uint8, 1),
        ('additional_copy_info_flag', ctypes.c_uint8, 1),
        ('DSM_trick_mode_flag', ctypes.c_uint8, 1),
        ('ES_rate_flag', ctypes.c_uint8, 1),
        ('ESCR_flag', ctypes.c_uint8, 1),
        ('PTS_DTS_flags', ctypes.c_uint8, 2),
        ('PES_Hdr_data_length', ctypes.c_uint8, 8),
    ]


# PES可选头部 PTS_DTS_flags为0x10时
class OptionPESHdrFixedPart_PTS_DTS_flags10(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('marker_bit1', ctypes.c_uint8, 1),
        ('PTS_32_30', ctypes.c_uint8, 3),
        ('fix_0010', ctypes.c_uint8, 4),
        ('marker_bit2', ctypes.c_uint8, 1),
        ('PTS_29_23', ctypes.c_uint8, 7),
        ('PTS_22_15', ctypes.c_uint8, 8),
        ('marker_bit3', ctypes.c_uint8, 1),
        ('PTS_14_8', ctypes.c_uint8, 7),
        ('PTS_7_0', ctypes.c_uint8, 8),
    ]
    # if (PTS_DTS_flags == '10') {
    #  '0010' 4 bslbf
    #  PTS [32..30] 3 bslbf
    #  marker_bit 1 bslbf
    #  PTS [29..15] 15 bslbf
    #  marker_bit 1 bslbf
    #  PTS [14..0] 15 bslbf
    #  marker_bit 1 bslbf
    #  }


# PES可选头部 PTS_DTS_flags为0x11时
class OptionPESHdrFixedPart_PTS_DTS_flags11(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('marker_bit1', ctypes.c_uint8, 1),
        ('PTS_32_30', ctypes.c_uint8, 3),
        ('fix_0011', ctypes.c_uint8, 4),
        ('marker_bit2', ctypes.c_uint8, 1),
        ('PTS_29_23', ctypes.c_uint8, 7),
        ('PTS_22_15', ctypes.c_uint8, 8),
        ('marker_bit3', ctypes.c_uint8, 1),
        ('PTS_14_8', ctypes.c_uint8, 7),
        ('PTS_7_0', ctypes.c_uint8, 8),
        ('marker_bit4', ctypes.c_uint8, 1),
        ('DTS_32_30', ctypes.c_uint8, 3),
        ('fix_0011', ctypes.c_uint8, 4),
        ('marker_bit5', ctypes.c_uint8, 1),
        ('DTS_29_23', ctypes.c_uint8, 7),
        ('DTS_22_15', ctypes.c_uint8, 8),
        ('marker_bit6', ctypes.c_uint8, 1),
        ('DTS_14_8', ctypes.c_uint8, 7),
        ('DTS_7_0', ctypes.c_uint8, 8),
    ]
    # if (PTS_DTS_flags == '11') {
    #  '0011' 4 bslbf
    #  PTS [32..30] 3 bslbf
    #  marker_bit 1 bslbf
    #  PTS [29..15] 15 bslbf
    #  marker_bit 1 bslbf
    #  PTS [14..0] 15 bslbf
    #  marker_bit 1 bslbf
    # '0001' 4 bslbf
    #  DTS [32..30] 3 bslbf
    #  marker_bit 1 bslbf
    #  DTS [29..15] 15 bslbf
    #  marker_bit 1 bslbf
    #  DTS [14..0] 15 bslbf
    #  marker_bit 1 bslbf
    #  }


# PES可选头部 ESCR_flag
class OptionPESHdrFixedPart_ESCR_flag(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('ESCR_base_29_28', ctypes.c_uint8, 2),
        ('marker_bit1', ctypes.c_uint8, 1),
        ('ESCR_base_32_30', ctypes.c_uint8, 3),
        ('Reserved', ctypes.c_uint8, 2),
        ('ESCR_base_27_20', ctypes.c_uint8, 8),
        ('ESCR_base_14_13', ctypes.c_uint8, 2),
        ('marker_bit2', ctypes.c_uint8, 1),
        ('ESCR_base_19_15', ctypes.c_uint8, 5),
        ('ESCR_base_12_5', ctypes.c_uint8, 8),
        ('ESCR_extension_8_7', ctypes.c_uint8, 2),
        ('marker_bit3', ctypes.c_uint8, 1),
        ('ESCR_base_4_0', ctypes.c_uint8, 5),
        ('marker_bit4', ctypes.c_uint8, 1),
        ('ESCR_extension_6_0', ctypes.c_uint8, 7),
    ]
    # if (ESCR_flag == '1') {
    #  Reserved 2 bslbf
    #  ESCR_base[32..30] 3 bslbf
    #  marker_bit 1 bslbf
    #  ESCR_base[29..15] 15 bslbf
    #  marker_bit 1 bslbf
    #  ESCR_base[14..0] 15 bslbf
    #  marker_bit 1 bslbf
    #  ESCR_extension 9 uimsbf
    #  marker_bit 1 bslbf
    #  }


# PES可选头部 ES_rate_flag
class OptionPESHdrFixedPart_ES_rate_flag(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('ES_rate_21_15', ctypes.c_uint8, 7),
        ('marker_bit1', ctypes.c_uint8, 1),
        ('ES_rate_14_7', ctypes.c_uint8, 8),
        ('marker_bit2', ctypes.c_uint8, 1),
        ('ES_rate_6_0', ctypes.c_uint8, 7),
    ]
    # if (ES_rate_flag == '1') {
    #  marker_bit 1 bslbf
    #  ES_rate 22 uimsbf
    #  marker_bit 1 bslbf
    #  }


class PTS_DTS(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('marker_bit1', ctypes.c_uint8, 1),
        ('ts32_30', ctypes.c_uint8, 3),
        ('fix_4bits', ctypes.c_uint8, 4),  # PTS is '0010' or '0011', DTS is '0001'
        ('ts29_22', ctypes.c_uint8, 8),
        ('marker_bit2', ctypes.c_uint8, 1),
        ('ts21_15', ctypes.c_uint8, 7),
        ('ts14_7', ctypes.c_uint8, 8),
        ('marker_bit3', ctypes.c_uint8, 1),
        ('ts6_0', ctypes.c_uint8, 7),
    ]


# PAT表的固定部分
class PATHdrFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('table_id', ctypes.c_uint8, 8),
        ('section_length11_8', ctypes.c_uint8, 4),
        ('reserved1', ctypes.c_uint8, 2),
        ('zero_bit', ctypes.c_uint8, 1),  # '0'
        ('section_syntax_indicator', ctypes.c_uint8, 1),
        ('section_length7_0', ctypes.c_uint8, 8),
        # ('transport_stream_id', ctypes.c_uint16, 16),
        ('transport_stream_id_15_8', ctypes.c_uint8, 8),
        ('transport_stream_id_7_0', ctypes.c_uint8, 8),
        ('current_next_indicator', ctypes.c_uint8, 1),
        ('version_number', ctypes.c_uint8, 5),
        ('reserved2', ctypes.c_uint8, 2),
        ('section_number', ctypes.c_uint8, 8),
        ('last_section_number', ctypes.c_uint8, 8),
    ]
    # PAT 信息 固定位共 56bit + N个PMT(每个PMT32bit) + CRC_32bit
    # #	字段名	占位	具体值	次序	说明
    # 0*	table_id	8 bits	0000 0000(即0x00)	第0个字节   00	PAT的table_id只能是0x00
    # 1*	section_syntax_indicator	1 bit	1   第1、2个字节 B0 1D	段语法标志位，固定为1
    # 2*	zero	1 bit	0
    # 3*	reserved	2 bits	11 (Binary)
    # 4*	section_length	12 bits	00 00 00 01 11 01(即0x1D，十进制值为29)	意思是 段长度为29字节
    # 5*	transport_stream_id	16 bits	‭00 10 00 10 00 00 00 01‬(即0x2201)	第3、4个字节 22 01	TS的识别号
    # 6*	reserved	2 bits	11  第5个字节   CF	TS的识别号
    # 7*	version_number	5 bits	0 01 11	一旦PAT有变化，版本号加1
    # 8*	current_next_indicator	1 bit	1	当前传送的PAT表可以使用，若为0则要等待下一个表
    # 9*	section_number	4 bits	00 00(即0x00)	第6个字节   00	给出section号，在sub_table中，第一个section其section_number为"0x00",每增加一个section,section_number加一
    # 10*	last_section_number	4 bits	00 00(即0x00)	第7个字节   00	sub_table中最后一个section的section_number
    pmt_list = []  # program_map_PID
    CRC_32 = None


# PAT表的PMT部分
class PATSubSection(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        # ('program_number', ctypes.c_uint16, 16),
        ('program_number_15_8', ctypes.c_uint8, 8),
        ('program_number_7_0', ctypes.c_uint8, 8),
        ('pid12_8', ctypes.c_uint8, 5),
        ('reserved', ctypes.c_uint8, 3),
        ('pid7_0', ctypes.c_uint8, 8),
    ]
    # #	字段名	占位	具体值	说明
    # 1*	program_number	16 bits	0x0000	program_number = 0x0000
    # 2*	reserved	3 bits	111	-
    # 3*	program_map_PID	13 bits	0x0000	因为program_number为0x0000，所以这里是network_id(NIT的PID)
    network_list = []  # network_PID


# CRC
class CRCFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('CRC_32_31_24', ctypes.c_uint8, 8),
        ('CRC_32_23_16', ctypes.c_uint8, 8),
        ('CRC_32_15_8', ctypes.c_uint8, 8),
        ('CRC_32_7_0', ctypes.c_uint8, 8),
    ]
    # #	字段名	占位	具体值	说明
    # 1*	CRC_32	32 bits


# PMT表头部固定部分
class PMTHdrFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('table_id', ctypes.c_uint8, 8),
        ('section_length11_8', ctypes.c_uint8, 4),
        ('reserved1', ctypes.c_uint8, 2),
        ('zero_bit', ctypes.c_uint8, 1),  # '0'
        ('section_syntax_indicator', ctypes.c_uint8, 1),
        ('section_length7_0', ctypes.c_uint8, 8),
        # ('transport_stream_id', ctypes.c_uint16, 16),
        ('program_number_15_8', ctypes.c_uint8, 8),
        ('program_number_7_0', ctypes.c_uint8, 8),
        ('current_next_indicator', ctypes.c_uint8, 1),
        ('version_number', ctypes.c_uint8, 5),
        ('reserved2', ctypes.c_uint8, 2),
        ('section_number', ctypes.c_uint8, 8),
        ('last_section_number', ctypes.c_uint8, 8),
        ('PCR_PID12_8', ctypes.c_uint8, 5),
        ('reserved3', ctypes.c_uint8, 3),
        ('PCR_PID7_0', ctypes.c_uint8, 8),
        ('program_info_length11_8', ctypes.c_uint8, 4),
        ('reserved4', ctypes.c_uint8, 4),
        ('program_info_length7_0', ctypes.c_uint8, 8),
    ]
    # table_id 8 uimsbf
    #  section_syntax_indicator 1 bslbf
    #  '0' 1 bslbf
    #  reserved 2 bslbf
    #  section_length 12 uimsbf
    #  program_number 16 uimsbf
    #  reserved 2 bslbf
    #  version_number 5 uimsbf
    #  current_next_indicator 1 bslbf
    #  section_number 8 uimsbf
    #  last_section_number 8 uimsbf
    #  reserved 3 bslbf
    #  PCR_PID 13 uimsbf
    #  reserved 4 bslbf
    #  program_info_length 12 uimsbf
    #  for (i = 0; i < N; i++) {
    #  descriptor()
    #  }
    descriptor1 = []
    DRM_data_bytes = None
    stream_list = []
    descriptor2 = []
    CRC_32 = None  # CRC_32 32 rpchof


# PMT表节目流信息部分
class PMTSubSectionFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('stream_type', ctypes.c_uint8, 8),
        ('elementaryPID12_8', ctypes.c_uint8, 5),
        ('reserved1', ctypes.c_uint8, 3),
        ('elementaryPID7_0', ctypes.c_uint8, 8),
        ('ES_info_length11_8', ctypes.c_uint8, 4),
        ('reserved2', ctypes.c_uint8, 4),
        ('ES_info_length7_0', ctypes.c_uint8, 8),
    ]
    #  for (i = 0; i < N1; i++) {
    #  stream_type 8 uimsbf
    #  reserved 3 bslbf
    #  elementary_PID 13 uimsbf
    #  reserved 4 bslbf
    #  ES_info_length 12 uimsbf
    #  for (i = 0; i < N2; i++) {
    #  descriptor()
    #  }
    #  }


# Chinadrm描述子部分信息
class ChinaDRMFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('descriptor_tag', ctypes.c_uint8, 8),
        ('descriptor_length', ctypes.c_uint8, 8),
        ('video_encryption_method', ctypes.c_uint8, 4),
        ('video_format', ctypes.c_uint8, 4),
        ('audio_encryption_method', ctypes.c_uint8, 4),
        ('audio_format', ctypes.c_uint8, 4),
    ]
    # video_format：表示该码流中加密内容的编码格式，规定如下。
    # 编码格式	规定
    # AVS+	0001
    # AVS2	0010
    # H.265	0011
    # H.264	0100
    # 保留	0000,0101~1111
    # video_encryption_method：表示该码流中内容加密的方式，规定如下。
    # 加密方式	规定
    # NONE	0000
    # SAMPLE_SM4	0001
    # SM4_CBC	0011
    # SAMPLE_AES	0100
    # AES_CBC	0101
    # 保留	0110~1111


# 节目视频流描述子信息
class VideoStreamDescriptorFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('descriptor_tag', ctypes.c_uint8, 8),
        ('descriptor_length', ctypes.c_uint8, 8),
        ('still_picture_flag', ctypes.c_uint8, 1),
        ('constrained_parameter_flag', ctypes.c_uint8, 1),
        ('MPEG_1_only_flag', ctypes.c_uint8, 1),
        ('frame_rate_code', ctypes.c_uint8, 4),
        ('multiple_frame_rate_flag', ctypes.c_uint8, 1),
    ]
    # descriptor_tag 8 uimsbf
    # descriptor_length 8 uimsbf
    # multiple_frame_rate_flag 1 bslbf
    # frame_rate_code 4 uimsbf
    # MPEG_1_only_flag 1 bslbf
    # constrained_parameter_flag 1 bslbf
    # still_picture_flag 1 bslbf


# 节目视频流描述子的可选字段信息部分
class VideoStreamDescriptorSubSectionFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('profile_and_level_indication', ctypes.c_uint8, 8),
        ('Reserved', ctypes.c_uint8, 5),
        ('frame_rate_extension_flag', ctypes.c_uint8, 1),
        ('chroma_format', ctypes.c_uint8, 2),
    ]
    # if (MPEG_1_only_flag = = '0'){
    # profile_and_level_indication 8 uimsbf
    # chroma_format 2 uimsbf
    # frame_rate_extension_flag 1 bslbf
    # Reserved 5 bslbf


# 节目音频流的描述子信息部分
class AudioStreamDescriptorFixedPart(ctypes.LittleEndianStructure):
    _pack_ = 1  # 1字节对齐
    _fields_ = [
        ('descriptor_tag', ctypes.c_uint8, 8),
        ('descriptor_length', ctypes.c_uint8, 8),
        ('reserved', ctypes.c_uint8, 3),
        ('variable_rate_audio_indicator', ctypes.c_uint8, 1),
        ('layer', ctypes.c_uint8, 2),
        ('ID', ctypes.c_uint8, 1),
        ('free_format_flag', ctypes.c_uint8, 1),
    ]
    #  descriptor_tag 8 uimsbf
    #  descriptor_length 8 uimsbf
    #  free_format_flag 1 bslbf
    #  ID 1 bslbf
    #  layer 2 bslbf
    #  variable_rate_audio_indicator 1 bslbf
    #  reserved 3 bslbf