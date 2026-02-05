#!/usr/bin/env python3

import cv2
import numpy as np

# Path to your image
image_path = "variance.png"

# Load image in grayscale
gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

if gray is None:
    raise ValueError("Image not found. Check the path.")


h, w = gray.shape
left_crop = int(w * 0.13)   # crop 13% from left
right_crop = int(w * 0.73)  # crop 27% from right
top_crop = int(h * 0.13)  # crop 27% from right
roi = gray[top_crop:h, left_crop:right_crop]  # keep center region only

# Compute variance
variance = np.var(roi)

print(f"Variance of pixel intensities: {variance}")
