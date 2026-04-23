"""
Vendored from https://github.com/IDLabMedia/NIMA (MIT License).

Neural IMage Assessment model architecture.
Replaces VGG-16 classifier head with a 10-class quality distribution head.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class NIMA(nn.Module):
    """Neural Image Assessment model by Google (Talebi & Milanfar, IEEE TIP)."""

    def __init__(self, base_model: nn.Module, num_classes: int = 10) -> None:
        super().__init__()
        self.features = base_model.features
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.75),
            nn.Linear(in_features=25088, out_features=num_classes),
            nn.Softmax(dim=-1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # type: ignore[override]
        out = self.features(x)
        out = out.view(out.size(0), -1)
        out = self.classifier(out)
        return out


def single_emd_loss(p: torch.Tensor, q: torch.Tensor, r: int = 2) -> torch.Tensor:
    """Earth Mover's Distance for a single sample pair."""
    assert p.shape == q.shape, "Length of the two distributions must be the same"
    length = p.shape[0]
    emd_loss = torch.tensor(0.0, device=p.device)
    for i in range(1, length + 1):
        emd_loss += torch.abs(torch.sum(p[:i] - q[:i])) ** r
    return (emd_loss / length) ** (1.0 / r)


def emd_loss(p: torch.Tensor, q: torch.Tensor, r: int = 2) -> torch.Tensor:
    """Earth Mover's Distance on a batch."""
    assert p.shape == q.shape, "Shape of the two distribution batches must be the same."
    mini_batch_size = p.shape[0]
    loss_vector = [single_emd_loss(p[i], q[i], r=r) for i in range(mini_batch_size)]
    return sum(loss_vector) / mini_batch_size
