"""
Unit tests for Machine Learning training, walk-forward cross-validation, and real-time inference.
"""

from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import pytest
from backend.app.ml.evaluation import ModelEvaluator
from backend.app.ml.model_manager import model_manager
from backend.app.ml.predict import PredictionEngine
from backend.app.ml.train import ModelTrainer


def generate_ohlcv_dataset(n_bars: int = 150) -> pd.DataFrame:
    """Generate synthetic OHLCV dataset for ML testing."""
    np.random.seed(101)
    start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    dates = [start_time + timedelta(minutes=15 * i) for i in range(n_bars)]

    returns = np.random.normal(loc=0.0005, scale=0.008, size=n_bars)
    prices = 90000.0 * np.cumprod(1 + returns)

    highs = prices * (1 + np.abs(np.random.normal(0, 0.003, n_bars)))
    lows = prices * (1 - np.abs(np.random.normal(0, 0.003, n_bars)))
    opens = (highs + lows) / 2.0
    volumes = np.random.uniform(10.0, 100.0, n_bars)

    df = pd.DataFrame(
        {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": prices,
            "volume": volumes,
        },
        index=dates,
    )
    df.index.name = "timestamp"
    return df


def test_model_evaluator():
    """Verify evaluation metric calculations."""
    y_true = np.array([1, 0, 1, 1, 0, 0, 1, 0])
    y_proba = np.array([0.9, 0.1, 0.8, 0.7, 0.2, 0.3, 0.6, 0.4])

    metrics = ModelEvaluator.evaluate_predictions(y_true, y_proba, threshold=0.5)
    assert metrics["accuracy"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0
    assert metrics["roc_auc"] == 1.0
    assert metrics["brier_score"] < 0.1


def test_walk_forward_training_pipeline():
    """Verify end-to-end Walk-Forward cross-validation and model training."""
    df = generate_ohlcv_dataset(150)
    trainer = ModelTrainer(horizon_candles=4, return_threshold=0.005)

    X, y = trainer.prepare_dataset(df)
    assert len(X) == len(y)
    assert len(X) > 0

    wf_results = trainer.walk_forward_validation(X, y, n_splits=3)
    assert len(wf_results) >= 2  # At least 2 valid walk-forward splits
    for fold in wf_results:
        assert "accuracy" in fold
        assert "precision" in fold
        assert "roc_auc" in fold

    # Train final model
    model, scaler, metadata = trainer.train_final_model(X, y, save=True)
    assert model is not None
    assert scaler is not None
    assert metadata["total_samples"] == len(X)
    assert len(metadata["feature_importances"]) > 0


def test_prediction_engine():
    """Verify real-time prediction output format and reasoning."""
    df = generate_ohlcv_dataset(100)
    pred = PredictionEngine.predict_from_dataframe(df)

    assert pred["decision"] in ("BUY", "HOLD / NO TRADE", "SELL")
    assert 0.0 <= pred["probabilities"]["buy"] <= 1.0
    assert 0.0 <= pred["probabilities"]["sell"] <= 1.0
    assert 0.0 <= pred["probabilities"]["hold"] <= 1.0
    assert 0.0 <= pred["confidence"] <= 1.0
    assert len(pred["reasoning"]) > 0
    assert isinstance(pred["features_snapshot"], dict)


def test_model_manager_reloading():
    """Verify ModelManager caching and reload mechanism."""
    model, scaler, meta = model_manager.load_model(force_reload=True)
    assert meta is not None
    assert "model_version" in meta
