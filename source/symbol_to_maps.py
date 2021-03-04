#! /usr/bin/python3.6

"""Creates symbol maps and ttydasm maps from a csv of symbol info.

This program takes a .csv of symbol information, and dumps the following:
- .MAP files for the .DOL and each .REL on its own
- Combined .MAP files per .REL area that include the .DOL symbols, 
  and the .REL symbols at their linked addresses.
- TTYDASM symbol map files per area (using linked addresses); will use the names
  of symbols if provided, or the literal value of symbols marked as strings."""
# Jonathan Aldrich 2021-02-09 ~ 2021-03-02

import codecs
import os
import sys
import numpy as np
import pandas as pd
from collections import defaultdict
from pathlib import Path

import jdalibpy.flags as flags

FLAGS = flags.Flags()

# Output directory (will create "maps" and "ttydasm" dirs underneath).
FLAGS.DefineString("out_path", "")
# Input symbols file.
FLAGS.DefineString("symbols_path", "")
# Rel bss location (if not provided, will not output REL .bss to combined maps.)
FLAGS.DefineInt("rel_bss_address")

# Whether to display debug strings.
FLAGS.DefineInt("debug_level", 1)

class SymbolToMapError(Exception):
    def __init__(self, message=""):
        self.message = message
        
def _GetOutputPath(path, create_parent=True):
    if create_parent and not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    return path
    
def _GetMapLines(symbols):
    """Returns a dict of area/sec name : list of lines for the map file."""
    res = defaultdict(list)
    rel_bss_addr = FLAGS.GetFlag("rel_bss_address")
    if FLAGS.GetFlag("debug_level"):
        print("Processing map lines...")
    for (index, row) in symbols.iterrows():
        if FLAGS.GetFlag("debug_level") and not index % 1000:
            print("Processing line %d..." % index)
        if row["area"] == "_main":
            text = "  %08x %08x %08x %2d %s\t%s\n" % (
                int(row["sec_offset"], 16), int(row["size"], 16), 
                int(row["ram_addr"], 16), int(row["align"]),
                row["name"], row["namespace"])
        else:
            if row["sec_type"] == "bss":
                if not rel_bss_addr:
                    continue
                ram_addr = rel_bss_addr + int(row["sec_offset"], 16)
            else:
                ram_addr = int(row["ram_addr"], 16)
            text = "  %08x %08x %08x %2d %s\t%s\n" % (
                int(row["sec_offset"], 16), int(row["size"], 16), 
                int(row["sec_offset"], 16), int(row["align"]),
                row["name"], row["namespace"])
            combined_text = "  %08x %08x %08x %2d %s\t%s\n" % (
                int(row["sec_offset"], 16), int(row["size"], 16), 
                ram_addr, int(row["align"]),
                row["name"], row["namespace"])
            res[(row["area"] + "_all", row["sec_name"])].append(combined_text)
        res[(row["area"], row["sec_name"])].append(text)
    return res
    
def _CreateMapFiles(out_path, map_lines, area):
    # Create a .MAP file with only symbols from the given area.
    lines = []
    sections = [
        ".init", ".ctors", ".dtors", ".rodata", ".data", ".bss", 
        ".sdata", ".sbss", ".sdata2", ".sbss2"]
    for section in sections:
        if (area, section) in map_lines:
            lines.append("%s section layout\n" % section)
            lines.append("  Starting          Virtual\n")
            lines.append("  address  Size     address\n")
            lines.append("  -------------------------\n")
            for line in map_lines[(area, section)]:
                lines.append(line)
            lines.append("\n")
    f = codecs.open(
        _GetOutputPath(out_path / "maps" / (area + ".map")), "w", "utf-8")
    for line in lines:
        f.write(line)
    # For RELs, also export .MAP files with .dol and .rel symbols included.
    if area == "_main":
        return
    lines = []
    for section in sections:
        lines.append("%s section layout\n" % section)
        lines.append("  Starting          Virtual\n")
        lines.append("  address  Size     address\n")
        lines.append("  -------------------------\n")
        for line in map_lines[("_main", section)]:
            if "rel_bss" not in line or not FLAGS.GetFlag("rel_bss_address"):
                lines.append(line)
        for line in map_lines[(area + "_all", section)]:
            lines.append(line)
        lines.append("\n")
    f = codecs.open(
        _GetOutputPath(out_path / "maps" / (area + "_all.map")), "w", "utf-8")
    for line in lines:
        f.write(line)

def _GetTtydasmLines(symbols):
    """Returns a dict of area : list of lines for the ttydasm symbols file."""
    res = defaultdict(list)
    if FLAGS.GetFlag("debug_level"):
        print("\nProcessing ttydasm lines...")
    for (index, row) in symbols.iterrows():
        if FLAGS.GetFlag("debug_level") and not index % 1000:
            print("Processing line %d..." % index)
        if row["area"] == "_main" or row["sec_name"] != ".bss":
            if ((row["name"][:4] == "str_" or row["name"][0] == "@")
                and row["type"] == "string"):
                # Use actual string in quotes, rather than name/namespace.
                name = '"%s"' % row["value"]
            else:
                name = "%s %s" % (row["name"], row["namespace"])
            text = "%08X:%s\n" % (int(row["ram_addr"], 16), name)
            res[(row["area"], row["sec_name"])].append(text)
    return res

def _CreateTtydasmFile(out_path, ttydasm_lines, area):
    lines = []
    for key in ttydasm_lines:
        if key[0] == area or key[0] == "_main":
            lines += ttydasm_lines[key]
    f = codecs.open(
        _GetOutputPath(out_path / "ttydasm" / (area + ".sym")), "w", "utf-8")
    for line in sorted(lines):
        f.write(line)

def main(argc, argv):
    in_path = FLAGS.GetFlag("symbols_path")
    if not os.path.exists(in_path):
        raise SymbolToMapError(
            "--symbols_path must be set to a valid CSV of symbols.")
    in_path = Path(in_path)
    
    out_path = FLAGS.GetFlag("out_path")
    if not out_path:
        raise SymbolToMapError("Must set an --out_path.")
    out_path = Path(out_path)
    
    symbols = pd.read_csv(in_path)
    map_lines = _GetMapLines(symbols)
    ttydasm_lines = _GetTtydasmLines(symbols)
    
    for area in symbols.area.unique():
        _CreateMapFiles(out_path, map_lines, area)
        _CreateTtydasmFile(out_path, ttydasm_lines, area)

if __name__ == "__main__":
    (argc, argv) = FLAGS.ParseFlags(sys.argv[1:])
    main(argc, argv)
