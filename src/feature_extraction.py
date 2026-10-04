from collections import Counter
import gc
import math
from pathlib import Path

import numpy as np
import pandas as pd
from Bio.SeqUtils.ProtParam import ProteinAnalysis


# Resolve project data paths relative to this file so the script works from any cwd.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Keep the amino-acid order stable so feature columns are always predictable.
STANDARD_AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
MAX_SEQUENCE_LENGTH = 40_000
SPLITS = ("train", "validation", "test")
CHUNK_SIZE = 5000
AMINO_ACID_FEATURE_COUNT = 1 + 20 + 400
PHYSICOCHEMICAL_FEATURE_NAMES = (
    "molecular_weight",
    "aromaticity",
    "instability_index",
    "isoelectric_point",
    "flexibility",
    "helix_fraction",
    "turn_fraction",
    "sheet_fraction",
    "hydrophobic_residue_fraction",
    "charged_residue_fraction",
    "positive_residue_fraction",
    "negative_residue_fraction",
    "polar_residue_fraction",
    "small_residue_fraction",
)
EXPECTED_PROTEIN_FEATURE_COUNT = AMINO_ACID_FEATURE_COUNT + len(
    PHYSICOCHEMICAL_FEATURE_NAMES
)
EXPECTED_PAIR_FEATURE_COUNT = 2 * EXPECTED_PROTEIN_FEATURE_COUNT
EXPECTED_OUTPUT_COLUMN_COUNT = EXPECTED_PAIR_FEATURE_COUNT + 3
PRESERVED_COLUMNS = ["protein_a", "protein_b", "interaction"]

# Explicit residue groups make each reported fraction reproducible.
HYDROPHOBIC_RESIDUES = set("AVILMFWY")
CHARGED_RESIDUES = set("DEKRH")
POSITIVE_RESIDUES = set("KRH")
NEGATIVE_RESIDUES = set("DE")
POLAR_RESIDUES = set("NQSTCY")
SMALL_RESIDUES = set("ACDGNPSTV")


def get_pair_feature_columns() -> list[str]:
    """Build feature column names in the same fixed order as pair extraction."""
    protein_feature_names = ["length"]
    protein_feature_names.extend(
        f"frequency_{amino_acid}" for amino_acid in STANDARD_AMINO_ACIDS
    )
    protein_feature_names.extend(
        f"frequency_dipeptide_{first}{second}"
        for first in STANDARD_AMINO_ACIDS
        for second in STANDARD_AMINO_ACIDS
    )
    protein_feature_names.extend(PHYSICOCHEMICAL_FEATURE_NAMES)

    return [
        f"protein_{protein_side}_{feature_name}"
        for protein_side in ("a", "b")
        for feature_name in protein_feature_names
    ]


