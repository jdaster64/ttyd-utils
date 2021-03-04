#! /usr/bin/python3.6

"""Annotates the result of map_to_symbols with heuristic type information.

This file must be run after the following binaries, using the same --out_path:
- dump_sections.py (to generate section_info and linked section .raw files)
- map_to_symbols.py (to generate map_symbols.csv)

This program augments the output of map_to_symbols.py, adding file-level and
RAM addresses of the identified symbols, as well as heuristically predicted
common types (e.g. floats, strings, pointers, TTYD evts) and values."""
# Jonathan Aldrich 2021-01-26 ~ 2021-03-04

import codecs
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

import jdalibpy.bindatastore as bd
import jdalibpy.flags as flags

FLAGS = flags.Flags()

# Output directory; should contain these outputs from previous binaries:
# - Section_info and linked sections from dump_sections.py
# - map_symbols.csv file from map_to_symbols.py
# Annotated symbols will be saved to /annotated_symbols.csv.
FLAGS.DefineString("out_path", "")

# Whether to display debug strings.
FLAGS.DefineInt("debug_level", 1)

class AnnotateMapSymbolsError(Exception):
    def __init__(self, message=""):
        self.message = message
        
def _InferType(view, size, exact):
    """Uses simple heuristics to try to determine the type/value of a symbol."""
    def _IsFloatCompatible(view, offset=0):
        u32 = view.ru32(offset)
        # Either 0.0 or in range +/- 1e-7 to 1e7.
        return not u32 or (0x33d6bf95 <= (u32 & 2**31-1) <= 0x4b189680)
        
    def _IsDoubleCompatible(view, offset=0):
        u64 = view.ru64(offset)
        # Either 0.0 or in range +/- 1e-7 to 1e7.
        return not u64 or (
            0x3e7ad7f29abcaf48 <= (u64 & 2**63-1) <= 0x416312d000000000)
            
    def _IsPointerCompatible(view, offset=0):
        u32 = view.ru32(offset)
        # Either 0.0 or in slightly reduced range of valid pointers
        # (the range is reduced so as to not be ambiguous w/valid Shift-JIS).
        return not u32 or (0x80000000 <= u32 < 0x81400000)
        
    def _IsEvtCompatible(view, size, exact):
        offset = 0
        last_command = -1
        while offset < size:
            command = view.ru32(offset)
            # Each command must be between 0x1 and 0x77.
            if not (1 <= command & 0xffff <= 0x77):
                return False
            # Must end in 00000002, 00000001 (RETURN, END).
            if last_command == 2 and command == 1:
                if not exact:
                    return True
                # Verify that this is the exact end of the evt command array.
                return offset + 4 == size
            # Advance by 4 bytes, plus 4 per argument to the evt command.
            offset += (command >> 16) * 4 + 4
            last_command = command
        # Reached maximum length of symbol without finding the end of an event.
        return False
            
    def _IsShiftJisCompatible(view, size, exact):
        offset = 0
        while offset < size:
            b = view.ru8(offset)
            if b == 0:
                # If not exactly at the end of the string, return False.
                if exact and offset + 1 != size:
                    return False
                # End of string; double-check for false multi-byte sequences.
                try:
                    s = codecs.decode(view.rcstring(0), "shift-jis")
                except:
                    return False
                # String should be technically valid, but make sure
                # that string isn't empty or a likely false positive.
                return not (view.rcstring(0) in (b"", b"\x40", b"C0"))
            elif 0x20 <= b < 0x7f or b in (9, 10, 13):
                # Printable one-byte sequence.
                offset += 1
            elif 0x81 <= b < 0xa0 or 0xe0 <= b <= 0xea or 0xed <= b <= 0xef:
                if offset + 1 == size:
                    return False
                # Valid multi-byte sequence.
                b2 = view.ru8(offset + 1)
                if not 0x40 <= b2 <= 0xfc:
                    return False
                offset += 2
            else:
                return False
        return False
        
    def _SanitizeString(s):
        s = s.replace("\\", "\\\\")
        s = s.replace("\t", "\\t")
        s = s.replace("\n", "\\n")
        s = s.replace("\r", "\\r")
        return s

    bs = view.rbytes(size)
    # Check most restrictive types first: valid evts, common float constants, 
    # Shift-JIS compatible strings of the exact length of the symbol.
    if exact and size & 3 == 0 and _IsEvtCompatible(view, size, exact=True):
        return ("evt", "")
    if size == 8 and view.ru64() == 0x4330000080000000:
        return ("double", "to-int")
    if size == 8 and view.ru64() == 0x4330000000000000:
        return ("double", "to-int-mask")
    if exact and _IsShiftJisCompatible(view, size, exact=True):
        s = codecs.decode(view.rcstring(), "shift-jis")
        return ("string", _SanitizeString(s))
    # If all zero bytes, return "zero".
    if sum(bs) == 0:
        return ("zero", 0.0)
    # Check for reasonable-looking floating-point, pointer, or vec3 values.
    if size == 4 and _IsFloatCompatible(view):
        return ("float", view.rf32())
    if size == 8 and _IsDoubleCompatible(view):
        return ("double", view.rf64())
    if size == 4 and _IsPointerCompatible(view):
        return ("pointer", "%08x" % view.ru32())
    if size == 12:
        if (_IsFloatCompatible(view, 0) and _IsFloatCompatible(view, 4) and
            _IsFloatCompatible(view, 8)):
            return ("vec3", "%f, %f, %f" % (
                view.rf32(0), view.rf32(4), view.rf32(8)))
    # Look for arbitrary floating-point arrays or non-exact-length evts/strings;
    # these are more likely to be false positives.
    if size & 3 == 0:
        if _IsEvtCompatible(view, size, exact=False):
            return ("evt", "")
        # TODO: Improve heuristics for detecting float arrays vs. strings?
        is_valid = True
        for offset in range(0, size, 4):
            if not _IsFloatCompatible(view, offset):
                is_valid = False
                break
        if is_valid:
            return ("floatarr", "")
        is_valid = True
        for offset in range(0, size, 4):
            if not _IsPointerCompatible(view, offset):
                is_valid = False
                break
        if is_valid:
            return ("pointerarr", "")
    if _IsShiftJisCompatible(view, size, exact=False):
        s = codecs.decode(view.rcstring(), "shift-jis")
        return ("string", _SanitizeString(s))
    # Not obviously compatible with any common types.
    return (None, None)
    
