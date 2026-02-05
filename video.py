#!/usr/bin/env python3

import os
import subprocess
# import whisper
import cv2
import numpy as np

# -----------------------------
# CONFIGURATION
# -----------------------------
VIDEO_PATH = "lecture.mp4"
OUTPUT_DIR = "sections"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SILENCE_THRESHOLD = "-30dB"   # FFmpeg silence detection threshold
SILENCE_DURATION = 1          # Minimum silence duration in seconds

#### This BLANK_VARIANCE_THRESHOLD will need to be calibrated for each slide
#### model

BLANK_VARIANCE_THRESHOLD = 75   # Variance threshold for blank slide detection
FRAME_INTERVAL = 2               # Seconds between frame checks
PAUSE_THRESHOLD = 10             # Audio pause threshold in seconds
MAX_GAPS_BETWEEN_BOUNDARIES = 5  # Max gap in seconds between 2 consecutive
                                 # blank slide frames


# -----------------------------
# 1. Detect blank slides
# -----------------------------

print("Detecting blank slides...")
cap = cv2.VideoCapture(VIDEO_PATH)
fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

visual_boundaries = [0.0]
frame_step = int(fps * FRAME_INTERVAL)

print("framestep: ", frame_step)

print("Getting boundaries")

last = 0.0

for i in range(0, frame_count, frame_step):
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ret, frame = cap.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    # Windows Panopto
    left_crop = int(w * 0.13)   # crop 13% from left
    right_crop = int(w * 0.73)  # crop 27% from right to ignore the webcam
    top_crop = int(h * 0.13)    # crop 13% from the top
    bottom_crop = h
    # Linux OBS
    # left_crop = int(w * 0.218)
    # right_crop = int(w * 0.898)
    # top_crop = int(h * 0.169)
    # bottom_crop = int(h * 0.981)
    roi = gray[top_crop:bottom_crop, left_crop:right_crop]  # keep center region only
    variance = np.var(roi)
    last = i / fps
    # print(i, last, variance)
    if variance < BLANK_VARIANCE_THRESHOLD:  # likely blank slide
        timestamp = last
        visual_boundaries.append(timestamp)
        print(i, timestamp, variance)
print("Boundaries: ", visual_boundaries)

# Add the last timestamp to get the last section
visual_boundaries.append(last)

cap.release()

# -----------------------------
# 2. Merge nearby boundaries
# -----------------------------

# Sort visual boundaries
# visual_boundaries.sort()

# Merge consecutive timestamps within a gap
merged_visual_boundaries = []
if visual_boundaries:
    current = visual_boundaries[0]
    for ts in visual_boundaries[1:]:
        if ts - current > MAX_GAPS_BETWEEN_BOUNDARIES:  # gap threshold in seconds
            merged_visual_boundaries.append(current)
            current = ts
    merged_visual_boundaries.append(current)
else:
    merged_visual_boundaries = []

# Replace visual_boundaries with merged version
visual_boundaries = merged_visual_boundaries
print("Merged boundaries: ", visual_boundaries)

# -----------------------------
# 3. Cut video into sections
# -----------------------------
print("Cutting video into sections...")
section_files = []
for idx in range(len(visual_boundaries) - 1):
    start = visual_boundaries[idx]
    end = visual_boundaries[idx + 1]
    output_file = os.path.join(OUTPUT_DIR, f"section_{idx+1}.mp4")
    cmd = [
        "ffmpeg",
        "-i", VIDEO_PATH,
        "-ss", str(start),
        "-to", str(end),
        "-c", "copy",
        output_file
    ]
    subprocess.run(cmd)
    section_files.append(output_file)


# # -----------------------------
# # 4. Remove silence (jump cuts) in each section
# # -----------------------------
# def remove_silence(input_file, output_file):
#     # Detect silence and output timestamps
#     cmd_detect = [
#         "ffmpeg", "-i", input_file,
#         "-af", f"silencedetect=noise={SILENCE_THRESHOLD}:d={SILENCE_DURATION}",
#         "-f", "null", "-"
#     ]
#     result = subprocess.run(cmd_detect, capture_output=True, text=True)
#
#     # Parse timestamps
#     speech_segments = []
#     last_end = 0
#     for line in result.stderr.splitlines():
#         if "silence_start" in line:
#             silence_start = float(line.split("silence_start:")[1])
#             speech_segments.append((last_end, silence_start))
#         if "silence_end" in line:
#             last_end = float(line.split("silence_end:")[1].split("|")[0])
#
#     # Add last segment if needed
#     if last_end < get_video_duration(input_file):
#         speech_segments.append((last_end, get_video_duration(input_file)))
#
#     # Build FFmpeg concat filter
#     filters = []
#     for i, (start, end) in enumerate(speech_segments):
#         filters.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}];"
#                        f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]")
#     filter_complex = "".join(filters) + "".join([f"[v{i}][a{i}]" for i in range(len(filters))]) + f"concat=n={len(filters)}:v=1:a=1[outv][outa]"
#
#     cmd_concat = [
#         "ffmpeg", "-i", input_file,
#         "-filter_complex", filter_complex,
#         "-map", "[outv]", "-map", "[outa]",
#         output_file
#     ]
#     subprocess.run(cmd_concat)
#
# def get_video_duration(file_path):
#     cmd = [
#         "ffprobe", "-v", "error", "-show_entries",
#         "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path
#     ]
#     result = subprocess.run(cmd, capture_output=True, text=True)
#     return float(result.stdout.strip())
#
# print("Removing silence from sections...")
# for section in section_files:
#     output_jumpcut = section.replace(".mp4", "_jumpcut.mp4")
#     remove_silence(section, output_jumpcut)
#
# print("All sections processed with jump cuts!")
#
