from __future__ import annotations

import numpy as np
from typing import Any
from ..forecast_models.base import AbstractForecastModel, ForecastModelResult

class AnomalyAwareForecastEngine:
    @staticmethod
    def detect_anomalies(series: list[float], method: str = 'zscore', threshold: float = 3.0) -> list[bool]:
        y = np.array(series, dtype=float)
        if method == 'zscore':
            mean = np.mean(y)
            std = np.std(y)
            if std == 0:
                return [False] * len(y)
            z_scores = np.abs((y - mean) / std)
            return (z_scores > threshold).tolist()
        elif method == 'iqr':
            q75, q25 = np.percentile(y, [75, 25])
            iqr = q75 - q25
            lower_bound = q25 - (threshold * iqr)
            upper_bound = q75 + (threshold * iqr)
            return ((y < lower_bound) | (y > upper_bound)).tolist()
        return [False] * len(y)

    @staticmethod
    def segment_series(series: list[float]) -> list[list[float]]:
        anomalies = AnomalyAwareForecastEngine.detect_anomalies(series)
        segments = []
        current = []
        
        for val, is_anomaly in zip(series, anomalies):
            if not is_anomaly:
                current.append(val)
            else:
                if current:
                    segments.append(current)
                    current = []
        if current:
            segments.append(current)
            
        return segments

    @staticmethod
    async def forecast_with_anomaly_mask(series: list[float], steps: int, model: AbstractForecastModel) -> ForecastModelResult:
        # Mask anomalies with np.nan and interpolate to create a clean series for training
        anomalies = AnomalyAwareForecastEngine.detect_anomalies(series)
        y = np.array(series, dtype=float)
        y[anomalies] = np.nan
        
        # Linear interpolation over anomalies
        nans, x = np.isnan(y), lambda z: z.nonzero()[0]
        if not nans.all():
            y[nans] = np.interp(x(nans), x(~nans), y[~nans])
            
        clean_series = y.tolist()
        timestamps = [str(i) for i in range(len(clean_series))]
        
        await model.train(clean_series, timestamps)
        return await model.forecast(steps, context={"anomaly_corrected": True})

    @staticmethod
    def compute_anomaly_severity(series: list[float]) -> float:
        anomalies = AnomalyAwareForecastEngine.detect_anomalies(series)
        if not anomalies:
            return 0.0
        return float(sum(anomalies) / len(series))
