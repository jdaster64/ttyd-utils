#! /usr/bin/python3.6

"""Dumps information regarding individual sections of TTYD DOL and REL files.

Takes input DOL and REL files, and dumps the following information:
- Each section, unlinked and linked for RELs
- Each entire file, unlinked and linked for RELs
- A .csv containing information on section ids, types, addresses and lengths."""
# Jonathan Aldrich 2021-01-18 ~ 2021-03-02

import glob
import math
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

import jdalibpy.bindatastore as bd
import jdalibpy.flags as flags

FLAGS = flags.Flags()

# Output directory.
FLAGS.DefineString("out_path", "")

# Input patterns for .DOL and .REL files for a single version of TTYD.
# REL pattern must contain a single asterisk that matches the REL's area name.
FLAGS.DefineString("dol", "")
FLAGS.DefineString("rel", "")

# Base address to use for linked RELs; must be in range [0x80000000, 0x81000000)
# or 0. If set to 0, will not output linked versions of the REL files/sections.
FLAGS.DefineInt("link_address", 0x80600000)
# Base addresses to use for specific RELs, specified as comma-delimited
# rel_name:HEX_ADDRESS pairs; e.g. "jon:80c779a0,gor:805ba9a0".
# Falls back to the value in --link_address if unspecified.
FLAGS.DefineString("link_address_overrides", "")
# Base address to use for REL bss sections; must be set in range
# [0x80000000, 0x81000000) if --link_address is non-zero.
FLAGS.DefineInt("rel_bss_address", 0x80a00000)

# Whether to display debug strings when each file starts being processed.
FLAGS.DefineInt("debug_level", 1)

class DumpSectionsError(Exception):
    def __init__(self, message=""):
        self.message = message
        
def _GetOutputPath(filepath, create_parent=True):
    path = Path(FLAGS.GetFlag("out_path")) / filepath
    if create_parent and not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    return path
        
def _LookupSymbolAddress(store, link_address, module_id, section_id, addend):
    if module_id > 0:
        section_table = store.view(0)[0x10]
        section_addr = section_table.ru32(section_id * 8) & ~3
        if section_addr:
            return link_address + section_addr + addend
        else:
            return FLAGS.GetFlag("rel_bss_address") + addend
    else:
        return addend
        
def _LinkRelImpEntry(store, link_address, rel_table, module_id):
    section_view = None
    current_section = 0
    section_offset = 0
    while True:
        offset = rel_table.ru16(0)
        type = rel_table.ru8(2)
        section = rel_table.ru8(3)
        addend = rel_table.ru32(4)
        if type == 203:
            break
        elif type == 202:
            current_section = section
            section_table = store.view(0)[0x10]
            section_addr = section_table.ru32(section * 8) & ~3
            section_view = store.view(section_addr)
            section_offset = 0
        else:
            section_offset += offset
            symbol_addr = _LookupSymbolAddress(
                store, link_address, module_id, section, addend)
            relocation_addr = link_address + section_addr + section_offset
            
            if type == 1:
                # Write the symbol's 32-bit address.
                section_view.w32(symbol_addr, section_offset)
            elif type == 2:
                # Write the symbol's 24-bit address / 4 shifted up two bits.
                mask = 0xFFFFFC
                value = section_view.ru32(section_offset) & ~mask
                value |= (symbol_addr & mask)
                section_view.w32(value, section_offset)
            elif type == 3:
                # Write the symbol's 16-bit address.
                section_view.w16(symbol_addr, section_offset)
            elif type == 4:
                # Write the low 16 bits of the symbol address.
                section_view.w16(symbol_addr, section_offset)
            elif type == 5:
                # Write the high 16 bits of the symbol address.
                section_view.w16(symbol_addr >> 16, section_offset)
            elif type == 6:
                # Write the high 16 bits of the symbol address + 0x8000.
                section_view.w16((symbol_addr + 0x8000) >> 16, section_offset)
            elif 7 <= type <= 9:
                # Write the symbol's 14-bit address / 4 shifted up two bits.
                mask = 0x3FFC
                value = section_view.ru32(section_offset) & ~mask
                value |= (symbol_addr & mask)
                section_view.w32(value, section_offset)
            elif type == 10:
                # Write the 24-bit address minus the relocation address,
                # divided by four and shifted up two bits.
                mask = 0xFFFFFC
                value = section_view.ru32(section_offset) & ~mask
                value |= ((symbol_addr - relocation_addr) & mask)
                section_view.w32(value, section_offset)
            elif 11 <= type <= 13:
                # Write the 14-bit address minus the relocation address,
                # divided by four and shifted up two bits.
                mask = 0x3FFC
                value = section_view.ru32(section_offset) & ~mask
                value |= ((symbol_addr - relocation_addr) & mask)
                section_view.w32(value, section_offset)
        # Advance to next relocation entry.
        rel_table = rel_table.at(8)

