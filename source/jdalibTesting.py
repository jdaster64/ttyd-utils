from pathlib import Path
import jdalibpy.flags as flags
import sys

flags = flags.Flags()
flags.DefineString("out", default_value="tools-out")
argc, argv = flags.ParseFlags(sys.argv[1:])
out = flags.GetFlag("out")
print(f"out path: {out}")

# Check if file exists in the out directory
out_dir = Path(out)
file_to_check = out_dir / "README.md"  # Replace filename.txt with your file name
if file_to_check.exists():
    print("File exists in the out directory")
else:
    print("File does not exist in the out directory")