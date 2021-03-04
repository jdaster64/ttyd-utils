#! /usr/bin/python3.6

"""Converts .MAP files into tables of symbol + predicted type information.

This program takes in .MAP files for the .DOL and .RELs in a single version of
TTYD, and produces a single .csv containing the areas, names/namespaces,
section offsets and sizes of all contained symbols."""
# Jonathan Aldrich 2021-01-22 ~ 2021-03-04

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

import jdalibpy.flags as flags

FLAGS = flags.Flags()

# Input pattern for the TTYD demo DOL .MAP file and REL .MAP files.
# REL pattern must contain a single asterisk that matches the REL name.
FLAGS.DefineString("dol_map", "")
FLAGS.DefineString("rel_map", "")

# Output directory.
FLAGS.DefineString("out_path", "")

# Whether to display debug strings.
FLAGS.DefineInt("debug_level", 1)

class MapToSymbolError(Exception):
    def __init__(self, message=""):
        self.message = message
    
def _ProcessMap(filepath, area):
    def _CreateSymbolDf(area, sec_id, sec_name, sec_type, line):
        # TODO: Add local / global information? Needs to be parsed from header.
        columns = [
            "area", "sec_id", "sec_name", "sec_type",
            "name", "namespace", "sec_offset", "size", "align"
        ]
        
        tokens = list(filter(None, line.split()))
        # Not a symbol, or symbol is unused / size 0; return an empty DataFrame.
        if (len(tokens) < 6 or tokens[4][0] == "." or tokens[0] == "UNUSED" or 
            not int(tokens[1], 16)):
            return pd.DataFrame(columns=columns)
        
        name = tokens[4]
        namespace = " ".join(tokens[5:])
        sec_offset = tokens[0]
        size = "%08x" % (int(tokens[1], 16))
        alignment = int(tokens[3], 10)
        
        return pd.DataFrame([[
            area, sec_id, sec_name, sec_type,
            name, namespace, sec_offset, size, alignment
        ]], columns=columns)
            
    dol_sections = {
        ".init" : 0, ".text": 1, ".ctors": 7, ".dtors": 8,
        ".rodata": 9, ".data": 10, ".sdata": 11, ".sdata2": 12,
        ".bss": 100, ".sbss": 101, ".sbss2": 102
    }
    rel_sections = {
        ".text": 1, ".ctors": 2, ".dtors": 3,
        ".rodata": 4, ".data": 5, ".bss": 6
    }
        
    # Loop over file's lines, adding symbol information.
    dfs = []
    sec_id = -1
    for line in open(filepath).readlines():
        if "Memory map" in line:
            break
        elif "section layout" in line:
            sec_name = line[:line.find(" ")]
            if area == "_main":
                if sec_name in dol_sections:
                    sec_id = dol_sections[sec_name]
                    if sec_id < 7:
                        sec_type = "text"
                    elif sec_id < 100:
                        sec_type = "data"
                    else:
                        sec_type = "bss"
                else:
                    sec_id = -1
            else:
                if sec_name in rel_sections:
                    sec_id = rel_sections[sec_name]
                    if sec_id < 4:
                        sec_type = "text"
                    elif sec_id < 6:
                        sec_type = "data"
                    else:
                        sec_type = "bss"
                else:
                    sec_id = -1
            if sec_id != -1:
                if FLAGS.GetFlag("debug_level"):
                    print("Extracting symbols from %s%s..." % (area, sec_name))
        elif sec_id != -1:
            # In a supported section; create DataFrame from line.
            dfs.append(_CreateSymbolDf(area, sec_id, sec_name, sec_type, line))    
    
    df = pd.concat(dfs, ignore_index=True)
    df = df.set_index(["area", "sec_id", "sec_offset"])
    df = df.sort_index()
    return df

def main(argc, argv):
    out_path = Path(FLAGS.GetFlag("out_path"))
    if not out_path:
        raise MapToSymbolError("Must provide a directory for --out_path.")
    elif not os.path.exists(out_path):
        os.makedirs(out_path)
    
    # Create list of symbol_info dataframes to be later merged.
    symbol_info = []

    # Parse symbols from .DOL map.
    dol_path = Path(FLAGS.GetFlag("dol_map"))
    if not dol_path.exists():
        raise MapToSymbolError("--dol_map file does not exist." % version)
    symbol_info.append(_ProcessMap(dol_path, "_main"))
    
    # Parse symbols from .REL maps.
    rel_pattern = FLAGS.GetFlag("rel_map")
    normalized_pattern = str(Path(rel_pattern))
    # Verify exactly one asterisk wildcard exists.
    lpos = normalized_pattern.find("*")
    rpos = normalized_pattern.rfind("*")
    if lpos != rpos or lpos == -1:
        raise MapToSymbolError(
            "--rel_map pattern must contain exactly one wildcard asterisk.")
    # Verify any files are matched.
    if not Path(".").glob(rel_pattern):
        raise MapToSymbolError("--rel_map pattern matched no files.")
    # For each file, get the full path and the part of the string
    # that replaced the asterisk (which should be the area's name).
    for fn in sorted(Path(".").glob(rel_pattern)):
        # Skip the DOL's map if it matches the REL pattern.
        if fn == dol_path:
            continue
        filepath = str(fn)
        area = filepath[lpos:rpos+1-len(normalized_pattern)]
        symbol_info.append(_ProcessMap(filepath, area))
        
    if not len(symbol_info):
        raise MapToSymbolError("No DOLs or RELs were processed.")
    # Concatenate all areas' symbols into one DataFrame.
    df = pd.concat(symbol_info)
    df = df.sort_index()
    df.to_csv(out_path / "map_symbols.csv", encoding="utf-8")

if __name__ == "__main__":
    (argc, argv) = FLAGS.ParseFlags(sys.argv[1:])
    main(argc, argv)
