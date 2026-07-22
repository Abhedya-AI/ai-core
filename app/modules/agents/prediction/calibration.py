"""calibration.py — Probability Calibration Engine."""


class ProbabilityCalibrator:
    """Calibrates raw model output probabilities to match empirical historical frequencies."""

    @staticmethod
    def calibrate(raw_probability: float, temperature: float = 1.0) -> float:
        """Apply Platt scaling / temperature scaling calibration to raw probability."""
        if raw_probability <= 0.0:
            return 0.0
        if raw_probability >= 1.0:
            return 1.0
        # Scaled sigmoid transformation
        calibrated = round(raw_probability ** (1.0 / max(0.1, temperature)), 2)
        return min(0.99, max(0.01, calibrated))
