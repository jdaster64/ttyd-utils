#! /usr/bin/python3.4

"""Converts between various number and datetime formats."""
# Jonathan Aldrich 2016-09-03

import calendar
import ctypes
import datetime
import sys
import time

HELP_STRING = """Modes:
    hex2dec, dec2hex, hex2float, float2hex      - Numeric conversion
    unix2utc, utc2unix, date2unix, now2unix     - Datetime conversion"""
    
SYNONYMS = {
    "hex2dec": ["hex2dec", "h2d", "hd", "2d", "2dec", "dec", "d",],
    "dec2hex": ["dec2hex", "d2h", "dh", "2h", "2hex", "hex", "h", "x",],
    "hex2float": ["hex2float", "h2f", "hf", "2f", "float", "f",],
    "float2hex": ["float2hex", "f2h", "fh", "f2", "bits",],
    "unix2utc": ["unix2utc", "u2u", "utc", "2utc", "uu",],
    "utc2unix": ["unix2utc", "time", "time2", "timestamp", "ts", "tm", "t",],
    "date2unix": ["date2unix", "date", "date2", "day",],
    "now2unix": ["now2unix", "now2u", "n2u", "nu", "nows", "now", "today",],
    "help": ["help",],
}

def hex2dec(h):
    return int(h, 16)

def dec2hex(d):
    if d < (1 << 32):
        return "0x%08x" % d
    if d < (1 << 64):
        return "0x%016x" % d
    return "0x%x" % d

def hex2float(h):
    u = int(h, 16)
    up = ctypes.pointer(ctypes.c_uint32(u))
    fp = ctypes.cast(up, ctypes.POINTER(ctypes.c_float))
    return fp.contents.value

def float2hex(f):
    fp = ctypes.pointer(ctypes.c_float(f))
    up = ctypes.cast(fp, ctypes.POINTER(ctypes.c_uint32))
    return "0x%08x" % up.contents.value

def unix2utc(u):
    return (datetime.datetime.utcfromtimestamp(int(u))
            .strftime("%Y-%m-%d %H:%M:%S"))

def utc2unix(s):
    d = datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    return calendar.timegm(d.timetuple())

def date2unix(s):
    d = datetime.datetime.strptime(s, "%Y-%m-%d")
    return calendar.timegm(d.timetuple())
    
def now2unix():
    return int(time.time())
        
def main(argc, argv):
    if argc < 1: print(HELP_STRING)
    elif argv[0] in SYNONYMS["help"]: print(HELP_STRING)
    elif argc == 1:
        if argv[0] in SYNONYMS["now2unix"]: print(now2unix())
        else: print(HELP_STRING)
    elif argc > 1:
        if argv[0] in SYNONYMS["hex2dec"]: print(hex2dec(argv[1]))
        elif argv[0] in SYNONYMS["dec2hex"]: print(dec2hex(int(argv[1])))
        elif argv[0] in SYNONYMS["hex2float"]: print(hex2float(argv[1]))
        elif argv[0] in SYNONYMS["float2hex"]: print(float2hex(float(argv[1])))
        elif argv[0] in SYNONYMS["unix2utc"]: print(unix2utc(argv[1]))
        elif argv[0] in SYNONYMS["utc2unix"]: print(utc2unix(" ".join(argv[1:])))
        elif argv[0] in SYNONYMS["date2unix"]: print(date2unix(argv[1]))
        else: print(HELP_STRING)            

if __name__ == "__main__":
    main(len(sys.argv) - 1, sys.argv[1:])
