# Protein–Protein Interaction Prediction

## Problem Statement

Protein–protein interactions (PPIs) are central to many biological processes. This project uses protein sequence-derived features and machine learning to predict whether a pair of proteins is likely to interact.

This is a computational prediction task and should not be treated as biological proof or a substitute for experimental validation.

## Objective

The goal is to build a reproducible machine learning research project that:

* Loads protein sequence data and interaction pairs
* Cleans and validates biological data
* Extracts sequence and physicochemical features
* Trains and evaluates machine learning models
* Predicts interactions for new protein pairs
* Provides a simple Streamlit web interface
* Applies security hardening to the prediction application
* Evaluates model performance using random and protein-disjoint testing

## Dataset

The project uses human protein sequence data and protein interaction pair files.

### Input Data

* FASTA file: `21591618/human_swissprot_oneliner.fasta`
* Positive interaction pairs:

  * `Intra0_pos_rr.txt`
  * `Intra1_pos_rr.txt`
  * `Intra2_pos_rr.txt`
* Negative interaction pairs:

  * `Intra0_neg_rr.txt`
  * `Intra1_neg_rr.txt`
  * `Intra2_neg_rr.txt`

### Processed Data

Main processed dataset:

`data/processed/ppi_train_features_exp3.csv`

The dataset contains:

* 163,177 protein-pair records
* 873 columns
* 870 numerical features
* Protein A identifier
* Protein B identifier
* Interaction target

Class distribution:

* Positive interactions: 81,589
* Negative interactions: 81,588

## Data Preprocessing

The preprocessing workflow:

1. Loads protein FASTA records.
2. Maps protein IDs to amino-acid sequences.
3. Validates amino-acid sequences.
4. Removes missing or invalid sequence records.
5. Creates positive and negative protein pairs.
6. Extracts fixed-length numerical features.
7. Separates protein identifiers from model features.
8. Checks for duplicate records and protein pairs.
9. Creates reproducible train/test splits.

The processed dataset contains:

* **0 exact duplicate rows**
* **0 duplicate protein pairs**

## Feature Extraction

The project creates fixed **870-dimensional pair features** for each protein pair.

Features include:

* Sequence length
* Amino-acid composition
* Dipeptide composition
* Molecular weight
* Aromaticity
* Instability index
* Isoelectric point
* Secondary structure fractions
* Other sequence-derived physicochemical descriptors

The same feature order is used during training and prediction.

## Machine Learning Models

The project evaluates:

* Logistic Regression
* Random Forest

The deployed prediction application currently uses:

`models/logistic_regression_exp3.joblib`

The selected model is the symmetric Exp3 Logistic Regression. It uses 870 order-invariant pair features: `pair_mean_*` and `pair_abs_difference_*`. These summarize each protein's sequence features as the pairwise mean and absolute difference, so swapping protein A and B does not change the representation.

## Model Evaluation

The project reports:

* Accuracy
* Precision
* Recall
* F1-score
* ROC-AUC
* Confusion matrix

### Random 80/20 Evaluation

**Historical random 80/20 row split.** These archived metrics are from `reports/model_evaluation_80_20.csv`, which randomly split rows from the training feature data. There are 3,923 shared proteins between its train and test subsets, so this is not pair- or protein-disjoint evaluation and is not an unseen-protein estimate. The archived metrics predate consistent use of the deployed probability threshold.

| Model               |   Accuracy |  Precision |     Recall |   F1-score |    ROC-AUC |
| ------------------- | ---------: | ---------: | ---------: | ---------: | ---------: |
| Logistic Regression |     59.12% |     58.95% |     60.04% |     59.49% |     62.72% |
| Random Forest       | **66.51%** | **66.26%** | **67.27%** | **66.76%** | **72.93%** |

Training samples: **130,541**

Testing samples: **32,636**

### Current Supplied Protein-Disjoint Holdout (51,909 Rows)

The supplied train, validation, and test partitions have no repeated undirected protein pairs and no shared protein IDs across splits. The 51,909-row test set is therefore both pair-disjoint and protein-disjoint from training.

The following Logistic Regression artifacts were evaluated on the **same 51,909 test pairs in the same order, with identical labels**, using positive probability `>= 0.5` for classification:

| Logistic Regression artifact | Feature representation | Accuracy | Precision | Recall | F1 | ROC-AUC |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Current symmetric Exp3 | 870 order-invariant `pair_mean_*` and `pair_abs_difference_*` features | 56.63% | 57.58% | 50.37% | 53.74% | 59.76% |
| Older Logistic Regression | 842 legacy side-specific features | 51.92% | 52.38% | 42.45% | 46.89% | 53.15% |

