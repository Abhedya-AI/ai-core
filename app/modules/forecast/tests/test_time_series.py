from __future__ import annotations
import pytest
import numpy as np

try:
    from app.modules.forecast.application.time_series.decomposition import TimeSeriesDecomposer
    from app.modules.forecast.application.time_series.smoothing import ExponentialSmoother, MovingAverageCalculator
    from app.modules.forecast.application.time_series.interpolation import MissingValueInterpolator
    from app.modules.forecast.application.time_series.confidence_bands import ConfidenceBandCalculator
    from app.modules.forecast.application.time_series.anomaly_aware import AnomalyAwareForecastEngine
    from app.modules.forecast.application.time_series.adaptive_window import AdaptiveForecastWindow
except ImportError:
    pass

class TestTimeSeriesDecomposer:
    def test_decompose_returns_trend_seasonal_residual(self, sample_time_series):
        d = TimeSeriesDecomposer()
        res = d.decompose(sample_time_series)
        assert "trend" in res
        assert "seasonal" in res
        assert "residual" in res

    def test_trend_is_smoothed(self, sample_time_series):
        d = TimeSeriesDecomposer()
        res = d.decompose(sample_time_series)
        assert len(res["trend"]) == len(sample_time_series)

    def test_residual_mean_near_zero(self, sample_time_series):
        d = TimeSeriesDecomposer()
        res = d.decompose(sample_time_series)
        mean_res = np.mean(res["residual"])
        assert abs(mean_res) < 0.1

    def test_seasonality_period_detection(self, sample_time_series):
        d = TimeSeriesDecomposer()
        period = d.detect_period(sample_time_series)
        assert period > 0

    def test_autocorrelation_function(self, sample_time_series):
        d = TimeSeriesDecomposer()
        acf = d.autocorrelation(sample_time_series)
        assert len(acf) > 0

class TestExponentialSmoother:
    def test_smooth_output_length(self, sample_time_series):
        s = ExponentialSmoother()
        res = s.smooth(sample_time_series)
        assert len(res) == len(sample_time_series)

    def test_smooth_reduces_noise(self, sample_time_series):
        s = ExponentialSmoother()
        res = s.smooth(sample_time_series)
        var_orig = np.var(sample_time_series)
        var_smooth = np.var(res)
        assert var_smooth < var_orig

    def test_double_smooth_trend(self, sample_time_series):
        s = ExponentialSmoother()
        res = s.double_smooth(sample_time_series)
        assert len(res) == len(sample_time_series)

class TestMovingAverageCalculator:
    def test_sma_correct_mean(self, sample_time_series):
        c = MovingAverageCalculator()
        sma = c.sma(sample_time_series, window=3)
        assert len(sma) == len(sample_time_series)

    def test_wma_weighted_correctly(self, sample_time_series):
        c = MovingAverageCalculator()
        wma = c.wma(sample_time_series, window=3)
        assert len(wma) == len(sample_time_series)

    def test_ema_exponential_decay(self, sample_time_series):
        c = MovingAverageCalculator()
        ema = c.ema(sample_time_series, window=3)
        assert len(ema) == len(sample_time_series)

    def test_rolling_stats_keys(self, sample_time_series):
        c = MovingAverageCalculator()
        stats = c.rolling_stats(sample_time_series, window=3)
        assert "mean" in stats
        assert "std" in stats

    def test_rolling_stats_mean_correct(self, sample_time_series):
        c = MovingAverageCalculator()
        stats = c.rolling_stats(sample_time_series, window=3)
        assert len(stats["mean"]) == len(sample_time_series)

class TestMissingValueInterpolator:
    def test_linear_interpolation(self):
        i = MissingValueInterpolator()
        res = i.linear([1.0, None, 3.0])
        assert res == [1.0, 2.0, 3.0]

    def test_forward_fill(self):
        i = MissingValueInterpolator()
        res = i.forward_fill([1.0, None, None])
        assert res == [1.0, 1.0, 1.0]

    def test_detect_missing_indices(self):
        i = MissingValueInterpolator()
        res = i.detect_missing([1.0, None, 3.0])
        assert res == [1]

    def test_anomaly_aware_recovery(self):
        i = MissingValueInterpolator()
        res = i.anomaly_aware_recovery([1.0, None, 1.0])
        assert res == [1.0, 1.0, 1.0]

    def test_no_missing_returns_unchanged(self):
        i = MissingValueInterpolator()
        res = i.linear([1.0, 2.0, 3.0])
        assert res == [1.0, 2.0, 3.0]

class TestConfidenceBandCalculator:
    def test_analytical_bands_width(self, sample_time_series):
        c = ConfidenceBandCalculator()
        bands = c.analytical_bands(sample_time_series, confidence=0.95)
        assert bands["upper"][0] > bands["lower"][0]

    def test_bands_contain_prediction(self, sample_time_series):
        c = ConfidenceBandCalculator()
        bands = c.analytical_bands(sample_time_series, confidence=0.95)
        assert all(u >= s >= l for u, s, l in zip(bands["upper"], sample_time_series, bands["lower"]))

    def test_propagated_bands_grow(self, sample_time_series):
        c = ConfidenceBandCalculator()
        bands = c.propagated_bands(sample_time_series, steps=10)
        assert bands["upper"][-1] - bands["lower"][-1] > bands["upper"][0] - bands["lower"][0]

class TestAnomalyAwareForecastEngine:
    def test_detect_anomalies_zscore(self, sample_time_series):
        e = AnomalyAwareForecastEngine()
        anomalies = e.detect_anomalies(sample_time_series)
        assert isinstance(anomalies, list)

    def test_compute_anomaly_severity(self, sample_time_series):
        e = AnomalyAwareForecastEngine()
        severity = e.compute_severity(sample_time_series)
        assert 0 <= severity <= 1

    def test_normal_series_low_severity(self):
        e = AnomalyAwareForecastEngine()
        series = [1.0] * 100
        severity = e.compute_severity(series)
        assert severity < 0.1

class TestAdaptiveForecastWindow:
    def test_select_horizon_stable_series(self, sample_time_series):
        w = AdaptiveForecastWindow()
        horizon = w.select_horizon(sample_time_series, volatility=0.01)
        assert horizon >= 24

    def test_recommend_model_family(self, sample_time_series):
        w = AdaptiveForecastWindow()
        fam = w.recommend_model(sample_time_series)
        assert fam in ["STATISTICAL", "ML", "DL"]

    def test_volatile_series_shorter_horizon(self):
        w = AdaptiveForecastWindow()
        h_stable = w.select_horizon([1.0]*100, volatility=0.01)
        h_volatile = w.select_horizon(np.random.normal(0, 10, 100).tolist(), volatility=0.9)
        assert h_volatile < h_stable

    def test_compute_volatility(self, sample_time_series):
        w = AdaptiveForecastWindow()
        v = w.compute_volatility(sample_time_series)
        assert v >= 0
