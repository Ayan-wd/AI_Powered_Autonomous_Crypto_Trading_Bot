"""
Model evaluation metrics for time-series financial machine learning.
Calculates classification metrics (Precision, Recall, F1, ROC-AUC) and financial expectancy metrics.
"""

from typing import Any, Dict
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


class ModelEvaluator:
    """Evaluator for trading classification models."""

    @staticmethod
    def evaluate_predictions(
        y_true: np.ndarray, y_pred_proba: np.ndarray, threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Evaluate binary classification probabilities against true labels.
        Returns accuracy, precision, recall, f1, roc_auc, brier_score, and sample counts.
        """
        y_true = np.asarray(y_true)
        y_pred_proba = np.asarray(y_pred_proba)

        # Binary decisions based on probability threshold
        y_pred = (y_pred_proba >= threshold).astype(int)

        total_samples = len(y_true)
        positive_samples = int(np.sum(y_true == 1))
        predicted_positives = int(np.sum(y_pred == 1))

        # Precision (how often was a BUY call actually profitable)
        precision = float(precision_score(y_true, y_pred, zero_division=0))
        recall = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        acc = float(accuracy_score(y_true, y_pred))

        # ROC AUC
        try:
            auc = float(roc_auc_score(y_true, y_pred_proba)) if len(np.unique(y_true)) > 1 else 0.5
        except ValueError:
            auc = 0.5

        # Brier score (calibration metric: lower is better calibrated)
        brier = float(brier_score_loss(y_true, y_pred_proba))

        return {
            "total_samples": total_samples,
            "positive_samples": positive_samples,
            "predicted_positives": predicted_positives,
            "accuracy": round(acc, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(auc, 4),
            "brier_score": round(brier, 4),
            "decision_threshold": threshold,
        }
