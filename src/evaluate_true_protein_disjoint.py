from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.feature_extraction import (
    EXPECTED_PAIR_FEATURE_COUNT,
    get_ordered_pair_feature_columns,
    get_pair_feature_columns,
    symmetrize_pair_feature_frame,
)


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "ppi_train_features_exp3.csv"
REPORT_DIR = PROJECT_ROOT / "reports"
PROTEIN_TRAIN_FRACTION = 0.80
SPLIT_RANDOM_STATE = 42
CLASSIFICATION_THRESHOLD = 0.5
EVALUATION_PROTOCOL = (
    "Shuffle unique protein IDs in a NumPy object array with "
    "RandomState(42); assign the first 80% of IDs to training and the rest "
    "to testing; retain a pair only when both proteins belong to the same "
    "partition; exclude cross-partition pairs; fit on retained training "
    "pairs and evaluate on retained testing pairs."
)

REPORT_DIR.mkdir(exist_ok=True)


# ============================================================
# Load dataset
# ============================================================

print("Loading dataset...")

df = pd.read_csv(DATA_PATH)

print(f"Dataset shape: {df.shape}")


# ============================================================
# Check required columns
# ============================================================

required_columns = {"protein_a", "protein_b", "interaction"}

missing = required_columns - set(df.columns)

if missing:
    raise ValueError(f"Missing required columns: {sorted(missing)}")

excluded_columns = {"protein_a", "protein_b", "interaction"}
feature_columns = [column for column in df.columns if column not in excluded_columns]
if feature_columns == get_ordered_pair_feature_columns():
    features = symmetrize_pair_feature_frame(df[feature_columns])
elif feature_columns == get_pair_feature_columns():
    features = df[feature_columns].astype(np.float32)
else:
    raise ValueError(
        f"Expected {EXPECTED_PAIR_FEATURE_COUNT} known features; "
        f"found {len(feature_columns)} columns."
    )
df = pd.concat(
    [df[["protein_a", "protein_b", "interaction"]], features], axis=1
)


# ============================================================
# Create TRUE protein-disjoint split
# ============================================================
#
# We assign each protein to either TRAIN or TEST.
# A protein must never appear in both groups.
#
# For each interaction pair, both proteins must belong
# to the same side. Pairs containing proteins from different
# sides are excluded from this evaluation.
# ============================================================

print("\nCreating protein-disjoint split...")

proteins = pd.unique(
    pd.concat(
        [
            df["protein_a"].astype(str),
            df["protein_b"].astype(str),
        ],
        ignore_index=True,
    )
).to_numpy(dtype=object, copy=True)

rng = np.random.RandomState(SPLIT_RANDOM_STATE)
rng.shuffle(proteins)

split_point = int(len(proteins) * PROTEIN_TRAIN_FRACTION)

train_proteins = set(proteins[:split_point])
test_proteins = set(proteins[split_point:])

print(f"Total unique proteins: {len(proteins)}")
print(f"Training proteins: {len(train_proteins)}")
print(f"Testing proteins: {len(test_proteins)}")


# ============================================================
# Keep only pairs where BOTH proteins belong to same split
# ============================================================

a = df["protein_a"].astype(str)
b = df["protein_b"].astype(str)

train_mask = a.isin(train_proteins) & b.isin(train_proteins)
test_mask = a.isin(test_proteins) & b.isin(test_proteins)

train_df = df.loc[train_mask].copy()
test_df = df.loc[test_mask].copy()

print(f"\nTraining rows: {len(train_df)}")
print(f"Testing rows: {len(test_df)}")


# ============================================================
# Verify ZERO protein overlap
# ============================================================

actual_train_proteins = set(train_df["protein_a"]) | set(train_df["protein_b"])
actual_test_proteins = set(test_df["protein_a"]) | set(test_df["protein_b"])

overlap = actual_train_proteins & actual_test_proteins

print(f"\nProtein overlap: {len(overlap)}")

if overlap:
    raise RuntimeError(
        "ERROR: Protein overlap detected between training and testing sets."
    )

print("SUCCESS: No protein appears in both training and testing sets.")


# ============================================================
# Prepare features
# ============================================================

feature_columns = [
    column
    for column in df.columns
    if column not in excluded_columns
]

X_train = train_df[feature_columns]
y_train = train_df["interaction"]

X_test = test_df[feature_columns]
y_test = test_df["interaction"]

print(f"\nNumber of features: {len(feature_columns)}")


# ============================================================
# Compare candidates on the same true protein-disjoint holdout
# ============================================================

models = {
    "Logistic Regression": Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
    ),
}
model_configurations = {
    "Logistic Regression": (
        "StandardScaler + LogisticRegression(max_iter=1000, random_state=42)"
    ),
    "Random Forest": (
        "RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)"
    ),
}
results = []
for model_name, model in models.items():
    print(f"\nTraining {model_name} on protein-disjoint training pairs...")
    model.fit(X_train, y_train)
    positive_class_index = list(model.classes_).index(1)
    probabilities = model.predict_proba(X_test)[:, positive_class_index]
    predictions = (probabilities >= CLASSIFICATION_THRESHOLD).astype(int)
    matrix = confusion_matrix(y_test, predictions, labels=[0, 1])
    true_negative, false_positive, false_negative, true_positive = matrix.ravel()
    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
        "f1": f1_score(y_test, predictions, zero_division=0),
        "roc_auc": roc_auc_score(y_test, probabilities),
        "positive_detection_rate": true_positive / (true_positive + false_negative),
        "negative_detection_rate": true_negative / (true_negative + false_positive),
    }
    print(f"\n{model_name} true protein-disjoint metrics")
    for metric_name, metric_value in metrics.items():
        print(f"  {metric_name}: {metric_value:.4f}")
    print("  Confusion matrix (rows=true [0, 1], columns=predicted [0, 1]):")
    print(matrix)
    results.append(
        {
            "model": model_name,
            "model_configuration": model_configurations[model_name],
            "evaluation_protocol": EVALUATION_PROTOCOL,
            "protein_split_random_state": SPLIT_RANDOM_STATE,
            "protein_train_fraction": PROTEIN_TRAIN_FRACTION,
            "classification_threshold": CLASSIFICATION_THRESHOLD,
            "feature_count": len(feature_columns),
            "training_rows": len(train_df),
            "testing_rows": len(test_df),
            "training_proteins": len(actual_train_proteins),
            "testing_proteins": len(actual_test_proteins),
            "protein_overlap": len(overlap),
            "training_positive_pairs": int(y_train.sum()),
            "testing_positive_pairs": int(y_test.sum()),
            "testing_negative_pairs": int((y_test == 0).sum()),
            "true_negative": int(true_negative),
            "false_positive": int(false_positive),
            "false_negative": int(false_negative),
            "true_positive": int(true_positive),
            **metrics,
        }
    )

output_path = REPORT_DIR / "true_protein_disjoint_model_comparison.csv"
pd.DataFrame(results).to_csv(output_path, index=False)
print(f"\nResults saved to: {output_path}")