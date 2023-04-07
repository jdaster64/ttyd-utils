import subprocess
import os
import hashlib
import sys
from pathlib import Path
import jdalibpy.flags as flags

if (len(sys.argv) != 8):
    print("""Required Args:\n
        --ver=\"version\"
        --out=\"path_to_out_folder\"
        --rels_directory=\"path_to_rel_folder\"
        --dol_directory=\"path_to_main_dol\"
        --ttyd_tools=\"path_to_ttyd_tools\"
        --ttyd_utils=\"path_to_ttyd_utils\"
        --ttydasm=\"path_to_file\"
        """)
    print("""Example Invocation from ttyd-utils/source/ directory:
        python3 ./setup.py --ver="us" --out="../../tools-out" --rels_directory="../../iso/files/rel" --dol_directory="../../iso/sys/main.dol" --ttyd_tools="../../ttyd-tools" --ttyd_utils="../../ttyd-utils" --ttydasm="../../tools/ttydasm.exe"
        """)
    sys.exit(1)

# Define all flags
flag_mgr = flags.Flags()
flag_mgr.DefineString("ver", default_value="none")
flag_mgr.DefineString("out", default_value="none")
flag_mgr.DefineString("rels_directory", default_value="none")
flag_mgr.DefineString("dol_directory", default_value="none")
flag_mgr.DefineString("ttyd_tools", default_value="none")
flag_mgr.DefineString("ttyd_utils", default_value="none")
flag_mgr.DefineString("ttydasm", default_value="none")

# Parse command-line arguments
argc, argv = flag_mgr.ParseFlags(sys.argv[1:])

# Get values of flags
ver = flag_mgr.GetFlag("ver").lower()
out_path = flag_mgr.GetFlag("out")
rels_directory = flag_mgr.GetFlag("rels_directory")
dol_directory = flag_mgr.GetFlag("dol_directory")
ttyd_tools = flag_mgr.GetFlag("ttyd_tools")
ttyd_utils = flag_mgr.GetFlag("ttyd_utils")
ttydasm = flag_mgr.GetFlag("ttydasm")

# print(f"ttydasm: {ver}")
# print(f"out path: {out_path}")
# print(f"rels_directory: {rels_directory}")
# print(f"dol_directory: {dol_directory}")
# print(f"ttyd_tools: {ttyd_tools}")
# print(f"ttyd_utils: {ttyd_utils}")
# print(f"ttydasm: {ttydasm}")

ttyd_utils_src_dir = f"{ttyd_utils}/source/"


#ttyd-tools
#https://github.com/PistonMiner/ttyd-tools


#ttyd-utils
#https://github.com/jdaster64/ttyd-utils


if (ver == "us"):
    csv = "us_symbols.csv"
    link_addr = '--link_address=0x805ba9a0'
    link_addr_overrides = '--link_address_overrides=jon:0x80c779a0,tst:0x80c779a0'
    rel_bss_addr = '--rel_bss_address=0x803c8460'
elif (ver == "jp"):
    csv = "jp_symbols.csv"
    link_addr = '--link_address=0x805b4420'
    link_addr_overrides = '--link_address_overrides=jon:0x80c71420,tst:0x80c71420'
    rel_bss_addr = '--rel_bss_address=0x803c48e0'
elif (ver == "pal"):
    csv = "eu_symbols.csv"
    link_addr = '--link_address=0x805fb8c0'
    link_addr_overrides = '--link_address_overrides=jon:0x80cb88c0,tst:0x80cb88c0'
    rel_bss_addr = '--rel_bss_address=0x803d44c0'

try:
    import pandas as pd
except ModuleNotFoundError:
    print("Pandas is not installed. Installing now...")
    subprocess.check_call(["pip", "install", "pandas"])
    import pandas as pd

dump_sections_args = [
    'python3',
    f"{ttyd_utils_src_dir}dump_sections.py",
    f'--out_path={out_path}',
    f'--dol={dol_directory}',
    f'--rel={rels_directory}/*.rel',
    f'{link_addr}',
    f'{link_addr_overrides}',
    f'{rel_bss_addr}'
]

symbol_to_maps_args = [
    'python3',
    f"{ttyd_utils_src_dir}symbol_to_maps.py",
    f'--out_path={out_path}',
    f'--symbols_path={ttyd_utils}/resources/{csv}',
    f'{rel_bss_addr}'
]

export_events_args = [
    'python3',
    f"{ttyd_utils_src_dir}export_events.py",
    f'--out_path={out_path}',
    f'--symbols_path={ttyd_utils}/resources/{csv}',
    f'--ttydasm_exe={ttydasm}'
]

export_classes_args = [
    'python3',
    f"{ttyd_utils_src_dir}export_classes.py",
    f'--out_path={out_path}',
    f'--symbols_path={ttyd_utils}/resources/{csv}',
]

combine_event_dumps_args = [
    'python3',
    f"{ttyd_utils_src_dir}combine_event_dumps.py",
    f'--out_path={out_path}',
]

sort_events_by_prefix_args = [
    'python3',
    f"{ttyd_utils_src_dir}sort_events_by_prefix.py",
    f"{out_path}/events",
]

