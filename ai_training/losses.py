"""
Boundary-Aware Loss Functions for Cadastral Parcel Segmentation.
Combines Binary Cross Entropy with Soft Dice Loss to address extreme
spatial boundary class imbalance.
"""

from typing import Optional, Any

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    class nn:
        class Module:
            pass


if TORCH_AVAILABLE:
    class DiceLoss(nn.Module):
        """Soft Dice Loss for binary boundary segmentation."""
        def __init__(self, smooth: float = 1.0):
            super().__init__()
            self.smooth = smooth

        def forward(self, pred: Any, target: Any) -> Any:
            pred = pred.contiguous().view(-1)
            target = target.contiguous().view(-1)

            intersection = (pred * target).sum()
            dice = (2.0 * intersection + self.smooth) / (pred.sum() + target.sum() + self.smooth)
            return 1.0 - dice


    class BCEDiceLoss(nn.Module):
        """
        Combined Binary Cross Entropy and Dice Loss.
        Loss = bce_weight * BCE + dice_weight * Dice
        """
        def __init__(self, bce_weight: float = 0.5, dice_weight: float = 0.5, pos_weight: Optional[float] = None):
            super().__init__()
            self.bce_weight = bce_weight
            self.dice_weight = dice_weight
            self.dice = DiceLoss()
            self.pos_weight = torch.tensor([pos_weight]) if pos_weight is not None else None

        def forward(self, pred: Any, target: Any) -> Any:
            eps = 1e-7
            pred_clamped = torch.clamp(pred, eps, 1.0 - eps)
            
            if self.pos_weight is not None:
                pos_w = self.pos_weight.to(pred.device)
                bce = -(pos_w * target * torch.log(pred_clamped) + (1.0 - target) * torch.log(1.0 - pred_clamped)).mean()
            else:
                bce = F.binary_cross_entropy(pred_clamped, target)

            dice = self.dice(pred, target)
            return self.bce_weight * bce + self.dice_weight * dice


    class FocalBoundaryLoss(nn.Module):
        """Focal Loss tailored for sparse boundary pixel detection."""
        def __init__(self, alpha: float = 0.25, gamma: float = 2.0):
            super().__init__()
            self.alpha = alpha
            self.gamma = gamma

        def forward(self, pred: Any, target: Any) -> Any:
            eps = 1e-7
            pred = torch.clamp(pred, eps, 1.0 - eps)
            pt = torch.where(target == 1, pred, 1.0 - pred)
            alpha_t = torch.where(target == 1, self.alpha, 1.0 - self.alpha)
            focal_loss = -alpha_t * ((1.0 - pt) ** self.gamma) * torch.log(pt)
            return focal_loss.mean()

else:
    class DiceLoss:
        def __init__(self, *args, **kwargs):
            pass

    class BCEDiceLoss:
        def __init__(self, *args, **kwargs):
            pass

    class FocalBoundaryLoss:
        def __init__(self, *args, **kwargs):
            pass
