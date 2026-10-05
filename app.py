import logging
import time

import streamlit as st

from src.feature_extraction import MAX_SEQUENCE_LENGTH
from src.predict import predict_interaction, validate_sequence


MAX_CHAT_MESSAGE_LENGTH = MAX_SEQUENCE_LENGTH
MAX_CHAT_HISTORY_MESSAGES = 20
PREDICTION_WINDOW_SECONDS = 60
MAX_PREDICTIONS_PER_WINDOW = 5
CHAT_CONTEXT_TTL_SECONDS = 600

LOGGER = logging.getLogger(__name__)

WELCOME_MESSAGE = {
    "role": "assistant",
    "content": (
        "Welcome to the PPI Research Assistant. Ask about protein-protein "
        "interaction, this project, the dataset, the features, or start a prediction."
    ),
}


st.set_page_config(
    page_title="PPI Predictor",
    page_icon="🧬",
)


def reset_chat_context() -> None:
    """Reset the assistant conversation state for a clean session."""
    st.session_state.chat_context = {
        "protein_a": None,
        "protein_b": None,
        "step": "idle",
        "started_at": None,
    }


def start_prediction_flow() -> None:
    reset_chat_context()
    st.session_state.chat_context["step"] = "waiting_for_protein_a"
    st.session_state.chat_context["started_at"] = time.monotonic()


def initialize_chat_state() -> None:
    """Create the chat memory structure once per browser session."""
    if "messages" not in st.session_state:
        st.session_state.messages = [WELCOME_MESSAGE.copy()]

    if "chat_context" not in st.session_state:
        reset_chat_context()

    st.session_state.setdefault("prediction_timestamps", [])


def append_chat_message(role: str, content: str) -> None:
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
        }
    )

    st.session_state.messages = st.session_state.messages[
        -MAX_CHAT_HISTORY_MESSAGES:
    ]


def safe_history_content(message: str, context_step: str) -> str:
    if context_step == "waiting_for_protein_a":
        return "[Protein A sequence redacted]"

    if context_step == "waiting_for_protein_b":
        return "[Protein B sequence redacted]"

    try:
        validate_sequence(message, "Input")
    except ValueError:
        return message

    if len(message.strip()) >= 8:
        return "[Protein-like input redacted]"

    return message


def allow_prediction() -> bool:
    now = time.monotonic()

    recent_timestamps = [
        timestamp
        for timestamp in st.session_state.prediction_timestamps
        if now - timestamp < PREDICTION_WINDOW_SECONDS
    ]

    st.session_state.prediction_timestamps = recent_timestamps

    if len(recent_timestamps) >= MAX_PREDICTIONS_PER_WINDOW:
        return False

    recent_timestamps.append(now)
    st.session_state.prediction_timestamps = recent_timestamps

    return True


def clear_prediction_inputs() -> None:
    st.session_state["protein_a_input"] = ""
    st.session_state["protein_b_input"] = ""


