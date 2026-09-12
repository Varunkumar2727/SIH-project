import os
import csv
import json
import zipfile
from typing import Dict, Any, List, Optional

class ExportPackageService:
    """
    Part 8 / Part 13: Geospatial Export & Deliverables Packaging.
    Generates tabular CSV reports, GeoJSON features, and offline survey ZIP bundles.
    """

    @classmethod
    def export_parcels_csv(cls, parcels: List[Dict[str, Any]], output_path: str) -> str:
        """Exports parcel attribute catalog to CSV."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fieldnames = [
            "parcel_id", "layer_type", "area_px", "perimeter_px",
            "compactness", "confidence", "access_status", "distance_to_road_px",
            "frontage_length_px", "status"
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in parcels:
                acc = p.get("accessibility", {})
                writer.writerow({
                    "parcel_id": p.get("id"),
                    "layer_type": p.get("layer_type", "AI_PROPOSED"),
                    "area_px": p.get("area_px", 0.0),
                    "perimeter_px": p.get("perimeter_px", 0.0),
                    "compactness": p.get("compactness", 0.0),
                    "confidence": p.get("confidence", 0.0),
                    "access_status": acc.get("access_status", "UNASSESSED"),
                    "distance_to_road_px": acc.get("distance_to_road_px", 0.0),
                    "frontage_length_px": acc.get("frontage_length_px", 0.0),
                    "status": p.get("status", "PROPOSED")
                })
        return output_path

    @classmethod
    def create_offline_survey_bundle(
        cls,
        output_zip_path: str,
        geojson_path: Optional[str] = None,
        csv_path: Optional[str] = None,
        pdf_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Packs GeoJSON, CSV, PDF, and survey manifest into a single ZIP for air-gapped / field use.
        """
        os.makedirs(os.path.dirname(output_zip_path), exist_ok=True)
        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            if geojson_path and os.path.exists(geojson_path):
                zipf.write(geojson_path, arcname="spatial_features.geojson")
            if csv_path and os.path.exists(csv_path):
                zipf.write(csv_path, arcname="parcel_attributes.csv")
            if pdf_path and os.path.exists(pdf_path):
                zipf.write(pdf_path, arcname="intelligence_dossier.pdf")

            # Include metadata manifest
            manifest = metadata or {}
            manifest["package_type"] = "OFFLINE_SURVEY_BUNDLE"
            zipf.writestr("manifest.json", json.dumps(manifest, indent=2))

        return output_zip_path
