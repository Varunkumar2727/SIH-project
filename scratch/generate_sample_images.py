import os
import cv2
import numpy as np

os.makedirs("data/sample_images", exist_ok=True)

w, h = 800, 600
img = np.zeros((h, w, 3), dtype=np.uint8)

# 1. Bare land base (warm tan/brown ground: BGR (80, 140, 170))
img[:] = (80, 140, 170)

# 2. Add vegetation patches (Vibrant Emerald green fields: BGR (30, 160, 30))
cv2.ellipse(img, (200, 150), (120, 90), 20, 0, 360, (30, 160, 30), -1)
cv2.ellipse(img, (650, 450), (140, 100), -15, 0, 360, (40, 170, 40), -1)
cv2.circle(img, (150, 480), 80, (25, 150, 25), -1)

# Fine tree details
for _ in range(25):
    rx = np.random.randint(60, 320)
    ry = np.random.randint(60, 240)
    cv2.circle(img, (rx, ry), np.random.randint(10, 22), (20, 130, 20), -1)

# 3. Add asphalt roads (Slate gray: BGR (70, 70, 70))
cv2.rectangle(img, (0, 280), (w, 330), (70, 70, 70), -1)
cv2.rectangle(img, (400, 0), (450, h), (65, 65, 65), -1)

# Road markings (White dashes)
for x in range(10, w, 40):
    cv2.line(img, (x, 305), (x + 20, 305), (230, 230, 230), 2)
for y in range(10, h, 40):
    cv2.line(img, (425, y), (425, y + 20), (230, 230, 230), 2)

# 4. Add Buildings (Red, Orange, Blue roof structures)
# Block 1 (North-West)
cv2.rectangle(img, (50, 50), (160, 130), (30, 40, 210), -1)    # Red roof BGR
cv2.rectangle(img, (180, 60), (260, 120), (40, 140, 230), -1)  # Orange roof BGR
cv2.rectangle(img, (280, 50), (370, 140), (200, 130, 40), -1)  # Blue roof BGR

# Block 2 (North-East)
cv2.rectangle(img, (480, 50), (590, 130), (35, 45, 215), -1)   # Red roof
cv2.rectangle(img, (620, 60), (740, 140), (30, 130, 220), -1)  # Orange roof
cv2.rectangle(img, (490, 160), (600, 240), (210, 120, 40), -1) # Blue roof

# Block 3 (South-West)
cv2.rectangle(img, (50, 360), (150, 440), (40, 50, 220), -1)   # Red roof
cv2.rectangle(img, (260, 360), (360, 450), (30, 120, 210), -1) # Orange roof

# Block 4 (South-East)
cv2.rectangle(img, (480, 360), (580, 440), (30, 40, 210), -1)  # Red roof
cv2.rectangle(img, (600, 350), (720, 420), (40, 140, 230), -1) # Orange roof

# Add subtle Gaussian noise without uint8 wrap around
noise = np.random.normal(0, 3, img.shape)
img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

cv2.imwrite("data/sample_images/sample_urban_1.jpg", img)
print("Updated sample_urban_1.jpg with correct uint8 clipping.")
