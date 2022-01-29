#! /usr/bin/python3.6

"""Dumps fields / byte representation of objects of given types from TTYD.

This file must be run after dump_sections.py using the same --out_path.

Given a symbols .csv annotated with type information, will export the fields
and raw byte representations of all instances of the class types defined in
export_classes_parsers.py."""
# Jonathan Aldrich 2021-03-03 ~ 2021-03-04

import codecs
import os
import sys
import numpy as np
import pandas as pd
from collections import defaultdict
from pathlib import Path

from export_classes_parsers import *
import jdalibpy.bindatastore as bd
import jdalibpy.flags as flags

FLAGS = flags.Flags()

# Output directory; should contain the outputs from dump_sections.py beforehand.
# Dumped object info will go into "/classes" and "/classes_raw" dirs underneath.
FLAGS.DefineString("out_path", "")
# Input symbols file.
FLAGS.DefineString("symbols_path", "")

# Whether to display debug strings.
FLAGS.DefineInt("debug_level", 1)

class ExportClassesError(Exception):
    def __init__(self, message=""):
        self.message = message
        
def _GetOutputPath(path, create_parent=True):
    if create_parent and not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    return path
    
def _LoadSectionRamAddrDict(in_path, section_info):
    """Constructs a dict of REL/section : ram base address."""
    if FLAGS.GetFlag("debug_level"):
        print("Loading section ram addresses...")
    
    section_info = section_info.set_index(["area", "id"])
        
    section_data = {}
    for sec_id in range(8, 13):
        ram_addr = int(section_info.loc[("_main", sec_id)]["ram_start"], 16)
        section_data["_main-%02d" % sec_id] = ram_addr
    
    rels_dir = in_path / "sections/rel_linked"
    areas = [f.name for f in os.scandir(rels_dir) if f.is_dir()]
    for area in areas:
        for sec_id in range(4, 6):
            ram_addr = int(section_info.loc[(area, sec_id)]["ram_start"], 16)
            section_data["%s-%02d" % (area, sec_id)] = ram_addr
    return section_data
        
def _LoadSectionDataDict(out_path, section_info):
    """Constructs a dict of area name : BDStore of that area's data sections."""
    if FLAGS.GetFlag("debug_level"):
        print("Loading section data...")
        
    res = defaultdict(lambda: bd.BDStore(big_endian=True))
    areas = list(section_info.area.unique())
    for (index, row) in section_info.iterrows():
        if row["type"] != "data":
            continue
        if row["area"] == "_main":
            # Include data sections from _main in all areas' BDStores.
            for area in areas:
                path = out_path / "sections/_main" / ("%02d.raw" % row["id"])
                res[area].RegisterFile(path, offset=int(row["ram_start"], 16))
        else:
            # Otherwise, include only in this area's BDStore.
            area = row["area"]
            path = out_path / "sections/rel_linked" / (
                "%s/%02d.raw" % (area, row["id"]))
            res[area].RegisterFile(path, offset=int(row["ram_start"], 16))
    return res
    
