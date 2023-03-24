import subprocess
import os
import hashlib
import sys

# Define the path for all tools to output to
out_path = "./tools-out"

tools_path = "tools"

# Path to the directory containing the rel files
rels_directory = "iso/files/rel"

# Path to main.dol
dol_directory = "iso/sys/main.dol"

# Path to ttyd-tools which you get from https://github.com/PistonMiner/ttyd-tools
ttyd_tools_directory = "ttyd-tools/"

# Path to ttyd-utils-master which you get from https://github.com/jdaster64/ttyd-utils
ttyd_utils_master_directory = "ttyd-utils-master/"
ttyd_utils_master_source_directory = f"{ttyd_utils_master_directory}source/"

ttydasm_directory = f"{tools_path}/ttydasm.exe"

try:
    import pandas as pd
except ModuleNotFoundError:
    print("Pandas is not installed. Installing now...")
    subprocess.check_call(["pip", "install", "pandas"])
    import pandas as pd

dump_sections_args = [
    'python3',
    f"{ttyd_utils_master_source_directory}dump_sections.py",
    f'--out_path={out_path}',
    f'--dol={dol_directory}',
    f'--rel={rels_directory}/*.rel',
    '--link_address=0x805ba9a0',
    '--link_address_overrides=jon:0x80c779a0,tst:0x80c779a0',
    '--rel_bss_address=0x803c8460'
]

symbol_to_maps_args = [
    'python3',
    f"{ttyd_utils_master_source_directory}symbol_to_maps.py",
    f'--out_path={out_path}',
    f'--symbols_path={ttyd_utils_master_directory}resources/us_symbols.csv',
    '--rel_bss_address=0x803c8460'
]

export_events_args = [
    'python3',
    f"{ttyd_utils_master_source_directory}export_events.py",
    f'--out_path={out_path}',
    f'--symbols_path={ttyd_utils_master_directory}resources/us_symbols.csv',
    f'--ttydasm_exe={ttydasm_directory}'
]

export_classes_args = [
    'python3',
    f"{ttyd_utils_master_source_directory}export_classes.py",
    f'--out_path={out_path}',
    f'--symbols_path={ttyd_utils_master_directory}resources/us_symbols.csv',
]

combine_event_dumps_args = [
    'python3',
    f"{ttyd_utils_master_source_directory}combine_event_dumps.py",
    f'--out_path={out_path}',
]

sort_events_by_prefix_args = [
    'python3',
    'tools/sort_events_by_prefix.py'
]

# List of rel files to check
rels = ["aaa", "aji", "bom", "dmo", "dou", "eki", "end", "gon", "gor", "gra", "hei", "hom", "jin", "jon", "kpa", "las", "moo", "mri", "muj",
"nok", "pik", "rsh", "sys", "tik", "tou", "tou2", "usu", "win", "yuu"]

# List of expected md5 values, ordered by the same index as the rel files
md5s = [
'f3ca3df5425a7eae7d65ecd43f9863b7', '2c123a7e426d334ffe4456ac94bff1d5', '7c54f5ee5eb30f24791ab3f969e93c56',
'eb07479364d1053cf63bf16ac6ae49fa', '8021d89909032192ec0c268d0119aa79', '95429d3a408e6b7423d6815a9de15f88',
'065a7f464a043d8253ffe69085a7355c', 'd5e494ccdbfdb4b9e74959bed81512a4', '375b3ce1e1fa8ac865c94b828c10ea28',
'6ca6acfec9993d3c3dabbed36d1a303c', '0c7a940e8a93908f73f85fd1faeec4ba', '4ab70b1215adeeba3e176dbbb2ddf6d2',
'8b309402f80e1e4597f70089a70ae68c', '7440b6821e095093dd1cacc3d8cad045', '75946e7686ce6f624bbdf1a60bec91d3',
'157527d44e48a7530ca79aec568eebaa', 'e5cc511f622f31ea2ecfcf675844b624', 'e3e8874fa43a72988c9c305493e07c42',
'4a903ad264e44c5ef64f549899bcd649', 'a44ee0df5d6fb9207ff70659cfdd9817', '6961bf10d8eeed70ffce58712551bd2f',
'88eaa0bc867e3b24724fcf22edcc60e5', 'e5655488ff599c5cfc3f42fd30df7451', 'ac17d353639983147231e2a0d6cf80b5',
'd9ff80367fb5f9a43efe2f73a620ca54', 'ac7039fd4c377077ee0d69124fef3d89', '7607bb4ca39ed0576175cd6dce840095',
'6cc3cf0dc6d26787ea0e0a11cc3254d5', '124e474373a7965e0e45fc845f9c9b3b']

