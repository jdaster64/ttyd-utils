import os
import shutil
import sys

if len(sys.argv) < 2:
    print("Usage: python script.py [directory]")
    sys.exit(1)

# define the directory path and list of prefixes to sort
directory = os.path.abspath(sys.argv[1])
prefixes = ["_main_battle", "_main_eff", "_main_evt", "_main_mot", "_main_npc", "_main_party", "_main_sac", "_main_seq", "_main_unit", "_main_win",
"aaa", "aji", "bom", "dmo", "dou", "eki", "end", "gon", "gor", "gra", "hei", "hom", "jin", "jon", "kpa", "las", "moo", "mri", "muj",
"nok", "pik", "rsh", "sys", "tik", "tst", "tou2", "tou", "usu", "win", "yuu"]

# create subdirectories for each prefix
for prefix in prefixes:
    subdir_path = os.path.join(directory, prefix)
    if not os.path.exists(subdir_path):
        os.mkdir(subdir_path)

# get all the files in the directory
all_files = os.listdir(directory)

# loop through each file and move to its corresponding subdirectory
for filename in all_files:
    src_path = os.path.join(directory, filename)
    if not os.path.isfile(src_path): # skip directories
        continue
    for prefix in prefixes:
        if filename.startswith(prefix):
            dst_path = os.path.join(directory, prefix, filename)
            if os.path.isdir(os.path.join(directory, prefix, filename)): # skip existing directories with the same name
                continue
            shutil.move(src_path, dst_path)
            break # move to next file once prefix is found
