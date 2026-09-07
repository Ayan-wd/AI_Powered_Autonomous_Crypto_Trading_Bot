"""
Model Manager & Registry.
Thread-safe singleton managing in-memory cached model binaries, scalers, and version registry.
Provides fallback heuristic model if no weights are found on disk.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
from xgboost import XGBClassifier
from backend.app.core.config import settings
from backend.app.core.logging import logger

MODELS_DIR = Path("models")


class ModelManager:
    """Singleton model lifecycle and memory caching manager."""

    _instance: Optional["ModelManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._model = None
            cls._instance._scaler = None
            cls._instance._metadata = {}
            cls._instance._loaded_version = None
        return cls._instance

    def load_model(self, force_reload: bool = False) -> Tuple[Optional[XGBClassifier], Optional[Any], Dict[str, Any]]:
        """
        Load active model weights, scaler, and metadata from disk.
        Returns cached instances if already loaded.
        """
        if self._model is not None and not force_reload:
            return self._model, self._scaler, self._metadata

        model_path = Path(settings.MODEL_PATH)
        scaler_path = Path(settings.FEATURE_SCALER_PATH)
        meta_path = MODELS_DIR / "metadata_latest.json"

        if model_path.exists() and scaler_path.exists():
            try:
                model = XGBClassifier()
                model.load_model(str(model_path))
                scaler = joblib.load(str(scaler_path))

                metadata = {}
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)

                self._model = model
                self._scaler = scaler
                self._metadata = metadata
                self._loaded_version = metadata.get("model_version", "v1.0.0")
                logger.info(f"Loaded ML model version: {self._loaded_version} from {model_path}")
                return self._model, self._scaler, self._metadata
            except Exception as e:
                logger.error(f"Error loading model from {model_path}: {e}")

        logger.info("No saved model weights found on disk. Operating in fallback quantitative heuristic mode.")
        self._model = None
        self._scaler = None
        self._metadata = {"model_version": "heuristic_fallback_v0"}
        return None, None, self._metadata

    def get_available_models(self) -> List[Dict[str, Any]]:
        """List all serialized model versions stored in the models/ directory."""
        models_info = []
        for meta_file in MODELS_DIR.glob("metadata_*.json"):
            if meta_file.name == "metadata_latest.json":
                continue
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    models_info.append(meta)
            except Exception as e:
                logger.warning(f"Failed to read {meta_file}: {e}")
        return sorted(models_info, key=lambda x: x.get("created_at", ""), reverse=True)


model_manager = ModelManager()
