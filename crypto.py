#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import sm4_d, DECRYPT

# SM4 CBC解密
def sm4_cbc_dec(buf, key, iv):
    if buf:
        buf_dec = None
        len_ = len(buf)
        res = len_ % 16
        # print "enc_buf_len:               ", len_
        # 最后 小于16bytes 不加密
        if res < 16:
            res_pos = len_ - res
            buf_enc = buf[:res_pos]
            buf_enc_list = [ord(b) for b in buf_enc]

            sm4_d.sm4_set_key(key, DECRYPT)
            dec_data = sm4_d.sm4_crypt_cbc(iv, buf_enc_list)

            # print "dec_data: ", dec_data
            for b in buf[res_pos:]:
                dec_data.append(int(ord(b)))
            buf_dec = dec_data
        # 最后 16bytes 不加密
        elif res == 0:
            res_pos = len_ - 16
            buf_enc = buf[:res_pos]
            buf_enc_list = [ord(b) for b in buf_enc]

            sm4_d.sm4_set_key(key, DECRYPT)
            dec_data = sm4_d.sm4_crypt_cbc(iv, buf_enc_list)

            # print "dec_data: ", dec_data
            for b in buf[res_pos:]:
                dec_data.append(int(ord(b)))
            buf_dec = dec_data

        # print "res buf: ",
        # for b in buf[res_pos:]:
        #     print int(ord(b)),
        # print ""
        # print "buf_dec : ", buf_dec
        return buf_dec


# 二义性替换
def ambiguity_transformation(buf):
    if buf:
        # print "ambiguity_transformation: ",
        # for b in buf:
        #     print "%02X" % ord(b),
        # print ""

        buf_ = buf
        len_ = len(buf)
        i = 0
        count_trans = 0

        while i < len_:
            if ord(buf[i]) == 0x00 and ord(buf[i + 1]) == 0x00 and ord(buf[i + 2]) == 0x03 and ord(buf[i + 3]) == 0x00:
                # print "00 00 03 00: ", i
                buf_ = buf_[:i - count_trans + 2] + buf_[i - count_trans + 3:]
                count_trans += 1
                # print "buf_                    : ",
                # for b in buf_:
                #     print "%02X" % ord(b),
                # print ""
                i += 4
            elif ord(buf[i]) == 0x00 and ord(buf[i + 1]) == 0x00 and ord(buf[i + 2]) == 0x03 and ord(buf[i + 3]) == 0x01:
                buf_ = buf_[:i - count_trans + 2] + buf_[i - count_trans + 3:]
                count_trans += 1
                i += 4
            elif ord(buf[i]) == 0x00 and ord(buf[i + 1]) == 0x00 and ord(buf[i + 2]) == 0x03 and ord(buf[i + 3]) == 0x02:
                buf_ = buf_[:i - count_trans + 2] + buf_[i - count_trans + 3:]
                count_trans += 1
                i += 4
            elif ord(buf[i]) == 0x00 and ord(buf[i + 1]) == 0x00 and ord(buf[i + 2]) == 0x03 and ord(buf[i + 3]) == 0x03:
                buf_ = buf_[:i - count_trans + 2] + buf_[i - count_trans + 3:]
                count_trans += 1
                i += 4
            else:
                i += 1

        # print "ambiguity_transformation: ",
        # for b in buf_:
        #     print "%02X" % ord(b),
        # print ""
        return buf_


# 生成解密后的.264文件
def output_dec_264_video(filepath, buf):
    if filepath and buf:
        # print "***buf", buf
        with open(filepath, "ab+") as f:
            f.write(buf)


def main():
    pass


if __name__ == "__main__":
    main()