def _AnnotateSymbols(symbols, section_info, out_path):
    def _AddSectionInfoFields(s, section_info):
        section = section_info.loc[(s["area"], s["sec_id"])]
        s["sec_name"] = section["name"]
        s["sec_type"] = section["type"]
        ram_addr = section["ram_start"]
        s["ram_addr"] = (
            "%08x" % (int(ram_addr, 16) + int(s["sec_offset"], 16))
            if isinstance(ram_addr, str) and ram_addr else np.nan
        )
        file_addr = section["file_start"]
        s["file_addr"] = (
            "%08x" % (int(file_addr, 16) + int(s["sec_offset"], 16))
            if isinstance(file_addr, str) and file_addr else np.nan
        )
        return s
    
    def _InferSymbolType(s, stores):
        # Not a data symbol.
        if s["sec_type"] != "data":
            return s
        # Symbol's section was not dumped, or out of range.
        section_lookup = "%s-%02d" % (s["area"], s["sec_id"])
        if section_lookup not in stores:
            return s
        offset = int(s["sec_offset"], 16)
        if offset < 0:
            return s
        # Otherwise, infer the type and value of the symbol, if possible.
        view = stores[section_lookup].view(offset)
        (t, v) = _InferType(view, int(s["size"], 16), exact=True)
        if t:
            s["type"] = t
            s["value"] = v
        return s

    # Create a copy of the symbols DataFrame with the desired output columns.
    df = pd.DataFrame(symbols, columns=[
        "area", "sec_id", "sec_offset", "sec_name", "sec_type", "ram_addr",
        "file_addr", "name", "namespace", "size", "align", "type", "value"])
    
    # Load previously dumped .DOL / .REL file sections into BDStores.
    stores = {}
    for sec_id in (0, 1, 7, 8, 9, 10, 11, 12):
        section_path = "sections/_main/%02d.raw" % sec_id
        store = bd.BDStore(big_endian=True)
        store.RegisterFile(out_path / section_path, offset=0)
        stores["_main-%02d" % sec_id] = store
    
    rels_dir = out_path / "sections/rel_linked"
    areas = [f.name for f in os.scandir(rels_dir) if f.is_dir()]
    for area in areas:
        for sec_id in range(1,6):
            store = bd.BDStore(big_endian=True)
            store.RegisterFile(rels_dir / area / ("%02d.raw" % sec_id), offset=0)
            stores["%s-%02d" % (area, sec_id)] = store
    
    # Fill in remaining columns based on section_info and dumped sections.
    if FLAGS.GetFlag("debug_level"):
        print("Converting section offsets to ram/file addresses...")
    df = df.apply(
        lambda s: _AddSectionInfoFields(s, section_info), axis=1)
        
    if FLAGS.GetFlag("debug_level"):
        print("Inferring symbol types...")
    df = df.apply(lambda s: _InferSymbolType(s, stores), axis=1)
    
    # Output the final table of joined symbols.
    df.to_csv(out_path / "annotated_symbols.csv", index=False)

def main(argc, argv):
    out_path = FLAGS.GetFlag("out_path")
    if not out_path or not os.path.exists(Path(out_path)):
        raise AnnotateMapSymbolsError(
            "--out_path must point to a valid directory.")
    out_path = Path(out_path)
    
    if not os.path.exists(out_path / "section_info.csv"):
        raise AnnotateMapSymbolsError(
            "You must first run dump_sections.py using the same --out_path.")
    section_info = pd.read_csv(out_path / "section_info.csv")
    section_info = section_info.set_index(["area", "id"])
    
    if not os.path.exists(out_path / "map_symbols.csv"):
        raise AnnotateMapSymbolsError(
            "You must first run map_to_symbols.py using the same --out_path.")
    symbols = pd.read_csv(out_path / "map_symbols.csv")
    
    _AnnotateSymbols(symbols, section_info, out_path)

if __name__ == "__main__":
    (argc, argv) = FLAGS.ParseFlags(sys.argv[1:])
    main(argc, argv)