def _LinkRel(store, link_address):
    header = store.view(0)
    imp_table = header[0x28]
    imp_size = header.ru32(0x2c)
    imp_offset = 0
    while imp_offset < imp_size:
        module_id = imp_table.ru32(imp_offset)
        rel_table = imp_table[imp_offset + 4]
        _LinkRelImpEntry(store, link_address, rel_table, module_id)
        imp_offset += 8

def _ProcessRel(area, filepath, link_address):
    def _CreateSectionDf(id, name, area, link_address, columns, section_tbl):
        file_start = section_tbl.ru32(8 * id) & ~3
        size = section_tbl.ru32(8 * id + 4)
        type = "data" if id > 3 else "text"
        if file_start == 0:
            type = "bss"
            file_start = np.nan
            file_end = np.nan
            ram_start = np.nan
            ram_end = np.nan
        else:
            ram_start = file_start + link_address
            file_end = file_start + size
            ram_end = ram_start + size
        if not link_address:
            ram_start = np.nan
            ram_end = np.nan
        return pd.DataFrame(
            [[area, id, name, type, file_start, file_end,
                ram_start, ram_end, size]], 
            columns=columns)
            
    def _OutputSections(area, store, linked_folder_name):
        f = open(_GetOutputPath("%s/%s.rel" % (linked_folder_name, area)), "wb")
        f.write(store.mem[0].data)
        f.close()
        
        section_tbl = store.view(0)[0x10]
        for id in range(1, 7):
            file_offset = section_tbl.ru32(8 * id) & ~3
            size = section_tbl.ru32(8 * id + 4)
            if size and id < 6:
                f = open(_GetOutputPath("sections/%s/%s/%02d.raw" 
                    % (linked_folder_name, area, id)), "wb")
                f.write(store.view(0).rbytes(size, file_offset))
                f.close()

    if FLAGS.GetFlag("debug_level"):
        print("Processing %s REL at %s..." % (area, filepath))
    
    store = bd.BDStore(big_endian=True)
    store.RegisterFile(filepath, offset=0)
    section_tbl = store.view(0)[0x10]
    
    # Output REL and its sections, unlinked and linked.
    _OutputSections(area, store, linked_folder_name="rel_unlinked")
    if link_address:
        _LinkRel(store, link_address)
        _OutputSections(area, store, linked_folder_name="rel_linked")
    
    # Construct DataFrame of REL section info.
    columns = [
        "area", "id", "name", "type",
        "file_start", "file_end", "ram_start", "ram_end", "size"]
    dfs = []
    for (id, name) in {
        1: ".text", 2: ".ctors", 3: ".dtors", 
        4: ".rodata", 5: ".data", 6: ".bss"
    }.items():
        dfs.append(_CreateSectionDf(
            id, name, area, link_address, columns, section_tbl))
    df = pd.concat(dfs, ignore_index=True)
    df = df.set_index(["area", "id", "name", "type"])
    
    return df
    
