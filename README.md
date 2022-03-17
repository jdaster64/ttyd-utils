### Jdaster64's PM:TTYD Utils & Docs (latest update: 2022-02-25)

### Credits
* **PistonMiner** for the TTYD scripting disassembly tool, ttydasm. (GitHub repo [here](https://github.com/PistonMiner/ttyd-tools).)
* PistonMiner and **Zephiles** for their contributions to the symbol maps, including nearly all of the main binary's .text symbols.
* Both of the above, **Jasper**, **SolidifiedGaming**, and others who've helped with TTYD documentation elsewhere.

### Contents
* **docs**:
  * **ttyd_structures_pseudocode** - Notes on various TTYD structure layouts / enums, mostly for battle-related stuff.
* **resources**:
  * **us_symbols.csv** - A near-complete symbol table for the US retail version of TTYD, including some type information (including marking ~all evts).
  * **eu_symbols.csv** - Same for the European / PAL version.
  * **jp_symbols.csv** - Same for the retail JP version.
  * Text files containing TTYD's battle units' and items' names in ID order, one per line.
  * A dump from an old curated table of symbol diffs between the JP demo and US retail versions of TTYD, used to locate individual functions / data / class instances (was used for older Python scripts)
* **source**:
  * **jdalibpy**:
    * General command-line flag (**flags**) & binary memory view utilities (**bindatastore**, and its crustier brother **bindump** for the old utils).
    * A couple unrelated tools I use occasionally on the command-line:
      * **conv** - Converts between various numeric and datetime formats.
      * **rngutil** - Simulates TTYD's (and a few other games') random number generators.
  * **TTYD utility scripts**: (explained more fully in source/README.md)
    * **dump_sections** - Provided .dol/.rel files from TTYD, dumps their individual sections.
    * **symbol_to_maps** - Converts a symbol table to .MAP files and symbol files for PistonMiner's *ttydasm* tool.
    * **extract_events** - Exports all labeled evts in a symbol table to text files using *ttydasm*.
    * **extract_classes** - Exports all labeled instances of various structures to .csv files, one for their fields and one for byte representations.
    * **map_to_symbols**, **annotate_map_symbols** - For converting existing .MAP files for other versions of TTYD (e.g. the JP demo) to symbol tables, for use with the other scripts.
    * Optional utilities:
      * **combine_event_dumps** - Combines all unique event dumps from extract_events into a single text file.
      * **combine_rels** - Builds custom REL files composed of symbols from one or more existing RELs.
  * **old_utils**:
    * Were used for some of the same purposes as the newer utilities, but much messier and generally less fully-featured.