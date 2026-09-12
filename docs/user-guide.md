# GeoCadastral AI — Survey Officer & Analyst User Guide

## 1. Getting Started
GeoCadastral AI assists survey officers, revenue department staff, and GIS teams in analyzing aerial drone imagery, verifying cadastral parcel boundaries, and monitoring land changes over time.

---

## 2. Core Operational Workflow

### Step 1: Upload Aerial Imagery
1. Navigate to the **Upload Imagery** card on the dashboard.
2. Select an aerial ortho or satellite image (`.tif`, `.tiff`, `.jpg`, `.png`).
3. If uploading a georeferenced GeoTIFF, the system automatically detects native CRS (e.g. `EPSG:32643`), affine pixel size, and geographic extent.
4. For unreferenced images, click **Calibrate Scale** or add **Ground Control Points (GCP)**.

### Step 2: Survey Control Points (GCP)
1. In the **GCP Calibration** panel, click **Add Ground Control Point**.
2. Click on the map to record pixel coordinates `(x, y)`.
3. Enter known surveyed control coordinates (Easting/Northing in UTM or WGS84 Lat/Lon).
4. After entering at least 3 points, click **Compute Transformation**. Review the calculated RMSE to verify survey accuracy.

### Step 3: Run AI Detection & Parcel Delineation
1. Click **Run AI Detection**.
2. The AI Segmentation Engine runs tiled inference (512x512 with 15% overlap) to segment buildings, roads, vegetation, water, and bare land.
3. The Parcel Engine generates proposed parcel boundaries with deterministic IDs (`AI-P-XXXXXXXX`).

### Step 4: Access Path & Frontage Intelligence
1. Road features are transformed into a topological network.
2. Parcels receive an automatic access assessment:
   * **DIRECT_ACCESS**: Parcel has direct frontage along a road.
   * **MARGINAL_ACCESS**: Parcel is within secondary road buffer.
   * **PHYSICAL_ACCESS_CONCERN**: No direct road connectivity detected.
   *(Note: This represents physical access only, not statutory right-of-way).*

### Step 5: Officer Review Queue & Field Verification
1. Click **Review Queue** in the top navigation bar.
2. Review pending cases generated from temporal changes or cadastral discrepancies.
3. Select a case to inspect evidence. Choose:
   * **Confirm Finding** to attest the observation.
   * **Assign Field Task** to dispatch a field verifier with GPS coordinates.
   * **Reject Finding** if imagery artifact or false alarm.

### Step 6: Export Government Deliverables
1. Click **Download Intelligence Dossier (PDF)** to generate the complete government report.
2. Use **Export GeoJSON** or **Export CSV** to obtain attribute catalogs for GIS software (QGIS, ArcGIS).
