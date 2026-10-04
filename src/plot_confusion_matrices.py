from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "models" / "confusion_matrices.png"
CLASS_LABELS = ("Non-Interaction", "Interaction")
CONFUSION_MATRICES = {
    "Logistic Regression - Validation": [[17935, 11651], [16564, 13035]],
    "Logistic Regression - Test": [[15913, 10039], [14917, 11040]],
    "Random Forest - Validation": [[24605, 4981], [23797, 5802]],
    "Random Forest - Test": [[21477, 4475], [20467, 5490]],
}


def save_confusion_matrices() -> Path:
    figure, axes = plt.subplots(2, 2, figsize=(12, 9))
    color_limit = max(max(row) for matrix in CONFUSION_MATRICES.values() for row in matrix)

    for axis, (title, values) in zip(axes.flat, CONFUSION_MATRICES.items()):
        matrix = np.asarray(values)
        image = axis.imshow(matrix, cmap="Blues", vmin=0, vmax=color_limit)
        axis.set_title(title)
        axis.set_xticks(range(len(CLASS_LABELS)), CLASS_LABELS)
        axis.set_yticks(range(len(CLASS_LABELS)), CLASS_LABELS)
        axis.set_xlabel("Predicted Class")
        axis.set_ylabel("Actual Class")

        for row in range(matrix.shape[0]):
            for column in range(matrix.shape[1]):
                text_color = "white" if matrix[row, column] > color_limit / 2 else "black"
                axis.text(
                    column,
                    row,
                    f"{matrix[row, column]:,}",
                    ha="center",
                    va="center",
                    color=text_color,
                )

    figure.colorbar(image, ax=axes.ravel().tolist(), label="Count", shrink=0.85)
    figure.savefig(OUTPUT_PATH, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return OUTPUT_PATH


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saved confusion matrices to {save_confusion_matrices()}")


if __name__ == "__main__":
    main()