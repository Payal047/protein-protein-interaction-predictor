import argparse
import hashlib
import sys
from threading import Lock
from pathlib import Path

import joblib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_extraction import (
    MAX_SEQUENCE_LENGTH,
    STANDARD_AMINO_ACIDS,
    extract_pair_features,
    get_pair_feature_columns,
)

MODELS_DIR = PROJECT_ROOT / "models"
MODEL_FILENAME = "logistic_regression_exp3.joblib"
MODEL_PATH = MODELS_DIR / MODEL_FILENAME
EXPECTED_MODEL_SHA256 = "7c8f1cbe26f5b5a23c27f842dfc4593e8c242be8953b5c0e72be9cf8a268e22b"
_MODEL_LOCK = Lock()
_CACHED_MODEL = None


def validate_sequence(sequence: str, label: str) -> str:
    """Validate a protein sequence before feature extraction."""
    if not isinstance(sequence, str):
        raise ValueError(f"{label} sequence is missing.")
    if len(sequence) > MAX_SEQUENCE_LENGTH:
        raise ValueError(
            f"{label} sequence must not exceed {MAX_SEQUENCE_LENGTH:,} residues."
        )
    if not sequence.isascii():
        raise ValueError(f"{label} sequence contains unsupported characters.")
    cleaned = sequence.strip().upper()
    if not cleaned:
        raise ValueError(f"{label} sequence is empty.")
    if set(cleaned) - set(STANDARD_AMINO_ACIDS):
        raise ValueError(f"{label} sequence contains unsupported characters.")
    return cleaned


def load_trusted_model():
    """Load only the integrity-checked project model; joblib files must be trusted."""
    global _CACHED_MODEL
    if _CACHED_MODEL is not None:
        return _CACHED_MODEL

    with _MODEL_LOCK:
        if _CACHED_MODEL is not None:
            return _CACHED_MODEL

        expected_models_dir = MODELS_DIR.resolve(strict=True)
        expected_model_path = MODEL_PATH.resolve(strict=True)
        if (
            expected_model_path.parent != expected_models_dir
            or expected_model_path.name != MODEL_FILENAME
            or not expected_model_path.is_file()
        ):
            raise RuntimeError("The trusted model artifact is unavailable.")

        with expected_model_path.open("rb") as model_file:
            digest = hashlib.sha256()
            for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
                digest.update(chunk)
            if digest.hexdigest() != EXPECTED_MODEL_SHA256:
                raise RuntimeError("The trusted model artifact failed integrity validation.")
            model_file.seek(0)
            loaded_model = joblib.load(model_file)

        if not callable(getattr(loaded_model, "predict", None)) or not callable(
            getattr(loaded_model, "predict_proba", None)
        ):
            raise RuntimeError("The trusted model artifact has an invalid format.")
        if getattr(loaded_model, "n_features_in_", None) != len(
            get_pair_feature_columns()
        ):
            raise RuntimeError("The trusted model artifact has an invalid feature schema.")

        _CACHED_MODEL = loaded_model
        return _CACHED_MODEL


def predict_interaction(sequence_a: str, sequence_b: str):
    """Predict whether the protein pair is likely to interact."""
    cleaned_a = validate_sequence(sequence_a, "Protein A")
    cleaned_b = validate_sequence(sequence_b, "Protein B")

    feature_columns = get_pair_feature_columns()
    features = extract_pair_features(cleaned_a, cleaned_b)
    feature_vector = pd.DataFrame([features], columns=feature_columns)

    model = load_trusted_model()
    prediction = int(model.predict(feature_vector)[0])
    prediction_probability = float(model.predict_proba(feature_vector)[0, list(model.classes_).index(1)])

    return prediction, prediction_probability


def main() -> None:
    """CLI wrapper for PPI prediction on two protein sequences."""
    parser = argparse.ArgumentParser(description="Predict whether two proteins are likely to interact.")
    parser.add_argument("sequence_a", help="Protein A sequence")
    parser.add_argument("sequence_b", help="Protein B sequence")
    args = parser.parse_args()

    try:
        prediction, probability = predict_interaction(args.sequence_a, args.sequence_b)
        label = "YES" if prediction == 1 else "NO"
        print("Predicted interaction: " + label)
        print(f"Probability: {probability * 100:.2f}%")
        print("This is a computational prediction and requires biological validation.")
    except ValueError as error:
        raise SystemExit(f"Input error: {error}") from error
    except Exception:
        raise SystemExit(
            "Prediction could not be completed. Verify the trusted model and try again."
        ) from None


if __name__ == "__main__":
    main()