def extract_protein_features(sequence: str) -> dict[str, float | int]:
    """Return sequence length, amino-acid proportions, and dipeptide proportions."""
    if not isinstance(sequence, str):
        raise ValueError("A protein sequence must be text.")
    if len(sequence) > MAX_SEQUENCE_LENGTH:
        raise ValueError(
            f"A protein sequence must not exceed {MAX_SEQUENCE_LENGTH:,} residues."
        )
    if not sequence.isascii():
        raise ValueError("A protein sequence contains unsupported characters.")

    # Normalize lowercase input so callers can pass sequences in either case.
    normalized_sequence = sequence.strip().upper()
    if not normalized_sequence:
        raise ValueError("A protein sequence must not be empty.")

    # Reject symbols outside the 20 standard amino acids instead of silently
    # producing misleading composition proportions.
    invalid_amino_acids = set(normalized_sequence) - set(STANDARD_AMINO_ACIDS)
    if invalid_amino_acids:
        raise ValueError("A protein sequence contains unsupported characters.")

    # Count each amino acid once, then divide by sequence length to get its
    # frequency as a proportion. Standard amino acids absent from a sequence
    # receive a proportion of zero.
    amino_acid_counts = Counter(normalized_sequence)
    sequence_length = len(normalized_sequence)
    features: dict[str, float | int] = {"length": sequence_length}
    for amino_acid in STANDARD_AMINO_ACIDS:
        features[f"frequency_{amino_acid}"] = (
            amino_acid_counts[amino_acid] / sequence_length
        )

    # Count overlapping adjacent amino-acid pairs, such as AC, CD, and DA in
    # the sequence ACDA. Divide by the number of adjacent positions so the
    # 400 proportions sum to one when the sequence has at least two residues.
    dipeptide_counts = Counter(
        normalized_sequence[index : index + 2]
        for index in range(sequence_length - 1)
    )
    dipeptide_count = sequence_length - 1
    for first_amino_acid in STANDARD_AMINO_ACIDS:
        for second_amino_acid in STANDARD_AMINO_ACIDS:
            dipeptide = first_amino_acid + second_amino_acid
            feature_name = f"frequency_dipeptide_{dipeptide}"
            features[feature_name] = (
                dipeptide_counts[dipeptide] / dipeptide_count
                if dipeptide_count > 0
                else 0.0
            )

    # Biopython supplies established sequence-based physicochemical measures.
    try:
        protein_analysis = ProteinAnalysis(normalized_sequence)
        flexibility_values = protein_analysis.flexibility()
        if not flexibility_values:
            raise ValueError(
                "sequence is too short for Biopython's flexibility calculation "
                f"({sequence_length} residues)."
            )

        helix_fraction, turn_fraction, sheet_fraction = (
            protein_analysis.secondary_structure_fraction()
        )
        physicochemical_features = {
            "molecular_weight": protein_analysis.molecular_weight(),
            "aromaticity": protein_analysis.aromaticity(),
            "instability_index": protein_analysis.instability_index(),
            "isoelectric_point": protein_analysis.isoelectric_point(),
            # Biopython gives a flexibility value per valid sequence window;
            # their mean produces one deterministic value per sequence.
            "flexibility": sum(flexibility_values) / len(flexibility_values),
            "helix_fraction": helix_fraction,
            "turn_fraction": turn_fraction,
            "sheet_fraction": sheet_fraction,
            "hydrophobic_residue_fraction": sum(
                amino_acid_counts[residue] for residue in HYDROPHOBIC_RESIDUES
            )
            / sequence_length,
            "charged_residue_fraction": sum(
                amino_acid_counts[residue] for residue in CHARGED_RESIDUES
            )
            / sequence_length,
            "positive_residue_fraction": sum(
                amino_acid_counts[residue] for residue in POSITIVE_RESIDUES
            )
            / sequence_length,
            "negative_residue_fraction": sum(
                amino_acid_counts[residue] for residue in NEGATIVE_RESIDUES
            )
            / sequence_length,
            "polar_residue_fraction": sum(
                amino_acid_counts[residue] for residue in POLAR_RESIDUES
            )
            / sequence_length,
            "small_residue_fraction": sum(
                amino_acid_counts[residue] for residue in SMALL_RESIDUES
            )
            / sequence_length,
        }
    except ValueError as error:
        raise ValueError(
            "Could not calculate features for this sequence. Check that it is "
            "valid and long enough."
        ) from error
    except Exception as error:
        raise ValueError("Sequence feature extraction failed.") from error

    for feature_name in PHYSICOCHEMICAL_FEATURE_NAMES:
        value = float(physicochemical_features[feature_name])
        if not math.isfinite(value):
            raise ValueError(
                f"Biopython produced a non-finite {feature_name} for a "
                f"sequence of {sequence_length} residues."
            )
        features[feature_name] = value

    return features


def extract_pair_features(sequence_a: str, sequence_b: str) -> dict[str, float | int]:
    """Return numerical sequence features for a protein pair."""
    features_a = extract_protein_features(sequence_a)
    features_b = extract_protein_features(sequence_b)

    # Prefix each feature with its protein side to keep both sequences distinct.
    pair_features = {
        f"protein_a_{feature_name}": value
        for feature_name, value in features_a.items()
    }
    pair_features.update(
        {
            f"protein_b_{feature_name}": value
            for feature_name, value in features_b.items()
        }
    )
    return pair_features


