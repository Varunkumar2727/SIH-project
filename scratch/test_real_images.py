import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.detection import analyze_image
from services.parcel_detection import generate_proposed_parcels

test_images = [
    "data/sample_images/real_aerial_1.jpg",
    "data/sample_images/real_aerial_2.jpg",
    "data/sample_images/real_aerial_3.jpg"
]

for img_path in test_images:
    filename = os.path.basename(img_path)
    print(f"\n=================== TESTING {filename} ===================")
    meta = {"is_georeferenced": False, "crs": "Image is not georeferenced"}
    
    results = analyze_image(img_path, filename.replace(".", "_"), meta)
    parcels = generate_proposed_parcels(results, meta)
    results["parcels"] = parcels["parcels"]
    results["stats"]["proposed_parcels"] = len(parcels["parcels"])
    
    print(f"Dimensions: {results['dimensions']['width']}x{results['dimensions']['height']}")
    print("Detection Mode:", results["detection_mode"])
    print("Stats:", json.dumps(results["stats"], indent=2))
