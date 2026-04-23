"""
NIMA inference wrapper for photo-curator.

Loads the pre-trained NIMA model (VGG-16 + 10-class quality head) and provides
batch scoring of images. Returns mean aesthetic score normalized to [0, 1].

Weights are downloaded from Google Drive on first use if not already cached.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import tempfile
from typing import Optional

import numpy as np
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image

# Lazy-import the vendored model to avoid hard dependency at module load time.
_model_instance: Optional[object] = None
_weights_path: Optional[Path] = None


def _get_weights_dir() -> Path:
    cache_dir = os.environ.get(
        "PHOTO_CURATOR_CACHE_DIR",
        str(Path(__file__).resolve().parent.parent.parent.parent / "data" / "cache"),
    )
    return Path(cache_dir) / "nima"


def _weights_path() -> Path:
    global _weights_path
    if _weights_path is None:
        _weights_path = _get_weights_dir() / "pretrained_weights.pth"
    return _weights_path


def _download_weights(weights_path: Path) -> Path:
    """Download NIMA pretrained weights from Google Drive.

    The original weights are hosted at:
    https://drive.google.com/file/d/1w9Ig_d6yZqUZSR63kPjZLrEjJ1n845B_/view?usp=sharing

    Falls back to a warning if download fails -- scoring will use heuristic fallback.
    """
    try:
        weights_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(
            f"Warning: could not create NIMA cache directory {weights_path.parent}: {exc}",
            file=sys.stderr,
        )  # noqa: T201
        fallback_weights_path = (
            Path(tempfile.gettempdir()) / "photo-curator-cache" / "nima" / "pretrained_weights.pth"
        )
        fallback_weights_path.parent.mkdir(parents=True, exist_ok=True)
        weights_path = fallback_weights_path

    # Try gdown first (lightweight), then urllib as fallback
    try:
        import gdown  # type: ignore[import-not-found,unused-ignore]

        drive_id = "1w9Ig_d6yZqUZSR63kPjZLrEjJ1n845B_"
        gdown.download(id=drive_id, output=str(weights_path), quiet=False)
        return weights_path
    except ImportError:
        pass

    try:
        import urllib.request  # noqa: F401

        drive_url = (
            "https://drive.google.com/uc?export=download&id=1w9Ig_d6yZqUZSR63kPjZLrEjJ1n845B_"
        )
        print(f"Downloading NIMA weights from {drive_url}")  # noqa: T201
        urllib.request.urlretrieve(drive_url, str(weights_path))  # type: ignore[union-attr]
        return weights_path
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: could not download NIMA weights: {exc}", file=sys.stderr)  # noqa: T201
        return Path()


def _ensure_weights(weights_path: Path) -> Path:
    try:
        if weights_path.exists():
            return weights_path
    except OSError as exc:
        print(
            f"Warning: could not access NIMA weights path {weights_path}: {exc}",
            file=sys.stderr,
        )  # noqa: T201

    fallback_weights_path = (
        Path(tempfile.gettempdir()) / "photo-curator-cache" / "nima" / "pretrained_weights.pth"
    )
    if weights_path != fallback_weights_path:
        try:
            if fallback_weights_path.exists():
                print(
                    f"Using fallback NIMA weights path: {fallback_weights_path}",
                    file=sys.stderr,
                )  # noqa: T201
                return fallback_weights_path
        except OSError as exc:
            print(
                f"Warning: could not access fallback NIMA weights path {fallback_weights_path}: {exc}",
                file=sys.stderr,
            )  # noqa: T201

    return _download_weights(weights_path)


# ImageNet normalization constants used by the original NIMA paper.
_IMAGENET_MEAN = [0.485, 0.456, 0.406]
_IMAGENET_STD = [0.229, 0.224, 0.225]

# Pre-composed transform: resize to 224x224 -> tensor -> normalize.
_preprocess_transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
    ]
)


def _load_model(weights_path: Path) -> object:
    """Load the NIMA model from pretrained weights.

    Returns a torch.nn.Module ready for inference (eval mode).
    Downloads ImageNet VGG-16 weights automatically via torchvision.
    """
    # Import the vendored model class.
    from photo_curator.nima.model import NIMA  # noqa: F811

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load ImageNet-pretrained VGG-16 (downloads automatically on first use).
    base_model = models.vgg16(pretrained=True)
    model = NIMA(base_model, num_classes=10)

    state_dict = torch.load(weights_path, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)
    model = model.to(device)
    model.eval()

    print(f"NIMA loaded on {device}")  # noqa: T201
    return model


def get_model(weights_path: Optional[Path] = None) -> object:
    """Get or create the singleton NIMA inference model.

    Args:
        weights_path: optional path to pretrained weights (auto-detected if omitted).

    Returns:
        torch.nn.Module in eval mode, ready for inference.
    """
    global _model_instance

    if _model_instance is not None:
        return _model_instance

    wp = weights_path or _weights_path()
    wp = _ensure_weights(wp)

    if not wp.exists():
        raise RuntimeError(
            "NIMA pretrained weights not found. "
            f"Expected at {wp}. Run with internet access to download, or place them manually."
        )

    _model_instance = _load_model(wp)
    return _model_instance


def assess_quality(image_np: np.ndarray) -> tuple[float, float]:
    """Assess aesthetic quality of a single image using the NIMA model.

    Args:
        image_np: numpy array in BGR format (OpenCV convention), uint8, HxWx3.

    Returns:
        (mean_score_normalized, std_score) where mean_score is in [0, 1]
        (mapped from the original 1-10 scale by dividing by 10).
    """
    model = get_model()

    # Convert BGR -> RGB for PIL.
    if image_np.shape[2] == 3:
        pil_image = Image.fromarray(image_np[:, :, ::-1]).convert("RGB")
    else:
        pil_image = Image.fromarray(image_np).convert("RGB")

    tensor = _preprocess_transform(pil_image).unsqueeze(0)

    device = next(model.parameters()).device
    tensor = tensor.to(device)

    with torch.no_grad():
        distribution = model(tensor)  # shape: (1, 10), softmax probabilities

    dist = distribution.view(10, 1)

    # Compute mean and std of the quality distribution.
    # Classes are 1-indexed (1=worst, 10=best).
    indices = torch.arange(1, 11, dtype=distribution.dtype, device=distribution.device)
    predicted_mean = torch.sum(indices * dist)  # scalar in [1, 10]

    predicted_std = torch.sqrt(torch.sum(dist * (indices - predicted_mean) ** 2))

    # Normalize mean to [0, 1].
    normalized_mean = float(predicted_mean.cpu().numpy()) / 10.0
    std_val = float(predicted_std.cpu().numpy())

    return normalized_mean, std_val


def assess_quality_batch(images: list[np.ndarray]) -> list[tuple[float, float]]:
    """Assess aesthetic quality of a batch of images using the NIMA model.

    Args:
        images: list of numpy arrays in BGR format (OpenCV), uint8, HxWx3.

    Returns:
        List of (mean_score_normalized, std_score) tuples.
    """
    model = get_model()

    device = next(model.parameters()).device
    results: list[tuple[float, float]] = []

    # Process in small batches to manage memory.
    batch_size = 8
    for i in range(0, len(images), batch_size):
        batch_images = images[i : i + batch_size]  # noqa: E203
        tensors = []
        for img_np in batch_images:
            if img_np.shape[2] == 3:
                pil_image = Image.fromarray(img_np[:, :, ::-1]).convert("RGB")
            else:
                pil_image = Image.fromarray(img_np).convert("RGB")
            tensor = _preprocess_transform(pil_image).unsqueeze(0)
            tensors.append(tensor.to(device))

        batch_tensor = torch.cat(tensors, dim=0)  # shape: (B, 3, 224, 224)

        with torch.no_grad():
            distributions = model(batch_tensor)  # shape: (B, 10)

        dists = distributions.view(-1, 10)

        indices = torch.arange(1, 11, dtype=distributions.dtype, device=distributions.device)
        means = torch.sum(indices * dists.T, dim=1) / 10.0  # normalize to [0, 1]
        stds = torch.sqrt(
            torch.sum(dists * (indices.unsqueeze(0) - indices.unsqueeze(0)) ** 2, dim=1)
        )

        for j in range(len(batch_images)):
            results.append((float(means[j].cpu().numpy()), float(stds[j].cpu().numpy())))

    return results
