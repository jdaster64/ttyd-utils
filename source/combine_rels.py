#! /usr/bin/python3.6

"""Constructs a new REL file from a list of symbols or regions in other RELs.

Takes the following inputs:
- A filepattern matching .REL files with a single wildcard replacing the name
- Either:
  - A list of data ranges to include in the custom REL, in the format:
    AREA:SEC_ID:START_OFFSET-END_OFFSET (e.g. aji:5:00001ab0-00001ae0)
- Or:
  - A list of newline-delimited symbol names or patterns to include, in format:
    AREA:NAMESPACE:SYMBOL/* (e.g. aji:unit_gundan_zako.o:*)
  - A symbol info .csv (must include data on all names you wish to include)
, then outputs the following:
- A .REL file containing all of the symbols requested
- A .csv file listing all the symbols' locations in the generated .REL file.

Will throw an error if any requested data has a relocation table entry that
requires a REL dependency that is not also included in the requested data.

TODO:
- Support alignment restrictions above 8 bytes.
- Add support for automatically looking up dependencies if using symbol names?
- Add support for subranges of particular symbols?"""
# Jonathan Aldrich 2021-05-16 ~ 2021-05-17

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

# Input patterns for the source .REL files.
FLAGS.DefineString("rel", "")
# Filepath to a text file containing data ranges to include in the output REL.
FLAGS.DefineString("symbol_ranges", "")
# Filepath to a text file containing desired symbols in the output REL.
FLAGS.DefineString("symbol_names", "")
# Filepath to a .csv file containing info on symbols in the source .REL files;
# must at least include info for all of the desired symbols.
FLAGS.DefineString("symbol_info", "")

# Whether to display debug strings.
FLAGS.DefineInt("debug_level", 1)

class CombineRelsError(Exception):
    def __init__(self, message=""):
        self.message = message
        
def _GetOutputPath(filepath, create_parent=True):
    path = Path(FLAGS.GetFlag("out_path")) / filepath
    if create_parent and not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    return path
    
