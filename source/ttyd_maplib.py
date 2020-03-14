#! /usr/bin/python3.4

"""Various utilities for dealing with TTYD symbol information."""
# Jonathan "jdaster64" Aldrich 2019-09-29

import os
import sys
import re
import numpy as np
import pandas as pd

import jdalibpy.flags as flags

FLAGS = flags.Flags()
# Filepath to a file in the format of REPO/resources/ttyd_*_symboldiffs_*.csv.
FLAGS.DefineString("input_diffs", "")

class TtydSymbolLibError(Exception):
    def __init__(self, message=""):
        self.message = message
        
def GetClassSize(classname):
    """
    Returns the size in bytes of a member of class `classname`, or -1
    if the class does not have a consistent size.
    """
    kClassNameSizes = {
        "AttackParams_t": 0xc0,
        "AudienceItemWeight_t": 0x8,
        "BattleLoadoutParams_t": 0x20,
        "BattleObjectData_t": 0x18,
        "BattleSetup_t": 0x44,
        "BattleSetupNoTbl_t": 0x8,
        "BattleStageData_t": 0x1b4,
        "BattleUnitDefense_t": 0x5,
        "BattleUnitDefenseAttr_t": 0x5,
        "BattleUnitEntry_t": 0x30,
        "BattleUnitParams_t": 0xc4,
        "BattleUnitParts_t": 0x4c,
        "BattleUnitStatusVulnerability_t": 0x16,
        "BattleWeightedLoadout_t": 0xc,
        "CookingRecipe_t": 0xc,
        "ItemData_t": 0x28,
        "ItemDropWeight_t": 0x8,
        "PointDropWeights_t": 0x50,
        "ShopItemList_t": 0x8,
        "ShopSellPriceList_t": 0x8,
    }
    return kClassNameSizes[classname] if classname in kClassNameSizes else -1
    

# TODO: Implement different base REL addresses per region, and add an option
#       to keep symbols starting with "@" to at least delineate them in Dolphin.
def GetSymbolInfoFromDiffsCsv(filepath, region="U"):
    """
    Input: filepath to a CSV file containing at least the following columns:
        "Sec"       - Section symbol is from, e.g. .text, .rodata, .data
        "Area"      - .rel file the symbol is from, or "_MS" for the main dol.
        "Symbol"    - Name / object file (namespace) the symbol is from.
        "Actual-B"  - Offset the symbol is found at, from the main dol when
                      loaded in the game for "_MS" symbols, or from the start
                      of the rel file for others.
        "Len-B"     - Size of the symbol in bytes.
        "Class"     - Type of the underlying structure; may not be of a
                      fixed size (e.g. "EventScript_t" for event scripts).
                      
    Output: pandas.DataFrame with the following columns:
        area, fullname, name, file, section, address, offset, length, class
    """
    df = pd.read_csv(filepath, header=0).dropna(
        axis=0, subset=["Actual-B", "Len-B"])
        
    def convert_diffs(row):
        section = row["Sec"]
        area = row["Area"]
        symbol_full_name = row["Symbol"]
        offset = int(row["Actual-B"], 0)
        length = int(row["Len-B"], 0)
        class_name = row["Class"]
        
        # Split full name into symbol name and namespace / object file.
        if symbol_full_name[-2:] == ".o":
            symbol_name = symbol_full_name[:symbol_full_name.rfind(" ")]
            symbol_file = symbol_full_name[symbol_full_name.rfind(" ")+1:]
        else:
            symbol_name = symbol_full_name
            symbol_file = ""
        # Calculate the absolute address based on the area / offset.
        # TODO: These aren't technically fixed addresses (especially jon).
        address = offset
        if row["Area"] == "jon":
            address += 0x80c779a0
        elif row["Area"] != "_MS":
            address += 0x805ba9a0
            
        return pd.Series(
            data=[area, symbol_full_name, symbol_name, symbol_file, section,
                  address, offset, length, class_name],
            index=["area", "fullname", "name", "file", "section",
                   "address", "offset", "length", "class"])
    
    # Filter out symbols w/unknown name or location, and sort by area + address.
    filter = (df["Actual-B"] != "UNUSED") & ~(df["Symbol"].str.contains("@"))
    df = df.loc[filter].apply(convert_diffs, axis=1)
    df.sort_values(["area", "address"], kind="mergesort", inplace=True)
    return df
    
def LookupSymbolName(df, area, address, classname=""):
    """
    Returns the full name of a symbol in from a DataFrame of symbol information
    (as returned by GetSymbolInfoFromDiffsCsv) based on its area and address.
    Matches can be in the area provided or in the main DOL ("_MS").
    
    If a classname is provided, will ensure that the symbol also matches it, and
    if the class has a defined size, will look for individual instances with
    a matching address in arrays of that class type, and return the name/index.
    
    If no match is found, returns the address as a hex string.
    """
    
    # TODO: Improve runtime further for common case.
    filter = df["area"].isin([area, "_MS"]) & df["address"] < address
    if classname:
       filter = filter & (df["class"] == classname)
    for idx, row in df.loc[filter].iloc[::-1].iterrows():
        class_size = GetClassSize(classname)
        if class_size > 0:
            array_len = row["length"] // class_size
            for array_idx in range(array_len):
                if row["address"] + class_size * array_idx == address:
                    format_sp =  "_%03x" if array_len > 255 else "_%02x"
                    return row["fullname"] + (format_sp % array_idx)
        elif row["address"] == address:
            return row["fullname"]
    return "0x%08x" % address
            
def main(argc, argv):
    # If main() is called, test the library on an input CSV.
    if not FLAGS.GetFlag("input_diffs"):
        raise TtydSymbolLibError("No input diffs CSV provided.")
        
    # Read symbol data from diffs file.
    df = GetSymbolInfoFromDiffsCsv(FLAGS.GetFlag("input_diffs"))
    # Print some sample data.
    print("Shape: %s" % (str(df.shape),))
    print(df.sample(n=5))
    print(df.dtypes)

if __name__ == "__main__":
    (argc, argv) = FLAGS.ParseFlags(sys.argv[1:])
    main(argc, argv)