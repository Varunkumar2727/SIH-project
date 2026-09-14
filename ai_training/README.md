# GeoCadastral AI — AI/ML Training & Cadastral Delineation Guide

This directory contains the training, dataset preparation, evaluation, and ONNX export pipeline for **Cadastral / Parcel Boundary Delineation** in the GeoCadastral AI system.

---

## 1. Datasets Overview & Strategy

### 1.1 Primary Dataset: CadastreVision (CadNET Benchmark)
* **Task**: Cadastral Boundary Delineation from high-resolution aerial and drone imagery.
* **Source**: CadastreVision Benchmark / DANS Data Portal / [CadNET Repository](https://github.com/jeroengrift/cadnet_jag).
* **Current status**: No real CadastreVision data is installed in this checkout. The small files under `data/cadastrevision/` are synthetic development fixtures and are rejected by the training pipeline.
* **Subset strategy**: Obtain only an authorised, labelled subset through the DANS/CadNET workflow. Patch generation extracts 512x512 pixel tiles with 15% overlap and preserves scene identity.

### 1.2 Secondary Datasets (Roadmap & Extensibility)
The following secondary datasets are cataloged for multi-modal feature expansion:
1. **SpaceNet Buildings Dataset v2**: Building footprint extraction and polygonal regularization.
2. **SpaceNet Roads Dataset (SpaceNet 3)**: Road network centerline extraction and connectivity graph synthesis.
3. **SpaceNet 5**: Advanced road network extraction with travel time / speed estimations.
4. **ISPRS UrbanSemLab**: Multi-class urban semantic segmentation (impervious surfaces, buildings, low vegetation, trees, cars).
5. **SpaceNet 7**: Multi-temporal urban development and building change monitoring.
6. **DeepGlobe Road Extraction**: Auxiliary road segmentation benchmark.
7. **OpenStreetMap (OSM)**: Reference GIS vector layers and topological ground truth context (requires proper [ODbL attribution](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines)).

---

## 2. Spatial Data Leakage Prevention

To guarantee scientifically valid evaluation metrics:
* Overlapping patches from the same continuous flight scene are **strictly grouped by `scene_id`**.
* Training ($70\%$), Validation ($15\%$), and Testing ($15\%$) sets are geographically isolated.
* Random patch splitting across scenes is prohibited to prevent train/test spatial leakage.

---

## 3. Model Architecture & Loss Formulation

* **Architecture**: `CadastralBoundaryUNet`
  - Input: 3-channel RGB image ($512 \times 512$)
  - Output: 1-channel boundary probability map ($[0.0, 1.0]$)
  - Parameter Size: ~7.8M parameters (optimized for cloud GPU training and fast CPU ONNX inference)
* **Loss Function**: `BCEDiceLoss`
  $$\mathcal{L} = 0.5 \cdot \mathcal{L}_{\text{BCE}} + 0.5 \cdot \mathcal{L}_{\text{Dice}}$$
  Addresses extreme boundary pixel sparsity ($<5\%$ boundary pixels per tile).
* **Metrics**: Real, non-fabricated IoU, Dice/F1, Precision, Recall, and Boundary F1 within a 3px tolerance ribbon.

---

## 4. Google Colab Execution Guide

Because the developer laptop has 4 GB RAM, full model training must be run in Google Colab with GPU acceleration:

1. Open [`notebooks/geocadastral_cadastrevision_training.ipynb`](../notebooks/geocadastral_cadastrevision_training.ipynb) in Google Colab.
2. Connect to a GPU Runtime (**Runtime > Change runtime type > T4 GPU**).
3. Run all cells top-to-bottom:
   - **Step 1-2**: Clone repo and install PyTorch & dependencies.
  - **Step 3-6**: Place an authorised CadastreVision subset in the configured input directory; the notebook validates imagery, masks, and scene IDs and fails if absent.
   - **Step 7-9**: Instantiate `CadastralBoundaryUNet` and train with `BCEDiceLoss`.
   - **Step 10-13**: Validate and evaluate on the test split with real metrics.
   - **Step 14-16**: Export model to ONNX (`geocadastral_cadastral_boundary_v1.onnx`) and generate metadata.
4. Download the exported ONNX model and place it in `backend/models/`.

---

## 5. Local Commands (Testing & Verification)

### Prepare Data Subset
```bash
python ai_training/prepare_cadastrevision.py --output_dir data/cadastrevision --patch_size 512 --overlap 0.15
```

### Export ONNX Model
```bash
python ai_training/export_onnx.py --checkpoint results/checkpoints/cadastral_boundary_best.pt --output backend/models/geocadastral_cadastral_boundary_v1.onnx --meta backend/models/geocadastral_cadastral_boundary_v1_meta.json
```

### Run AI Backend Unit Tests
```bash
python -m unittest backend/tests/test_ai_model.py
```

---

## 6. Licensing & Attribution
- **CadastreVision**: DANS Data Station / CadNET Project.
- **OpenStreetMap Data**: &copy; OpenStreetMap contributors under Open Database License (ODbL).
- **Statutory Positioning**: Model outputs are AI-assisted decision-support indicators and require formal surveyor verification before statutory cadastral registration.