dol_md5 = '9800df7555210cb392e0cbc9f88488c5'

failed_file_count = 0

if not os.path.isdir(ttyd_tools_directory):
    print("ttyd-tools not found.")
    print("Get ttyd-tools from https://github.com/PistonMiner/ttyd-tools")
    input()
    sys.exit(1)

if not os.path.isdir(ttyd_utils_master_directory):
    print("ttyd-utils-master not found.")
    print("Get ttyd-utils-master from https://github.com/jdaster64/ttyd-utils")
    input()
    sys.exit(1)

if not os.path.isdir(rels_directory):
    print("Rel directory at iso/files/rel/ could not be found.")
    print("Extract an iso to the iso/ directory.")
    print("Using dolphin \"extract entire disc\"")
    print("Press any key to exit...")
    input()
    sys.exit(1)

# Open the file and read its contents
with open(dol_directory, 'rb') as f:
    data = f.read()
    # Calculate the md5 hash of the file contents
    md5 = hashlib.md5(data).hexdigest()
    if md5 == dol_md5:
        print(f"main.dol - \033[1;32mSuccess:\033[0m {md5}")
    else:
        print(f"main.dol - \033[1;31mFail:\033[0m {md5}")
        print("main.dol md5 does not match")
        print("Press any key to exit...")
        input()
        sys.exit(1)


# Loop through each rel file in the directory
for i, rel in enumerate(rels):
    # Create the full path to the rel file
    filepath = os.path.join(rels_directory, rel + '.rel')
    
    # Open the file and read its contents
    with open(filepath, 'rb') as f:
        data = f.read()
        
    # Calculate the md5 hash of the file contents
    md5 = hashlib.md5(data).hexdigest()
    
    # Compare the calculated md5 to the expected md5 for this rel file
    if md5 == md5s[i]:
        print(f"{rel}.rel - \033[1;32mSuccess:\033[0m {md5}")
    else:
        print(f"{rel}.rel - \033[1;31mFail:\033[0m {md5}")
        failed_file_count += 1

if failed_file_count != 0:
    print("A non-matching rel file was found")
    print("Press any key to exit...")
    input()
    sys.exit(1)


# Use the os.makedirs() function to create the folder
os.makedirs(out_path, exist_ok=True)

# Use subprocess.run() to call the script and wait for it to finish
completed_process = subprocess.run(dump_sections_args, check=True)
if completed_process.returncode != 0:
    print(f"Error: the script exited with status {completed_process.returncode}")


completed_process = subprocess.run(symbol_to_maps_args, check=True)
if completed_process.returncode != 0:
    print(f"Error: the script exited with status {completed_process.returncode}")


completed_process = subprocess.run(export_events_args, check=True)
if completed_process.returncode != 0:
    print(f"Error: the script exited with status {completed_process.returncode}")

completed_process = subprocess.run(export_classes_args, check=True)
if completed_process.returncode != 0:
    print(f"Error: the script exited with status {completed_process.returncode}")


# completed_process = subprocess.run(combine_event_dumps_args, check=True)
# if completed_process.returncode != 0:
#     print(f"Error: the script exited with status {completed_process.returncode}")


completed_process = subprocess.run(sort_events_by_prefix_args, check=True)
if completed_process.returncode != 0:
    print(f"Error: the script exited with status {completed_process.returncode}")
