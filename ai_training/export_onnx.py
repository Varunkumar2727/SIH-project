"""
ONNX Model Export & Verification Utility.

Exports trained PyTorch Cadastral Boundary U-Net weights to ONNX format,
validates with ONNX Runtime execution provider, and writes companion metadata.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional
import numpy as np

# Add repo root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ai_training.model import CadastralBoundaryUNet, TORCH_AVAILABLE


def export_pytorch_to_onnx(
    checkpoint_path: Optional[str] = None,
    output_onnx_path: str = "backend/models/geocadastral_cadastral_boundary_v1.onnx",
    metadata_path: str = "backend/models/geocadastral_cadastral_boundary_v1_meta.json",
    opset_version: int = 17,
    test_metrics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Exports PyTorch model weights to ONNX format and verifies with ONNX Runtime.
    """
    output_dir = os.path.dirname(output_onnx_path)
    metadata_dir = os.path.dirname(metadata_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    if metadata_dir:
        os.makedirs(metadata_dir, exist_ok=True)

    if not TORCH_AVAILABLE:
        raise RuntimeError("PyTorch is required to export a trained model; no fallback ONNX graph is generated.")
    if not checkpoint_path or not os.path.exists(checkpoint_path):
        raise FileNotFoundError(
            "A trained checkpoint is required for ONNX export. Refusing to export untrained or placeholder weights."
        )

    import torch

    model = CadastralBoundaryUNet(in_channels=3, num_classes=1, base_channels=32)
    print(f"[EXPORT] Loading checkpoint from {checkpoint_path}")
    chk = torch.load(checkpoint_path, map_location="cpu")
    if "model_state_dict" in chk:
        model.load_state_dict(chk["model_state_dict"])
    else:
        model.load_state_dict(chk)
    provenance = chk.get("training_provenance") if isinstance(chk, dict) else None
    if not provenance or provenance.get("is_synthetic") or not provenance.get("dataset_name"):
        raise ValueError(
            "Checkpoint provenance is missing or synthetic; refusing to mark its ONNX export as trained."
        )
    if not test_metrics and "metrics" in chk:
        test_metrics = chk["metrics"]

    model.eval()

    # Dummy input for tracing (Batch Size 1, Channels 3, Height 512, Width 512)
    dummy_input = torch.randn(1, 3, 512, 512, dtype=torch.float32)

    print(f"[EXPORT] Exporting ONNX graph to {output_onnx_path} (opset {opset_version})...")
    torch.onnx.export(
        model,
        dummy_input,
        output_onnx_path,
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size", 2: "height", 3: "width"},
            "output": {0: "batch_size", 2: "height", 3: "width"}
        }
    )
    print("[EXPORT] ONNX export successful!")

    # Verify ONNX Runtime against the actual PyTorch output.
    verification_res = verify_onnx_model(output_onnx_path, model=model)
    print(f"[VERIFY] ONNX Runtime execution verification: {verification_res['status']}")

    # Write companion metadata JSON
    metadata = {
        "model_id": "geocadastral_cadastral_boundary_v1",
        "name": "GeoCadastral Cadastral Boundary Segmenter v1",
        "version": "1.0.0",
        "task": "cadastral_boundary_segmentation",
        "classes": ["background", "cadastral_boundary"],
        "num_classes": 1,
        "input_shape": [1, 3, 512, 512],
        "output_shape": [1, 1, 512, 512],
        "input_name": "input",
        "output_name": "output",
        "framework": "PyTorch / ONNX Runtime",
        "architecture": "CadastralBoundaryUNet",
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225],
            "scale": 255.0
        },
        "model_name": "GeoCadastral Cadastral Boundary Segmenter v1",
        "dataset_name": provenance.get("dataset_name"),
        "dataset_subset": provenance,
        "training_dataset": provenance.get("dataset_name"),
        "metrics": test_metrics or {"status": "NOT_PROVIDED"},
        "checkpoint": os.path.abspath(checkpoint_path),
        "checkpoint_path": os.path.abspath(checkpoint_path),
        "onnx_file": os.path.abspath(output_onnx_path),
        "onnx_path": os.path.abspath(output_onnx_path),
        "license_attribution": "CadastreVision/CadNET and the authorised source subset; confirm applicable DANS terms before release.",
        "training_environment": {
            "framework": "PyTorch",
            **provenance.get("training_environment", {}),
            "export_device": "cpu"
        },
        "training_date": chk.get("training_date") if isinstance(chk, dict) else None,
        "onnx_verification": verification_res,
        "export_date": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "status": "TRAINED_AND_VERIFIED" if verification_res.get("status") == "PASSED" and verification_res.get("pytorch_onnx_allclose") else "EXPORT_VERIFICATION_FAILED"
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"[SUCCESS] Model metadata written to {metadata_path}")
    return metadata


def verify_onnx_model(onnx_path: str, model: Optional[Any] = None) -> Dict[str, Any]:
    """
    Loads the ONNX file with ONNX Runtime, runs a test inference on 512x512 tensor,
    and validates output dimensions and probability ranges.
    """
    import onnxruntime as ort

    if not os.path.exists(onnx_path):
        raise FileNotFoundError(f"ONNX model file not found at {onnx_path}")

    session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    # Test tensor (1, 3, 512, 512)
    test_tensor = np.random.randn(1, 3, 512, 512).astype(np.float32)
    output = session.run([output_name], {input_name: test_tensor})[0]
    pytorch_onnx_allclose = None
    max_abs_error = None
    if model is not None:
        import torch
        with torch.no_grad():
            pytorch_output = model(torch.from_numpy(test_tensor)).numpy()
        max_abs_error = float(np.max(np.abs(pytorch_output - output)))
        pytorch_onnx_allclose = bool(np.allclose(pytorch_output, output, rtol=1e-3, atol=1e-4))

    val_min, val_max = float(np.min(output)), float(np.max(output))

    expected_shape = [1, 1, 512, 512]
    shape_ok = list(output.shape) == expected_shape
    range_ok = bool(val_min >= 0.0 and val_max <= 1.0)
    verification_status = "PASSED" if shape_ok and range_ok and (pytorch_onnx_allclose is not False) else "FAILED"

    return {
        "status": verification_status,
        "input_shape": list(test_tensor.shape),
        "output_shape": list(output.shape),
        "output_min": round(val_min, 4),
        "output_max": round(val_max, 4),
        "providers": session.get_providers(),
        "shape_ok": shape_ok,
        "probability_range_ok": range_ok,
        "pytorch_onnx_allclose": pytorch_onnx_allclose,
        "max_abs_error": max_abs_error
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export PyTorch model to ONNX.")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to .pt checkpoint")
    parser.add_argument("--output", type=str, default="backend/models/geocadastral_cadastral_boundary_v1.onnx")
    parser.add_argument("--meta", type=str, default="backend/models/geocadastral_cadastral_boundary_v1_meta.json")
    parser.add_argument("--opset", type=int, default=17)
    args = parser.parse_args()

    export_pytorch_to_onnx(
        checkpoint_path=args.checkpoint,
        output_onnx_path=args.output,
        metadata_path=args.meta,
        opset_version=args.opset
    )