def knowledge_response(message: str) -> str:
    """Provide a local, project-aware response to common PPI project questions."""
    query = message.strip().lower()

    if any(
        term in query
        for term in ("what is ppi", "protein-protein interaction")
    ):
        return (
            "Protein-protein interaction (PPI) is a physical or functional "
            "association between two proteins. In this project, we treat PPI "
            "as a supervised prediction task: given protein sequences, the "
            "model predicts whether a pair is likely to interact."
        )

    if "how does this project work" in query:
        return (
            "This project validates protein sequences, extracts 870 feature "
            "values for each protein pair, loads a saved Experiment 3 model, "
            "and predicts whether the pair is likely to interact. It is a "
            "computational screening tool, not biological proof."
        )

    if "what dataset" in query or "dataset are you using" in query:
        return (
            "The project uses the provided human protein FASTA database and "
            "interaction pair files from the project folder. The model uses "
            "the preserved train/validation/test split and the saved "
            "Experiment 3 feature files."
        )

    if "what are the 870 features" in query or "870 feature" in query:
        return (
            "The Experiment 3 pipeline uses 870 numerical pair features: "
            "sequence length, amino-acid composition, dipeptide composition, "
            "and physicochemical descriptors such as molecular weight, "
            "aromaticity, instability index, isoelectric point, and "
            "secondary-structure fractions for both proteins."
        )

    if "what is fasta" in query:
        return (
            "FASTA is a common file format for biological sequences. It stores "
            "a protein identifier followed by the amino-acid sequence, for "
            "example: >ProteinID\\nMKTIIALSYIFCLVFA."
        )

    if "what is logistic regression" in query:
        return (
            "Logistic Regression is a linear classifier that estimates the "
            "probability of a binary outcome. In this project, it is trained "
            "on the sequence-derived features and predicts whether the "
            "interaction label is 0 or 1."
        )

    if "what is random forest" in query:
        return (
            "Random Forest is an ensemble of decision trees. It averages many "
            "tree decisions and is often useful for capturing non-linear "
            "patterns in tabular biological features."
        )

    if "what is roc-auc" in query or "roc auc" in query:
        return (
            "ROC-AUC measures how well a classifier separates positive and "
            "negative classes across thresholds. A higher value means better "
            "ranking of positive examples, but it is not a biological proof "
            "of interaction."
        )

    if (
        "accuracy" in query
        or "precision" in query
        or "recall" in query
        or "f1" in query
    ):
        return (
            "Accuracy measures how often the model is correct overall. "
            "Precision measures how many predicted positives are actually "
            "positive. Recall measures how many true positives are recovered. "
            "F1-score balances precision and recall. These metrics are "
            "reported for validation and test data."
        )

    if (
        "experiment 1" in query
        or "experiment 2" in query
        or "experiment 3" in query
    ):
        return (
            "This project compares different experimental workflows, and the "
            "current saved model used for prediction is the Experiment 3 "
            "pipeline. Experiment 3 uses the fixed 870-feature representation "
            "and the saved model files in the models folder."
        )

    if "feature extraction" in query:
        return (
            "Feature extraction converts each protein sequence into numeric "
            "values such as amino-acid frequencies, dipeptide frequencies, "
            "and physicochemical descriptors. These features help the machine "
            "learning model learn patterns from sequence information."
        )

    if "data leakage" in query:
        return (
            "Data leakage occurs when information from the validation or test "
            "split is used during training. This project preserves the "
            "train/validation/test split and avoids mixing them during "
            "model fitting."
        )

    if (
        "why is my prediction probability high" in query
        or "probability" in query
    ):
        return (
            "The probability reflects the model's confidence based on the "
            "extracted features. A high probability means the model sees the "
            "pair as more similar to previously observed positive interactions, "
            "but it is still only a computational prediction."
        )

    if "does yes mean" in query or "can yes prove" in query:
        return (
            "No. A YES prediction means the model thinks the pair is likely "
            "to interact based on feature patterns. It does not prove a "
            "biological interaction and requires experimental validation."
        )

    if "can this system diagnose disease" in query:
        return (
            "No. This system is a computational PPI screening tool. It is not "
            "a diagnostic system for disease and should not be used to "
            "diagnose or treat medical conditions."
        )

    if "recommend antibiotics" in query or "antibiotics" in query:
        return (
            "No. This model is not designed to recommend antibiotics or "
            "medical treatment. It is a student research PPI prediction tool "
            "and not a clinical decision system."
        )

    if "limitations" in query or "what are the limitations" in query:
        return (
            "The main limitations are that this is sequence-based, not "
            "experimental, and the model only learns from the data provided. "
            "It cannot prove biological interaction and should be treated as "
            "a screening aid only."
        )

    if "how can this model be improved" in query:
        return (
            "The model can be improved by adding more informative biological "
            "features, evaluating alternative models, checking for protein "
            "overlap across splits, and validating on external datasets."
        )

    if "amino acid" in query or "sequence validation" in query:
        return (
            "Sequence validation checks that each protein sequence is "
            "non-empty, uses only standard amino-acid letters, and does not "
            "contain numbers or unsupported characters. This prevents invalid "
            "feature extraction."
        )

    if "what is protein sequence" in query:
        return (
            "A protein sequence is the linear order of amino acids in a "
            "protein. It provides the raw biological information that the "
            "model converts into numeric features."
        )

    if "what is interaction" in query or "how is the prediction made" in query:
        return (
            "The model extracts the same 870 numeric features from both "
            "sequences, passes them to a saved classifier, and produces a "
            "probability for the positive class."
        )

    if query in {"hello", "hi", "hey"}:
        return (
            "Hello. I can help answer questions about PPI, the project, "
            "the model, or guide a protein interaction prediction."
        )

    if (
        "predict protein interaction" in query
        or "i want to predict" in query
    ):
        start_prediction_flow()
        return "Sure. Please provide Protein A sequence."

    return (
        "I can help with general PPI questions, the project workflow, the "
        "dataset, feature extraction, model concepts, or a guided protein "
        "interaction prediction. Ask a question or say 'I want to predict "
        "protein interaction'."
    )


