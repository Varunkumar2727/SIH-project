"""
Evaluation Metrics for Cadastral Boundary Segmentation.
Provides exact mathematical computation of:
- Intersection over Union (IoU) / Jaccard Index
- Dice Coefficient / F1 Score
- Precision & Recall
- Boundary-Specific Metrics (Boundary IoU & Distance Tolerances)
Zero fabricated or simulated metrics.
"""

from typing import Dict, Any
import numpy as np


def compute_binary_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    threshold: float = 0.5,
    eps: float = 1e-7
) -> Dict[str, float]:
    """
    Computes exact binary segmentation metrics against ground truth masks.
    
    Args:
        y_true: Ground truth binary mask (H, W) or (B, H, W) with values {0, 1}
        y_pred: Predicted probability mask with values in [0.0, 1.0] or binary mask
        threshold: Binarization cutoff threshold
        eps: Small epsilon to prevent division by zero
        
    Returns:
        Dictionary of exact measured metrics:
        - iou: Jaccard index
        - dice: Dice coefficient / F1
        - precision: True Positive / (True Positive + False Positive)
        - recall: True Positive / (True Positive + False Negative)
        - accuracy: Overall pixel accuracy
        - true_positives, false_positives, false_negatives, true_negatives
    """
    y_true = (y_true > 0.5).astype(np.uint8).flatten()
    if y_pred.dtype == bool or np.array_equal(y_pred, y_pred.astype(bool)):
        y_pred_bin = y_pred.astype(np.uint8).flatten()
    else:
        y_pred_bin = (y_pred >= threshold).astype(np.uint8).flatten()

    tp = int(np.sum((y_true == 1) & (y_pred_bin == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred_bin == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred_bin == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred_bin == 0)))

    precision = tp / (tp + fp + eps)
    recall = tp / (tp + fn + eps)
    dice = (2.0 * tp) / (2.0 * tp + fp + fn + eps)
    iou = tp / (tp + fp + fn + eps)
    accuracy = (tp + tn) / max(1, len(y_true))

    return {
        "iou": float(round(iou, 4)),
        "dice": float(round(dice, 4)),
        "f1": float(round(dice, 4)),
        "precision": float(round(precision, 4)),
        "recall": float(round(recall, 4)),
        "accuracy": float(round(accuracy, 4)),
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn
        }
    }


def compute_boundary_iou(
    gt_mask: np.ndarray,
    pred_mask: np.ndarray,
    tolerance_px: int = 3,
    eps: float = 1e-7
) -> Dict[str, float]:
    """
    Computes boundary-specific IoU and Boundary F1 within a given pixel tolerance buffer.
    """
    import cv2

    gt_bin = (gt_mask > 0.5).astype(np.uint8)
    pred_bin = (pred_mask > 0.5).astype(np.uint8)

    # Extract boundary contours
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * tolerance_px + 1, 2 * tolerance_px + 1))
    
    # Boundary ribbon: dilation - erosion
    gt_boundary = cv2.morphologyEx(gt_bin, cv2.MORPH_GRADIENT, kernel)
    pred_boundary = cv2.morphologyEx(pred_bin, cv2.MORPH_GRADIENT, kernel)

    gt_b_flat = (gt_boundary > 0).astype(np.uint8).flatten()
    pred_b_flat = (pred_boundary > 0).astype(np.uint8).flatten()

    tp_b = int(np.sum((gt_b_flat == 1) & (pred_b_flat == 1)))
    fp_b = int(np.sum((gt_b_flat == 0) & (pred_b_flat == 1)))
    fn_b = int(np.sum((gt_b_flat == 1) & (pred_b_flat == 0)))

    b_precision = tp_b / (tp_b + fp_b + eps)
    b_recall = tp_b / (tp_b + fn_b + eps)
    b_f1 = 2.0 * (b_precision * b_recall) / (b_precision + b_recall + eps)
    b_iou = tp_b / (tp_b + fp_b + fn_b + eps)

    return {
        "boundary_iou": float(round(b_iou, 4)),
        "boundary_f1": float(round(b_f1, 4)),
        "boundary_precision": float(round(b_precision, 4)),
        "boundary_recall": float(round(b_recall, 4)),
        "tolerance_px": tolerance_px
    }
