import cv2
import numpy as np

img = cv2.imread("data/sample_images/sample_urban_1.jpg")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Crop building region (50..160, 50..130)
bld_crop = hsv[50:130, 50:160]
print("Building HSV mean:", np.mean(bld_crop, axis=(0, 1)))

# Check road mask (0..280 to w..330)
road_crop = hsv[280:330, 0:800]
print("Road HSV mean:", np.mean(road_crop, axis=(0, 1)))
