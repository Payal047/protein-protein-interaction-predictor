import argparse
import sys
from pathlib import Path

import joblib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_extraction import extract_pair_features, get_pair_feature_columns

MODEL_PATH = PROJECT_ROOT / "models" / "logistic_regression_exp3.joblib"
STANDARD_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")


def validate_sequence(sequence: str, label: str) -> str:
    """Validate a protein sequence before feature extraction."""
    if sequence is None:
        raise ValueError(f"{label} sequence is missing.")
    cleaned = sequence.strip().upper()
    if not cleaned:
        raise ValueError(f"{label} sequence is empty.")
    invalid_characters = sorted(set(cleaned) - STANDARD_AMINO_ACIDS)
    if invalid_characters:
        invalid_text = "".join(invalid_characters)
        raise ValueError(f"{label} contains non-standard amino acids: {invalid_text}")
    return cleaned


def predict_interaction(sequence_a: str, sequence_b: str, model_path: Path | None = None):
    """Predict whether the protein pair is likely to interact."""
    cleaned_a = validate_sequence(sequence_a, "Protein A")
    cleaned_b = validate_sequence(sequence_b, "Protein B")

    feature_columns = get_pair_feature_columns()
    features = extract_pair_features(cleaned_a, cleaned_b)
    feature_vector = pd.DataFrame([features], columns=feature_columns)

    selected_model_path = model_path or MODEL_PATH
    model = joblib.load(selected_model_path)
    prediction = int(model.predict(feature_vector)[0])
    prediction_probability = float(model.predict_proba(feature_vector)[0, list(model.classes_).index(1)])

    return prediction, prediction_probability


def main() -> None:
    """CLI wrapper for PPI prediction on two protein sequences."""
    parser = argparse.ArgumentParser(description="Predict whether two proteins are likely to interact.")
    parser.add_argument("sequence_a", help="Protein A sequence")
    parser.add_argument("sequence_b", help="Protein B sequence")
    parser.add_argument(
        "--model",
        type=Path,
        default=MODEL_PATH,
        help="Path to the saved Experiment 3 model (.joblib)",
    )
    args = parser.parse_args()

    try:
        prediction, probability = predict_interaction(args.sequence_a, args.sequence_b, args.model)
        label = "YES" if prediction == 1 else "NO"
        print("Predicted interaction: " + label)
        print(f"Probability: {probability * 100:.2f}%")
        print("This is a computational prediction and requires biological validation.")
    except ValueError as error:
        raise SystemExit(f"Input error: {error}") from error


if __name__ == "__main__":
    main()
