# Data Acquisition

## Current status

No real labelled CadastreVision data is included in this repository. The checked-in `data/cadastrevision/` files are synthetic development fixtures and must not be used for claimed training. The training pipeline fails with `REAL CADASTREVISION DATA NOT FOUND` until an authorised subset is installed.

## Primary: CadastreVision / CadNET

- **Contains:** cadastral-boundary benchmark imagery and reference data for the Netherlands; the public CadastreVision repository documents sample tile extents and the related DANS dataset.
- **Labels:** cadastral reference data is available only through the legitimately accessible benchmark/reference distribution. Confirm the exact files and terms at the DANS portal before use.
- **Small subset:** obtain only selected benchmark tiles and their matching reference data from the DANS portal, or follow the CadNET repository data setup. The repository documents `sample_tiles_10k_split.gpkg`, `brk_reference.gpkg`, imagery, and scene metadata as inputs to preprocessing.
- **Filtering:** use the published sample-tile/area files to select a few complete scenes, then retain the matching imagery and cadastral reference features for those scenes. The current project does not implement or claim a CadastreVision OGC API, WFS, database endpoint, or geographic-filter service.
- **Official locations:** [CadastreVision repository](https://github.com/jeroengrift/cadastrevision), [CadNET repository](https://github.com/jeroengrift/cadnet_jag), and the [DANS dataset record](https://dansdataportal.nl/dataset.xhtml?persistentId=doi%3A10.17026%2FPT%2FOS3OWX). Verify redirects and terms at acquisition time.
- **Credentials/restrictions:** use the portal account or permission process if required. Do not bypass access restrictions. The CadastreVision GitHub README says some 8 cm imagery and overlap-analysis data were not published there.
- **Expected raw layout:**

```text
data/raw_cadastrevision/
  <scene>.<tif|tiff|png|jpg>
  <scene>_mask.png                 # already rasterized and image-aligned, or
  <scene>_boundaries.geojson       # vector boundaries with an explicit CRS, or
  <scene>_boundaries.gpkg          # vector boundaries with an explicit CRS
```

  The current adapter accepts a matching image-aligned mask or the matching vector annotation. Vector annotations are reprojected to the image CRS, invalid geometries are repaired where possible, polygon boundaries are rasterized, and the resulting mask is validated as binary. Preserve a `scene_id` in the manifest or use filenames that identify one scene; do not split adjacent patches across scenes.
- **Usage:** primary cadastral-boundary training direction; not present in this checkout.

## Secondary and context sources

- **SpaceNet Buildings:** labelled building footprints; use a small AWS sample tarball for a future building module. CC BY-SA 4.0 applies according to the official page.
- **SpaceNet Roads / SpaceNet 3:** labelled road centerlines and a documented AWS sample tarball; future road module, not cadastral supervision.
- **SpaceNet 5:** road networks with travel-time information; future routing/road extension, not current MVP.
- **ISPRS UrbanSemLab:** semantic/urban benchmark reference data. Downloads are large and access terms apply; use only a selected permitted area later.
- **SpaceNet 7:** multi-temporal building footprints and change data; future change-detection module.
- **DeepGlobe Road Extraction:** road pixel masks; a sample download is documented, but its challenge/internal-use terms must be reviewed before use.
- **OpenStreetMap:** GIS/reference context under ODbL. Do not treat it as cadastral legal ground truth; include visible attribution and model-training notices where applicable.
- **Bhuvan:** imagery/data archive with portal downloads and access policies. Use as Indian context or testing only unless labels and permission are confirmed.
- **Bhoonidhi:** browse/order satellite data hub and API access by request. Use only through its stated access and terms; it is not automatically a labelled training dataset.
- **Google Earth Engine catalog:** catalogue and processing access, not a universal labelled dataset. Review each collection's terms and export only permitted imagery.
- **Karnataka/K-GIS:** use only an authorised, documented government or survey release with explicit training permission.

Do not download a complete large dataset for this MVP. Record source version, selected scenes, licence, checksum, and acquisition date in the training metadata.
