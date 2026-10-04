from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "reports"
DATASET_CANDIDATES = (
    PROCESSED_DIR / "ppi_train_features_exp3.csv",
    PROCESSED_DIR / "ppi_train_features.csv",
)
TARGET_COLUMN = "interaction"
ID_COLUMNS = {"protein_a", "protein_b"}
TEST_SIZE = 0.20
RANDOM_STATE = 42
METRIC_NAMES = ("Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC")


def load_dataset() -> tuple[Path, pd.DataFrame, pd.Series]:
    """Load the project's real training features and binary interaction labels."""
    dataset_path = next(
        (path for path in DATASET_CANDIDATES if path.is_file()), None
    )
    if dataset_path is None:
        expected_paths = "\n".join(f"  - {path}" for path in DATASET_CANDIDATES)
        raise FileNotFoundError(
            "No processed training feature dataset was found. Expected one of:\n"
            f"{expected_paths}\nRun the project's feature extraction first."
        )

    columns = pd.read_csv(dataset_path, nrows=0).columns.tolist()
    if TARGET_COLUMN not in columns:
        raise ValueError(
            f"The dataset {dataset_path} has no '{TARGET_COLUMN}' label column."
        )
    feature_columns = [
        column
        for column in columns
        if column != TARGET_COLUMN and column not in ID_COLUMNS
    ]
    if not feature_columns:
        raise ValueError(f"No feature columns were found in {dataset_path}.")

    # Load only model inputs and labels, directly as float32 to limit memory use.
    dataset = pd.read_csv(
        dataset_path,
        usecols=feature_columns + [TARGET_COLUMN],
        dtype={column: np.float32 for column in feature_columns},
    )
    if dataset.empty:
        raise ValueError(f"The dataset contains no rows: {dataset_path}")
    if dataset[feature_columns].isna().to_numpy().any():
        raise ValueError(f"The dataset contains missing feature values: {dataset_path}")

    labels = dataset.pop(TARGET_COLUMN)
    if labels.isna().any() or set(labels.unique()) != {0, 1}:
        raise ValueError(
            f"'{TARGET_COLUMN}' must contain both binary labels 0 and 1; "
            f"found {sorted(labels.dropna().unique().tolist())}."
        )
    return dataset_path, dataset, labels.astype(np.int8)


def evaluate_model(model, training_features, testing_features, training_labels, testing_labels):
    """Fit a classifier and return test metrics and its confusion matrix."""
    model.fit(training_features, training_labels)
    predictions = model.predict(testing_features)
    positive_class_index = list(model.classes_).index(1)
    positive_probabilities = model.predict_proba(testing_features)[:, positive_class_index]
    metrics = {
        "Accuracy": accuracy_score(testing_labels, predictions),
        "Precision": precision_score(testing_labels, predictions, zero_division=0),
        "Recall": recall_score(testing_labels, predictions, zero_division=0),
        "F1-Score": f1_score(testing_labels, predictions, zero_division=0),
        "ROC-AUC": roc_auc_score(testing_labels, positive_probabilities),
    }
    matrix = confusion_matrix(testing_labels, predictions, labels=[0, 1])
    return metrics, matrix


def save_comparison_chart(results: dict[str, dict[str, float]]) -> Path:
    """Save the requested grouped chart for the four threshold metrics."""
    chart_path = OUTPUT_DIR / "model_performance_comparison.png"
    chart_metrics = ("Accuracy", "Precision", "Recall", "F1-Score")
    positions = np.arange(len(chart_metrics))
    bar_width = 0.36

    figure, axis = plt.subplots(figsize=(9, 5.5))
    for offset, (model_name, metrics) in zip(
        (-bar_width / 2, bar_width / 2), results.items()
    ):
        bars = axis.bar(
            positions + offset,
            [metrics[name] for name in chart_metrics],
            bar_width,
            label=model_name,
        )
        axis.bar_label(bars, fmt="%.3f", padding=3, fontsize=8)

    axis.set_title("PPI Model Performance on the Held-Out Test Split")
    axis.set_ylabel("Score")
    axis.set_ylim(0, 1.12)
    axis.set_xticks(positions, chart_metrics)
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.25)
    axis.set_axisbelow(True)
    figure.tight_layout()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(chart_path, dpi=180)
    plt.close(figure)
    return chart_path


def main() -> None:
    dataset_path, features, labels = load_dataset()
    training_features, testing_features, training_labels, testing_labels = (
        train_test_split(
            features,
            labels,
            test_size=TEST_SIZE,
            random_state=RANDOM_STATE,
            stratify=labels,
        )
    )

    models = {
        "Logistic Regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }
    results = {}
    matrices = {}
    for model_name, model in models.items():
        results[model_name], matrices[model_name] = evaluate_model(
            model,
            training_features,
            testing_features,
            training_labels,
            testing_labels,
        )

    # Each metric is on a 0-1 scale; the mean gives a transparent overall comparison.
    overall_scores = {
        model_name: float(np.mean(list(metrics.values())))
        for model_name, metrics in results.items()
    }
    best_model = max(overall_scores, key=overall_scores.get)
    comparison_reason = (
        f"{best_model} has the higher mean across Accuracy, Precision, Recall, "
        f"F1-Score, and ROC-AUC ({overall_scores[best_model]:.4f} vs. "
        f"{overall_scores[next(name for name in results if name != best_model)]:.4f})."
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results_path = OUTPUT_DIR / "model_evaluation_80_20.csv"
    result_rows = []
    for model_name, metrics in results.items():
        result_rows.append(
            {
                "model": model_name,
                "dataset": str(dataset_path.relative_to(PROJECT_ROOT)),
                "training_samples": len(training_labels),
                "testing_samples": len(testing_labels),
                **{name.lower().replace("-", "_"): value for name, value in metrics.items()},
                "mean_metric_score": overall_scores[model_name],
            }
        )
    pd.DataFrame(result_rows).to_csv(results_path, index=False)
    chart_path = save_comparison_chart(results)

    print("=" * 40)
    print("       PPI PREDICTION RESULTS")
    print("=" * 40)
    print(f"Dataset: {dataset_path.relative_to(PROJECT_ROOT)}")
    print(f"Training samples: {len(training_labels)}")
    print(f"Testing samples: {len(testing_labels)}")

    for model_name in models:
        print(f"\n{model_name.upper()}")
        for metric_name in METRIC_NAMES:
            print(f"{metric_name}: {results[model_name][metric_name]:.4f}")
        print("\nConfusion Matrix (rows=true [0, 1], columns=predicted [0, 1]):")
        print(matrices[model_name])

    print("\n" + "=" * 40)
    print("MODEL COMPARISON")
    print("=" * 40)
    print(f"Best Model: {best_model}")
    print(f"Reason: {comparison_reason}")
    print("=" * 40)
    print(f"CSV results: {results_path.relative_to(PROJECT_ROOT)}")
    print(f"Comparison chart: {chart_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()