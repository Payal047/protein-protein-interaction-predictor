from pathlib import Path
import runpy


def main() -> None:
    """Run the evaluator that writes reports/true_protein_disjoint_model_comparison.csv."""
    evaluator_path = Path(__file__).with_name("evaluate_true_protein_disjoint.py")
    runpy.run_path(str(evaluator_path), run_name="__main__")


if __name__ == "__main__":
    main()