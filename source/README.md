### Guide to using the TTYD-Utils suite

The Python utilities in this directory cannot be used directly to create Paper
Mario: The Thousand-Year Door mods, but can be considered a means of creating
a directory in which one can look up the location of code one wishes to change.

To make full use of these utilities, you need:

* A reasonably up-to-date Python 3 installation with NumPy and Pandas available.
* A binary of PistonMiner's *ttydasm* tool
  (can be obtained [here](https://github.com/PistonMiner/ttyd-tools/releases)).
* The extracted boot.dol and \*.rel files from any version of TTYD.
* Either:
  * A .csv containing symbol data for the same version
    (**resources/us_symbols.csv** will suffice for the retail US version), or
  * .MAP files containing symbol information for the .dol and .rel files for
    the same version, which can be used to produce a symbol csv.
  
After acquiring them, you can run the utilities in this directory in the
following order (making sure to use the same *--out_path* for each invocation):

#### Step 1. Dump the raw data from the sections of the .dol/.rel files.

**dump_sections.py** takes the .dol/.rel files provided, and outputs the following:
* A .csv file containing information regarding the type, size, and file-/RAM-relative
  locations of the sections of all the provided binary files.
* .raw dumps of every complete binary file and individual section.

Providing a link address (with optional area-specific overrides)
will also generate versions of the .REL file / section dumps that have
gone through the linking process, meaning e.g. pointers in evts or data
structures will have their values filled in rather than being placeholders.
Providing *some* value is required for many of the later utilities to run
correctly; by default, --link_address is set to an arbitrary value far enough
into the RAM space to not overlap the .DOL's sections, but it isn't the real
link address used for any particular version of TTYD.

Providing a rel_bss address will ensure that the .bss sections in .rel files
are correctly linked to a separate memory location; supplying an accurate
address (the address of the symbol *rel_bss seq_mapchange.o*) is not required,
but doing so will make sure the correct addresses are used for .rel BSS symbols
when exporting .MAP files in Step 3.

**Sample invocation:**
```
dump_sections.py \
  --out_path=YOUR_OUTPUT_PATH \
  --dol=PATH_TO_YOUR_DOL.dol \
  --rel=PATH_TO_YOUR_REL_FOR_AREA_*.rel \
  --link_address=0x80600000 \
  --link_address_overrides=jon:0x80c00000,tst:0x80c00000 \
  --rel_bss_address=0x80a00000
```

#### Step 2. If necessary, convert your externally-sourced .MAP files to a symbol table.

* **NOTE:** *You can skip this step if using the already-provided **resources/us_symbols.csv** file.*

Running the **map_to_symbols** and **annotate_map_symbols** utilities in sequence
will produce a .csv of symbols with the same columns as **resources/us_symbols.csv**,
and some heuristically-predicted common types (notably, strings and evts).
The resulting file will be in `YOUR_OUTPUT_PATH/annotated_symbols.csv`.

**Sample invocations:**
```
map_to_symbols.py \
  --out_path=YOUR_OUTPUT_PATH \
  --dol_map=PATH_TO_YOUR_DOL_MAP.map \
  --rel_map=PATH_TO_YOUR_REL_MAP_FOR_AREA_*.map

annotate_map_symbols.py --out_path=YOUR_OUTPUT_PATH
```

#### Step 3. Export .MAP files and ttydasm symbol files using the symbol table.

The **symbol_to_maps** utility produces .MAP files from your symbol table,
which can be useful if you don't already have them as a more human-readable
format (as well as for labeling symbols in the Dolphin emulator), as well as
symbol files for ttydasm, which are immensely useful for producing more 
readable script dumps.

The exact files produced are:
* One .MAP file and one ttydasm symbol file containing only the .dol symbols.
* Per .rel file:
  * One .MAP file and one ttydasm symbol file containing the .dol's symbols and 
    that .rel's symbols (w/RAM-relative addresses, as specified in Step 1).
  * One .MAP file containing only the .rel's symbols (w/section-relative addresses).

**Sample invocation:**
```
symbol_to_maps.py \
  --out_path=YOUR_OUTPUT_PATH \
  --symbols_path=PATH_TO_YOUR_SYMBOLS_FILE.csv
```

#### Step 4. Export evt scripts to text files using ttydasm.

The **extract_events** utility takes the ttydasm symbol files and dumped
sections, and uses PistonMiner's *ttydasm* tool to produce text dumps of
all symbols labeled with the "evt" type in the provided symbols csv.

The provided **resources/us_symbols.csv** file should have ~all such evts
in the US version of TTYD marked accurately; barring that, the binary in Step 2
should be fairly good at identifying them if you have the start addresses
correctly labeled.

**Example output script:**
```
...
805C6FE4:   switchi GSW(0)
805C6FEC:     case_int_lt 336
805C6FF4:       callc [evt_npc_set_position evt_npc.o] ["me"] 30 10 -950
805C700C:       callc [evt_npc_set_ry evt_npc.o] ["me"] 270
805C701C:   end_switch
...
```

**Sample invocation:**
```
extract_events.py \
  --out_path=YOUR_OUTPUT_PATH \
  --symbols_path=PATH_TO_YOUR_SYMBOLS_FILE.csv \
  --ttydasm_exe=PATH_TO_TTYDASM.exe
```

#### Step 5. Export instances of certain C data types to .csv files.

The **extract_classes** utility takes the dumped section info from Step 1,
and produces .csv dumps containing the field values and bytewise representation
of all instances of the class types supported in **extract_classes_parsers**.

Note that by default nothing will be exported if you're using the
**annotated_symbols.csv** file provided in Step 2; currently none of the
supported types are automatically detectable, and have to be manually annotated.
The **resources/us_symbols.csv** file should have most instances of the
supported types already annotated, however.

Currently, the list of supported types and their fields are hardcoded, but
support may be added to specify one's own struct definitions in the future.
These are the currently supported types (for the US version, if the struct
varies across versions; see **docs/ttyd_structures_pseudocode.txt** for
further reference):
```
AudienceItemWeight
BattleGroupSetup
BattleSetupData
BattleSetupNoTable
BattleSetupWeightedLoadout
BattleStageData
BattleStageFallObjectData
BattleStageNozzleData
BattleUnitPoseTable
BattleStageObjectData
BattleUnitDataTable
BattleUnitDefense
BattleUnitDefenseAttr
BattleUnitKind
BattleUnitKindPart
BattleUnitPoseTable
BattleUnitSetup
BattleWeapon
CookingRecipe
ItemData
ItemDropData
PointDropData
ShopItemTable
ShopSellPriceList
StatusVulnerability
```

**Sample invocation:**
```
extract_classes.py \
  --out_path=YOUR_OUTPUT_PATH \
  --symbols_path=PATH_TO_YOUR_SYMBOLS_FILE.csv
```
