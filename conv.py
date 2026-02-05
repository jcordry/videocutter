#!/usr/bin/env python3

import sys
import subprocess
import os

def convert_mkv_to_mp4(input_file):
    if not input_file.lower().endswith(".mkv"):
        print("Error: Input file must be an .mkv file")
        sys.exit(1)

    if not os.path.isfile(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    output_file = os.path.splitext(input_file)[0] + ".mp4"

    cmd = [
        "ffmpeg",
        "-y",                # overwrite output if it exists
        "-i", input_file,
        "-c:v", "copy",      # copy video stream if possible
        "-c:a", "copy",      # copy audio stream if possible
        "-movflags", "+faststart",
        output_file
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"Conversion successful: {output_file}")
    except subprocess.CalledProcessError:
        print("Stream copy failed, retrying with re-encoding...")

        # Fallback: re-encode
        cmd_reencode = [
            "ffmpeg",
            "-y",
            "-i", input_file,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-movflags", "+faststart",
            output_file
        ]

        subprocess.run(cmd_reencode, check=True)
        print(f"Conversion successful (re-encoded): {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python mkv_to_mp4.py <input.mkv>")
        sys.exit(1)

    convert_mkv_to_mp4(sys.argv[1])
