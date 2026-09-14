import os
import json
import uuid
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image

router = APIRouter(prefix="/api")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
MODELS_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": "GeoCadastral AI",
        "version": "1.0.0",
        "timestamp": time.time()
    }


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    allowed_exts = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed formats: JPG, JPEG, PNG, TIFF, GeoTIFF."
        )

    image_id = f"img_{uuid.uuid4().hex[:10]}"
    file_path = os.path.join(UPLOAD_DIR, f"{image_id}{ext}")

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    try:
        with Image.open(file_path) as img:
            width, height = img.size
            format_name = img.format
            mode = img.mode
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid or corrupted image file: {str(e)}")

    from services.geospatial import extract_geotiff_metadata

    if ext in [".tif", ".tiff"]:
        geospatial_meta = extract_geotiff_metadata(file_path)
        is_georeferenced = geospatial_meta.get("georeferenced", False)
        crs_info = geospatial_meta.get("crs") if is_georeferenced else (geospatial_meta.get("reason") or "Image is not georeferenced")
        bounds = geospatial_meta.get("bounds")
        transform = geospatial_meta.get("transform")
    else:
        is_georeferenced = False
        crs_info = "Image is not georeferenced"
        bounds = None
        transform = None
        geospatial_meta = {
            "georeferenced": False,
            "crs": "Not available",
            "epsg": None,
            "coordinate_type": "pixel",
            "units": "pixels",
            "measurement": "Pixel / Manual Calibration",
            "bounds": None,
            "pixel_size": None,
            "transform": None,
            "width": width,
            "height": height
        }

    meta = {
        "image_id": image_id,
        "filename": file.filename,
        "saved_path": file_path,
        "url": f"/api/images/upload/{image_id}{ext}",
        "width": width,
        "height": height,
        "format": format_name,
        "mode": mode,
        "is_georeferenced": is_georeferenced,
        "crs": crs_info,
        "bounds": bounds,
        "transform": transform,
        "geospatial": geospatial_meta,
        "upload_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    meta_path = os.path.join(UPLOAD_DIR, f"{image_id}_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return meta


@router.post("/analyze/{image_id}")
async def analyze_image_endpoint(image_id: str):
    from services.ai.feature_detector import FeatureDetector
    from services.parcel.parcel_engine import ParcelEngine
    from services.ai.overlay_generator import generate_ai_overlay
    from services.geojson_export import export_to_geojson

    matching_files = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(image_id) and not f.endswith("_meta.json")]
    if not matching_files:
        raise HTTPException(status_code=404, detail=f"Image ID '{image_id}' not found.")

    image_filename = matching_files[0]
    image_path = os.path.join(UPLOAD_DIR, image_filename)

    meta_path = os.path.join(UPLOAD_DIR, f"{image_id}_meta.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            meta = json.load(f)

    # 1. Real AI Feature Detection via ONNX Model / ModelManager
    try:
        detector = FeatureDetector()
        detection_results = detector.detect_features(image_path, meta)
    except Exception as e:
        # Graceful fallback to OpenCV heuristic if AI encounters environment issues
        from services.detection import analyze_image
        detection_results = analyze_image(image_path, image_id, meta)

    # 2. Topological Parcel Boundary Delineation (Curtilage Buffer + Road Separation)
    try:
        parcels = ParcelEngine.process_proposed_parcels(detection_results, meta)
    except Exception as e:
        parcels = []

    detection_results["image_id"] = image_id
    detection_results["detection_mode"] = "AI Deep Learning (ONNX Runtime)"
    detection_results["parcels"] = parcels
    detection_results["stats"]["proposed_parcels"] = len(parcels)
    detection_results["geospatial"] = meta.get("geospatial")
    detection_results["is_georeferenced"] = meta.get("is_georeferenced", False)
    detection_results["crs"] = meta.get("crs")
    detection_results["transform"] = meta.get("transform")

    # 3. High-Contrast Overlay Image Generation
    try:
        overlay_url = generate_ai_overlay(image_path, image_id, detection_results, parcels, RESULTS_DIR)
        detection_results["overlay_url"] = overlay_url
    except Exception:
        detection_results["overlay_url"] = ""

    geojson_data = export_to_geojson(detection_results, meta)
    geojson_path = os.path.join(RESULTS_DIR, f"{image_id}.geojson")
    with open(geojson_path, "w") as f:
        json.dump(geojson_data, f, indent=2)

    results_path = os.path.join(RESULTS_DIR, f"{image_id}_results.json")
    with open(results_path, "w") as f:
        json.dump(detection_results, f, indent=2)

    return detection_results


@router.post("/train")
async def train_model_endpoint(epochs: int = 5):
    """Triggers ML Segmentation model training pipeline."""
    from services.model_training import train_aerial_segmentation_model
    try:
        history = train_aerial_segmentation_model(epochs=epochs)
        return {
            "status": "success",
            "message": "AI Segmentation Model training completed successfully!",
            "epochs": epochs,
            "training_history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")


@router.get("/results/{image_id}")
async def get_results(image_id: str, measurement_mode: str = "pixels"):
    results_path = os.path.join(RESULTS_DIR, f"{image_id}_results.json")
    if not os.path.exists(results_path):
        raise HTTPException(status_code=404, detail=f"No results found for image ID '{image_id}'.")

    with open(results_path, "r") as f:
        data = json.load(f)

    meta_path = os.path.join(UPLOAD_DIR, f"{image_id}_meta.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            meta = json.load(f)

    from services.geospatial import MeasurementService
    formatter = MeasurementService.get_formatter(measurement_mode, meta)

    if "features" in data:
        for ftype, features_list in data["features"].items():
            for feature in features_list:
                feature["formatted_area"] = formatter.format_area(
                    feature.get("area_px", 0),
                    polygon=feature.get("polygon")
                )
    
    if "parcels" in data:
        for parcel in data["parcels"]:
            parcel["formatted_area"] = formatter.format_area(
                parcel.get("area_px", 0),
                polygon=parcel.get("polygon")
            )

    data["calibration"] = meta.get("calibration")
    data["geospatial"] = meta.get("geospatial")
    data["is_georeferenced"] = meta.get("is_georeferenced", False)
    data["crs"] = meta.get("crs")
    data["transform"] = meta.get("transform")
    data["gcps"] = meta.get("gcps", [])
    data["gcp_transformation"] = meta.get("gcp_transformation")
    data["active_georeferencing"] = meta.get("active_georeferencing")

    # Determine clearly identified georeferencing method
    if meta.get("active_georeferencing") == "gcp" and meta.get("gcp_transformation"):
        data["georeferencing_method"] = "GCP Affine Transformation"
    elif meta.get("is_georeferenced"):
        data["georeferencing_method"] = "GeoTIFF Native CRS/Transform"
    elif meta.get("calibration"):
        data["georeferencing_method"] = "Manual Calibration"
    else:
        data["georeferencing_method"] = "Pixel Mode"

    return data


@router.get("/coordinates/{image_id}")
async def get_coordinates(image_id: str, x: float, y: float):
    """
    Returns real-world coordinates for a given pixel (x=col, y=row).
    Prioritizes active GCP transformation if applied, otherwise native GeoTIFF.
    """
    meta_path = os.path.join(UPLOAD_DIR, f"{image_id}_meta.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail=f"Image metadata for '{image_id}' not found.")

    with open(meta_path, "r") as f:
        meta = json.load(f)

    geospatial = meta.get("geospatial") or {}
    gcp_trans = meta.get("gcp_transformation") or {}
    is_gcp_active = (meta.get("active_georeferencing") == "gcp") and bool(gcp_trans.get("transform"))

    if is_gcp_active:
        transform = gcp_trans["transform"]
        crs = gcp_trans["crs"]
        is_georef = True
        method = "gcp"
    else:
        is_georef = meta.get("is_georeferenced", False) or geospatial.get("georeferenced", False)
        transform = meta.get("transform") or geospatial.get("transform")
        crs = meta.get("crs") or geospatial.get("crs")
        method = "geotiff" if is_georef else "none"

    if not is_georef or not transform or not crs:
        return {
            "pixel": {"x": round(x, 2), "y": round(y, 2)},
            "georeferenced": False,
            "coordinates": "Not available"
        }

    try:
        from services.geospatial import pixel_to_world, transform_coordinates
        world_x, world_y = pixel_to_world(x, y, transform)
        lon, lat = transform_coordinates(world_x, world_y, src_crs=crs, dst_crs="EPSG:4326")
        is_proj = "4326" not in str(crs)
        return {
            "pixel": {"x": round(x, 2), "y": round(y, 2)},
            "georeferenced": True,
            "method": method,
            "crs": crs,
            "rmse": gcp_trans.get("rmse") if is_gcp_active else None,
            "coordinate_type": "projected" if is_proj else "geographic",
            "units": "metre" if is_proj else "degree",
            "native": {
                "x": round(world_x, 2),
                "y": round(world_y, 2),
                "label_x": "Easting" if is_proj else "Longitude",
                "label_y": "Northing" if is_proj else "Latitude"
            },
            "wgs84": {
                "lat": round(lat, 6),
                "lon": round(lon, 6)
            }
        }
    except Exception as e:
        return {
            "pixel": {"x": round(x, 2), "y": round(y, 2)},
            "georeferenced": False,
            "coordinates": "Not available",
            "error": str(e)
        }


# =========================================================================
# Ground Control Points (GCP) Endpoints
# =========================================================================

from pydantic import BaseModel, Field

class GCPItemRequest(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    image_x: float
    image_y: float
    coordinate_type: str = "projected"
    world_x: Optional[float] = None
    world_y: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation: Optional[float] = None
    crs: str = "EPSG:32643"
    description: Optional[str] = None
    source: Optional[str] = "Field Survey"
    accuracy: Optional[float] = None

class GCPCalculateRequest(BaseModel):
    target_crs: Optional[str] = None


@router.get("/gcps/{image_id}")
async def get_gcps_endpoint(image_id: str):
    meta_path = os.path.join(UPLOAD_DIR, f"{image_id}_meta.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail=f"Image metadata for '{image_id}' not found.")

    with open(meta_path, "r") as f:
        meta = json.load(f)

    return {
        "image_id": image_id,
        "gcps": meta.get("gcps", []),
        "transformation": meta.get("gcp_transformation"),
        "active": meta.get("active_georeferencing") == "gcp"
    }


@router.post("/gcps/{image_id}")
async def add_gcp_endpoint(image_id: str, req: GCPItemRequest):
    meta_path = os.path.join(UPLOAD_DIR, f"{image_id}_meta.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail=f"Image metadata for '{image_id}' not found.")

    with open(meta_path, "r") as f:
        meta = json.load(f)

    from services.gcp import validate_gcp, normalize_gcp

    gcp_dict = req.dict()
    is_valid, err_msg = validate_gcp(gcp_dict)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    gcps = meta.get("gcps", [])
    index = len(gcps) + 1
    normalized = normalize_gcp(gcp_dict, index=index)

    existing_idx = next((i for i, g in enumerate(gcps) if g["id"] == normalized["id"]), None)
    if existing_idx is not None:
        gcps[existing_idx] = normalized
    else:
        gcps.append(normalized)

    meta["gcps"] = gcps

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return {
        "status": "success",
        "gcp": normalized,
        "total_gcps": len(gcps)
    }


@router.delete("/gcps/{image_id}/{gcp_id}")
async def delete_gcp_endpoint(image_id: str, gcp_id: str):
    meta_path = os.path.join(UPLOAD_DIR, f"{image_id}_meta.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail=f"Image metadata for '{image_id}' not found.")

    with open(meta_path, "r") as f:
        meta = json.load(f)

    gcps = meta.get("gcps", [])
    new_gcps = [g for g in gcps if g["id"] != gcp_id]

    if len(new_gcps) == len(gcps):
        raise HTTPException(status_code=404, detail=f"GCP with ID '{gcp_id}' not found.")

    meta["gcps"] = new_gcps

    if len(new_gcps) < 3:
        meta["gcp_transformation"] = None
        if meta.get("active_georeferencing") == "gcp":
            meta["active_georeferencing"] = None

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return {
        "status": "success",
        "deleted_id": gcp_id,
        "remaining_gcps": len(new_gcps)
    }


@router.post("/gcps/{image_id}/calculate")
async def calculate_gcp_endpoint(image_id: str, req: Optional[GCPCalculateRequest] = None):
    meta_path = os.path.join(UPLOAD_DIR, f"{image_id}_meta.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail=f"Image metadata for '{image_id}' not found.")

    with open(meta_path, "r") as f:
        meta = json.load(f)

    gcps = meta.get("gcps", [])
    if len(gcps) < 3:
        raise HTTPException(
            status_code=400,
            detail=f"At least 3 Ground Control Points are required to calculate an affine transformation (currently {len(gcps)})."
        )

    from services.gcp import calculate_gcp_transformation

    target_crs = req.target_crs if req and req.target_crs else meta.get("crs")
    try:
        res = calculate_gcp_transformation(
            gcps=gcps,
            target_crs=target_crs,
            image_width=meta.get("width"),
            image_height=meta.get("height")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    meta["gcp_transformation"] = res
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return res


@router.post("/gcps/{image_id}/apply")
async def apply_gcp_endpoint(image_id: str):
    """
    Activates the calculated GCP transformation as the primary georeferencing method.
    Re-exports GeoJSON and updates results accordingly.
    """
    meta_path = os.path.join(UPLOAD_DIR, f"{image_id}_meta.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail=f"Image metadata for '{image_id}' not found.")

    with open(meta_path, "r") as f:
        meta = json.load(f)

    gcp_trans = meta.get("gcp_transformation")
    if not gcp_trans or not gcp_trans.get("transform"):
        raise HTTPException(status_code=400, detail="No calculated GCP transformation found. Please calculate transformation first.")

    meta["active_georeferencing"] = "gcp"

    # Re-export GeoJSON with active GCP transform if results exist
    results_path = os.path.join(RESULTS_DIR, f"{image_id}_results.json")
    if os.path.exists(results_path):
        with open(results_path, "r") as f:
            detection_results = json.load(f)
        from services.geojson_export import export_to_geojson
        geojson_data = export_to_geojson(detection_results, meta)
        geojson_path = os.path.join(RESULTS_DIR, f"{image_id}.geojson")
        with open(geojson_path, "w") as f:
            json.dump(geojson_data, f, indent=2)

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return {
        "status": "success",
        "active_georeferencing": "gcp",
        "rmse": gcp_trans.get("rmse"),
        "crs": gcp_trans.get("crs")
    }


@router.post("/gcps/{image_id}/reset")
async def reset_gcp_endpoint(image_id: str):
    """
    Deactivates GCP georeferencing and restores native GeoTIFF or manual calibration.
    """
    meta_path = os.path.join(UPLOAD_DIR, f"{image_id}_meta.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail=f"Image metadata for '{image_id}' not found.")

    with open(meta_path, "r") as f:
        meta = json.load(f)

    meta["active_georeferencing"] = None

    # Re-export GeoJSON without GCP
    results_path = os.path.join(RESULTS_DIR, f"{image_id}_results.json")
    if os.path.exists(results_path):
        with open(results_path, "r") as f:
            detection_results = json.load(f)
        from services.geojson_export import export_to_geojson
        geojson_data = export_to_geojson(detection_results, meta)
        geojson_path = os.path.join(RESULTS_DIR, f"{image_id}.geojson")
        with open(geojson_path, "w") as f:
            json.dump(geojson_data, f, indent=2)

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return {
        "status": "success",
        "active_georeferencing": None
    }


from pydantic import BaseModel

class CalibrationRequest(BaseModel):
    pixel_distance: float
    real_distance: float
    unit: str

@router.post("/calibrate/{image_id}")
async def calibrate_image(image_id: str, req: CalibrationRequest):
    meta_path = os.path.join(UPLOAD_DIR, f"{image_id}_meta.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail="Image metadata not found.")

    with open(meta_path, "r") as f:
        meta = json.load(f)

    # Convert unit to meters
    multiplier = 1.0
    if req.unit.lower() == "feet":
        multiplier = 0.3048
    elif req.unit.lower() == "kilometers":
        multiplier = 1000.0

    real_distance_m = req.real_distance * multiplier
    meters_per_pixel = real_distance_m / req.pixel_distance if req.pixel_distance > 0 else 0

    meta["calibration"] = {
        "pixel_distance": req.pixel_distance,
        "real_distance": req.real_distance,
        "unit": req.unit,
        "meters_per_pixel": meters_per_pixel
    }

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return {"status": "success", "calibration": meta["calibration"]}


@router.get("/geojson/{image_id}")
async def get_geojson(image_id: str):
    geojson_path = os.path.join(RESULTS_DIR, f"{image_id}.geojson")
    if not os.path.exists(geojson_path):
        raise HTTPException(status_code=404, detail=f"No GeoJSON found for image ID '{image_id}'.")

    return FileResponse(
        geojson_path,
        media_type="application/geo+json",
        filename=f"geocadastral_{image_id}.geojson"
    )


@router.get("/images/upload/{filename}")
async def get_uploaded_image(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image file not found.")
    return FileResponse(file_path)


@router.get("/images/result/{filename}")
async def get_result_image(filename: str):
    file_path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Overlay image not found.")
    return FileResponse(file_path)
