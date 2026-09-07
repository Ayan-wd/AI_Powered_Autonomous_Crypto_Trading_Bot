"""
XGBoost Model Training & Walk-Forward Cross-Validation Pipeline.
Strict chronological time-series splitting, zero lookahead leakage,
feature scaler serialization, and versioned metadata logging.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler
from xgboost import XGBClassifier
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.features.feature_engineering import FEATURE_COLUMNS, FeaturePipeline
from backend.app.ml.evaluation import ModelEvaluator

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)


class ModelTrainer:
    """XGBoost training pipeline with walk-forward cross-validation."""

    def __init__(
        self,
        horizon_candles: int = 4,
        return_threshold: float = 0.005,
        stop_loss_threshold: float = 0.010,
        model_version: Optional[str] = None,
    ):
        self.horizon = horizon_candles
        self.return_threshold = return_threshold
        self.stop_loss_threshold = stop_loss_threshold
        self.version = model_version or f"xgb_btc_15m_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    def prepare_dataset(self, df_candles: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Compute features and target labels from OHLCV DataFrame.
        Drops trailing horizon candles to prevent target leakage.
        """
        df_features = FeaturePipeline.build_features(df_candles, drop_na=True)
        target = FeaturePipeline.create_classification_target(
            df_features,
            horizon_candles=self.horizon,
            return_threshold=self.return_threshold,
            stop_loss_threshold=self.stop_loss_threshold,
        )

        # Align features and target (drop trailing NaNs from target horizon)
        valid_mask = target.notna()
        X = df_features.loc[valid_mask, FEATURE_COLUMNS]
        y = target.loc[valid_mask].astype(int)

        logger.info(f"Dataset prepared: {len(X)} samples. Positive BUY rate: {y.mean() * 100:.2f}%")
        return X, y

    def walk_forward_validation(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_splits: int = 3,
        min_train_samples: int = 40,
    ) -> List[Dict[str, Any]]:
        """
        Execute expanding-window Walk-Forward cross-validation.
        Guarantees that test data is strictly in the future of training data.
        """
        n_samples = len(X)
        if n_samples < (min_train_samples + 15):
            raise ValueError(f"Insufficient samples for walk-forward validation: {n_samples}")

        # Compute step size for test windows
        available_test = n_samples - min_train_samples
        test_step = max(10, available_test // n_splits)

        results = []
        logger.info(f"Running expanding-window Walk-Forward Validation ({n_splits} folds) on {n_samples} samples...")

        for fold in range(n_splits):
            train_end = min_train_samples + (fold * test_step)
            test_end = min(train_end + test_step, n_samples)

            if train_end >= n_samples or (test_end - train_end) < 5:
                break

            X_train = X.iloc[:train_end]
            y_train = y.iloc[:train_end]
            X_val = X.iloc[train_end:test_end]
            y_val = y.iloc[train_end:test_end]

            # Fit scaler strictly on training slice
            scaler = RobustScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)

            # Class weighting to handle imbalance
            neg_count = np.sum(y_train == 0)
            pos_count = max(np.sum(y_train == 1), 1)
            scale_pos_weight = float(neg_count / pos_count)

            model = XGBClassifier(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.04,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                scale_pos_weight=scale_pos_weight,
                random_state=42,
                eval_metric="logloss",
            )
            model.fit(X_train_scaled, y_train)

            val_preds_proba = model.predict_proba(X_val_scaled)[:, 1]
            fold_metrics = ModelEvaluator.evaluate_predictions(
                y_val.values, val_preds_proba, threshold=settings.MIN_PREDICTION_CONFIDENCE
            )
            fold_metrics["fold"] = fold + 1
            fold_metrics["train_size"] = len(X_train)
            fold_metrics["test_size"] = len(X_val)
            fold_metrics["train_start"] = str(X_train.index[0])
            fold_metrics["train_end"] = str(X_train.index[-1])
            fold_metrics["val_start"] = str(X_val.index[0])
            fold_metrics["val_end"] = str(X_val.index[-1])

            results.append(fold_metrics)
            logger.info(
                f"Fold {fold + 1} (Train {len(X_train)} / Val {len(X_val)}) - "
                f"Accuracy: {fold_metrics['accuracy']:.4f}, Precision: {fold_metrics['precision']:.4f}, "
                f"ROC-AUC: {fold_metrics['roc_auc']:.4f}"
            )

        return results

    def train_final_model(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        save: bool = True,
    ) -> Tuple[XGBClassifier, RobustScaler, Dict[str, Any]]:
        """
        Train the production model on full data and serialize weights + scaler + metadata.
        """
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X)

        neg_count = np.sum(y == 0)
        pos_count = max(np.sum(y == 1), 1)
        scale_pos_weight = float(neg_count / pos_count)

        model = XGBClassifier(
            n_estimators=150,
            max_depth=4,
            learning_rate=0.03,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.2,
            reg_lambda=1.5,
            scale_pos_weight=scale_pos_weight,
            random_state=42,
            eval_metric="logloss",
        )
        model.fit(X_scaled, y)

        # Feature importances
        importances = {
            col: round(float(imp), 4)
            for col, imp in zip(FEATURE_COLUMNS, model.feature_importances_)
        }
        sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))

        metadata = {
            "model_version": self.version,
            "algorithm": "XGBoost",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "target_horizon_candles": self.horizon,
            "target_return_threshold": self.return_threshold,
            "stop_loss_threshold": self.stop_loss_threshold,
            "total_samples": len(X),
            "feature_columns": FEATURE_COLUMNS,
            "feature_importances": sorted_importances,
            "hyperparameters": {
                "n_estimators": 150,
                "max_depth": 4,
                "learning_rate": 0.03,
                "subsample": 0.85,
                "colsample_bytree": 0.85,
                "scale_pos_weight": round(scale_pos_weight, 3),
            },
        }

        if save:
            model_path = MODELS_DIR / f"{self.version}.json"
            scaler_path = MODELS_DIR / f"scaler_{self.version}.joblib"
            meta_path = MODELS_DIR / f"metadata_{self.version}.json"

            model.save_model(str(model_path))
            joblib.dump(scaler, str(scaler_path))
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            # Update default standard pointers
            model.save_model("models/xgboost_btc_15m.json")
            joblib.dump(scaler, "models/scaler_btc_15m.joblib")
            with open("models/metadata_latest.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Model saved to {model_path} and models/xgboost_btc_15m.json")

        return model, scaler, metadata