def _CombineRels(rel_pattern_str, symbol_table):
    def _CreateExportedTableFormat(row):
        """Converts a symbol table row to exported format."""
        return pd.DataFrame(
            [["custom", row["sec_id"], "%08x" % row["out_offset"], row["name"],
              row["namespace"], "%08x" % row["size"], row["align"]]],
            columns=[
                "area", "sec_id", "sec_offset",
                "name", "namespace", "size", "align"])

    def _CreateLookupRowWithOutput(row, out_offset):
        """Takes the input symbol_info row and adds the out_offset."""
        return pd.DataFrame(
            [[row["area"], row["sec_id"], row["sec_offset"], 
              row["sec_offset_end"], row["name"], row["namespace"], 
              row["size"], row["align"], out_offset]],
            columns=[
                "area", "sec_id", "sec_offset", "sec_offset_end",
                "name", "namespace", "size", "align", "out_offset"])
                
    def _LookupNewOffset(symbol_table, area, sec_id, sec_offset):
        """Returns the new offset corresponding to the old one if one exists.
        
        If the old offset corresponds to a symbol not in symbol_table, returns
        None, assuming that symbol won't be included in the combined REL.
        Raises an error if there are multiple matches in symbol_table."""
        matches = symbol_table[
            (symbol_table.area == area) &
            (symbol_table.sec_id == sec_id) &
            (symbol_table.sec_offset <= sec_offset) & 
            (symbol_table.sec_offset_end > sec_offset)]
        if matches.shape[0] < 1:
            return None
        if matches.shape[0] > 1:
            raise CombineRelsError(
                "Ambiguous symbol match at %s:%d:%08x." % 
                (area, sec_id, sec_offset))
        # Return the new offset + how far into the symbol the old offset is.
        return (matches["out_offset"].iloc[0] + 
            sec_offset - matches["sec_offset"].iloc[0])
        
    def _WriteToBuffer(buffer, offset, value, size):
        """Writes an integer value of the given size to a buffer."""
        for x in range(size):
            buffer[offset + x] = ((value >> ((size-1-x)*8)) & 0xff)
        
    def _AppendToBuffer(buffer, value, size):
        """Writes an integer value of the given size to the end of a buffer."""
        for x in range(size):
            buffer.append((value >> ((size-1-x)*8)) & 0xff)

    # Buffers for each section's raw, unlinked data (for .bss, track the length)
    section_data = [[] for x in range(6)]
    bss_length = 0
    
    # Copy all symbols into their respective sections' buffers, and create
    # a new lookup DataFrame including the output locations.
    # (For .bss data, keep track of the total length of the combined sections.)
    dfs = []
    for area in sorted(symbol_table.area.unique()):
        if FLAGS.GetFlag("debug_level"):
            print("Processing %s symbols..." % area)
            
        store = bd.BDStore(big_endian=True)
        store.RegisterFile(rel_pattern_str.replace("*", area), offset=0)
        section_tbl = store.view(0)[0x10]
        
        for (index, row) in symbol_table.iterrows():
            if row["area"] == area:
                # Add symbol's data to its respective section.
                if row["sec_id"] == 6:
                    # Pad to alignment to find start point of next symbol.
                    while bss_length % 8 != row["sec_offset"] % 8:
                        bss_length += 1
                    out_offset = bss_length
                    # Add size of symbol to bss_length (bss data is not stored).
                    bss_length += row["size"]
                else:
                    id = row["sec_id"]
                    if id > 1:
                        # If not .text section (fixed-alignment of 4), pad to
                        # alignment to find the start point of next symbol.
                        while len(section_data[id]) % 8 != row["sec_offset"] % 8:
                            section_data[id].append(0)
                    out_offset = len(section_data[id])
                    # Copy bytes from original symbol into section_data.
                    file_offset = section_tbl.ru32(8 * id) & ~3
                    for b in store.view(0).rbytes(
                        row["size"], file_offset + row["sec_offset"]):
                        section_data[id].append(b)
                # Add the new location of the symbol to a new table.        
                dfs.append(_CreateLookupRowWithOutput(row, out_offset))
    
    # Join all lookup rows with output offsets, and order lexicographically.
    df = pd.concat(dfs, ignore_index=True)
    symbol_table = df.sort_values(by=["area", "sec_id", "sec_offset"])
    
    if FLAGS.GetFlag("debug_level"):
        print("REL symbols extracted; %d symbols processed." % 
            symbol_table.shape[0])
    
    # Buffers for each section's relocatable data (against the same REL).
    rel_data = [[] for x in range(6)]
    rel_offsets = [0 for x in range(6)]
    # Buffers for each section's relocatable data (against the main DOL).
    rel_data_main = [[] for x in range(6)]
    rel_offsets_main = [0 for x in range(6)]
    
    # Port all needed relocation information from the original .REL files.
    for area in sorted(symbol_table.area.unique()):
        if FLAGS.GetFlag("debug_level"):
            print("Processing %s relocation tables..." % area)
            
        store = bd.BDStore(big_endian=True)
        store.RegisterFile(rel_pattern_str.replace("*", area), offset=0)
        
        header = store.view(0)
        imp_table = header[0x28]
        imp_size = header.ru32(0x2c)
        imp_offset = 0
        while imp_offset < imp_size:
            module_id = imp_table.ru32(imp_offset)
            rel_table = imp_table[imp_offset + 4]
            imp_offset += 8

            current_section = 0
            section_offset = 0
            while True:
                offset = rel_table.ru16(0)
                type = rel_table.ru8(2)
                section = rel_table.ru8(3)
                addend = rel_table.ru32(4)
                # Advance to next relocation entry.
                rel_table = rel_table.at(8)
                
                if type == 203:
                    # End of rel table.
                    break
                elif type == 202:
                    # Section change rel entry.
                    current_section = section
                    section_offset = 0
                else:
                    # Assuming no symbols in .bss have linkage; need to add
                    # specific support for that if I'm mistaken.
                    if current_section > 5:
                        raise CombineRelsError("Linking to section 6!")
                        
                    section_offset += offset
                    new_offset = _LookupNewOffset(
                        symbol_table, area, current_section, section_offset)
                    # Not used in combined REL; move to next entry.
                    if new_offset == None:
                        continue
                    # Look up the linked-to symbol address in the combined REL.
                    # (if module_id == 0, i.e. linking to DOL, just use addend.)
                    if module_id != 0:
                        addend = _LookupNewOffset(
                            symbol_table, area, section, addend)
                    # If an address could not be found, a dependency must have
                    # been missing from the input symbol_table; for shame.
                    if addend == None:
                        raise CombineRelsError(
                            "Symbol missing dependency at %s:%d:%08x." % (
                                area, current_section, section_offset))
                    # Update the current offset for the given section/imp.
                    if module_id == 0:
                        offset = new_offset - rel_offsets_main[current_section]
                        rel_offsets_main[current_section] = new_offset
                    else:
                        offset = new_offset - rel_offsets[current_section]
                        rel_offsets[current_section] = new_offset
                    # Add this relocation to the respective table.
                    rel_table_buffer = (rel_data_main[current_section] if
                        module_id == 0 else rel_data[current_section])
                    _AppendToBuffer(rel_table_buffer, offset, 2)
                    _AppendToBuffer(rel_table_buffer, type, 1)
                    _AppendToBuffer(rel_table_buffer, section, 1)
                    _AppendToBuffer(rel_table_buffer, addend, 4)
    
    if FLAGS.GetFlag("debug_level"):
        print("Relocation tables processed.")
    
    # Construct the final REL from the buffers put together beforehand.
    rel = []
    
    # REL header.
    _AppendToBuffer(rel, 40, 4)     # id (arbitrary custom value)
    _AppendToBuffer(rel, 0, 4)      # next
    _AppendToBuffer(rel, 0, 4)      # prev
    _AppendToBuffer(rel, 15, 4)     # numSections
    _AppendToBuffer(rel, 0x4c, 4)   # sectionInfoOffset
    _AppendToBuffer(rel, 0, 4)      # nameOffset
    _AppendToBuffer(rel, 0, 4)      # nameSize
    _AppendToBuffer(rel, 3, 4)      # version
    _AppendToBuffer(rel, bss_length, 4)  # bssSize
    _AppendToBuffer(rel, 0, 4)      # relOffset - will be filled in later.
    _AppendToBuffer(rel, 0, 4)      # impOffset - will be filled in later.
    _AppendToBuffer(rel, 0x10, 4)   # impSize
    _AppendToBuffer(rel, 0, 4)      # prolog/epilog/unresolved/bssSection
    _AppendToBuffer(rel, 0, 4)      # prolog offset
    _AppendToBuffer(rel, 0, 4)      # epilog offset
    _AppendToBuffer(rel, 0, 4)      # unresolved offset
    _AppendToBuffer(rel, 8, 4)      # align
    _AppendToBuffer(rel, 8, 4)      # bssAlign
    _AppendToBuffer(rel, 0, 4)      # fixSize - will be filled in later.
    
    # Section table (initialize to 15 section table entries' worth of zeroes).
    for _ in range(15 * 8):
        rel.append(0)
    # Section 1 (text)
    section_start = len(rel)
    _WriteToBuffer(rel, 0x54, section_start | 1, 4)
    rel += section_data[1]
    _WriteToBuffer(rel, 0x58, len(rel) - section_start, 4)
    # Sections 2 and 3 (unused)
    _WriteToBuffer(rel, 0x5c, len(rel), 4)
    _WriteToBuffer(rel, 0x60, 4, 4)
    _AppendToBuffer(rel, 0, 4)
    _WriteToBuffer(rel, 0x64, len(rel), 4)
    _WriteToBuffer(rel, 0x68, 4, 4)
    _AppendToBuffer(rel, 0, 4)
    # Section 4 (rodata)
    while len(rel) % 8 != 0:
        rel.append(0)
    section_start = len(rel)
    _WriteToBuffer(rel, 0x6c, section_start, 4)
    rel += section_data[4]
    _WriteToBuffer(rel, 0x70, len(rel) - section_start, 4)
    # Section 5 (data)
    while len(rel) % 8 != 0:
        rel.append(0)
    section_start = len(rel)
    _WriteToBuffer(rel, 0x74, section_start, 4)
    rel += section_data[5]
    _WriteToBuffer(rel, 0x78, len(rel) - section_start, 4)
    # Section 6 (bss)
    _WriteToBuffer(rel, 0x7c, 0, 4)
    _WriteToBuffer(rel, 0x80, bss_length, 4)
    # Pad before imp table (not necessary, but easier to read in a hex editor.)
    while len(rel) % 8 != 0:
        rel.append(0)
    
    imp_table = len(rel)
    rel_table = len(rel) + 0x10
    _WriteToBuffer(rel, 0x24, rel_table, 4)  # relOffset
    _WriteToBuffer(rel, 0x28, imp_table, 4)  # impOffset
    _WriteToBuffer(rel, 0x48, rel_table, 4)  # fixSize
    # Reserve space for imp table.
    for _ in range(16):
        rel.append(0)
    # Copy REL -> REL relocation data.
    _WriteToBuffer(rel, imp_table, 40, 4)
    _WriteToBuffer(rel, imp_table + 4, len(rel), 4)
    for x in range(6):
        if len(rel_data[x]):
            _AppendToBuffer(rel, 0, 2)      # offset
            _AppendToBuffer(rel, 202, 1)    # type (change section)
            _AppendToBuffer(rel, x, 1)      # section
            _AppendToBuffer(rel, 0, 4)      # addend
            rel += rel_data[x]
    _AppendToBuffer(rel, 0, 2)              # offset
    _AppendToBuffer(rel, 203, 1)            # type (end of table)
    _AppendToBuffer(rel, 0, 1)              # section
    _AppendToBuffer(rel, 0, 4)              # addend
    # Copy REL -> DOL relocation data.
    _WriteToBuffer(rel, imp_table + 8, 0, 4)
    _WriteToBuffer(rel, imp_table + 12, len(rel), 4)
    for x in range(6):
        if len(rel_data_main[x]):
            _AppendToBuffer(rel, 0, 2)      # offset
            _AppendToBuffer(rel, 202, 1)    # type (change section)
            _AppendToBuffer(rel, x, 1)      # section
            _AppendToBuffer(rel, 0, 4)      # addend
            rel += rel_data_main[x]
    _AppendToBuffer(rel, 0, 2)              # offset
    _AppendToBuffer(rel, 203, 1)            # type (end of table)
    _AppendToBuffer(rel, 0, 1)              # section
    _AppendToBuffer(rel, 0, 4)              # addend
    
    # Export the final REL.
    out_rel = open(_GetOutputPath("custom.rel"), "wb")
    out_rel.write(bytes(rel))
    
    # Export the table of symbol info.
    # TODO: Add column with file-relative offsets?
    dfs = []
    for (index, row) in symbol_table.iterrows():
        dfs.append(_CreateExportedTableFormat(row))
    df = pd.concat(dfs, ignore_index=True)
    df = df.sort_values(by=["area", "sec_id", "sec_offset"])
    df.to_csv(_GetOutputPath("custom_symbols.csv"), index=False)
    