The older artifact is the available legacy `models/logistic_regression.joblib`; it is not a separate prior symmetric Exp3 artifact. Because no previous symmetric Exp3 artifact is available, this comparison does **not** establish that symmetrization alone caused the performance difference. It compares the two available models and feature representations under the same test pairs and labels.

### Deterministic True Protein-Disjoint Evaluation

The current evaluator partitions unique protein IDs using a NumPy array shuffled with `RandomState(42)`, assigns 80% of IDs to training and 20% to testing, retains only pairs whose endpoints are both in the same partition, and excludes cross-partition pairs. It fits **both Logistic Regression** (StandardScaler plus `LogisticRegression(max_iter=1000, random_state=42)`) **and Random Forest** (`n_estimators=200`, `random_state=42`) using the retained training pairs, then evaluates each on the retained test pairs with positive probability `>= 0.5`. The output is `reports/true_protein_disjoint_model_comparison.csv`.

The legacy 6,108-row deterministic evaluation recorded an in-memory Logistic Regression result: 106,269 training pairs, 6,108 test pairs, 3,399 training proteins, 786 test proteins, zero protein overlap, and 50,800 excluded cross-partition pairs. Its historical metrics were 52.23% accuracy, 51.85% precision, 51.68% recall, 51.77% F1, and 53.04% ROC-AUC (confusion matrix `[[1624,1454],[1464,1566]]`). These results are weak unseen-protein performance and are not a substitute for the current two-model report.

### Legacy Unattributed True-Disjoint Report

`reports/true_protein_disjoint_evaluation.csv` is preserved legacy data with metrics of 51.44% accuracy, 55.61% precision, 10.46% recall, 17.61% F1, and 52.41% ROC-AUC. Its estimator and evaluation-protocol provenance are unknown. These metrics must not be attributed to Logistic Regression or Random Forest or assumed to use the deterministic protocol above. The current evaluator writes to the separate `reports/true_protein_disjoint_model_comparison.csv` and does not overwrite this legacy report.

The separate `reports/protein_disjoint_evaluation.csv` is a historical random-row split with 130,541 training rows, 32,636 test rows, and 3,923 shared proteins. It is not protein-disjoint and is labeled accordingly.

### Historical Cross-Validation

The README's archived 3-fold Random Forest figures were not independently reproduced: no corresponding cross-validation script or saved fold results were found in the workspace. Treat these values as unverified historical results:

* Accuracy: **61.11%**
* Precision: **61.60%**
* Recall: **58.18%**
* F1-score: **59.84%**
* ROC-AUC: **65.53%**

These results demonstrate that performance varies depending on the evaluation strategy.

## Important Evaluation Limitation

The random 80/20 split contains substantial protein overlap between training and testing:

* Unique training proteins: 4,267
* Unique testing proteins: 3,941
* Proteins appearing in both: 3,923

Therefore, the random split should not be interpreted as a completely unseen-protein evaluation.

The random row, supplied pair-/protein-disjoint holdout, and legacy deterministic true protein-disjoint evaluation are distinct protocols. Do not use random-row results as an unseen-protein claim or treat the unattributed legacy report as model-specific evidence.

## Prediction System

The prediction system accepts two protein sequences and returns:

* Predicted interaction: `YES` or `NO`
* Interaction probability
* Biological validation warning

Example:

```text
Predicted interaction: YES or NO
Probability: <model-generated probability>

This is a computational prediction and requires biological validation.
```

The system should be used as a computational screening and educational tool, not as experimental evidence.

## How to Run

### Activate the virtual environment

```powershell
.\venv\Scripts\Activate.ps1
```

### Install dependencies

```powershell
pip install -r requirements.txt
```

### Run model evaluation

This runs the historical random-row comparison and fits both candidate models; it is not an inference-only evaluation.

```powershell
python -m src.evaluate_model
```

### Evaluate saved Experiment 3 models

This evaluates the existing Logistic Regression and Random Forest artifacts without fitting them.

```powershell
python -m src.evaluate_experiment3
```

### Run protein-disjoint evaluation

This fits both Logistic Regression and Random Forest on the deterministic true protein-disjoint training subset and writes `reports/true_protein_disjoint_model_comparison.csv`. It does not overwrite the legacy `reports/true_protein_disjoint_evaluation.csv`.

```powershell
python -m src.evaluate_protein_disjoint
```

### Run prediction