def extract_dataset_features(input_path: Path, output_path: Path) -> None:
    """Convert a cleaned PPI CSV to features using bounded memory per chunk."""
    required_columns = {"protein_a", "protein_b", "sequence_a", "sequence_b", "interaction"}
    pair_feature_columns = get_pair_feature_columns()
    output_columns = ["protein_a", "protein_b"] + pair_feature_columns + ["interaction"]
    rows_processed = 0
    chunk_number = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Each source chunk is released after writing so memory use stays bounded.
    for chunk_number, pairs in enumerate(
        pd.read_csv(input_path, chunksize=CHUNK_SIZE), start=1
    ):
        # A chunk from read_csv can retain a global index. Reset it before using
        # any of its columns so every value is aligned by row position.
        pairs = pairs.reset_index(drop=True)

        missing_columns = required_columns - set(pairs.columns)
        if missing_columns:
            missing_names = ", ".join(sorted(missing_columns))
            raise ValueError(f"{input_path} is missing required columns: {missing_names}")

        # Build features in a positional numeric matrix. This avoids combining
        # pandas objects whose indexes could trigger unintended alignment.
        feature_matrix = np.empty(
            (len(pairs), EXPECTED_PAIR_FEATURE_COUNT), dtype=np.float64
        )
        for row_index, (sequence_a, sequence_b) in enumerate(
            zip(pairs["sequence_a"].tolist(), pairs["sequence_b"].tolist())
        ):
            pair_features = extract_pair_features(sequence_a, sequence_b)
            feature_matrix[row_index] = list(pair_features.values())
            del pair_features

        # Feature values and metadata are all supplied positionally from this
        # reset chunk. The input sequence columns are intentionally not saved.
        feature_dataset = pd.DataFrame(
            feature_matrix, columns=pair_feature_columns, copy=False
        )
        feature_dataset.insert(0, "protein_a", pairs["protein_a"].to_numpy(copy=True))
        feature_dataset.insert(1, "protein_b", pairs["protein_b"].to_numpy(copy=True))
        feature_dataset["interaction"] = pairs["interaction"].to_numpy(copy=True)
        feature_dataset = feature_dataset[output_columns]

        # Fail before writing this chunk if its shape or values are malformed.
        if len(feature_dataset.columns) != EXPECTED_OUTPUT_COLUMN_COUNT:
            raise AssertionError(
                f"Chunk {chunk_number}: expected "
                f"{EXPECTED_OUTPUT_COLUMN_COUNT} output columns, "
                f"found {len(feature_dataset.columns)}."
            )
        if feature_dataset.isna().to_numpy().any():
            raise AssertionError(
                f"Chunk {chunk_number}: output chunk contains NaN values; "
                "the chunk was not written."
            )
        numeric_feature_columns = feature_dataset[pair_feature_columns]
        if not all(
            pd.api.types.is_numeric_dtype(numeric_feature_columns[column])
            for column in pair_feature_columns
        ):
            raise AssertionError(
                f"Chunk {chunk_number}: one or more of the 842 feature columns "
                "are not numeric; the chunk was not written."
            )

        # Write a header for the first chunk and append later chunks without one.
        feature_dataset.to_csv(
            output_path,
            index=False,
            mode="w" if chunk_number == 1 else "a",
            header=chunk_number == 1,
        )
        rows_processed += len(pairs)
        print(
            f"Chunk {chunk_number}: processed {rows_processed} rows; "
            f"output: {output_path}"
        )

        # Explicitly release large temporary objects before loading the next chunk.
        del pairs, feature_matrix, feature_dataset, numeric_feature_columns
        gc.collect()

    # Empty input files still get a correctly ordered header row.
    if chunk_number == 0:
        pd.DataFrame(columns=output_columns).to_csv(output_path, index=False)

    # Read only the header to verify the output schema without loading feature data.
    written_columns = pd.read_csv(output_path, nrows=0).columns.tolist()
    numerical_columns = [
        column
        for column in written_columns
        if column not in PRESERVED_COLUMNS
    ]
    if len(numerical_columns) != EXPECTED_PAIR_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_PAIR_FEATURE_COUNT} numerical pair features in "
            f"{output_path}, but found {len(numerical_columns)}."
        )
    if written_columns != output_columns:
        raise ValueError(f"Unexpected output column names or order in {output_path}.")

    # Count output NaNs in chunks so this final validation also uses bounded memory.
    output_nan_count = 0
    for output_chunk in pd.read_csv(output_path, chunksize=CHUNK_SIZE):
        output_nan_count += int(output_chunk.isna().sum().sum())
        del output_chunk

    print(f"Total rows processed: {rows_processed}")
    print(f"Final column count: {len(written_columns)}")
    print(f"Total NaN count in output file: {output_nan_count}")


def main() -> None:
    """Generate separate Experiment 3 outputs without replacing earlier runs."""
    for split_name in SPLITS:
        input_path = PROCESSED_DIR / f"ppi_{split_name}.csv"
        output_path = PROCESSED_DIR / f"ppi_{split_name}_features_exp3.csv"
        if not input_path.is_file():
            raise FileNotFoundError(f"Cleaned dataset was not found: {input_path}")
        extract_dataset_features(input_path, output_path)


if __name__ == "__main__":
    main()