us_dol_md5 = '9800df7555210cb392e0cbc9f88488c5'
us_rels = ["aaa", "aji", "bom", "dmo", "dou", "eki", "end", "gon", "gor", "gra", "hei", "hom", "jin", "jon", "kpa", "las", "moo", "mri", "muj",
"nok", "pik", "rsh", "sys", "tik", "tou", "tou2", "usu", "win", "yuu"]
us_md5s = [
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


pal_dol_md5 = '9ac2fd3b4d3d0efb00d9ee2563c7da24'
pal_rels = ["aaa", "aji", "bom", "dmo", "dou", "eki", "end", "gon", "gor", "gra", "hei", "hom", "jin", "jon", "kpa", "las", "moo", "mri", "muj",
"nok", "pik", "rsh", "sys", "tik", "tou", "tou2", "tst", "usu", "win", "yuu"]
pal_md5s = [
    '07a3a6cf5ff42e0a1453418cb0620f94', 'c11f9cc01ef57110615ed84a50cf7c72', '927581c71ac05a9c6e18ae09f30c08f2',
    '6dd7be05ae9d6e15c30896045432fe3e', 'c05cc4633721adc0205d5e718d182b64', 'def7fa886824c1165c8dd97676ed643f',
    'ecc5774997dc52cebe98b3666267c377', '9a6f892c08291b57331e4e4b3d048291', '326e4af6b775b3729dc205f2f32d5ace',
    '62c32160f3b90c715122c5cb30d262f7', '6f11fe4b0b701ace7c0a7f88b21264ea', 'b467afbe1067142110c47e7692b899b9',
    '14c73e0c89599b56fe93a3d31e21b67b', '50628475c16bf438003e188ddfbc7856', '77eb3e11526600b9e11941a5d44705c5',
    '420537465433c7b9f96485d75cb04679', 'f722a153d7b1f20f665e5e7d5946a3a8', '6c3b639ce286e2a12a0d644dd7611f0b',
    'b8d4c2785fe4448db6d4a7ffa21d2a5c', '40cc8087fa5dffba022d5e6812069cd5', 'ccfcfd86ce75beffffb82fe4dc329a3e',
    '8f37ee4e040f760eb95043844cec6fde', '9abc39cf495e93534fd663df404eda7c', 'a249851048681037c9e8cf92ea84c19f',
    '6b451e92553956f11390dfad5091f060', '7230b8ea8b36c1492519c7a80b7d0e36', '69845d6c8ee11435edb3e642fab54a79',
    '7e030a82e2758edecfe7b8d60a3a9662', '8b631f373f1601ec3af00eb8f86fd825', '15d1a4c8e31666a6d01bcd2de59a5957',
    '25ebdd4978ef4b39d751ccb3236cda2b', '4db17ad0ac333e7523deddf9f2f8bac6'
]

jp_dol_md5 = '67b32111d4855254149542440ea24070'
jp_rels = ["aaa", "aji", "bom", "dmo", "dou", "eki", "end", "gon", "gor", "gra", "hei", "hom", "jin", "jon", "kpa", "las", "moo", "mri", "muj",
"nok", "pik", "rsh", "sys", "tik", "tou", "tou2", "usu", "win", "yuu"]
jp_md5s = [
    '408fc74378eb669b0c07c3d5f7ed3bf7', 'fc18c58f9d3a03fd978265f64f9e6ca8', '0e0a507355e949aa08f1f7dfc47f7705',
    '079fa33ddde37627f9970c836302f74b', 'ee8362bf9a676184fb24c29b829f19b2', 'ebd99038d9896c2c4528fabcdd40cae6',
    '4ca5127bdda82e8be8c14faa544e0397', '6dd060a56c579169c7146df1e9a6821d', '8aeff996005dfd457e6852407a6f038e',
    'b5f78ea4e6a51d398ac5142c096bc8c2', 'd454d744a49c21ae743ee2fab60d2ba5', '6c89b1abd62ab7a420608522b4b6facc',
    '646339544d80047b0fd572864052e405', 'e9bdea6bcdeb06375ba439a571f24559', '0ddda07c5cf76e8ced8c0b704e5917c3',
    '6df4cd281211026a2de8706509292468', '284092810a870aff12666059fdf5eb9a', 'f8462bd42e6f66bded476b2df3bb7a01',
    'a80e2dbed49582b91166faff069ff63b', 'd62666c9053cbba81a4bc87740405723', 'c9f68697351a68b46033cc68a78d1c7c',
    '0630bdf8b783bae0365f3023f453e55c', '1e3fb8d804d39ed3225db7bfe525a515', 'a921cebbcd9160cb3f4b15c20249b78e',
    '17ca61a0a8690d5e6ad196b4f95ee4b9', 'd5a0db39419005cb9d93ac07c5ca3d4f', '0b8f7cfc4ef173db0461539290080d94',
    'a332196692e93ec8bfdd9d3fe9b3fcb1', '29b98c270ab0930f5683e8e198cd292a', '4500720279c007fd200b568ff1e9ed1a',
    '412e5d0bbcd5ee4c879250cec7929977'
]

if (ver == "us"):
    md5s = us_md5s
    rels = us_rels
    dol_md5 = us_dol_md5
elif (ver == "jp"):
    md5s = jp_md5s
    rels = jp_rels
    dol_md5 = jp_dol_md5
elif (ver == "pal"):
    md5s = pal_md5s
    rels = pal_rels
    dol_md5 = pal_dol_md5

combined_dict = {rel: md5 for rel, md5 in zip(rels, md5s)}


failed_file_count = 0

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
for rel, expected_md5 in combined_dict.items():
    # Create the full path to the rel file
    filepath = os.path.join(rels_directory, rel + '.rel')
    
    # Open the file and read its contents
    with open(filepath, 'rb') as f:
        data = f.read()
        
    # Calculate the md5 hash of the file contents
    md5 = hashlib.md5(data).hexdigest()
    
    # Compare the calculated md5 to the expected md5 for this rel file
    if md5 == expected_md5:
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