```powershell
python src/predict.py "MKT..." "GQY..."
```

### Start Streamlit

```powershell
streamlit run app.py
```

## How to Use the Prediction System

1. Enter the amino-acid sequence for Protein A.
2. Enter the amino-acid sequence for Protein B.
3. The system validates both sequences.
4. The 870 features are extracted.
5. The saved model generates a prediction.
6. The application displays the prediction and probability.
7. The result is clearly labeled as a computational prediction.

## Interactive PPI Research Assistant

The application includes a simple rule-based research assistant that helps users with:

* General PPI questions
* Project workflow questions
* Dataset and feature discussions
* Sequence validation guidance
* Machine learning concepts
* Accuracy, precision, recall, F1-score and ROC-AUC
* Guided protein-pair prediction

The chatbot is intended for educational demonstration and does not replace biological validation.

### Supported Questions

Examples include:

* What is PPI?
* How does this project work?
* What is FASTA?
* What are the 870 features?
* What is ROC-AUC?
* Can a YES prediction prove biological interaction?
* Can this system diagnose disease?
* Can this system recommend antibiotics?

## Sequence Validation

The prediction pipeline validates protein sequences using the standard amino-acid alphabet.

Invalid inputs such as empty sequences, unsupported characters, numbers and invalid symbols are rejected.

## Security Hardening

The application was reviewed and hardened against common application-level risks.

Security measures include:

* Input length limits
* Protein sequence validation
* Safe invalid-input handling
* Chat history limited to 20 messages
* Guided sequences redacted from chat history
* Prediction context expiration after 10 minutes
* Prediction rate limiting of five predictions per Streamlit session within 60 seconds
* Trusted model-path enforcement
* Fixed expected model artifact
* SHA-256 model integrity verification
* Model interface and feature-count validation
* Generic user-facing error handling
* No user-controlled model-file loading
* No SQL interface
* No shell/subprocess execution
* No arbitrary filesystem path input
* No file-upload attack surface in the prediction workflow

### Security Testing

The project was checked using:

* Bandit static security analysis
* pip-audit dependency vulnerability scanning
* Local secret scanning
* Git history secret scanning
* Python syntax validation
* Adversarial chatbot testing

Bandit reported **zero security issues**.

`pip-audit` reported **no known vulnerabilities** in the declared dependencies.

After remediation, the project received a **95/100 heuristic security score**. This is an internal security assessment and is not a formal security certification.

### Deployment Security

The application does not include built-in authentication and is intended for local use.

Before public deployment, additional controls should include:

* HTTPS/TLS
* Authentication or access control where required
* Deployment-wide rate limiting
* Secure credential management
* Monitoring and logging

The session-based prediction limit should not be considered a replacement for infrastructure-level rate limiting.

The saved `.joblib` model uses Python pickle-based serialization through `joblib`. Only the trusted fixed model artifact should be loaded.

## Limitations

* This is a sequence-based computational model.
* Predictions are not experimental evidence.
* Performance depends on the dataset and selected features.
* Random splits can contain substantial protein overlap.
* Protein-disjoint evaluation provides a stronger generalization check but is still not laboratory validation.
* The model does not diagnose diseases.
* The model does not determine whether a drug or antibiotic should be prescribed.
* Biological conclusions require independent experimental or validated database evidence.

## Future Scope

Possible extensions include:

* External benchmark validation
* Protein-disjoint and family-level benchmark datasets
* More biologically informed features
* Deep learning models
* Protein language model embeddings
* Graph-based protein interaction models
* Ensemble methods
* Explainable AI
* Confidence calibration
* Integration with experimentally validated PPI databases
* Experimental validation pipelines

## Research Reproducibility

Important evaluation scripts and results are stored in the repository.

```text
src/
├── feature_extraction.py
├── predict.py
├── evaluate_model.py
├── evaluate_protein_disjoint.py
└── evaluate_true_protein_disjoint.py

models/
└── logistic_regression_exp3.joblib

reports/
├── model_evaluation_80_20.csv
├── protein_disjoint_evaluation.csv
├── true_protein_disjoint_evaluation.csv
├── true_protein_disjoint_model_comparison.csv
└── confusion_matrices.png
```

The project is designed so that model evaluation and prediction can be reproduced from the saved scripts, model artifact, data-processing pipeline and dependency specification.

## Disclaimer

This project is intended for **research, educational, and computational screening purposes only**.

A predicted protein interaction is not proof that two proteins physically interact in a biological system. Experimental or independently validated biological evidence is required before drawing scientific or medical conclusions.