def _CreateCombinedRelSymbolTable(symbol_info, symbol_names):
    """Creates a lookup table of `symbol_info` data matching `symbol_names`."""
    def _CreateLookupRow(row):
        """Converts a symbol_info row into a lookup-friendly format."""
        sec_offset = int(row["sec_offset"], 16)
        size = int(row["size"], 16)
        return pd.DataFrame(
            [[row["area"], row["sec_id"], sec_offset, sec_offset + size,
              row["name"], row["namespace"], size, row["align"]]],
            columns=[
                "area", "sec_id", "sec_offset", "sec_offset_end",
                "name", "namespace", "size", "align"])
        
    dfs = []
    # TODO: Speed up / validate by looking up rows via symbol_names instead?
    for (index, row) in symbol_info.iterrows():
        full_symbol = "%s:%s:%s" % (row["area"], row["namespace"], row["name"])
        wildcard_symbol = "%s:%s:*" % (row["area"], row["namespace"])
        if (full_symbol in symbol_names) or (wildcard_symbol in symbol_names):
            dfs.append(_CreateLookupRow(row))
    if not len(dfs):
        raise CombineRelsError("No symbols found matching --symbol_names.")
        
    df = pd.concat(dfs, ignore_index=True)
    df = df.sort_values(by=["area", "sec_id", "sec_offset"])
    
    if FLAGS.GetFlag("debug_level"):
        print("Symbol lookup table finished; %d symbols found." % df.shape[0])
    return df
    
