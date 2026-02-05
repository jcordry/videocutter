#!/usr/bin/env python3

import sys
import subprocess
import tempfile
import os

def main():
    if len(sys.argv) < 3:
        print("Usage: python join_mp4s.py output.mp4 input1.mp4 input2.mp4 ...")
        sys.exit(1)

    output_file = sys.argv[1]
    input_files = sys.argv[2:]

    # Create a temporary file list for ffmpeg concat demuxer
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        for file in input_files:
            if not os.path.isfile(file):
                print(f"File not found: {file}")
                sys.exit(1)
            # ffmpeg requires each file to be prefixed with 'file'
            f.write(f"file '{os.path.abspath(file)}'\n")
        list_file = f.name

    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            output_file
        ]

        subprocess.run(cmd, check=True)
        print(f"Successfully created {output_file}")

    except subprocess.CalledProcessError:
        print("ffmpeg failed to concatenate the files.")
        sys.exit(1)

    finally:
        os.remove(list_file)

if __name__ == "__main__":
    main()
