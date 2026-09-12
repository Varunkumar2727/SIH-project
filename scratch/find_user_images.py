import glob
import os
import cv2

temp_dir = r"C:\Users\varun\.gemini\antigravity-ide\brain\9d0ce26a-7a02-452b-aba9-7a9c0dcb0180\.tempmediaStorage"
files = glob.glob(os.path.join(temp_dir, "*.png")) + glob.glob(os.path.join(temp_dir, "*.jpg"))
files.sort(key=os.path.getmtime, reverse=True)

print("Latest files:")
for f in files[:6]:
    img = cv2.imread(f)
    if img is not None:
        print(f, img.shape)