def _CreateCombinedRelRangeLookupTable(symbol_ranges):
    """Creates a lookup table in symbol-info format from a series of range
       strings, assuming a standard alignment and using dummy names/namespaces.
       
       Does not validate that section names, ids, or ranges are valid;
       use the symbol name variant if you care about pre-checking that."""
    def _CreateLookupRow(area, sec_id, start_offset, end_offset):
        """Converts a symbol_info row into a lookup-friendly format."""
        sec_id = int(sec_id)
        sec_offset = int(start_offset, 16)
        sec_offset_end = int(end_offset, 16)
        size = sec_offset_end - sec_offset
        align = 8 if sec_id > 3 else 4
        return pd.DataFrame(
            [[area, sec_id, sec_offset, sec_offset_end,
              "%s-%08x-%08x" % (area, sec_offset, sec_offset_end),
              "", size, align]],
            columns=[
                "area", "sec_id", "sec_offset", "sec_offset_end",
                "name", "namespace", "size", "align"])
        
    dfs = []
    for line in symbol_ranges:
        tokens = line.split(":")
        if len(tokens) != 3:
            raise CombineRelsError(
                "Ranges must be specified in format 'AREA:SEC_ID:START-END'.")
        range_tokens = tokens[2].split("-")
        if len(range_tokens) != 2:
            raise CombineRelsError(
                "Ranges must be specified in format 'AREA:SEC_ID:START-END'.")
        dfs.append(_CreateLookupRow(
            tokens[0], tokens[1], range_tokens[0], range_tokens[1]))
        
    df = pd.concat(dfs, ignore_index=True)
    df = df.sort_values(by=["area", "sec_id", "sec_offset"])
    
    if FLAGS.GetFlag("debug_level"):
        print("Lookup table finished; %d ranges found." % df.shape[0])
    return df
    