def generate_chat_response(message: str) -> str:
    """Route a user message through the knowledge base or guided prediction flow."""

    if not isinstance(message, str):
        return "Please enter a text message."

    if len(message) > MAX_CHAT_MESSAGE_LENGTH:
        return (
            f"Messages must not exceed "
            f"{MAX_CHAT_MESSAGE_LENGTH:,} characters."
        )

    context = st.session_state.chat_context
    started_at = context.get("started_at")

    if (
        context["step"] != "idle"
        and (
            started_at is None
            or time.monotonic() - started_at > CHAT_CONTEXT_TTL_SECONDS
        )
    ):
        reset_chat_context()
        return (
            "That prediction session expired. Start a new prediction "
            "to continue."
        )

    query = message.strip()
    lowered = query.lower()

    if context["step"] == "waiting_for_protein_a":
        try:
            protein_a = validate_sequence(query, "Protein A")
            context["protein_a"] = protein_a
            context["step"] = "waiting_for_protein_b"

            return "Thank you. Now provide Protein B sequence."

        except ValueError as error:
            return str(error)

    if context["step"] == "waiting_for_protein_b":
        try:
            protein_b = validate_sequence(query, "Protein B")
            context["protein_b"] = protein_b
            context["step"] = "waiting_for_confirmation"

            return (
                "I have both sequences. Would you like me to run the "
                "computational prediction?"
            )

        except ValueError as error:
            return str(error)

    if context["step"] == "waiting_for_confirmation":

        if lowered in {
            "yes",
            "yes please",
            "run it",
            "predict",
            "predict now",
        }:
            protein_a = context["protein_a"]
            protein_b = context["protein_b"]

            if protein_a is None or protein_b is None:
                reset_chat_context()
                return (
                    "I am missing one of the sequences. Please provide "
                    "both sequences again."
                )

            if not allow_prediction():
                reset_chat_context()
                return (
                    "Prediction limit reached. Please wait before trying again."
                )

            try:
                prediction, probability = predict_interaction(
                    protein_a,
                    protein_b,
                )

                label = "YES" if prediction == 1 else "NO"

                reset_chat_context()

                return (
                    f"Prediction: {label}\n"
                    f"Model probability: {probability * 100:.2f}%\n\n"
                    "This is a computational prediction and does not prove "
                    "a biological interaction. Experimental/biological "
                    "validation is required."
                )

            except ValueError as error:
                reset_chat_context()
                return str(error)

            except Exception:
                LOGGER.error("Chat prediction failed.")
                reset_chat_context()

                return (
                    "Prediction could not be completed. "
                    "Please try again later."
                )

        if lowered in {"no", "cancel", "stop"}:
            reset_chat_context()
            return (
                "Okay. I am ready when you want to predict a new protein pair."
            )

    if (
        "predict protein interaction" in lowered
        or "i want to predict" in lowered
    ):
        start_prediction_flow()
        return "Sure. Please provide Protein A sequence."

    return knowledge_response(message)


