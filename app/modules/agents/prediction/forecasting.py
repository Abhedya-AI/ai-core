"""forecasting.py — Multi-Horizon Forecasting Engine."""

from app.modules.agents.prediction.inference import ModelInferenceEngine
from app.modules.agents.prediction.models import PredictionFeatures, PredictionOutput, PredictionWindow


class MultiHorizonForecaster:
    """Executes multi-horizon forecasting across 15m, 1h, 6h, 24h, 7d, and 30d windows."""

    STANDARD_WINDOWS = [
        PredictionWindow(horizon_hours=0.25, horizon_label="15m"),
        PredictionWindow(horizon_hours=1.0, horizon_label="1h"),
        PredictionWindow(horizon_hours=6.0, horizon_label="6h"),
        PredictionWindow(horizon_hours=24.0, horizon_label="24h"),
        PredictionWindow(horizon_hours=168.0, horizon_label="7d"),
        PredictionWindow(horizon_hours=720.0, horizon_label="30d"),
    ]

    def __init__(self, inference_engine: ModelInferenceEngine | None = None) -> None:
        self.engine = inference_engine or ModelInferenceEngine()

    def forecast_horizons(
        self,
        model_name: str,
        features: PredictionFeatures,
        windows: list[PredictionWindow] | None = None,
    ) -> list[PredictionOutput]:
        """
        Run multi-horizon forecasts.

        Returns:
            list of PredictionOutput objects across requested time windows.
        """
        target_windows = windows or [
            PredictionWindow(horizon_hours=1.0, horizon_label="1h"),
            PredictionWindow(horizon_hours=24.0, horizon_label="24h"),
            PredictionWindow(horizon_hours=168.0, horizon_label="7d"),
        ]

        outputs = []
        for w in target_windows:
            out = self.engine.run_inference(model_name, features, w)
            if out:
                outputs.append(out)
        return outputs
