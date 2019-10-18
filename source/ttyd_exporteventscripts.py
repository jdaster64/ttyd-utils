#! /usr/bin/python3.4

"""Exports EventScripts from diffs data using PistonMiner's ttydasm tool."""
# Jonathan "jdaster64" Aldrich 2019-09-30

import codecs
import os
import sys
import subprocess
import numpy as np
import pandas as pd

import jdalibpy.flags as flags
import ttyd_maplib

FLAGS = flags.Flags()
FLAGS.DefineString("input_diffs", "")
FLAGS.DefineString("input_ram_pattern", "")
FLAGS.DefineString("ttydasm_exe", "")
FLAGS.DefineString("ttydasm_symbols_pattern", "")
FLAGS.DefineString("output_dir", "")

class ExportEventScriptsError(Exception):
    def __init__(self, message=""):
        self.message = message
        
def _ParseScript(df_row):
    area = df_row["area"]
    sym_area = "tik" if area == "_MS" else area
    eventname = df_row["eventname"]
    symbol_file = FLAGS.GetFlag("ttydasm_symbols_pattern").replace("*",sym_area)
    outfile = codecs.open(
        os.path.join(
            FLAGS.GetFlag("output_dir"), "%s_%s.txt" % (area, eventname)
        ), "w", encoding="utf-8")
    print("Parsing event %s_%s" % (area, eventname,))
    subprocess.check_call([
        FLAGS.GetFlag("ttydasm_exe"),
        "--base-address=0x80000000",
        "--start-address=0x%x" % (df_row["address"],),
        "--symbol-file=%s" % (symbol_file,),
        FLAGS.GetFlag("input_ram_pattern").replace("*", sym_area)],
        stdout=outfile)
    outfile.flush()
            
def main(argc, argv):
    if not FLAGS.GetFlag("input_diffs"):
        raise ExportEventScriptsError("No input diffs CSV provided.")
    if not FLAGS.GetFlag("input_ram_pattern"):
        raise ExportEventScriptsError("No input ram filepattern provided.")
    if not FLAGS.GetFlag("output_dir"):
        raise ExportEventScriptsError("No output script directory provided.")
    if (not FLAGS.GetFlag("ttydasm_exe") or 
        not FLAGS.GetFlag("ttydasm_symbols_pattern")):
        raise ExportEventScriptsError(
            "Both ttydasm executable and symbol filepattern must be provided.")
        
    # Get a DataFrame of symbol information from the input diffs file.
    df = ttyd_maplib.GetSymbolInfoFromDiffsCsv(FLAGS.GetFlag("input_diffs"))
    
    # Store the name of the output event file in the dataframe.
    def get_event_name(row):
        if row["file"]:
            # TODO: Add an option to include area in the "uniqueness" key.
            return "%s_%s" % (row["file"][:-2], row["name"])
        else:
            return row["fullname"]
    
    # Keep only event scripts.
    df = df.loc[df["class"] == "EventScript_t"]
    df["eventname"] = df.apply(get_event_name, axis=1)
    # Remove non-events and deduplicate by event name.
    df.drop_duplicates(subset=["eventname"], inplace=True)
    # Sort by area and address for debugging convenience's sake.
    df.sort_values(["area", "address"], kind="mergesort", inplace=True)
        
    # Process each event using ttydasm.
    for idx, row in df.iterrows():
        _ParseScript(row)

if __name__ == "__main__":
    (argc, argv) = FLAGS.ParseFlags(sys.argv[1:])
    main(argc, argv)