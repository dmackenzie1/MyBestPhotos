"""NIMA (Neural Image Assessment) -- vendored from https://github.com/IDLabMedia/NIMA."""

from photo_curator.nima.inference import assess_quality, assess_quality_batch, get_model
from photo_curator.nima.model import NIMA, emd_loss, single_emd_loss

__all__ = [
    "NIMA",
    "emd_loss",
    "single_emd_loss",
    "assess_quality",
    "assess_quality_batch",
    "get_model",
]
