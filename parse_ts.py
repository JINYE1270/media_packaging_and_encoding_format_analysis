#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import *
from mpeg_ts import *
from bit_operation import *

TS_PKT_LEN = 188
TS_SYNC_BYTE = 0x47
PES_START_CODE = 0x010000  # PES分组起始标志0x000001
CRC32_LEN = 4
INVALID_VAL = -1

MAX_READ_PKT_NUM = 10000
MAX_CHECK_PKT_NUM = 3

# PID type
PID_PAT, PID_NULL, PID_UNSPEC = 0x0000, 0x1fff, 0xffff
# Stream id
PES_STREAM_VIDEO, PES_STREAM_AUDIO = 0xE0, 0xC0
# Video stream type
ES_TYPE_MPEG1V, ES_TYPE_MPEG2V, ES_TYPE_MPEG4V, ES_TYPE_H264 = 0x01, 0x02, 0x10, 0x1b
# Audio stream type
ES_TYPE_MPEG1A, ES_TYPE_MPEG2A, ES_TYPE_AAC, ES_TYPE_AC3, ES_TYPE_DTS = 0x03, 0x04, 0x0f, 0x81, 0x8a


class TSPacket:
    pid_map = {
        'PMT': PID_UNSPEC,
        'PCR': PID_UNSPEC,
        'VIDEO': PID_UNSPEC,
        'AUDIO': PID_UNSPEC,
    }

    def __init__(self, buf):
        self.buf = buf
        self.ts_header = None
        self.pat = None
        self.pat_program = None
        self.crc = None
        self.pid = PID_UNSPEC
        self.cc = INVALID_VAL
        self.pmt_pid = PID_UNSPEC
        self.pmt = None
        self.chinadrm_descriptor = None
        self.pmt_streams = None
        self.video_descriptor = None
        self.video_descriptor_sub = None
        self.audio_descriptor = None
        self.stream_id = INVALID_VAL
        self.adapt = None
        self.pes = None
        self.pes_optionheader = None
        self.pcr = INVALID_VAL
        self.pts = INVALID_VAL
        self.dts = INVALID_VAL

    def parse(self):
        if not self.buf or (TS_PKT_LEN != len(self.buf)):
            print '###### Input data length is not 188 bytes!', len(self.buf), self.buf
            return False

        if TS_SYNC_BYTE != ord(self.buf[0]):
            print '###### The first byte of packet is not 0x47!'
            return False

        self.ts_header = TSHdrFixedPart.from_buffer_copy(self.buf[0:sizeof(TSHdrFixedPart)])
        self.pid = mk_word(self.ts_header.pid12_8, self.ts_header.pid7_0)
        self.cc = self.ts_header.continuity_counter

        if self.is_pat():
            # print '********Start to Parse PAT********'
            self.__parse_pat()
            # self.show_tsheaderinfo()
            # self.show_patinfo()
        elif self.is_pmt():
            # print '********Start to Parse PMT********'
            self.__parse_pmt()
            # self.show_tsheaderinfo()
            # self.show_pmtinfo()
        elif self.__has_payload() and self.is_video():
            # print '********Start to Parse PES********'
            self.__parse_pes()
            # self.show_tsheaderinfo()
            # self.show_pesinfo()

        return True

    def show_tsheaderinfo(self):
        print '==============TSHeader=============='
        print 'sync_byte:0x%X' % self.ts_header.sync_byte
        print 'transport_error_indicator:0x%X' % self.ts_header.transport_error_indicator
        print 'payload_unit_start_indicator:0x%X' % self.ts_header.payload_unit_start_indicator
        print 'transport_priority:0x%X' % self.ts_header.transport_priority
        print 'pid:0x%X' % self.pid
        print 'transport_scrambling_control:0x%X' % self.ts_header.transport_scrambling_control
        print 'adaptation_field_control:0x%X' % self.ts_header.adaptation_field_control
        print 'continuity_counter:0x%X' % self.ts_header.continuity_counter

        if self.__has_adapt_field():
            print '==============Adaptation Field=============='
            print 'adaptation_field_length:0x%X' % self.adapt.adaptation_field_length
            print 'discontinuity_indicator:0x%X' % self.adapt.discontinuity_indicator
            print 'random_access_indicator:0x%X' % self.adapt.random_access_indicator
            print 'elementary_stream_priority_indicator:0x%X' % self.adapt.elementary_stream_priority_indicator
            print 'PCR_flag:0x%X' % self.adapt.PCR_flag
            print 'OPCR_flag:0x%X' % self.adapt.OPCR_flag
            print 'splicing_point_flag:0x%X' % self.adapt.splicing_point_flag
            print 'transport_private_data_flag:0x%X' % self.adapt.transport_private_data_flag
            print 'adaptation_field_extension_flag:0x%X' % self.adapt.adaptation_field_extension_flag

    def show_patinfo(self):
        print '==============PAT=============='
        print 'table_id:0x%X' % self.pat.table_id
        print 'section_syntax_indicator:0x%X' % self.pat.section_syntax_indicator
        print 'zero:0x%X' % self.pat.zero_bit
        print 'reserved:0x%X' % self.pat.reserved1
        print 'section_length:0x%X' % mk_word(self.pat.section_length11_8, self.pat.section_length7_0)
        print 'transport_stream_id:0x%X' % mk_word(self.pat.transport_stream_id_15_8, self.pat.transport_stream_id_7_0)
        print 'reserved:0x%X' % self.pat.reserved2
        print 'version_number:0x%X' % self.pat.version_number
        print 'current_next_indicator:0x%X' % self.pat.current_next_indicator
        print 'section_number:0x%X' % self.pat.section_number
        print 'last_section_number:0x%X' % self.pat.last_section_number
        print 'program_number:0x%X' % mk_word(self.pat_program.program_number_15_8, self.pat_program.program_number_7_0)
        print 'reserved:0x%X' % self.pat_program.reserved
        for p in self.pat.pmt_list:
            if mk_word(self.pat_program.program_number_15_8, self.pat_program.program_number_7_0) == 0x0:
                print 'network_PID:0x%X' % p
            else:
                print 'program_map_PID:0x%X' % p
        print 'CRC_32:0x%X' % self.pat.CRC_32

    def show_pmtinfo(self):
        print '==============PMT=============='
        print 'table_id:0x%X' % self.pmt.table_id
        print 'section_syntax_indicator:0x%X' % self.pmt.section_syntax_indicator
        print 'zero:0x%X' % self.pmt.zero_bit
        print 'reserved:0x%X' % self.pmt.reserved1
        print 'section_length:0x%X' % mk_word(self.pmt.section_length11_8, self.pmt.section_length7_0)
        print 'program_number:0x%X' % mk_word(self.pmt.program_number_15_8, self.pmt.program_number_7_0)
        print 'reserved:0x%X' % self.pmt.reserved2
        print 'version_number:0x%X' % self.pmt.version_number
        print 'current_next_indicator:0x%X' % self.pmt.current_next_indicator
        print 'section_number:0x%X' % self.pmt.section_number
        print 'last_section_number:0x%X' % self.pmt.last_section_number
        print 'reserved:0x%X' % self.pmt.reserved3
        print 'PCR_PID:0x%X' % mk_word(self.pmt.PCR_PID12_8, self.pmt.PCR_PID7_0)
        print 'reserved:0x%X' % self.pmt.reserved4
        print 'program_info_length:0x%X' % mk_word(self.pmt.program_info_length11_8, self.pmt.program_info_length7_0)

        if mk_word(self.pmt.program_info_length11_8,
                   self.pmt.program_info_length7_0) != 0x0 and self.chinadrm_descriptor.descriptor_tag == 0xC0:
            print '==============ChinaDRM descriptor=============='
            print 'descriptor_tag:0x%X' % self.chinadrm_descriptor.descriptor_tag
            print 'descriptor_length:0x%X' % self.chinadrm_descriptor.descriptor_length
            print 'video_format:0x%X' % self.chinadrm_descriptor.video_format,
            if self.chinadrm_descriptor.video_format == 1:
                print '（AVS+）'
            elif self.chinadrm_descriptor.video_format == 2:
                print '（AVS2）'
            elif self.chinadrm_descriptor.video_format == 3:
                print '（H.265）'
            elif self.chinadrm_descriptor.video_format == 4:
                print '（H.264）'
            else:
                print '（Reserved）'
            print 'video_encryption_method:0x%X' % self.chinadrm_descriptor.video_encryption_method,
            if self.chinadrm_descriptor.video_encryption_method == 0:
                print '（NONE）'
            elif self.chinadrm_descriptor.video_encryption_method == 1:
                print '（SAMPLE_SM4）'
            elif self.chinadrm_descriptor.video_encryption_method == 3:
                print '（SM4_CBC）'
            elif self.chinadrm_descriptor.video_encryption_method == 4:
                print '（SAMPLE_AES）'
            elif self.chinadrm_descriptor.video_encryption_method == 5:
                print '（AES_CBC）'
            else:
                print '（Reserved）'
            print 'audio_format:0x%X' % self.chinadrm_descriptor.audio_format
            print 'audio_encryption_method:0x%X' % self.chinadrm_descriptor.audio_encryption_method
            print 'DRM_data_bytes:', self.pmt.DRM_data_bytes

        for i in range(0, len(self.pmt.stream_list)):
            print '==============Streams=============='
            print 'stream_type:0x%X' % self.pmt.stream_list[i][0]
            print 'reserved:0x%X' % self.pmt.stream_list[i][1]
            print 'elementary_PID:0x%X' % self.pmt.stream_list[i][2]
            print 'reserved:0x%X' % self.pmt.stream_list[i][3]
            print 'ES_info_length:0x%X' % self.pmt.stream_list[i][4]

            if self.pmt.stream_list[i][4] != 0x0:
                if self.__is_video_stream(self.pmt.stream_list[i][0]):
                    print '==============Video_stream_descriptor=============='
                    print 'descriptor_tag:0x%X' % self.pmt.descriptor2[i][0]
                    print 'descriptor_length:0x%X' % self.pmt.descriptor2[i][1]
                    print 'multiple_frame_rate_flag:0x%X' % self.pmt.descriptor2[i][2]
                    print 'frame_rate_code:0x%X' % self.pmt.descriptor2[i][3]
                    print 'MPEG_1_only_flag:0x%X' % self.pmt.descriptor2[i][4]
                    print 'constrained_parameter_flag:0x%X' % self.pmt.descriptor2[i][5]
                    print 'still_picture_flag:0x%X' % self.pmt.descriptor2[i][6]
                    if self.pmt.descriptor2[i][4] == 0x0:
                        print 'profile_and_level_indication:0x%X' % self.pmt.descriptor2[i][7]
                        print 'chroma_format:0x%X' % self.pmt.descriptor2[i][8]
                        print 'frame_rate_extension_flag:0x%X' % self.pmt.descriptor2[i][9]
                        print 'Reserved:0x%X' % self.pmt.descriptor2[i][10]

                elif self.__is_audio_stream(self.pmt.stream_list[i][0]):
                    print '==============Audio_stream_descriptor=============='
                    print 'descriptor_tag:0x%X' % self.pmt.descriptor2[i][0]
                    print 'descriptor_length:0x%X' % self.pmt.descriptor2[i][1]
                    print 'free_format_flag:0x%X' % self.pmt.descriptor2[i][2]
                    print 'ID:0x%X' % self.pmt.descriptor2[i][3]
                    print 'layer:0x%X' % self.pmt.descriptor2[i][4]
                    print 'variable_rate_audio_indicator:0x%X' % self.pmt.descriptor2[i][5]
                    print 'reserved:0x%X' % self.pmt.descriptor2[i][6]
        print 'CRC_32:0x%X' % self.pmt.CRC_32

    def show_pesinfo(self):
        if self.ts_header.payload_unit_start_indicator == 0x01:
            print '==============PES=============='
            print 'packet_start_code_prefix:0x%X' % mk_word24(self.pes.packet_start_code_prefix_23_16,
                                                              self.pes.packet_start_code_prefix_15_8,
                                                              self.pes.packet_start_code_prefix_7_0)
            print 'stream_id:0x%X' % self.pes.stream_id
            print 'PES_packet_length:0x%X' % mk_word(self.pes.PES_packet_length_15_8, self.pes.PES_packet_length_7_0)
            print '10:0x%X' % self.pes_optionheader.fix_10
            print 'PES_scrambling_control:0x%X' % self.pes_optionheader.PES_scrambling_control
            print 'PES_priority:0x%X' % self.pes_optionheader.PES_priority
            print 'data_alignment_indicator:0x%X' % self.pes_optionheader.data_alignment_indicator
            print 'copyright:0x%X' % self.pes_optionheader.copyright
            print 'original_or_copy:0x%X' % self.pes_optionheader.original_or_copy
            print 'PTS_DTS_flags:0x%X' % self.pes_optionheader.PTS_DTS_flags
            print 'ESCR_flag:0x%X' % self.pes_optionheader.ESCR_flag
            print 'ES_rate_flag:0x%X' % self.pes_optionheader.ES_rate_flag
            print 'DSM_trick_mode_flag:0x%X' % self.pes_optionheader.DSM_trick_mode_flag
            print 'additional_copy_info_flag:0x%X' % self.pes_optionheader.additional_copy_info_flag
            print 'PES_CRC_flag:0x%X' % self.pes_optionheader.PES_CRC_flag
            print 'PES_extension_flag:0x%X' % self.pes_optionheader.PES_extension_flag
            print 'PES_header_data_length:0x%X' % self.pes_optionheader.PES_Hdr_data_length
            print 'PES_packet_data_byte:',
            for i in self.pes.PES_packet_data_byte:
                print '%02X' % ord(i),
        elif self.ts_header.payload_unit_start_indicator == 0x00:
            print '==============PES=============='
            print "PES all video data!!!"
            print 'PES_packet_data_byte:',
            if self.pes:
                for i in self.pes.PES_packet_data_byte:
                    print '%02X' % ord(i),
            else:
                print "(none)"

    def is_pat(self):
        return PID_PAT == self.pid

    def is_pmt(self):
        return (PID_UNSPEC != self.pid) and (TSPacket.pid_map['PMT'] == self.pid)

    def is_video(self):
        return TSPacket.pid_map['VIDEO'] == self.pid

    def is_audio(self):
        return TSPacket.pid_map['AUDIO'] == self.pid

    def __has_adapt_field(self):
        return 0 != (self.ts_header.adaptation_field_control & 0x2)

    def __has_payload(self):
        return (self.ts_header.payload_unit_start_indicator == 1) or (self.ts_header.adaptation_field_control & 0x1)

    def __get_adapt_field(self):
        if self.__has_adapt_field():
            self.adapt = AdaptFixedPart.from_buffer_copy(self.buf[sizeof(TSHdrFixedPart):])
        return self.adapt

    def __get_adapt_len(self):
        adapt_len = 0
        adapt = self.__get_adapt_field()
        if adapt:
            # 'adaptation_field_length' field is 1 byte
            adapt_len = adapt.adaptation_field_length + 1
        return adapt_len

    def __get_pcr(self):
        pcr_val = INVALID_VAL
        adapt = self.__get_adapt_field()
        if adapt and adapt.adaptation_field_length > 0 and adapt.PCR_flag:
            pcr = PCR.from_buffer_copy(self.buf[sizeof(TSHdrFixedPart) + sizeof(AdaptFixedPart):])
            pcr_val = mk_pcr(pcr.base32_25, pcr.base24_17, pcr.base16_9, pcr.base8_1, pcr.base0)
        return pcr_val

    def __is_video_stream(self, stream_type):
        return stream_type in (ES_TYPE_MPEG1V, ES_TYPE_MPEG2V, ES_TYPE_MPEG4V, ES_TYPE_H264)

    def __is_audio_stream(self, stream_type):
        return stream_type in (ES_TYPE_MPEG1A, ES_TYPE_MPEG2A, ES_TYPE_AC3, ES_TYPE_AAC, ES_TYPE_DTS)

    def __get_payload_offset(self):
        return sizeof(TSHdrFixedPart) + self.__get_adapt_len()

    def __get_table_start_pos(self):
        pos = 0
        if self.__has_payload():
            pos = self.__get_payload_offset()
            # 'pointer_field' field is 1 byte,
            # and whose value is the number of bytes before payload
            pos += ord(self.buf[pos]) + 1
        return pos

    def __get_pts(self, option_hdr_pos):
        pts_val = INVALID_VAL
        pts_pos = option_hdr_pos + sizeof(OptionPESHdrFixedPart)
        option_hdr = OptionPESHdrFixedPart.from_buffer_copy(self.buf[option_hdr_pos:pts_pos])
        if option_hdr.PTS_DTS_flags & 0x2:
            pts = PTS_DTS.from_buffer_copy(self.buf[pts_pos:pts_pos + sizeof(PTS_DTS)])
            pts_val = mk_pts_dts(pts.ts32_30, pts.ts29_22, pts.ts21_15, pts.ts14_7, pts.ts6_0)
        return pts_val

    def __get_dts(self, option_hdr_pos):
        dts_val = INVALID_VAL
        pts_pos = option_hdr_pos + sizeof(OptionPESHdrFixedPart)
        option_hdr = OptionPESHdrFixedPart.from_buffer_copy(self.buf[option_hdr_pos:pts_pos])
        if option_hdr.PTS_DTS_flags & 0x1:
            dts_pos = pts_pos + sizeof(PTS_DTS)
            dts = PTS_DTS.from_buffer_copy(self.buf[dts_pos:dts_pos + sizeof(PTS_DTS)])
            dts_val = mk_pts_dts(dts.ts32_30, dts.ts29_22, dts.ts21_15, dts.ts14_7, dts.ts6_0)
        return dts_val

    def __parse_pat(self):
        pat_pos = self.__get_table_start_pos()
        section_pos = pat_pos + sizeof(PATHdrFixedPart)
        self.pat = PATHdrFixedPart.from_buffer_copy(self.buf[pat_pos:section_pos])
        section_len = mk_word(self.pat.section_length11_8, self.pat.section_length7_0)
        # 3 means the "section_length" field and fileds before it ,count 24bit = 3 bytes
        all_subsection_len = section_len - sizeof(PATHdrFixedPart) - CRC32_LEN + 3
        subsection_len = sizeof(PATSubSection)
        program_num = 0
        for i in xrange(0, all_subsection_len, subsection_len):
            tmp_buf = self.buf[section_pos + i:section_pos + i + subsection_len]
            self.pat_program = PATSubSection.from_buffer_copy(tmp_buf)
            pid = mk_word(self.pat_program.pid12_8, self.pat_program.pid7_0)
            # if 0x00 == self.pat_program.program_number:
            if 0x00 == mk_word(self.pat_program.program_number_15_8, self.pat_program.program_number_7_0):
                self.pat_program.network_list.append(pid)
            else:
                self.pmt_pid = pid  # program_map_PID
                if pid not in self.pat.pmt_list:
                    self.pat.pmt_list.append(pid)
                # break
            program_num += 1

        crc_pos = section_pos + all_subsection_len * program_num
        self.crc = CRCFixedPart.from_buffer_copy(self.buf[crc_pos:crc_pos + 4])
        crc_tmp = mk_word32(self.crc.CRC_32_31_24, self.crc.CRC_32_23_16, self.crc.CRC_32_15_8, self.crc.CRC_32_7_0)
        self.pat.CRC_32 = crc_tmp

        TSPacket.pid_map['PMT'] = self.pmt_pid

    def __parse_pmt(self):
        pmt_pos = self.__get_table_start_pos()
        section_pos = pmt_pos + sizeof(PMTHdrFixedPart)
        self.pmt = PMTHdrFixedPart.from_buffer_copy(self.buf[pmt_pos:section_pos])
        TSPacket.pid_map['PCR'] = mk_word(self.pmt.PCR_PID12_8, self.pmt.PCR_PID7_0)
        section_len = mk_word(self.pmt.section_length11_8, self.pmt.section_length7_0)
        program_info_len = mk_word(self.pmt.program_info_length11_8, self.pmt.program_info_length7_0)
        if program_info_len != 0:
            self.chinadrm_descriptor = ChinaDRMFixedPart.from_buffer_copy(
                self.buf[section_pos:section_pos + program_info_len])
            drm_data_pos = section_pos + 4
            self.pmt.DRM_data_bytes = self.buf[drm_data_pos:(self.chinadrm_descriptor.descriptor_length - 2) * 8]

        all_subsection_len = section_len - (sizeof(PMTHdrFixedPart) - 3) - program_info_len - CRC32_LEN
        subsection_len = sizeof(PMTSubSectionFixedPart)
        section_pos += program_info_len
        i = 0
        while i < all_subsection_len:
            tmp_buf = self.buf[section_pos + i:section_pos + i + subsection_len]
            self.pmt_streams = PMTSubSectionFixedPart.from_buffer_copy(tmp_buf)
            elementary_pid = mk_word(self.pmt_streams.elementaryPID12_8, self.pmt_streams.elementaryPID7_0)
            es_info_len = mk_word(self.pmt_streams.ES_info_length11_8, self.pmt_streams.ES_info_length7_0)
            stream = [self.pmt_streams.stream_type, self.pmt_streams.reserved1, elementary_pid,
                      self.pmt_streams.reserved2, es_info_len]
            if stream not in self.pmt.stream_list:
                self.pmt.stream_list.append(stream)

            if self.__is_video_stream(self.pmt_streams.stream_type):
                TSPacket.pid_map['VIDEO'] = elementary_pid
            elif self.__is_audio_stream(self.pmt_streams.stream_type):
                TSPacket.pid_map['AUDIO'] = elementary_pid

            descriptor_pos_start = section_pos + i + subsection_len
            descriptor_pos_end = descriptor_pos_start + sizeof(VideoStreamDescriptorFixedPart)
            if es_info_len != 0 and self.__is_video_stream(self.pmt_streams.stream_type):
                vdptinfo_tmp = []
                self.video_descriptor = VideoStreamDescriptorFixedPart.from_buffer_copy(
                    self.buf[descriptor_pos_start:descriptor_pos_end])
                vdptinfo_tmp.append(self.video_descriptor.descriptor_tag)
                vdptinfo_tmp.append(self.video_descriptor.descriptor_length)
                vdptinfo_tmp.append(self.video_descriptor.multiple_frame_rate_flag)
                vdptinfo_tmp.append(self.video_descriptor.frame_rate_code)
                vdptinfo_tmp.append(self.video_descriptor.MPEG_1_only_flag)
                vdptinfo_tmp.append(self.video_descriptor.constrained_parameter_flag)
                vdptinfo_tmp.append(self.video_descriptor.still_picture_flag)

                if self.video_descriptor.MPEG_1_only_flag == '0':
                    self.video_descriptor_sub = VideoStreamDescriptorSubSectionFixedPart.from_buffer_copy(
                        self.buf[descriptor_pos_end:descriptor_pos_end + 4])
                    vdptinfo_tmp.append(self.video_descriptor_sub.profile_and_level_indication)
                    vdptinfo_tmp.append(self.video_descriptor_sub.chroma_format)
                    vdptinfo_tmp.append(self.video_descriptor_sub.frame_rate_extension_flag)
                    vdptinfo_tmp.append(self.video_descriptor_sub.Reserved)
                self.pmt.descriptor2.append(vdptinfo_tmp)

            elif es_info_len == 0 and self.__is_video_stream(self.pmt_streams.stream_type):
                vdptinfo_tmp = []
                self.pmt.descriptor2.append(vdptinfo_tmp)

            elif es_info_len != 0 and self.__is_audio_stream(self.pmt_streams.stream_type):
                adptinfo_tmp = []
                self.audio_descriptor = AudioStreamDescriptorFixedPart.from_buffer_copy(
                    self.buf[descriptor_pos_start:descriptor_pos_start + sizeof(AudioStreamDescriptorFixedPart)])
                adptinfo_tmp.append(self.audio_descriptor.descriptor_tag)
                adptinfo_tmp.append(self.audio_descriptor.descriptor_length)
                adptinfo_tmp.append(self.audio_descriptor.free_format_flag)
                adptinfo_tmp.append(self.audio_descriptor.ID)
                adptinfo_tmp.append(self.audio_descriptor.layer)
                adptinfo_tmp.append(self.audio_descriptor.variable_rate_audio_indicator)
                adptinfo_tmp.append(self.audio_descriptor.reserved)
                self.pmt.descriptor2.append(adptinfo_tmp)

            elif es_info_len == 0 and self.__is_audio_stream(self.pmt_streams.stream_type):
                adptinfo_tmp = []
                self.pmt.descriptor2.append(adptinfo_tmp)

            i += subsection_len + es_info_len

        crc_pos = section_pos + all_subsection_len
        self.crc = CRCFixedPart.from_buffer_copy(self.buf[crc_pos:crc_pos + 4])
        crc_tmp = mk_word32(self.crc.CRC_32_31_24, self.crc.CRC_32_23_16, self.crc.CRC_32_15_8, self.crc.CRC_32_7_0)
        self.pmt.CRC_32 = crc_tmp

    def __parse_pes(self):
        pes_pos = self.__get_payload_offset()
        option_hdr_pos = pes_pos + sizeof(PESHdrFixedPart)
        if option_hdr_pos > TS_PKT_LEN:
            return
        self.pes = PESHdrFixedPart.from_buffer_copy(self.buf[pes_pos:option_hdr_pos])
        if self.ts_header.payload_unit_start_indicator == 0x01:
            packet_start_code_prefix = mk_word24(self.pes.packet_start_code_prefix_23_16,
                                                 self.pes.packet_start_code_prefix_15_8,
                                                 self.pes.packet_start_code_prefix_7_0)
            if PES_START_CODE == packet_start_code_prefix:
                self.stream_id = self.pes.stream_id
                if (self.pes.stream_id & PES_STREAM_VIDEO) or (self.pes.stream_id & PES_STREAM_AUDIO):
                    self.pts = self.__get_pts(option_hdr_pos)
                    self.dts = self.__get_dts(option_hdr_pos)

            self.pes_optionheader = OptionPESHdrFixedPart.from_buffer_copy(
                self.buf[option_hdr_pos:option_hdr_pos + sizeof(OptionPESHdrFixedPart)])
            self.pes.PES_packet_data_byte = self.buf[option_hdr_pos + sizeof(
                OptionPESHdrFixedPart) + self.pes_optionheader.PES_Hdr_data_length:]
        elif self.ts_header.payload_unit_start_indicator == 0x00:
            self.pes.PES_packet_data_byte = self.buf[pes_pos:]

        with open(file_path_enc_cbc_h264, "ab+") as file_:
            file_.write(self.pes.PES_packet_data_byte)

class TSParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.fd = None
        self.pkt_no = 0
        self.show_pid = PID_UNSPEC
        self.grep = 'ALL'

    def set_show_param(self, pid, grep):
        if pid is not None:
            self.show_pid = pid
        if grep:
            self.grep = grep

    def parse(self):
        self.__open_file()
        if not self.__seek_to_first_pkt():
            print '###### Seek to first packet failed!'
            exit(-1)

        cur_pos = self.fd.tell()
        print 'Seek to first packet, offset: 0x%08X' % cur_pos

        read_len = MAX_READ_PKT_NUM * TS_PKT_LEN
        try:
            count = 0
            while True:
                buf = self.fd.read(read_len)
                if not buf:
                    break
                real_len = len(buf)

                for i in xrange(0, real_len, TS_PKT_LEN):
                    if ord(buf[i]) != 0x47:
                        print '###### PktNo: %08d, Offset: 0x%08X, Sync byte error!' % (self.pkt_no + 1, cur_pos),
                        print 'First byte<0x%02X>' % ord(buf[i])
                        if not self.__seek_to_first_pkt(cur_pos):
                            print '###### Seek to next ts packet failed!'
                            exit(-1)
                        cur_pos = self.fd.tell()
                        break

                    pkt = TSPacket(buf[i:i + TS_PKT_LEN])
                    success = pkt.parse()
                    if success and self.__is_show_pkt(pkt):
                        self.__print_packet_info(pkt, cur_pos)
                        cur_pos += TS_PKT_LEN
                        self.pkt_no += 1

                count += 1

            print 'Parse file complete!'
        except IOError as (errno, strerror):
            print '###### Read file error! error({0}): {1}'.format(errno, strerror)

        self.__close_file()

    def __open_file(self):
        try:
            self.fd = open(self.file_path, 'rb')
            print 'Open file<%s> success.' % self.file_path
        except IOError as (errno, strerror):
            print '###### Open file<%s> failed! error({0}): {1}'.format(errno, strerror)
            exit(-1)

    def __close_file(self):
        if self.fd:
            self.fd.close()
            self.fd = None
            print 'Close file<%s>' % self.file_path

    def __seek_to_first_pkt(self, pos=0):
        try:
            self.fd.seek(pos)
            buf = self.fd.read(MAX_READ_PKT_NUM * TS_PKT_LEN)
            loop_num = len(buf) - MAX_CHECK_PKT_NUM * TS_PKT_LEN
            for i in xrange(0, loop_num):
                if ord(buf[i]) == TS_SYNC_BYTE:
                    for n in xrange(0, MAX_CHECK_PKT_NUM):
                        if ord(buf[i + n * TS_PKT_LEN]) != TS_SYNC_BYTE:
                            break
                    else:
                        self.fd.seek(pos + i)
                        return True
        except IOError as (errno, strerror):
            print '###### Read file error! error({0}): {1}'.format(errno, strerror)

        return False

    def __is_show_pkt(self, pkt):
        show = True
        if PID_UNSPEC != self.show_pid:
            show = pkt.pid == self.show_pid
        elif 'ALL' != self.grep:
            show = pkt.is_pat() and 'PAT' in self.grep
            show = show or pkt.is_pmt() and 'PMT' in self.grep
            show = show or pkt.pcr > 0 and 'PCR' in self.grep
            show = show or pkt.pts > 0 and 'PTS' in self.grep
            show = show or pkt.dts > 0 and 'DTS' in self.grep
        return show

    def __print_packet_info(self, pkt, offset):
        args = (self.pkt_no, offset, pkt.pid, pkt.cc)
        # print 'PktNo: %08u, Offset: 0x%08X, PID: 0x%04X, CC: %02u,' % args,

        # if pkt.is_pat():
        #     print 'PAT,',
        # elif pkt.is_pmt():
        #     print 'PMT,',
        # elif pkt.pcr >= 0:
        #     print 'PCR: %d(%s),' % (pkt.pcr, timedelta(seconds=ts2second(pkt.pcr))),
        # elif PID_NULL == pkt.pid:
        #     print 'Null Packet,',
        #
        # if pkt.pts >= 0:
        #     print 'PTS: %d(%s),' % (pkt.pts, timedelta(seconds=ts2second(pkt.pts))),
        # if pkt.dts >= 0:
        #     print 'DTS: %d(%s),' % (pkt.dts, timedelta(seconds=ts2second(pkt.dts))),
        #
        # if pkt.is_video():
        #     print 'Video',
        # elif pkt.is_audio():
        #     print 'Audio',
        #
        # print ''
        # print "\n"
        pass


def main():

    if os.path.exists(file_path_enc_cbc_h264):
        os.remove(file_path_enc_cbc_h264)

    try:
        ts_parser = TSParser(file_path_enc_cbc_ts)
        ts_parser.parse()
    except KeyboardInterrupt:
        print '\n^C received, Exit.'


if __name__ == '__main__':
    main()
    exit(0)
