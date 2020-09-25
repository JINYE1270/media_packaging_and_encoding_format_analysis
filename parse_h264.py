#!/usr/bin/env python
# -*-coding: utf-8 -*-
from avc import *
from crypto import *
from common import *
import os
import time

MAX_READ_H264_NUM = 10000
MAX_READ_H264_NUM_IDR_SLICE = 10000
MAX_H264_SLICE_LEN = 184
START_CODE = 0x00000001

# nal_unit_type
NALU_TYPE_SLICE = 1
NALU_TYPE_DPA = 2
NALU_TYPE_DPB = 3
NALU_TYPE_DPC = 4
NALU_TYPE_IDR = 5
NALU_TYPE_SEI = 6
NALU_TYPE_SPS = 7
NALU_TYPE_PPS = 8
NALU_TYPE_AUD = 9
NALU_TYPE_EOSEQ = 10
NALU_TYPE_EOSTREAM = 11
NALU_TYPE_FILL = 12
# NALU_TYPE_SLICE = 0x01
# NALU_TYPE_DPA = 0x02
# NALU_TYPE_DPB = 0x03
# NALU_TYPE_DPC = 0x04
# NALU_TYPE_IDR = 0x05
# NALU_TYPE_SEI = 0x06
# NALU_TYPE_SPS = 0x07
# NALU_TYPE_PPS = 0x08
# NALU_TYPE_AUD = 0x09
# NALU_TYPE_EOSEQ = 0x010
# NALU_TYPE_EOSTREAM = 0x011
# NALU_TYPE_FILL = 0x012

class H264RBSPParse:
    def __init__(self, buf):
        self.buf = buf
        self.nal_header = None
        self.sei = None
        self.uuid = None
        self.cei = None
        self.slice = None

    def parse(self):

        if self.buf:
            # 赋值nal类型
            self.nal_header = H264NALUHdrFixedPart.from_buffer_copy(self.buf[4:5])
            # print "nal_unit_type: ", self.nal_header.nal_unit_type

        if self.is_sei():
            self.sei = SEIMSGFixedPart.from_buffer_copy(self.buf[5:7])
            # 解析包含cei信息的sei
            if self.sei.last_payload_type_byte == 5:
                if self.sei.last_payload_size_byte >= 50:
                    self.__parse_sei()
                    # self.show_nalheaderinfo()
                    # self.show_ceiinfo()
                else:
                    output_dec_264_video(file_path_dec_cbc_h264, self.buf)
                    # print "+++write sei done!!!\n"
            else:
                output_dec_264_video(file_path_dec_cbc_h264, self.buf)
                # print "===write sei done!!!\n"
        elif self.is_slice_or_idr():
            buf_enc = self.__parse_slice_or_idr()
            # time1 = time.time()
            buf_dec = sm4_cbc_dec(buf_enc, key_data, iv_data)
            # time2 = time.time()
            # print "sm4_cbc_dec             : ", int(round((time2 - time1) * 1000))
            # print "buf_header:           ",
            # for b in self.buf[0:36]:
            #     print "%02X" % ord(b),
            # print ""
            # print "buf_dec:              ",
            # for b in range(0, 36):
            #     print "||",
            # for b in buf_dec:
            #     print "%02x" % int(b),
            # print ""
            dec_str = "".join([chr(b) for b in buf_dec])
            write_str = self.buf[0:36] + dec_str
            # print "write_str:            ",
            # for b in write_str:
            #     print "%02X" % ord(b),
            # print ""
            output_dec_264_video(file_path_dec_cbc_h264, write_str)
            # print "===write slice done!!!\n"
        else:
            output_dec_264_video(file_path_dec_cbc_h264, self.buf)
            # print "===write other done!!!\n"

        return True

    def is_sei(self):
        if self.nal_header.nal_unit_type == NALU_TYPE_SEI:
            return True
        else:
            return False

    def is_slice_or_idr(self):
        if self.nal_header.nal_unit_type == NALU_TYPE_SLICE or self.nal_header.nal_unit_type == NALU_TYPE_IDR:
            return True
        else:
            return False

    def __parse_sei(self):
        if self.buf:
            # 先做二义性替换
            buf_ = ambiguity_transformation(self.buf)
            # 解析cei信息
            # start code(4 bytes) + last_payload_type_byte(1 byte) + last_payload_size_byte(1 byte)
            self.uuid = buf_[7:23]
            # print "==uuid: ",
            # for i in range(7, 23):
            #     print "%02X" % ord(buf_[i]),
            # print ""
            self.cei = CEI_DATAFixedPart.from_buffer_copy(buf_[23:24])
            if self.cei.encryption_flag == 0x01:
                self.cei.current_key_id = buf_[24:40]
            if self.cei.next_key_id_flag == 0x01:
                self.cei.next_key_id = buf_[40:56]
            self.cei.IV_length = buf_[56:57]
            self.cei.IV = buf_[57:57 + ord(self.cei.IV_length)]
        else:
            print "sei data None!\n"

    def __parse_slice_or_idr(self):
        if self.buf:
            # 先做二义性替换，二义性替换部分为加密部分
            # time1 = time.time()
            buf_ = ambiguity_transformation(self.buf[36:])
            # time2 = time.time()
            # print "ambiguity_transformation: ", int(round((time2 - time1) * 1000))

            # 提取解密部分
            # start code(4 bytes) + NAL_unite_type_bit(1 bytes) + uncrypted_leader(31 bytes)
            # buf_enc = buf_[36:]
            buf_enc = buf_
            # print "After ambiguity transformation: ",
            # for b in buf_enc:
            #     print "%02X" % ord(b),
            # print ""
            return buf_enc
        else:
            print "idr or slice None!\n"
            return ""

    def show_nalheaderinfo(self):
        print '==============NAL Header=============='
        print 'forbidden_zero_bit:0x%X' % self.nal_header.forbidden_zero_bit
        print 'nal_ref_idc:0x%X' % self.nal_header.nal_ref_idc
        print 'nal_unit_type:0x%X' % self.nal_header.nal_unit_type

    def show_ceiinfo(self):
        if self.sei.last_payload_type_byte == 5:
            if self.sei.last_payload_size_byte >= 50:
                print '==============CEI=============='
                print 'encryption_flag:0x%X' % self.cei.encryption_flag
                print 'next_key_id_flag:0x%X' % self.cei.next_key_id_flag
                print 'reserved:0x%X' % self.cei.reserved
                if self.cei.encryption_flag == 0x01:
                    print "current_key_id: 0x",
                    for c in self.cei.current_key_id:
                        print "%02X" % ord(c),
                    print ""
                if self.cei.next_key_id_flag == 0x01:
                    print "next_key_id: 0x",
                    for n in self.cei.next_key_id:
                        print "%02X" % ord(n),
                    print ""
                print 'IV_length:0x%X' % ord(self.cei.IV_length)
                print "IV: 0x",
                for i in self.cei.IV:
                    print "%02X" % ord(i),
                print ""

