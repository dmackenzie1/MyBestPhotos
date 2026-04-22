from __future__ import annotations

from dataclasses import dataclass

import cv2
from loguru import logger
import numpy as np


@dataclass
class NimaAssessor:
    device: str = "cpu"
    _metric: object | None = None
    _disabled: bool = False

    def _initialize(self) -> object | None:
        if self._metric is not None or self._disabled:
            return self._metric
        try:
            import pyiqa
            import torch

            resolved_device = self.device
            if self.device.startswith("cuda") and not torch.cuda.is_available():
                resolved_device = "cpu"
            self._metric = pyiqa.create_metric("nima", device=resolved_device)
            self.device = resolved_device
            logger.info("Initialized pyiqa NIMA scorer on device={device}", device=self.device)
            return self._metric
        except (
            Exception
        ) as exc:  # pragma: no cover - runtime dependency/runtime model availability path
            self._disabled = True
            logger.warning(
                "Unable to initialize pyiqa NIMA scorer, using heuristic fallback: {error}",
                error=str(exc),
            )
            return None

    def score(self, image_bgr: np.ndarray) -> float | None:
        metric = self._initialize()
        if metric is None:
            return None
        try:
            import torch

            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            tensor = (
                torch.from_numpy(image_rgb)
                .permute(2, 0, 1)
                .unsqueeze(0)
                .float()
                .div(255.0)
                .to(self.device)
            )
            with torch.inference_mode():
                score_value = float(metric(tensor).detach().cpu().mean().item())

            # NIMA is commonly returned on a 1..10 scale; normalize to 0..1 for our DB contract.
            if score_value > 1.0:
                score_value = score_value / 10.0
            return max(0.0, min(1.0, score_value))
        except Exception as exc:  # pragma: no cover - runtime model failure fallback
            logger.warning(
                "pyiqa NIMA scoring failed for one image, using fallback scorer: {error}",
                error=str(exc),
            )
            return None


_SHARED_ASSESSOR: NimaAssessor | None = None


def get_nima_assessor() -> NimaAssessor:
    global _SHARED_ASSESSOR
    if _SHARED_ASSESSOR is None:
        _SHARED_ASSESSOR = NimaAssessor()
    return _SHARED_ASSESSOR