def _ProcessDol(filepath):
    def _CreateSectionDf(id, name, section_info, columns):
        file_start = section_info[id][0]
        ram_start = section_info[id][1]
        size = section_info[id][2]
        return pd.DataFrame(
            [["_main", id, name, "text" if id < 7 else "data", file_start, 
                file_start + size, ram_start, ram_start + size, size]], 
            columns=columns)
        
    def _CreateBssDf(id, name, section_info, columns, bss_end=None):
        ram_start = section_info[id][1] + section_info[id][2]
        ram_end = bss_end if bss_end else section_info[id + 1][1]
        size = ram_end - ram_start
        return pd.DataFrame(
            [["_main", id + 90, name, "bss", np.nan, np.nan,
                ram_start, ram_end, size]], 
            columns=columns)

    if FLAGS.GetFlag("debug_level"):
        print("Processing _main DOL at %s..." % str(filepath))
    
    store = bd.BDStore(big_endian=True)
    store.RegisterFile(filepath, offset=0)
    view = store.view(0)
    
    # Put together list of (file_start, ram_start, size) tuples.
    sections = [None for x in range(18)]
    for x in range(18):
        sections[x] = (view.ru32(0), view.ru32(0x48), view.ru32(0x90))
        view = view.at(4)
    # Get start / end / size of .bss range.
    view = store.view(0)
    bss_start = view.ru32(0xd8)
    bss_size = view.ru32(0xdc)
    bss_end = bss_start + bss_size
    
    # Output DOL in its entirety, and its individual sections.
    f = open(_GetOutputPath("_main.dol"), "wb")
    f.write(store.mem[0].data)
    f.close()
    for id in range(18):
        if sections[id][2]:  # size > 0
            f = open(_GetOutputPath("sections/_main/%02d.raw" % id), "wb")
            f.write(view.rbytes(sections[id][2], sections[id][0]))
            f.close()
    
    # Construct DataFrame of DOL section info.
    columns = [
        "area", "id", "name", "type",
        "file_start", "file_end", "ram_start", "ram_end", "size"]
    dfs = []
    dfs.append(_CreateSectionDf(0, ".init", sections, columns))
    dfs.append(_CreateSectionDf(1, ".text", sections, columns))
    dfs.append(_CreateSectionDf(7, ".ctors", sections, columns))
    dfs.append(_CreateSectionDf(8, ".dtors", sections, columns))
    dfs.append(_CreateSectionDf(9, ".rodata", sections, columns))
    dfs.append(_CreateSectionDf(10, ".data", sections, columns))
    dfs.append(_CreateBssDf(10, ".bss", sections, columns))
    dfs.append(_CreateSectionDf(11, ".sdata", sections, columns))
    dfs.append(_CreateBssDf(11, ".sbss", sections, columns))
    dfs.append(_CreateSectionDf(12, ".sdata2", sections, columns))
    dfs.append(_CreateBssDf(12, ".sbss2", sections, columns, bss_end=bss_end))
    df = pd.concat(dfs, ignore_index=True)
    df = df.set_index(["area", "id", "name", "type"])
    return df

def main(argc, argv):
    if not FLAGS.GetFlag("out_path"):
        raise DumpSectionsError("Must provide a directory for --out_path.")
    elif not os.path.exists(Path(FLAGS.GetFlag("out_path"))):
        os.makedirs(Path(FLAGS.GetFlag("out_path")))

    link_address_overrides = {}
    for kv in filter(None, FLAGS.GetFlag("link_address_overrides").split(",")):
        (key, value) = kv.split(":")
        link_address_overrides[key] = int(value, 16)
    
    # Create list of section_info dataframes to be later merged.
    section_info = []
    
    # Process the DOL, outputting it and its individual sections.
    dol_path = Path(FLAGS.GetFlag("dol"))
    if not dol_path.exists():
        raise DumpSectionsError("--dol must point to a valid .DOL file.")
    section_info.append(_ProcessDol(dol_path))
    
    # Process RELs, outputting them and their sections (linked and unlinked).
    rel_pattern = FLAGS.GetFlag("rel")
    normalized_pattern = str(Path(rel_pattern))
    # Verify exactly one asterisk wildcard exists.
    lpos = normalized_pattern.find("*")
    rpos = normalized_pattern.rfind("*")
    if lpos != rpos or lpos == -1:
        raise DumpSectionsError(
            "--rel pattern must contain exactly one wildcard asterisk.")
    # Verify any files are matched.
    if not glob.glob(rel_pattern):
        raise DumpSectionsError("--rel pattern matched no files.")
    # For each file, get the full path and the part of the string
    # that replaced the asterisk (which should be the area's name).
    for fn in sorted(glob.glob(rel_pattern)):
        filepath = str(fn)
        area = filepath[lpos:rpos+1-len(normalized_pattern)]
        
        link_address = FLAGS.GetFlag("link_address")
        if link_address and area in link_address_overrides:
            link_address = link_address_overrides[area]
        if link_address:
            if not (0x80000000 <= link_address < 0x81000000):
                raise DumpSectionsError(
                    "Link address must be 0 or in range [0x8000,0x8100)0000.")
            if not (0x80000000 <= FLAGS.GetFlag("rel_bss_address") <
                    0x81000000):
                raise DumpSectionsError(
                    "REL bss address must be in range [0x8000,0x8100)0000.")
        section_info.append(_ProcessRel(area, filepath, link_address))
    
    # Finalize section_info.csv.
    # Concatenate section_info tables from DOL and RELs.
    df = pd.concat(section_info)
    # Convert values to eight-digit hex strings, with empty strings for NaNs.
    df = df.applymap(lambda val: "" if math.isnan(val) else "%08x" % int(val))
    # Export to csv.
    df.to_csv(_GetOutputPath("section_info.csv"))

if __name__ == "__main__":
    (argc, argv) = FLAGS.ParseFlags(sys.argv[1:])
    main(argc, argv)