class H264Parse:
    def __init__(self, file_path):
        self.file_path = file_path
        self.fd = None
        self.current_start_code_pos = 0
        self.h264_header = None

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

    def __seek_to_next_pes_start(self, current_start_code_pos):
        if current_start_code_pos is not None:
            try:
                self.fd.seek(current_start_code_pos)
                # 先读5个字节，用于获取当前的nal的类型
                buf_ = self.fd.read(5)
                if buf_:
                    # 赋值nal类型
                    self.h264_header = H264NALUHdrFixedPart.from_buffer_copy(buf_[4:5])
                    nal_unit_type = self.h264_header.nal_unit_type

                    # 根据nal类型，判断应该开多大的buffer
                    self.fd.seek(current_start_code_pos)
                    if nal_unit_type == NALU_TYPE_SLICE or nal_unit_type == NALU_TYPE_IDR:
                        buf = self.fd.read(MAX_READ_H264_NUM_IDR_SLICE * MAX_H264_SLICE_LEN)
                    else:
                        buf = self.fd.read(MAX_READ_H264_NUM * MAX_H264_SLICE_LEN)

                    if buf:
                        loop_num = len(buf)
                        for i in xrange(0, loop_num):
                            # 找到PES起始码
                            # print ord(buf[i]), ord(buf[i + 1]), ord(buf[i + 2]), ord(buf[i + 3])
                            if ord(buf[i]) == 0x00 and ord(buf[i + 1]) == 0x00 and ord(buf[i + 2]) == 0x00 and ord(
                                    buf[i + 3]) == 0x01:
                                current_start_code_pos = i + current_start_code_pos
                                # print "current_start_code_pos: ", i
                                # 找到下一个PES起始码
                                i += 1
                                while i < loop_num:
                                    if ord(buf[i]) == 0x00 and ord(buf[i + 1]) == 0x00 and ord(buf[i + 2]) == 0x00 and ord(
                                            buf[i + 3]) == 0x01:
                                        next_start_code_pos = i + current_start_code_pos
                                        # print "next_start_code_pos: ", i
                                        return next_start_code_pos
                                    else:
                                        i += 1
                else:
                    return "EXIT"

            except IOError as (errno, strerror):
                print '###### Read file error! error({0}): {1}'.format(errno, strerror)
        print "current_start_code_pos is None"
        return "EXIT"

    def parse_h264(self):
        self.__open_file()
        cur_pos = self.fd.tell()
        print 'Seek to first packet, offset: %d' % cur_pos

        count = 1
        self.current_start_code_pos = 0
        try:
            while True:
                # if count > 30:
                #     break
                # print "-----current_start_code_pos: ", self.current_start_code_pos
                # print "============================================================"
                # time1 = time.time()
                next_pes_start_code = self.__seek_to_next_pes_start(self.current_start_code_pos)
                # time2 = time.time()
                # print "seek_to_next_pes_start  : ", int(round((time2 - time1) * 1000))

                if next_pes_start_code == "EXIT":
                    break
                # print "-----next_pes_start_code: ", next_pes_start_code
                pes_len = 0
                if next_pes_start_code != 0:
                    pes_len = next_pes_start_code - self.current_start_code_pos
                self.fd.seek(self.current_start_code_pos)
                buf = self.fd.read(pes_len)
                if not buf:
                    break

                # print "The %d PES data part: " % count,
                # for b in buf:
                #     print "%02X" % ord(b),
                # print ""

                # print "The %d PES data part: " % count,
                # for b in buf[0:10]:
                #     print "%02X" % ord(b),
                # print ""
                h264rbsp = H264RBSPParse(buf)
                h264rbsp.parse()

                # count += 1
                self.current_start_code_pos += pes_len

            print 'Parse file complete!'
        except IOError as (errno, strerror):
            print '###### Read file error! error({0}): {1}'.format(errno, strerror)

        self.__close_file()

def main():

    if os.path.exists(file_path_dec_cbc_h264):
        os.remove(file_path_dec_cbc_h264)

    try:
        ts_parser = H264Parse(file_path_enc_cbc_h264)
        ts_parser.parse_h264()
    except KeyboardInterrupt:
        print '\n^C received, Exit.'


if __name__ == "__main__":
    main()
