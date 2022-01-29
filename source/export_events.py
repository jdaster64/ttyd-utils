#! /usr/bin/python3.6

"""Exports TTYD event scripts using PistonMiner's TTYDASM tool.

This file must be run after the following binaries, using the same --out_path:
- dump_sections.py (to generate section_info and linked section .raw files)
- symbol_to_maps.py (to generate ttydasm symbols)

Given a symbols .csv and a binary of PistonMiner's TTYDASM tool, this program
will then generate .txt dumps of all symbols with the type "evt", filling in
symbol references with the names (or values, for string typed symbols)
contained in the previously generated TTYDASM symbol maps."""
# Jonathan Aldrich 2021-02-09 ~ 2021-03-02

import codecs
import os
import sys
import numpy as np
import pandas as pd
import subprocess
from pathlib import Path

import jdalibpy.flags as flags

FLAGS = flags.Flags()

# Output directory; should contain these outputs from previous binaries:
# - Section_info and linked sections from dump_sections.py
# - Ttydasm symbol maps from symbol_to_maps.py
# Dumped events will go into "/events" dir underneath.
FLAGS.DefineString("out_path", "")
# Input symbols file.
FLAGS.DefineString("symbols_path", "")
# Path to TTYDASM binary.
FLAGS.DefineString("ttydasm_exe", "")

# Whether to display debug strings.
FLAGS.DefineInt("debug_level", 1)

class ExportEventsError(Exception):
    def __init__(self, message=""):
        self.message = message
    
def _LoadTtydasmPathDict(in_path, areas):
    """Constructs a dict of area name : ttydasm symbol paths."""
    if FLAGS.GetFlag("debug_level"):
        print("Loading ttydasm symbols...")        
    ttydasm_symbols = {}
    for area in areas:
        filepath = in_path / "ttydasm" / ("%s.sym" % area)
        if not os.path.exists(filepath):
            raise ExportEventsError(
                "You must first run symbol_to_maps.py using the same --out_path.")
        ttydasm_symbols[area] = str(filepath)
    return ttydasm_symbols

def _LoadSectionDataDict(in_path, section_info):
    """Constructs a dict of area/section : data filepath + ram base address."""
    if FLAGS.GetFlag("debug_level"):
        print("Loading section data...")
    
    section_data = {}
    for sec_id in (0, 1, 7, 8, 9, 10, 11, 12):
        dat_path = in_path / ("sections/_main/%02d.raw" % sec_id)
        ram_addr = int(section_info.loc[("_main", sec_id)]["ram_start"], 16)
        section_data["_main-%02d" % sec_id] = (str(dat_path), ram_addr)
        
    rels_dir = in_path / "sections/rel_linked"
    areas = [f.name for f in os.scandir(rels_dir) if f.is_dir()]
    for area in areas:
        for sec_id in range(1, 6):
            dat_path = rels_dir / area / ("%02d.raw" % sec_id)
            ram_addr = int(section_info.loc[(area, sec_id)]["ram_start"], 16)
            section_data["%s-%02d" % (area, sec_id)] = (str(dat_path), ram_addr)
    return section_data

def _ExportEvents(out_path, symbols, ttydasm_symbols, section_map):
    def _GetEventName(row):
        if row["type"] != "evt":
            return None
        # Strip namespace down to last object name without its extension.
        ns = row["namespace"].split(" ")[-1]
        if ns.find("."):
            ns = ns[:ns.find(".")]
        return "%s_%s_%s" % (row["area"], ns, row["name"])

    if FLAGS.GetFlag("debug_level"):
        print("Exporting events...")
        
    ttydasm_exe = FLAGS.GetFlag("ttydasm_exe")
    if not ttydasm_exe or not os.path.exists(Path(ttydasm_exe)):
        raise ExportEventsError("--ttydasm_exe must point to a valid binary.")
    if not os.path.exists(out_path / "events"):
        os.makedirs(out_path / "events")
        
    for (index, row) in symbols.iterrows():
        event_name = _GetEventName(row)
        if not event_name:
            continue
        if FLAGS.GetFlag("debug_level"):
            print("Processing %s..." % event_name)
        outfile = codecs.open(
            out_path / "events" / ("%s.txt" % event_name), "w", encoding="utf-8")
        (ram_filepath, base_address) = section_map[
            "%s-%02d" % (row["area"], row["sec_id"])]
        ram_addr = base_address + int(row["sec_offset"], 16)
        subprocess.check_call([
            str(Path(ttydasm_exe)),
            "--base-address=0x%08x" % base_address,
            "--start-address=0x%08x" % ram_addr,
            "--symbol-file=%s" % ttydasm_symbols[row["area"]],
            ram_filepath],
            stdout=outfile)
        outfile.flush()

def main(argc, argv):
    out_path = FLAGS.GetFlag("out_path")
    if not out_path or not os.path.exists(Path(out_path)):
        raise ExportEventsError("--out_path must point to a valid directory.")
    out_path = Path(out_path)
    
    if not os.path.exists(out_path / "section_info.csv"):
        raise ExportEventsError(
            "You must first run dump_sections.py using the same --out_path.")
    section_info = pd.read_csv(out_path / "section_info.csv")
    section_info = section_info.set_index(["area", "id"])
    
    symbols_path = FLAGS.GetFlag("symbols_path")
    if not symbols_path or not os.path.exists(Path(symbols_path)):
        raise ExportEventsError(
            "--symbols_path must point to a valid symbols csv.")
    symbols = pd.read_csv(Path(symbols_path))
    
    ttydasm_symbols =   _LoadTtydasmPathDict(out_path, symbols.area.unique())
    section_map =       _LoadSectionDataDict(out_path, section_info)
    _ExportEvents(out_path, symbols, ttydasm_symbols, section_map)

if __name__ == "__main__":
    (argc, argv) = FLAGS.ParseFlags(sys.argv[1:])
    main(argc, argv)
