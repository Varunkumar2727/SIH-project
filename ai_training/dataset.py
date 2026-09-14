"""
Dataset and DataLoader Pipeline for Cadastral Boundary Segmentation.
Provides:
- 512x512 Patch Loading
- Leakage-Free Geographic Scene Partitioning
- Normalization (Standard / ImageNet)
- Geometric & Radiometric Augmentations
"""

import os
import glob
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from PIL import Image

try:
    # pyrefly: ignore [missing-import]
    import torch
    # pyrefly: ignore [missing-import]
    from torch.utils.data import Dataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    class Dataset:
        pass


class CadastralPatchDataset(Dataset):
    """
    PyTorch Dataset for Aerial Imagery and Cadastral Boundary Masks.
    """
    def __init__(
        self,
        samples: List[Dict[str, Any]],
        image_size: int = 512,
        augment: bool = False,
        normalize_mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
        normalize_std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
    ):
        self.samples = samples
        self.image_size = image_size
        self.augment = augment
        self.mean = np.array(normalize_mean, dtype=np.float32).reshape(1, 1, 3)
        self.std = np.array(normalize_std, dtype=np.float32).reshape(1, 1, 3)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        sample = self.samples[idx]
        image_path = sample["image_path"]
        mask_path = sample.get("mask_path")

        # Load image
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Training image not found: {image_path}")
        img = Image.open(image_path).convert("RGB")
        img = img.resize((self.image_size, self.image_size), Image.Resampling.BILINEAR)
        img_np = np.array(img, dtype=np.float32) / 255.0

        # Load mask
        if not mask_path or not os.path.exists(mask_path):
            raise FileNotFoundError(f"Training mask not found: {mask_path}")
        mask = Image.open(mask_path).convert("L")
        mask = mask.resize((self.image_size, self.image_size), Image.Resampling.NEAREST)
        mask_np = (np.array(mask, dtype=np.float32) > 127).astype(np.float32)

        # Augmentation
        if self.augment:
            # Random horizontal flip
            if np.random.rand() > 0.5:
                img_np = np.fliplr(img_np)
                mask_np = np.fliplr(mask_np)
            # Random vertical flip
            if np.random.rand() > 0.5:
                img_np = np.flipud(img_np)
                mask_np = np.flipud(mask_np)
            # Random 90-degree rotations
            rot_k = np.random.randint(0, 4)
            if rot_k > 0:
                img_np = np.rot90(img_np, rot_k)
                mask_np = np.rot90(mask_np, rot_k)

        # Normalize image
        img_norm = (img_np - self.mean) / (self.std + 1e-7)

        # Format to CHW for PyTorch
        img_tensor = np.transpose(img_norm, (2, 0, 1)).astype(np.float32)
        mask_tensor = np.expand_dims(mask_np, axis=0).astype(np.float32)

        if TORCH_AVAILABLE:
            return torch.from_numpy(img_tensor.copy()), torch.from_numpy(mask_tensor.copy()), sample.get("sample_id", f"sample_{idx}")
        return img_tensor.copy(), mask_tensor.copy(), sample.get("sample_id", f"sample_{idx}")


def split_dataset_by_scene(
    samples: List[Dict[str, Any]],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Partitions samples into train, val, and test splits strictly grouped by scene/flight ID
    to eliminate spatial data leakage between adjacent or overlapping patches.
    """
    np.random.seed(seed)
    scene_map: Dict[str, List[Dict[str, Any]]] = {}

    for s in samples:
        scene_id = s.get("scene_id") or s.get("flight_id") or "scene_01"
        if scene_id not in scene_map:
            scene_map[scene_id] = []
        scene_map[scene_id].append(s)

    scenes = sorted(list(scene_map.keys()))
    if any(not scene_id or scene_id == "scene_01" for scene_id in scenes):
        raise ValueError("Every sample must provide an explicit scene_id or flight_id")
    np.random.shuffle(scenes)

    train_samples, val_samples, test_samples = [], [], []

    if len(scenes) >= 3:
        n_scenes = len(scenes)
        n_train = max(1, int(n_scenes * train_ratio))
        n_val = max(1, int(n_scenes * val_ratio))
        if n_train + n_val >= n_scenes:
            n_val = 1
            n_train = n_scenes - 2
        
        train_scenes = scenes[:n_train]
        val_scenes = scenes[n_train:n_train + n_val]
        test_scenes = scenes[n_train + n_val:]
        if not test_scenes and len(val_scenes) > 1:
            test_scenes = [val_scenes.pop()]

        for sc in train_scenes:
            train_samples.extend(scene_map[sc])
        for sc in val_scenes:
            val_samples.extend(scene_map[sc])
        for sc in test_scenes:
            test_samples.extend(scene_map[sc])
    else:
        raise ValueError(
            "Scene-level train/validation/test splitting requires at least 3 distinct scenes; "
            f"received {len(scenes)}. Add real labelled areas instead of splitting patches from one scene."
        )

    if not train_samples or not val_samples or not test_samples:
        raise ValueError(
            "Scene split produced an empty train, validation, or test partition; "
            f"scenes={len(scenes)}"
        )

    return {
        "train": train_samples,
        "val": val_samples,
        "test": test_samples,
        "total": len(samples)
    }
