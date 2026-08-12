from __future__ import annotations

import numpy as np

class MissingValueInterpolator:
    @staticmethod
    def detect_missing_indices(series: list[float | None]) -> list[int]:
        return [i for i, val in enumerate(series) if val is None or np.isnan(val)]

    @staticmethod
    def interpolate_linear(series: list[float | None], timestamps: list[str] | None = None) -> list[float]:
        y = np.array(series, dtype=float)
        nans, x = np.isnan(y), lambda z: z.nonzero()[0]
        if nans.all():
            return [0.0] * len(series)
        y[nans] = np.interp(x(nans), x(~nans), y[~nans])
        return y.tolist()

    @staticmethod
    def interpolate_forward_fill(series: list[float | None]) -> list[float]:
        res = []
        last_val = 0.0
        for val in series:
            if val is not None and not np.isnan(val):
                last_val = val
            res.append(float(last_val))
        return res

    @staticmethod
    def interpolate_polynomial(series: list[float | None], timestamps: list[str] | None = None, degree: int = 2) -> list[float]:
        y = np.array(series, dtype=float)
        nans = np.isnan(y)
        if nans.all() or sum(~nans) <= degree:
            return MissingValueInterpolator.interpolate_linear(series)
            
        x_valid = np.where(~nans)[0]
        y_valid = y[~nans]
        coeffs = np.polyfit(x_valid, y_valid, degree)
        poly = np.poly1d(coeffs)
        
        x_nans = np.where(nans)[0]
        y[nans] = poly(x_nans)
        return y.tolist()

    @staticmethod
    def recover_missing(series: list[float | None], method: str = 'linear') -> list[float]:
        if method == 'linear':
            return MissingValueInterpolator.interpolate_linear(series)
        elif method == 'ffill':
            return MissingValueInterpolator.interpolate_forward_fill(series)
        elif method == 'polynomial':
            return MissingValueInterpolator.interpolate_polynomial(series)
        return MissingValueInterpolator.interpolate_linear(series)

    @staticmethod
    def anomaly_aware_recovery(series: list[float | None], z_threshold: float = 3.0) -> list[float]:
        y = np.array([v if v is not None else np.nan for v in series], dtype=float)
        
        # Initial fill to compute stats
        temp_y = np.array(MissingValueInterpolator.interpolate_linear(series))
        mean = np.mean(temp_y)
        std = np.std(temp_y)
        
        if std > 0:
            z_scores = np.abs((temp_y - mean) / std)
            anomalies = z_scores > z_threshold
            y[anomalies] = np.nan
            
        return MissingValueInterpolator.interpolate_linear(y.tolist())
