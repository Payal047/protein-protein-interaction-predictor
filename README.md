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

Random Forest was also evaluated and produced stronger performance in the current evaluation.

## Model Evaluation

The project reports:

* Accuracy
* Precision
* Recall
* F1-score
* ROC-AUC
* Confusion matrix

### Random 80/20 Evaluation

A stratified random 80/20 split was used.

| Model               |   Accuracy |  Precision |     Recall |   F1-score |    ROC-AUC |
| ------------------- | ---------: | ---------: | ---------: | ---------: | ---------: |
| Logistic Regression |     59.12% |     58.95% |     60.04% |     59.49% |     62.72% |
| Random Forest       | **66.51%** | **66.26%** | **67.27%** | **66.76%** | **72.93%** |

Training samples: **130,541**

Testing samples: **32,636**

### Protein-Disjoint Evaluation

A separate protein-disjoint evaluation was performed to provide a stronger assessment of generalization.

Random Forest results:

| Metric           |     Result |
| ---------------- | ---------: |
| Training samples |    130,541 |
| Testing samples  |     32,636 |
| Accuracy         | **65.37%** |
| F1-score         | **65.45%** |
| ROC-AUC          | **71.80%** |

The reproducible evaluation script is:

`src/evaluate_protein_disjoint.py`

Saved results:

`reports/protein_disjoint_evaluation.csv`

### Cross-Validation

A 3-fold Random Forest cross-validation experiment produced:

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

The protein-disjoint evaluation provides a stronger generalization check.

## Prediction System

The prediction system accepts two protein sequences and returns:

* Predicted interaction: `YES` or `NO`
* Interaction probability
* Biological validation warning

Example:

```text
Predicted interaction: NO
Probability: 20.31%

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

```powershell
python src/evaluate_model.py
```

### Run protein-disjoint evaluation

```powershell
python src/evaluate_protein_disjoint.py
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
└── evaluate_protein_disjoint.py

models/
└── logistic_regression_exp3.joblib

reports/
├── model_evaluation_80_20.csv
├── protein_disjoint_evaluation.csv
└── confusion_matrices.png
```

The project is designed so that model evaluation and prediction can be reproduced from the saved scripts, model artifact, data-processing pipeline and dependency specification.

## Disclaimer

This project is intended for **research, educational, and computational screening purposes only**.

A predicted protein interaction is not proof that two proteins physically interact in a biological system. Experimental or independently validated biological evidence is required before drawing scientific or medical conclusions.
