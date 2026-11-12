"""Serialize nested model output without invalid JSON NaN/Infinity values."""
import math
import numpy as np


def np_clean(value):
    if isinstance(value, dict):
        return {str(k): np_clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [np_clean(v) for v in value]
    if isinstance(value, np.generic):
        return np_clean(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
