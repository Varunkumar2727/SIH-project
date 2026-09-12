import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.detection import analyze_image
from services.parcel_detection import generate_proposed_parcels
from services.geojson_export import export_to_geojson

img_path = "data/sample_images/sample_urban_1.jpg"
meta = {"is_georeferenced": False, "crs": "Image is not georeferenced"}

results = analyze_image(img_path, "test_sample_1", meta)
parcels = generate_proposed_parcels(results, meta)
results["parcels"] = parcels["parcels"]
results["stats"]["proposed_parcels"] = len(parcels["parcels"])

geojson_doc = export_to_geojson(results, meta)

print("=== PIPELINE TEST RESULTS ===")
print("Detection Mode:", results["detection_mode"])
print("Stats:", json.dumps(results["stats"], indent=2))
print("GeoJSON Features Count:", len(geojson_doc["features"]))
print("Sample GeoJSON Feature:", json.dumps(geojson_doc["features"][0], indent=2))
