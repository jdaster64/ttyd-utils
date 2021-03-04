#! /usr/bin/python3.4

"""Generates symbol maps given input diffs, in standard or ttydasm format."""
# Jonathan "jdaster64" Aldrich 2019-09-29

import codecs
import os
import sys
import re
import numpy as np
import pandas as pd

import jdalibpy.flags as flags
import ttyd_maplib

FLAGS = flags.Flags()
# Filepath to a file in the format of REPO/resources/ttyd_*_symboldiffs_*.csv.
FLAGS.DefineString("input_diffs", "")
# Filepath to a ttydasm symbol file to combine with the symbols generated from
# the diffs file.
FLAGS.DefineString("input_ttydasm_symbase", "")
# Output directory for MAP files.
FLAGS.DefineString("output_maps_dir", "")
# Output directory for ttydasm symbol files.
FLAGS.DefineString("output_ttydasm_maps_dir", "")

class GenerateSymbolMapsError(Exception):
    def __init__(self, message=""):
        self.message = message
            
def main(argc, argv):
    if not FLAGS.GetFlag("input_diffs"):
        raise GenerateSymbolMapsError("No input diffs CSV provided.")
    if (not FLAGS.GetFlag("output_maps_dir") and 
        not FLAGS.GetFlag("output_ttydasm_maps_dir")):
        raise GenerateSymbolMapsError(
            "Neither a standard nor ttydasm output dir provided.")
        
    # Get a DataFrame of symbol information from the input diffs file.
    df = ttyd_maplib.GetSymbolInfoFromDiffsCsv(FLAGS.GetFlag("input_diffs"))
    
    # Store symbol info in map file and ttydasm map file formats in dataframe.
    def get_mapfile_row(row):
        return "0x%08x 0x%06x 0x%08x 0 %s\n" % (
            row["address"], row["length"], row["address"], row["fullname"])
    def get_ttydasm_row(row):
        return "%08X:%s\n" % (row["address"], row["fullname"])
    
    df["maprow"] = df.apply(get_mapfile_row, axis=1)
    df["ttydasmrow"] = df.apply(get_ttydasm_row, axis=1)
    
    # Sort by section and remove duplicate symbol addresses in the same area.
    sections = [".text", ".rodata", ".data", ".sdata"]
    df["section"] = pd.Categorical(df["section"], sections)
    df.sort_values(["area", "section"], kind="mergesort", inplace=True)
    # Probably can be removed; artifact of when this supported a base map.
    df.drop_duplicates(subset=["area", "fullname", "address"], inplace=True)
    
    # Output standard maps for the DOL & each REL represented in the diffs file.
    for area in df.area.unique():
        print("Generating symbol map file for %s..." % (area,))
        
        filename = "boot.map" if area == "_MS" else "%s.map" % (area,)
        outfile = open(
            os.path.join(FLAGS.GetFlag("output_maps_dir"), filename), "w")
        df_area = df.loc[df["area"].isin(["_MS", area])]
        for section in sections:
            df_section = df_area.loc[df_area["section"] == section]
            if len(df_section.index) > 0:
                outfile.write("%s section layout\n" % (section,))
                for text in df_section["maprow"]:
                    outfile.write(text)
                outfile.write("\n")
    
    # Sort by area and address only, regardless of section for ttydasm symbols.
    df.sort_values(["area", "address"], kind="mergesort", inplace=True)
    
    # Output ttydasm maps for the DOL & each REL represented in the diffs file.
    for area in df.area.unique():
        print("Generating ttydasm symbols for %s..." % (area,))
    
        filename = "%s.sym" % ("Start_us" if area == "_MS" else area,)
        outfile = codecs.open(os.path.join(
            FLAGS.GetFlag("output_ttydasm_maps_dir"), filename), 
            "w", encoding="utf-8")
            
        # Deduplicate with base ttydasm symbols. (TODO: Clean this up!)
        symbols = []
        if FLAGS.GetFlag("input_ttydasm_symbase"):
            for sym in codecs.open(
                FLAGS.GetFlag("input_ttydasm_symbase"), "r", encoding="utf-8"
            ).readlines():
                symbols.append(sym)
        base_symbol_addresses = [sym[:sym.find(":")] for sym in symbols]
        
        df_area = df.loc[df["area"].isin(["_MS", area])]
        for sym in df_area["ttydasmrow"]:
            if sym[:sym.find(":")] not in base_symbol_addresses:
                symbols.append(sym)
                
        for sym in sorted(symbols):
            outfile.write(sym)

if __name__ == "__main__":
    (argc, argv) = FLAGS.ParseFlags(sys.argv[1:])
    main(argc, argv)