def _GetSymbolsToDump(symbol_table, section_addrs):
    """Creates a table of symbols to dump w/ export_classes_parsers."""
    if FLAGS.GetFlag("debug_level"):
        print("Finding symbols to dump...")
        
    columns = ["area", "name", "namespace", "address", "type"]
    data = []
    # Load struct defs from export_classes_parsers.
    struct_defs = GetStructDefs()
    for (index, row) in symbol_table[symbol_table.sec_type == "data"].iterrows():
        # No type / unsupported type, skip.
        if row["type"] not in struct_defs:
            continue
        type_def = struct_defs[row["type"]]
        
        # See how many instances there are, if the type can appear in arrays.
        arr_count = type_def.array
        if arr_count == SINGLE_INSTANCE:
            arr_count = 1
        elif arr_count == ZERO_TERMINATED:
            # If array is a single null entry, dump it, otherwise ignore it.
            arr_count = max(int(row["size"], 16) // type_def.size - 1, 1)
        elif arr_count == UNKNOWN_LENGTH:
            arr_count = int(row["size"], 16) // type_def.size
            
        # Add a row to the output dataframe per instance.
        ram_addr = section_addrs[
            "%s-%02d" % (row["area"], row["sec_id"])
        ] + int(row["sec_offset"], 16)
        for x in range(arr_count):
            name = row["name"]
            # Append the hexadecimal index in the array, if > 1 instance.
            if arr_count > 1:
                name += ("_%02x" if arr_count <= 256 else "_%03x") % x
            # Add to the output dataframe.
            data.append([
                row["area"], name, row["namespace"],
                ram_addr + x * type_def.size, row["type"]])
            # Add substructures to output dataframe, if necessary.
            # TODO: Implement support for recursive substructures?
            if type_def.substructs is None:
                continue
            for subtype_def in type_def.substructs:
                subname = name + "_" + subtype_def.name
                subtype_ram_addr = ram_addr + subtype_def.offset
                data.append([
                    row["area"], subname, row["namespace"],
                    subtype_ram_addr, subtype_def.datatype])
    
    return pd.DataFrame(data, columns=columns)
    
def _CreateSymbolLookupTable(symbol_table, symbols_to_dump):
    """Creates a table for replacing pointer fields w/what they point to."""
    if FLAGS.GetFlag("debug_level"):
        print("Creating symbol lookup table...")
        
    # Filter out bss symbols, and add numeric "address" column.
    symbol_table = symbol_table[symbol_table.sec_type != "bss"].copy()
    symbol_table["address"] = symbol_table["ram_addr"].apply(lambda x: int(x,16))
    # Filter to only necessary columns.
    symbol_table = pd.DataFrame(symbol_table, columns=[
        "area", "name", "namespace", "address", "type"])
    # Add symbols from symbols_to_dump, removing existing matches if necessary.
    lookup_table = pd.concat([symbol_table, symbols_to_dump])
    lookup_table = lookup_table.drop_duplicates(
        keep="last", subset=["area", "address"])
    # Index by area + address for easy lookup.
    return lookup_table.set_index(["area", "address"])
    
def _DumpSymbols(out_path, symbols_to_dump, lookup_table, stores):
    """Dumps all symbols of supported types to .csv files in out_path."""
    for classtype in sorted(symbols_to_dump.type.unique()):
        if FLAGS.GetFlag("debug_level"):
            print("Dumping instances of %s..." % classtype)
        
        dfs = []
        dfs_raw = []
        # Dump each instance of the class, both to fields and raw bytes.
        instances = symbols_to_dump.loc[symbols_to_dump["type"] == classtype]
        for (index, row) in instances.iterrows():
            view = stores[row["area"]].view(row["address"])
            dfs.append(ParseClass(view, row, lookup_table))
            dfs_raw.append(ParseClassRawBytes(view, row))
        # Merge dataframes and save to .csv files.
        pd.concat(dfs).to_csv(
            _GetOutputPath(out_path / "classes" / (classtype + ".csv")),
            encoding="utf-8", index=False)
        pd.concat(dfs_raw).to_csv(
            _GetOutputPath(out_path / "classes_raw" / (classtype + ".csv")),
            encoding="utf-8", index=False)

def main(argc, argv):
    out_path = FLAGS.GetFlag("out_path")
    if not out_path or not os.path.exists(Path(out_path)):
        raise ExportClassesError("--out_path must point to a valid directory.")
    out_path = Path(out_path)
    
    if not os.path.exists(out_path / "section_info.csv"):
        raise ExportClassesError(
            "You must first run dump_sections.py using the same --out_path.")
    section_info = pd.read_csv(out_path / "section_info.csv")
            
    symbols_path = FLAGS.GetFlag("symbols_path")
    if not symbols_path or not os.path.exists(Path(symbols_path)):
        raise ExportClassesError(
            "--symbols_path must point to a valid symbols csv.")
    symbol_table = pd.read_csv(Path(symbols_path))
    
    # Create inputs necessary for dumping symbols.
    
    section_addrs   = _LoadSectionRamAddrDict(out_path, section_info)
    symbols_to_dump = _GetSymbolsToDump(symbol_table, section_addrs)
    lookup_table    = _CreateSymbolLookupTable(symbol_table, symbols_to_dump)
    stores          = _LoadSectionDataDict(out_path, section_info)
    
    _DumpSymbols(out_path, symbols_to_dump, lookup_table, stores)
    

if __name__ == "__main__":
    (argc, argv) = FLAGS.ParseFlags(sys.argv[1:])
    main(argc, argv)
