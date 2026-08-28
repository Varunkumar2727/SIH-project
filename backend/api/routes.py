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

    is_georeferenced = False
    crs_info = "Image is not georeferenced"
    bounds = None

    if ext in [".tif", ".tiff"]:
        try:
            import rasterio
            with rasterio.open(file_path) as src:
                if src.crs is not None:
                    is_georeferenced = True
                    crs_info = str(src.crs)
                    bounds = [src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top]
        except Exception:
            pass

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
        "upload_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    meta_path = os.path.join(UPLOAD_DIR, f"{image_id}_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return meta


@router.post("/analyze/{image_id}")
async def analyze_image_endpoint(image_id: str):
    from services.detection import analyze_image
    from services.parcel_detection import generate_proposed_parcels
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

    try:
        detection_results = analyze_image(image_path, image_id, meta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during feature detection: {str(e)}")

    try:
        parcel_results = generate_proposed_parcels(detection_results, meta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during parcel boundary generation: {str(e)}")

    detection_results["parcels"] = parcel_results["parcels"]
    detection_results["stats"]["proposed_parcels"] = len(parcel_results["parcels"])

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
                feature["formatted_area"] = formatter.format_area(feature.get("area_px", 0))
    
    if "parcels" in data:
        for parcel in data["parcels"]:
            parcel["formatted_area"] = formatter.format_area(parcel.get("area_px", 0))

    data["calibration"] = meta.get("calibration")
    return data


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
