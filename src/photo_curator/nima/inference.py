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

from photo_curator.pipeline_v1.scoring import compute_clip_aesthetic

try:
    import cv2  # noqa: F401
except ImportError:
    cv2 = None  # type: ignore[assignment]

# Lazy-import the vendored model to avoid hard dependency at module load time.
_model_instance: Optional[object] = None
_cached_weights_path: Optional[Path] = None
_weights_download_failed: bool = False
_model_init_error: Optional[RuntimeError] = None


def _get_explicit_weights_path() -> Optional[Path]:
    raw_path = os.environ.get("PHOTO_CURATOR_NIMA_WEIGHTS_PATH", "").strip()
    if not raw_path:
        return None
    expanded = Path(raw_path).expanduser()
    if expanded.is_file():
        return expanded
    return None


def _get_mounted_weights_path() -> Optional[Path]:
    """Check for weights mounted into the container at /data/nima/."""
    mounted = Path("/data/nima/pretrained_weights.pth")
    if mounted.is_file():
        return mounted
    return None


def _get_weights_dir() -> Path:
    cache_dir = os.environ.get(
        "PHOTO_CURATOR_CACHE_DIR",
        str(Path(__file__).resolve().parent.parent.parent.parent / "data" / "cache"),
    )
    return Path(cache_dir) / "nima"


def _weights_path() -> Path:
    global _cached_weights_path
    if _cached_weights_path is None:
        _cached_weights_path = _get_weights_dir() / "pretrained_weights.pth"
    return _cached_weights_path


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
        global _weights_download_failed
        print(f"Warning: could not download NIMA weights: {exc}", file=sys.stderr)  # noqa: T201
        _weights_download_failed = True
        return None


def _ensure_weights(weights_path: Path) -> Optional[Path]:
    try:
        if weights_path.is_file():
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
            if fallback_weights_path.is_file():
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

    result = _download_weights(weights_path)
    if result is None and weights_path != fallback_weights_path:
        try:
            if fallback_weights_path.is_file():
                print(
                    f"Using fallback NIMA weights path after download failure: {fallback_weights_path}",
                    file=sys.stderr,
                )  # noqa: T201
                return fallback_weights_path
        except OSError:
            pass
    return result


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
        torch.nn.Module in eval mode, ready for inference, or None if weights unavailable.
    """
    global _model_instance, _model_init_error

    if _model_instance is not None:
        return _model_instance

    if _model_init_error is not None:
        raise _model_init_error

    # Check explicit env var first (via helper)
    wp = _get_explicit_weights_path()
    if wp is None:
        wp = _get_mounted_weights_path()  # Check mounted volume next
    if wp is None and _weights_download_failed:
        return None  # Already tried download, skip repeated attempts
    elif wp is None:
        wp = weights_path or _weights_path()
        wp = _ensure_weights(wp)

    if not wp.is_file():
        _model_init_error = RuntimeError(
            "NIMA pretrained weights not found. "
            f"Expected at {wp}. "
            "Run with internet access to download, place them manually, "
            "or set PHOTO_CURATOR_NIMA_WEIGHTS_PATH to a local weights file."
        )
        raise _model_init_error

    try:
        _model_instance = _load_model(wp)
    except Exception as exc:  # noqa: BLE001
        _model_init_error = RuntimeError(
            f"Failed to initialize NIMA model from weights at {wp}: {exc}"
        )
        raise _model_init_error from exc

    return _model_instance


def heuristic_score(image_np: np.ndarray) -> tuple[float, float]:
    """Heuristic aesthetic score when NIMA weights are unavailable.

    Uses the shared CLIP-aesthetic scoring math but takes a raw image
    and returns (mean_normalized_to_0_1, std) matching assess_quality's output signature.

    This is a drop-in replacement for assess_quality() — same function signature, same return type.
    """
    if cv2 is None:
        raise RuntimeError("cv2 (opencv-python-headless) required for heuristic scoring")

    gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY) if image_np.ndim == 3 else image_np
    height, width = gray.shape[:2]
    if height == 0 or width == 0:
        return (0.5, 0.1)

    # Blur score: Laplacian variance
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    blur_score = float(laplacian.var()) / (width * height + 1e-6)

    # Contrast score: std of intensity normalized to [0, 1]
    contrast_score = float(gray.std()) / 255.0

    # Entropy score: histogram entropy normalized to [0, 1]
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist / hist.sum()
    entropy_score = float(-np.sum(hist * np.log2(hist + 1e-6))) / 8.0

    # Technical quality: weighted combination of blur, contrast, brightness
    technical_quality_score = max(
        0.0, min(1.0, (1.0 - blur_score) * 0.4 + contrast_score * 0.3 + entropy_score * 0.3)
    )

    # Composition balance via gradient-based saliency centering
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    saliency = cv2.magnitude(grad_x, grad_y)
    total = float(saliency.sum()) + 1e-6
    yy, xx = np.indices(gray.shape, dtype=np.float32)
    cx = float(np.sum(xx * saliency) / total)
    cy = float(np.sum(yy * saliency) / total)
    thirds = [
        (width / 3.0, height / 3.0),
        (2.0 * width / 3.0, height / 3.0),
        (width / 3.0, 2.0 * height / 3.0),
        (2.0 * width / 3.0, 2.0 * height / 3.0),
    ]
    min_distance = min(np.hypot(cx - tx, cy - ty) for tx, ty in thirds)
    max_distance = float(np.hypot(width, height))
    composition_balance_score = max(0.0, min(1.0, 1.0 - (min_distance / (max_distance + 1e-6))))

    clip_aesthetic_score, _aesthetic_spread, _keep_spread = compute_clip_aesthetic(
        technical_quality_score,
        composition_balance_score,
        blur_score,
        technical_quality_score,
    )

    # Return mean and std matching CLIP aesthetic output format
    return (clip_aesthetic_score, 0.1 + (1.0 - clip_aesthetic_score) * 0.05)


def assess_quality(image_np: np.ndarray) -> tuple[float, float]:
    """Assess aesthetic quality of a single image using the NIMA model.

    Args:
        image_np: numpy array in BGR format (OpenCV convention), uint8, HxWx3.

    Returns:
        (mean_score_normalized, std_score) where mean_score is in [0, 1]
        (mapped from the original 1-10 scale by dividing by 10).
    """
    model = get_model()
    if model is None:
        raise RuntimeError("NIMA weights unavailable — call heuristic_score() instead")

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
        centered = indices.unsqueeze(0) - (means * 10.0).unsqueeze(1)
        stds = torch.sqrt(torch.sum(dists * centered**2, dim=1))

        for j in range(len(batch_images)):
            results.append((float(means[j].cpu().numpy()), float(stds[j].cpu().numpy())))

    return results
