import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from pathlib import Path

DATA_FILE = Path("data/processed/ppi_train_features_exp3.csv")
OUTPUT_FILE = Path("reports/protein_disjoint_evaluation.csv")

df = pd.read_csv(DATA_FILE)

X = df.drop(columns=["interaction", "protein_a", "protein_b"])
y = df["interaction"]

# Keep both proteins from the same pair together
groups = df["protein_a"].astype(str) + "_" + df["protein_b"].astype(str)

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=42
)

train_idx, test_idx = next(splitter.split(X, y, groups))

X_train = X.iloc[train_idx]
X_test = X.iloc[test_idx]
y_train = y.iloc[train_idx]
y_test = y.iloc[test_idx]

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, predictions)
f1 = f1_score(y_test, predictions)
roc_auc = roc_auc_score(y_test, probabilities)

results = pd.DataFrame([{
    "evaluation": "Protein-disjoint evaluation",
    "training_samples": len(train_idx),
    "testing_samples": len(test_idx),
    "accuracy": accuracy,
    "f1_score": f1,
    "roc_auc": roc_auc,
    "random_state": 42
}])

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
results.to_csv(OUTPUT_FILE, index=False)

print("=== PROTEIN-DISJOINT EVALUATION ===")
print(f"Training samples: {len(train_idx)}")
print(f"Testing samples: {len(test_idx)}")
print(f"Accuracy: {accuracy:.4f} ({accuracy:.2%})")
print(f"F1-score: {f1:.4f} ({f1:.2%})")
print(f"ROC-AUC: {roc_auc:.4f} ({roc_auc:.2%})")
print()
print(f"Results saved to: {OUTPUT_FILE}")