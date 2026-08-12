"""
app/modules/risk_prediction/tests/test_time_series_engine.py
Tests for the TimeSeriesEngine numerical computation functions.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from app.modules.risk_prediction.application.feature_engineering.time_series_engine import (
    TimeSeriesEngine,
)


@pytest.fixture
def engine() -> TimeSeriesEngine:
    return TimeSeriesEngine()


@pytest.fixture
def simple_values() -> list[float]:
    return [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]


@pytest.fixture
def constant_values() -> list[float]:
    return [5.0] * 10


@pytest.fixture
def noisy_values() -> list[float]:
    np.random.seed(42)
    return (np.sin(np.linspace(0, 4 * np.pi, 100)) + np.random.normal(0, 0.1, 100)).tolist()


class TestRollingStats:
    def test_rolling_mean(self, engine, simple_values):
        result = engine.compute_rolling_stats(simple_values, window=5)
        assert "mean" in result
        assert result["mean"] == pytest.approx(8.0, rel=0.01)  # Last 5: [6,7,8,9,10]

    def test_rolling_std(self, engine, simple_values):
        result = engine.compute_rolling_stats(simple_values, window=5)
        assert "std" in result
        assert result["std"] > 0

    def test_rolling_min_max(self, engine, simple_values):
        result = engine.compute_rolling_stats(simple_values, window=5)
        assert result["min"] == pytest.approx(6.0, rel=0.01)
        assert result["max"] == pytest.approx(10.0, rel=0.01)

    def test_empty_values(self, engine):
        result = engine.compute_rolling_stats([], window=5)
        assert result["mean"] == 0.0

    def test_single_value(self, engine):
        result = engine.compute_rolling_stats([5.0], window=5)
        assert result["mean"] == 5.0

    def test_constant_series(self, engine, constant_values):
        result = engine.compute_rolling_stats(constant_values, window=5)
        assert result["std"] == pytest.approx(0.0, abs=1e-6)
        assert result["mean"] == 5.0

    def test_window_larger_than_data(self, engine):
        result = engine.compute_rolling_stats([1.0, 2.0, 3.0], window=10)
        assert result["mean"] == pytest.approx(2.0, rel=0.01)


class TestTrendSlope:
    def test_positive_trend(self, engine, simple_values):
        slope, r2 = engine.compute_trend_slope(simple_values)
        assert slope > 0
        assert r2 > 0.99  # Perfect linear trend

    def test_negative_trend(self, engine):
        values = [10.0, 9.0, 8.0, 7.0, 6.0, 5.0]
        slope, r2 = engine.compute_trend_slope(values)
        assert slope < 0

    def test_constant_trend(self, engine, constant_values):
        slope, r2 = engine.compute_trend_slope(constant_values)
        assert abs(slope) < 1e-10

    def test_empty_values(self, engine):
        slope, r2 = engine.compute_trend_slope([])
        assert slope == 0.0

    def test_single_value(self, engine):
        slope, r2 = engine.compute_trend_slope([5.0])
        assert slope == 0.0

    def test_r_squared_perfect_linear(self, engine, simple_values):
        _, r2 = engine.compute_trend_slope(simple_values)
        assert r2 > 0.99


class TestRateOfChange:
    def test_rate_of_change_increasing(self, engine):
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        timestamps = [(now + timedelta(minutes=i)).isoformat() for i in range(5)]
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        roc = engine.compute_rate_of_change(values, timestamps)
        assert roc > 0

    def test_rate_of_change_constant(self, engine):
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        timestamps = [(now + timedelta(minutes=i)).isoformat() for i in range(5)]
        values = [5.0] * 5
        roc = engine.compute_rate_of_change(values, timestamps)
        assert abs(roc) < 1e-6

    def test_rate_of_change_empty(self, engine):
        roc = engine.compute_rate_of_change([], [])
        assert roc == 0.0


class TestDriftDetection:
    def test_drift_above_baseline(self, engine):
        # Values 3 std above mean → high drift
        values = [10.0] * 20  # All values are 5 std above mean=0, std=2
        drift = engine.detect_drift(values, baseline_mean=0.0, baseline_std=2.0)
        assert drift > 0.5

    def test_no_drift_within_baseline(self, engine):
        values = [1.0, 1.1, 0.9, 1.0, 1.05]  # Within 1 std of mean=1
        drift = engine.detect_drift(values, baseline_mean=1.0, baseline_std=0.5)
        assert drift < 0.5

    def test_drift_score_bounded(self, engine):
        values = [1000.0] * 10
        drift = engine.detect_drift(values, baseline_mean=0.0, baseline_std=1.0)
        assert 0.0 <= drift <= 1.0

    def test_zero_std_baseline(self, engine):
        # Should not raise ZeroDivisionError
        drift = engine.detect_drift([1.0, 2.0], baseline_mean=1.5, baseline_std=0.0)
        assert 0.0 <= drift <= 1.0


class TestInterpolation:
    def test_interpolate_missing_none(self, engine):
        values = [1.0, None, 3.0]
        result = engine.interpolate_missing(values)
        assert result[1] == pytest.approx(2.0, rel=0.01)

    def test_interpolate_no_missing(self, engine):
        values = [1.0, 2.0, 3.0]
        result = engine.interpolate_missing(values)
        assert result == [1.0, 2.0, 3.0]

    def test_interpolate_all_missing(self, engine):
        values = [None, None, None]
        result = engine.interpolate_missing(values)
        assert all(r == 0.0 for r in result)

    def test_interpolate_leading_none(self, engine):
        values = [None, 2.0, 4.0]
        result = engine.interpolate_missing(values)
        assert result[0] is not None

    def test_interpolate_trailing_none(self, engine):
        values = [2.0, 4.0, None]
        result = engine.interpolate_missing(values)
        assert result[2] is not None

    def test_interpolate_multiple_consecutive(self, engine):
        values = [0.0, None, None, None, 4.0]
        result = engine.interpolate_missing(values)
        assert result[2] == pytest.approx(2.0, rel=0.1)


class TestEWMA:
    def test_ewma_smoothing(self, engine):
        values = [1.0, 10.0, 1.0, 10.0, 1.0]
        smoothed = engine.compute_ewma(values, alpha=0.3)
        # EWMA should be smoother than raw values
        assert len(smoothed) == len(values)
        # Variance of smoothed should be less than variance of raw
        raw_var = float(np.var(values))
        smooth_var = float(np.var(smoothed))
        assert smooth_var < raw_var

    def test_ewma_empty(self, engine):
        result = engine.compute_ewma([], alpha=0.3)
        assert result == []

    def test_ewma_single(self, engine):
        result = engine.compute_ewma([5.0], alpha=0.3)
        assert result == [5.0]

    def test_ewma_constant(self, engine, constant_values):
        result = engine.compute_ewma(constant_values, alpha=0.3)
        assert all(abs(r - 5.0) < 1e-6 for r in result)


class TestZScore:
    def test_zscore_above_mean(self, engine):
        z = engine.compute_zscore(value=7.0, mean=5.0, std=2.0)
        assert z == pytest.approx(1.0, rel=0.01)

    def test_zscore_at_mean(self, engine):
        z = engine.compute_zscore(value=5.0, mean=5.0, std=2.0)
        assert z == pytest.approx(0.0, abs=1e-10)

    def test_zscore_negative(self, engine):
        z = engine.compute_zscore(value=3.0, mean=5.0, std=2.0)
        assert z == pytest.approx(-1.0, rel=0.01)

    def test_zscore_zero_std(self, engine):
        # Should not raise ZeroDivisionError
        z = engine.compute_zscore(value=5.0, mean=5.0, std=0.0)
        assert z == 0.0


class TestSeasonalityDecomposition:
    def test_decompose_returns_components(self, engine, noisy_values):
        result = engine.decompose_seasonality(noisy_values)
        assert "trend" in result
        assert "seasonal" in result

    def test_decompose_trend_length(self, engine, noisy_values):
        result = engine.decompose_seasonality(noisy_values)
        assert len(result["trend"]) == len(noisy_values)

    def test_decompose_empty(self, engine):
        result = engine.decompose_seasonality([])
        assert result["trend"] == []

    def test_decompose_short_series(self, engine):
        result = engine.decompose_seasonality([1.0, 2.0, 3.0])
        assert "trend" in result


class TestTemporalScore:
    def test_temporal_score_returns_dict(self, engine):
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        timestamps = [(now - timedelta(minutes=i * 5)).isoformat() for i in range(10)]
        result = engine.compute_temporal_score(timestamps)
        assert "recency_score" in result
        assert "frequency_score" in result
        assert "gap_score" in result

    def test_temporal_score_empty(self, engine):
        result = engine.compute_temporal_score([])
        assert all(v == 0.0 for v in result.values())

    def test_temporal_score_recent_data_high_recency(self, engine):
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        recent_timestamps = [now.isoformat(), (now - timedelta(seconds=30)).isoformat()]
        result = engine.compute_temporal_score(recent_timestamps)
        assert result["recency_score"] > 0.5

    def test_temporal_score_old_data_low_recency(self, engine):
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        old_timestamps = [(now - timedelta(hours=48)).isoformat()]
        result = engine.compute_temporal_score(old_timestamps)
        assert result["recency_score"] < 0.5
