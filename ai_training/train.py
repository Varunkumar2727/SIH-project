"""
PyTorch Training Engine for Cadastral Boundary Segmentation.
Executes:
1. Leakage-free scene splitting
2. Mixed-precision training & gradient clipping
3. Real validation metrics (IoU, Dice/F1, Precision, Recall)
4. Checkpointing best model weights (.pt)
5. Zero fabricated metrics.
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime, timezone
from typing import Dict, Any
import numpy as np

# Add repo root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ai_training.model import CadastralBoundaryUNet, TORCH_AVAILABLE
from ai_training.losses import BCEDiceLoss
from ai_training.metrics import compute_binary_metrics, compute_boundary_iou
from ai_training.dataset import CadastralPatchDataset, split_dataset_by_scene


def run_training_pipeline(
    data_dir: str = "data/cadastrevision",
    checkpoints_dir: str = "results/checkpoints",
    epochs: int = 15,
    batch_size: int = 2,
    lr: float = 1e-4,
    device_name: str = "auto"
) -> Dict[str, Any]:
    """
    Executes the real training pipeline. PyTorch is required; no mock training path exists.
    """
    os.makedirs(checkpoints_dir, exist_ok=True)
    manifest_path = os.path.join(data_dir, "manifest.json")

    if not os.path.exists(manifest_path):
        from ai_training.prepare_cadastrevision import prepare_cadastrevision_subset
        print("[INFO] Manifest not found. Initializing dataset preparation...")
        manifest = prepare_cadastrevision_subset(
            raw_dir="data/raw_cadastrevision",
            output_dir=data_dir
        )
    else:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

    samples = manifest.get("samples", [])
    if manifest.get("is_synthetic") or "synthetic" in manifest.get("dataset_name", "").lower():
        raise ValueError(
            "REAL CADASTREVISION DATA NOT FOUND: the manifest is an explicitly synthetic development fixture. "
            "Training requires a legitimate labelled CadastreVision subset."
        )
    if not samples:
        raise ValueError("No training samples found in manifest.")

    splits = split_dataset_by_scene(samples, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)
    print(f"[DATASET] Total: {len(samples)} | Train: {len(splits['train'])} | Val: {len(splits['val'])} | Test: {len(splits['test'])}")

    if not TORCH_AVAILABLE:
        raise RuntimeError(
            "PyTorch is required for real training. Run the Colab notebook on a GPU runtime."
        )

    import torch
    from torch.utils.data import DataLoader

    if device_name == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device_name)

    print(f"[RUNTIME] Training device: {device}")

    # Create Datasets & DataLoaders
    train_dataset = CadastralPatchDataset(splits["train"], image_size=512, augment=True)
    val_dataset = CadastralPatchDataset(splits["val"], image_size=512, augment=False)
    test_dataset = CadastralPatchDataset(splits["test"], image_size=512, augment=False)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)

    # Initialize Model, Loss, Optimizer
    model = CadastralBoundaryUNet(in_channels=3, num_classes=1, base_channels=32)
    model.to(device)

    criterion = BCEDiceLoss(bce_weight=0.5, dice_weight=0.5)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    use_amp = device.type == "cuda"
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

    best_val_loss = float("inf")
    best_val_iou = 0.0
    history = []

    print("=" * 60)
    print("STARTING CADASTRAL BOUNDARY U-NET TRAINING")
    print("=" * 60)

    for epoch in range(1, epochs + 1):
        model.train()
        running_train_loss = 0.0

        for batch_idx, (images, masks, _) in enumerate(train_loader):
            images = images.to(device)
            masks = masks.to(device)

            optimizer.zero_grad()
            with torch.cuda.amp.autocast(enabled=use_amp):
                preds = model(images)
                loss = criterion(preds, masks)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()

            running_train_loss += loss.item() * images.size(0)

        epoch_train_loss = running_train_loss / max(1, len(train_dataset))
        scheduler.step()

        # Validation pass
        model.eval()
        running_val_loss = 0.0
        val_gts = []
        val_preds = []

        with torch.no_grad():
            for images, masks, _ in val_loader:
                images = images.to(device)
                masks = masks.to(device)
                preds = model(images)
                loss = criterion(preds, masks)
                running_val_loss += loss.item() * images.size(0)

                val_gts.append(masks.cpu().numpy())
                val_preds.append(preds.cpu().numpy())

        epoch_val_loss = running_val_loss / max(1, len(val_dataset))

        if val_gts:
            all_val_gt = np.concatenate(val_gts, axis=0)
            all_val_pred = np.concatenate(val_preds, axis=0)
            val_metrics = compute_binary_metrics(all_val_gt, all_val_pred, threshold=0.45)
        else:
            val_metrics = {"iou": 0.0, "dice": 0.0, "precision": 0.0, "recall": 0.0}

        epoch_record = {
            "epoch": epoch,
            "train_loss": round(float(epoch_train_loss), 4),
            "val_loss": round(float(epoch_val_loss), 4),
            "val_iou": val_metrics["iou"],
            "val_dice": val_metrics["dice"],
            "val_precision": val_metrics["precision"],
            "val_recall": val_metrics["recall"],
            "lr": float(optimizer.param_groups[0]["lr"])
        }
        history.append(epoch_record)

        print(f"Epoch [{epoch:02d}/{epochs:02d}] | Train Loss: {epoch_train_loss:.4f} | Val Loss: {epoch_val_loss:.4f} | Val IoU: {val_metrics['iou']:.4f} | Val F1: {val_metrics['dice']:.4f}")

        # Checkpoint if best
        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            best_val_iou = val_metrics["iou"]
            checkpoint_path = os.path.join(checkpoints_dir, "cadastral_boundary_best.pt")
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "metrics": val_metrics,
                "config": {
                    "architecture": "CadastralBoundaryUNet",
                    "in_channels": 3,
                    "num_classes": 1,
                    "base_channels": 32
                },
                "training_provenance": {
                    "dataset_name": manifest.get("dataset_name"),
                    "is_synthetic": bool(manifest.get("is_synthetic", False)),
                    "sample_count": len(samples),
                    "scene_count": len({s.get("scene_id") or s.get("flight_id") for s in samples}),
                    "training_environment": {
                        "device": str(device),
                        "cuda_available": bool(torch.cuda.is_available())
                    }
                },
                "training_date": datetime.now(timezone.utc).isoformat()
            }, checkpoint_path)

    # Test Evaluation
    print("-" * 60)
    print("RUNNING FINAL TEST SET EVALUATION...")
    test_checkpoint = torch.load(os.path.join(checkpoints_dir, "cadastral_boundary_best.pt"), map_location=device)
    model.load_state_dict(test_checkpoint["model_state_dict"])
    model.eval()

    test_gts = []
    test_preds = []
    with torch.no_grad():
        for images, masks, _ in test_loader:
            images = images.to(device)
            preds = model(images)
            test_gts.append(masks.numpy())
            test_preds.append(preds.cpu().numpy())

    if test_gts:
        all_test_gt = np.concatenate(test_gts, axis=0)
        all_test_pred = np.concatenate(test_preds, axis=0)
        test_metrics = compute_binary_metrics(all_test_gt, all_test_pred, threshold=0.45)
    else:
        test_metrics = {"iou": 0.0, "dice": 0.0, "precision": 0.0, "recall": 0.0}

    print(f"[TEST METRICS] IoU: {test_metrics['iou']:.4f} | F1: {test_metrics['dice']:.4f} | Precision: {test_metrics['precision']:.4f} | Recall: {test_metrics['recall']:.4f}")

    results_summary = {
        "status": "COMPLETED",
        "epochs_completed": epochs,
        "best_val_loss": round(float(best_val_loss), 4),
        "best_val_iou": round(float(best_val_iou), 4),
        "test_metrics": test_metrics,
        "checkpoint_file": os.path.join(checkpoints_dir, "cadastral_boundary_best.pt"),
        "history": history
    }

    with open(os.path.join(checkpoints_dir, "training_summary.json"), "w") as f:
        json.dump(results_summary, f, indent=2)

    return results_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Cadastral Boundary Segmentation Model.")
    parser.add_argument("--data_dir", type=str, default="data/cadastrevision")
    parser.add_argument("--checkpoints_dir", type=str, default="results/checkpoints")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-4)
    args = parser.parse_args()

    run_training_pipeline(
        data_dir=args.data_dir,
        checkpoints_dir=args.checkpoints_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr
    )