def main() -> None:
    """Render the main PPI prediction and research assistant interface."""

    initialize_chat_state()

    st.title("Protein–Protein Interaction Predictor")

    st.caption(
        "Computational prediction only — biological validation is still required."
    )

    st.markdown("### PPI Prediction System")

    if st.session_state.pop("clear_prediction_inputs", False):
        st.session_state["protein_a_input"] = ""
        st.session_state["protein_b_input"] = ""

    protein_a = st.text_input(
        "Protein A sequence",
        placeholder="e.g. MKT...",
        max_chars=MAX_SEQUENCE_LENGTH,
        key="protein_a_input",
    )

    protein_b = st.text_input(
        "Protein B sequence",
        placeholder="e.g. GQY...",
        max_chars=MAX_SEQUENCE_LENGTH,
        key="protein_b_input",
    )

    if st.button("Predict interaction"):
        st.session_state.pop("last_prediction", None)

        try:
            clean_a = validate_sequence(
                protein_a,
                "Protein A",
            )

            clean_b = validate_sequence(
                protein_b,
                "Protein B",
            )

            if not allow_prediction():
                st.error(
                    "Prediction limit reached. Please wait before trying again."
                )

            else:
                prediction, probability = predict_interaction(
                    clean_a,
                    clean_b,
                )

                st.session_state.last_prediction = (
                    "YES" if prediction == 1 else "NO",
                    probability,
                    clean_a,
                    clean_b,
                )

                st.session_state.clear_prediction_inputs = True
                st.rerun()

        except ValueError as error:
            st.error(f"Input error: {error}")

        except Exception:
            LOGGER.error("Form prediction failed.")
            st.error(
                "Prediction could not be completed. Please try again later."
            )

    if "last_prediction" in st.session_state:
        label, probability, predicted_protein_a, predicted_protein_b = (
            st.session_state.last_prediction
        )

        st.subheader("Prediction result")

        st.write("**Protein A**")
        st.code(predicted_protein_a)

        st.write("**Protein B**")
        st.code(predicted_protein_b)

        st.metric(
            "Predicted interaction",
            label,
        )

        st.metric(
            "Probability",
            f"{probability * 100:.2f}%",
        )

        st.warning(
            "This result is a computational prediction and does not prove "
            "a biological interaction."
        )

    st.button(
        "Clear sequence inputs",
        on_click=clear_prediction_inputs,
    )

    st.markdown("---")

    st.markdown("### PPI Research Assistant")

    st.caption(
        "Ask questions about protein-protein interactions, this project, "
        "machine learning methods, or use the assistant to guide a "
        "PPI prediction."
    )

    if st.button("Clear chat history"):
        reset_chat_context()
        st.session_state.messages = [WELCOME_MESSAGE.copy()]
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Type your question or provide a protein sequence...",
        max_chars=MAX_CHAT_MESSAGE_LENGTH,
    )

    if prompt:
        if len(prompt) > MAX_CHAT_MESSAGE_LENGTH:
            st.error(
                f"Messages must not exceed "
                f"{MAX_CHAT_MESSAGE_LENGTH:,} characters."
            )

        else:
            context_step = st.session_state.chat_context["step"]

            append_chat_message(
                "user",
                safe_history_content(
                    prompt,
                    context_step,
                ),
            )

            assistant_reply = generate_chat_response(prompt)

            append_chat_message(
                "assistant",
                assistant_reply,
            )

            st.rerun()


if __name__ == "__main__":
    main()