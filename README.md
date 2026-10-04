# Protein–Protein Interaction Prediction

## Problem statement
Protein–protein interactions (PPIs) are central to many biological processes. In this project, we use sequence-derived features and machine learning to predict whether a pair of proteins is likely to interact. This is a computational prediction task and should not be treated as biological proof.

## Objective
The goal is to build a reproducible research project that:
- loads protein sequence data and interaction pairs,
- cleans and validates the data,
- extracts sequence and physicochemical features,
- trains and evaluates machine learning models,
- predicts new interactions for protein pairs,
- provides a simple Streamlit user interface.

## Dataset
The project uses the provided human protein FASTA data and the interaction pair files in the dataset folder.

- FASTA file: 21591618/human_swissprot_oneliner.fasta
- Processed feature files: data/processed/ppi_train_features_exp3.csv, ppi_validation_features_exp3.csv, ppi_test_features_exp3.csv

## Data preprocessing
The preprocessing workflow:
- loads the FASTA protein records,
- maps protein IDs to their sequences,
- validates the amino-acid alphabet,
- removes missing or invalid sequence records,
- ensures the train/validation/test splits are preserved without introducing leakage,
- writes cleaned pair files for downstream feature extraction.

## Feature extraction
The feature extraction workflow builds fixed 870-dimensional pair features for each protein pair using:
- sequence length,
- amino-acid composition,
- dipeptide composition,
- physicochemical descriptors such as molecular weight, aromaticity, instability index, isoelectric point, and secondary structure fractions.

The model receives the same fixed feature order for every split.

## Machine learning models
The saved Experiment 3 models in this project are:
- Logistic Regression
- Random Forest

These saved models are loaded for evaluation and prediction without retraining.

## Evaluation metrics
The project reports the following metrics:
- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC
- Confusion matrix

## Results
The current saved Experiment 3 models produce the following results on the project validation and test sets.

### Validation
- Logistic Regression: Accuracy 0.5233, Precision 0.5280, Recall 0.4404, F1 0.4802, ROC-AUC 0.5358
- Random Forest: Accuracy 0.5138, Precision 0.5381, Recall 0.1960, F1 0.2874, ROC-AUC 0.5334

### Test
- Logistic Regression: Accuracy 0.5192, Precision 0.5237, Recall 0.4253, F1 0.4694, ROC-AUC 0.5320
- Random Forest: Accuracy 0.5195, Precision 0.5509, Recall 0.2115, F1 0.3057, ROC-AUC 0.5429

These values are computational results and should be interpreted as model performance estimates, not biological proof of interaction.

## How to run the project
1. Create or activate the project virtual environment.
2. Install dependencies from requirements.txt.
3. Run the evaluation script:
   python src/evaluate_experiment3.py
4. Run the prediction script with two protein sequences:
   python src/predict.py "MKT..." "GQY..."
5. Start the web interface:
   streamlit run app.py

## How to use the prediction system
- Enter the amino-acid sequence for Protein A and Protein B.
- The system validates the input using the standard amino-acid alphabet.
- The same 870 features used during Experiment 3 are extracted.
- A saved model predicts whether the pair is likely to interact.
- The output is labeled as a computational prediction and requires further biological validation.

## Limitations
- This project is a sequence-based computational model, not an experimental assay.
- Model performance depends on the training data and feature choices.
- Predictions are not direct evidence of a biological interaction.
- The model should be interpreted as a screening aid rather than a definitive biological answer.

## Interactive PPI Research Assistant
The application includes a simple rule-based research assistant that helps users with:
- general PPI questions,
- project workflow questions,
- dataset and feature discussion,
- sequence validation guidance,
- machine learning concepts such as Logistic Regression, Random Forest, accuracy, precision, recall, F1-score, and ROC-AUC,
- guided prediction of a new protein pair.

The chatbot is intended for educational demonstration. It does not replace biological validation or experimental testing.

### Supported questions
Examples include:
- What is PPI?
- How does this project work?
- What is FASTA?
- What are the 870 features?
- What is ROC-AUC?
- Can a YES prediction prove biological interaction?
- Can this system diagnose disease or recommend antibiotics?

### Prediction conversation flow
The assistant can guide a user through the prediction flow:
1. Provide Protein A sequence.
2. Provide Protein B sequence.
3. Confirm that the user wants to run the computational prediction.
4. The app reuses the existing saved Experiment 3 model and prediction logic.
5. The result is reported as a computational prediction with a warning that experimental validation is required.

### Sequence validation
The assistant and the prediction pipeline both reuse the same validation rules. Invalid sequences are rejected with errors such as:
- empty inputs,
- unsupported characters,
- numbers,
- non-standard amino-acid symbols.

## Security and deployment
The prediction and feature-extraction paths accept ASCII standard amino-acid sequences up to 40,000 residues. Chat messages have the same maximum length, chat history is capped at 20 entries, guided sequences are redacted from that history, and unfinished chat prediction context expires after 10 minutes. Prediction requests are limited to five per Streamlit session in a rolling 60-second window.

The saved model is loaded with `joblib`, which uses Python pickle serialization and can execute code while loading. Treat `models/logistic_regression_exp3.joblib` as trusted executable content. The application only loads that fixed artifact after checking its location and SHA-256 digest; never load user-uploaded or otherwise untrusted model files. An intentional model replacement requires reviewing the new artifact and updating the expected digest in `src/predict.py`.

The application has no built-in authentication and is intended for local use. Before exposing it to other users, put it behind TLS and an authenticated proxy or platform access control, and add deployment-wide request limits: the built-in prediction limit is per Streamlit session and can be bypassed by creating new sessions. Keep Streamlit's security protections enabled. Store credentials outside source control; `.env` variants and common private-key files are ignored by Git, but ignore rules do not remove secrets already committed to repository history.

## Future scope
Possible extensions include:
- adding more biologically informed features,
- investigating alternative models and ensemble methods,
- validating against external benchmark datasets,
- improving explainability for individual predictions,
- connecting predictions to experimental validation pipelines.
