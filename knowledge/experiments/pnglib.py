# -*- coding: utf-8 -*-
"""极简 PNG 读取（支持 8bit RGB/RGBA/灰度），供截图像素分析复用。"""
import struct, zlib

def read_png(path):
    data = open(path, 'rb').read()
    pos = 8; w = h = 0; idat = b''; bpp = 3
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos+4])[0]
        tag = data[pos+4:pos+8]
        if tag == b'IHDR':
            w, h, bit, ctype = struct.unpack('>IIBB', data[pos+8:pos+18])
            assert bit == 8
            bpp = {0:1, 2:3, 4:2, 6:4}[ctype]
        elif tag == b'IDAT':
            idat += data[pos+8:pos+8+ln]
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * bpp
    img = []
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]; p += 1
        row = bytearray(raw[p:p+stride]); p += stride
        if f == 1:
            for i in range(bpp, stride):
                row[i] = (row[i] + row[i-bpp]) & 255
        elif f == 2:
            for i in range(stride):
                row[i] = (row[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = row[i-bpp] if i >= bpp else 0
                row[i] = (row[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = row[i-bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i-bpp] if i >= bpp else 0
                pp = a + b - c
                pa, pb, pc = abs(pp-a), abs(pp-b), abs(pp-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[i] = (row[i] + pr) & 255
        prev = row
        img.append(row)
    return w, h, bpp, img

def gray(img, x, y, bpp):
    o = x * bpp
    if bpp == 1:
        return img[y][o]
    return (img[y][o] + img[y][o+1] + img[y][o+2]) // 3
