### Jdaster64's PM:TTYD Utils & Docs

### Credits
* **PistonMiner** for the TTYD scripting disassembly tool, ttydasm. (GitHub repo [here](https://github.com/PistonMiner/ttyd-tools).)
* PistonMiner and **Zephiles** for their contributions to the symbol maps, including nearly all of the main binary's .text symbols.

### Contents
* **docs**: 
  * **ttyd_structures_pseudocode** - Notes on various TTYD structure layouts / enums, mostly for battle-related stuff.
* **resources**:
  * A dump from a curated table of symbol diffs between the JP demo and US retail versions of TTYD, used to locate individual functions / data / class instances, and to power the various Python scripts. (Will be updated in the future by myself and others, and will hopefully eventually have equivalent coverage for PAL / JP in the future.)
  * Text files containing TTYD's battle units' and items' names in ID order, one per line.
* **source**:
  * **jdalibpy**:
    * General command-line flag (**flags**) & binary memory view (**bindump**) utilities.
    * A couple unrelated tools I use occasionally on the command-line:
      * **conv** - Converts between various numeric and datetime formats.
      * **rngutil** - Simulates TTYD's (and a few other games') random number generators.
  * **ttyd_exporteventscripts** - Exports all labeled EventScripts in a symbol diffs file using PistonMiner's ttydasm tool.
  * **ttyd_extractclassdata** - Exports CSVs of all the instances of various class types from symbol diffs and TTYD RAM snapshots.
  * **ttyd_generatesymbolmaps** - Exports MAP files and ttydasm symbol files per area of TTYD from symbol diffs.
  * **ttyd_maplib** - A library of common functions used by the above utilities.