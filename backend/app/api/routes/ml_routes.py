"""
Machine Learning API routes for training, real-time prediction, and model version inspection.
"""

from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.market_data import MarketDataEngine
from backend.app.database.database import get_db
from backend.app.database.models import ModelMetadata
from backend.app.ml.model_manager import model_manager
from backend.app.ml.predict import PredictionEngine
from backend.app.ml.train import ModelTrainer

router = APIRouter(prefix="/ml", tags=["Machine Learning"])
market_engine = MarketDataEngine()


@router.get("/predict")
async def get_live_prediction(
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="15m"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate live AI prediction (BUY / HOLD / SELL probabilities, confidence, and factual rationale)
    from the latest market candles.
    """
    try:
        df = await market_engine.get_candles_dataframe(
            symbol=symbol.upper(), timeframe=timeframe, limit=200, session=db
        )
        if df.empty or len(df) < 50:
            return {
                "status": "INSUFFICIENT_DATA",
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "candle_count": len(df),
                "decision": "HOLD / NO TRADE",
                "probabilities": {"buy": 0.10, "sell": 0.10, "hold": 0.80},
                "confidence": 0.80,
                "reasoning": [f"Insufficient candle history ({len(df)} candles). Need 50+ to generate features."],
            }

        prediction = PredictionEngine.predict_from_dataframe(df)
        prediction["status"] = "OK"
        return prediction
    except Exception as e:
        logger.error(f"Prediction inference error: {e}")
        return {
            "status": "ERROR",
            "message": str(e),
            "decision": "HOLD / NO TRADE",
            "probabilities": {"buy": 0.0, "sell": 0.0, "hold": 1.0},
            "confidence": 1.0,
            "reasoning": [f"Inference pipeline error: {str(e)} -> Preserving capital"],
        }


@router.post("/train", status_code=status.HTTP_200_OK)
async def train_model(
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="15m"),
    limit_candles: int = Query(default=1000, ge=100, le=1000),
    horizon_candles: int = Query(default=4, ge=1, le=20),
    return_threshold: float = Query(default=0.005, gt=0.0, le=0.05),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute training pipeline on historical candles with Walk-Forward cross-validation,
    serialize weights & scaler, and hot-reload the model into memory.
    """
    try:
        logger.info(f"Starting ML model training on {symbol.upper()} ({timeframe}) with {limit_candles} candles...")
        df = await market_engine.get_candles_dataframe(
            symbol=symbol.upper(), timeframe=timeframe, limit=limit_candles, session=db
        )

        if len(df) < 80:
            return {
                "status": "ERROR",
                "message": f"Need at least 80 candles for train/val split. Got {len(df)} candles.",
            }

        trainer = ModelTrainer(
            horizon_candles=horizon_candles,
            return_threshold=return_threshold,
        )

        X, y = trainer.prepare_dataset(df)
        wf_results = trainer.walk_forward_validation(X, y, n_splits=3)
        model, scaler, metadata = trainer.train_final_model(X, y, save=True)

        # Force reload active model in singleton manager
        model_manager.load_model(force_reload=True)

        # Record run into database
        avg_acc = float(sum(r["accuracy"] for r in wf_results) / len(wf_results)) if wf_results else 0.0
        avg_prec = float(sum(r["precision"] for r in wf_results) / len(wf_results)) if wf_results else 0.0
        avg_f1 = float(sum(r["f1_score"] for r in wf_results) / len(wf_results)) if wf_results else 0.0

        db_model_record = ModelMetadata(
            model_version=metadata["model_version"],
            algorithm="XGBoost",
            target_horizon=horizon_candles,
            target_threshold=return_threshold,
            train_start=X.index[0],
            train_end=X.index[-1],
            val_accuracy=avg_acc,
            val_precision=avg_prec,
            val_f1=avg_f1,
            walk_forward_metrics_json=str(wf_results),
            feature_list_json=str(metadata["feature_columns"]),
        )
        db.add(db_model_record)
        await db.commit()

        return {
            "status": "TRAINING_COMPLETE",
            "model_version": metadata["model_version"],
            "total_samples": len(X),
            "walk_forward_metrics": wf_results,
            "average_val_accuracy": round(avg_acc, 4),
            "average_val_precision": round(avg_prec, 4),
            "top_features": list(metadata["feature_importances"].items())[:5],
        }
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return {"status": "ERROR", "message": f"Training failed: {str(e)}"}


@router.get("/models")
async def list_models():
    """List all available model artifacts and version metadata."""
    return model_manager.get_available_models()
