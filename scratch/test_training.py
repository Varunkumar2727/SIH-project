import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.model_training import train_aerial_segmentation_model

print("Testing Model Training Pipeline...")
history = train_aerial_segmentation_model(epochs=5)
print("Training execution verified cleanly!")