def _RemoveComments(raw_input):
    """Removes '#' comments, blank lines and trailing whitespace from input."""
    filtered_inputs = []
    for line in raw_input:
        if line.find('#') != -1:
            line = line[:line.find('#')]
        line = line.rstrip()
        if line:
            filtered_inputs.append(line)
    return filtered_inputs    

def main(argc, argv):
    if not FLAGS.GetFlag("out_path"):
        raise CombineRelsError("Must provide a directory for --out_path.")
    elif not os.path.exists(Path(FLAGS.GetFlag("out_path"))):
        os.makedirs(Path(FLAGS.GetFlag("out_path")))
        
    # Validate rel filepattern, verifying exactly one asterisk wildcard exists.
    rel_pattern = FLAGS.GetFlag("rel")
    normalized_pattern = str(Path(rel_pattern))
    lpos = normalized_pattern.find("*")
    rpos = normalized_pattern.rfind("*")
    if lpos != rpos or lpos == -1:
        raise CombineRelsError(
            "--rel pattern must contain exactly one wildcard asterisk.")
    
    # Attempt to read range data, and symbol name data / info.
    symbol_ranges_path = FLAGS.GetFlag("symbol_ranges")
    symbol_names_path = FLAGS.GetFlag("symbol_names")
    symbol_info_path = FLAGS.GetFlag("symbol_info")
    
    can_use_ranges = os.path.exists(symbol_ranges_path)
    can_use_names = (
        os.path.exists(symbol_names_path) and os.path.exists(symbol_info_path))
        
    # Determine which symbols or data ranges to include in the combined REL.
    # Prioritize symbol names over ranges, if both are specified.
    symbol_table = None
    if can_use_names:
        symbol_info = pd.read_csv(Path(symbol_info_path))
        symbol_names = [line.rstrip() for line in open(Path(symbol_names_path))]
        symbol_names = _RemoveComments(symbol_names)
        if len(symbol_names) < 1:
            raise CombineRelsError("--symbol_names has no requested symbols.")
        
        symbol_table = _CreateCombinedRelSymbolTable(symbol_info, symbol_names)
    elif can_use_ranges:
        symbol_ranges = [line.rstrip() for line in open(Path(symbol_ranges_path))]
        symbol_ranges = _RemoveComments(symbol_ranges)
        if len(symbol_ranges) < 1:
            raise CombineRelsError("--symbol_ranges has no requested ranges.")
        
        symbol_table = _CreateCombinedRelRangeLookupTable(symbol_ranges)
    else:
        raise CombineRelsError(
            "Must specify either --symbol_ranges, or "
            "--symbol_names and --symbol_info.")

    # Attempt to construct the combined REL from the requested data.
    _CombineRels(normalized_pattern, symbol_table)
    
if __name__ == "__main__":
    (argc, argv) = FLAGS.ParseFlags(sys.argv[1:])
    main(argc, argv)
