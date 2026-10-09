import base64
from pathlib import Path

import streamlit as st

from src.feature_extraction import MAX_SEQUENCE_LENGTH


CSS = """
<style>
:root {
    --navy: #102a43;
    --blue: #1769aa;
    --blue-dark: #0d4f88;
    --blue-soft: #eaf4fc;
    --green: #16815a;
    --green-soft: #eaf8f1;
    --red: #c94a46;
    --red-soft: #fff0ef;
    --ink: #24364a;
    --muted: #66758a;
    --border: #dce5ee;
    --surface: #ffffff;
    --background: #f4f7fa;
}
html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
[data-testid="stAppViewContainer"] {
    background: var(--background);
    color: var(--ink);
}
[data-testid="stAppViewContainer"] > .main { max-width: 1540px; margin: 0 auto; }
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container { padding: 1.35rem 1rem 1.5rem; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] { justify-content: flex-start; min-height: 40px; border: 1px solid transparent; border-radius: 8px; background: #ffffff; color: #536579; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover { border-color: #d8e9f6; background: var(--blue-soft); color: var(--blue-dark); }
.brand-row { display: flex; align-items: center; gap: 0.75rem; padding: 0 0.45rem 1.25rem; border-bottom: 1px solid var(--border); }
.brand-mark { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 12px; background: var(--blue-soft); font-size: 1.35rem; box-shadow: inset 0 0 0 1px #d8e9f6; }
.brand-title { color: var(--navy); font-size: 1.18rem; font-weight: 750; margin: 0; }
.brand-subtitle { color: var(--muted); font-size: 0.78rem; margin: 0.15rem 0 0; }
.side-label { color: #8a98a9; font-size: 0.68rem; font-weight: 750; letter-spacing: 0.08em; text-transform: uppercase; margin: 1.15rem 0.5rem 0.45rem; }
.nav-item { display: flex; align-items: center; gap: 0.65rem; color: #536579; padding: 0.65rem 0.75rem; border-radius: 9px; font-size: 0.9rem; font-weight: 600; }
.nav-item.active { color: var(--blue-dark); background: var(--blue-soft); }
.nav-icon { width: 20px; text-align: center; }
.sidebar-note { margin: 1.25rem 0.5rem 0; padding: 0.85rem; border: 1px solid #d9e8f5; border-radius: 10px; background: #f7fbfe; color: var(--muted); font-size: 0.76rem; line-height: 1.45; }
.main-header { margin: 0.1rem 0 1.15rem; }
.eyebrow { display: inline-flex; align-items: center; gap: 0.4rem; color: var(--blue); font-size: 0.72rem; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; }
.eyebrow:before { content: ""; width: 20px; height: 2px; border-radius: 2px; background: var(--blue); }
.main-header h1 { color: var(--navy); font-size: clamp(1.85rem, 3.1vw, 2.75rem); line-height: 1.08; margin: 0.5rem 0 0.58rem; letter-spacing: -0.025em; }
.main-header p { color: var(--muted); font-size: 0.98rem; line-height: 1.55; margin: 0; }
.hero-card, .panel, .result-card, .info-card { border: 1px solid var(--border); border-radius: 14px; background: var(--surface); box-shadow: 0 1px 3px rgba(18, 45, 70, 0.04); }
.hero-card { padding: 1.15rem 1.2rem; margin-bottom: 1rem; }
.workflow { display: flex; align-items: center; flex-wrap: wrap; gap: 0.45rem; margin-top: 0.9rem; }
.workflow-step { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.46rem 0.7rem; border: 1px solid #dbe7f1; border-radius: 8px; background: #f8fbfd; color: #40556c; font-size: 0.78rem; font-weight: 650; }
.workflow-arrow { color: #93a3b3; font-size: 0.82rem; }
.panel { padding: 1.15rem; margin-bottom: 1rem; }
.panel h2, .panel h3 { color: var(--navy); margin: 0; }
.panel h2 { font-size: 1.08rem; }
.panel h3 { font-size: 0.95rem; }
.panel-description { color: var(--muted); font-size: 0.82rem; line-height: 1.45; margin: 0.35rem 0 0.95rem; }
.sequence-label { color: #33495f; font-size: 0.78rem; font-weight: 750; margin: 0 0 0.4rem; }
.sequence-input { margin-bottom: 0.8rem; }
[data-testid="stTextArea"] { border: 1px solid #cdd9e4; border-radius: 10px; background: #fff; box-shadow: 0 1px 2px rgba(18, 45, 70, 0.025); transition: border-color 0.15s ease, box-shadow 0.15s ease; }
[data-testid="stTextArea"]:focus { border-color: var(--blue); box-shadow: 0 0 0 3px rgba(23, 105, 170, 0.10); }
[data-testid="stTextArea"] textarea { border: 0; border-radius: 10px; padding: 0.85rem 0.95rem; background: #ffffff; color: #273b4e; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.84rem; letter-spacing: 0.02em; }
.secondary-button [data-testid="stButton"] > button { border-color: #c9d7e4; color: var(--blue-dark); background: white; border-radius: 8px; }
.action-row { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap; margin-top: 0.25rem; }
.action-hint { color: var(--muted); font-size: 0.72rem; }
.result-card { padding: 1.25rem; margin: 0.25rem 0 1rem; border-width: 1px; overflow: hidden; position: relative; }
.result-card:before { content: ""; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: var(--green); }
.result-card.negative:before { background: var(--red); }
.result-card:after { content: ""; position: absolute; inset: 0; pointer-events: none; border-radius: inherit; box-shadow: inset 0 1px 0 rgba(255,255,255,0.7); }
.result-title-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
.result-kicker { color: var(--muted); font-size: 0.75rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.07em; }
.result-label { margin-top: 0.25rem; color: var(--navy); font-size: 1.65rem; font-weight: 800; }
.result-card.positive .result-label { color: var(--green); }
.result-card.negative .result-label { color: var(--red); }
.result-badge { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.42rem 0.65rem; border-radius: 999px; font-size: 0.75rem; font-weight: 750; }
.positive .result-badge { background: var(--green-soft); color: var(--green); }
.negative .result-badge { background: var(--red-soft); color: var(--red); }
.probability-row { display: flex; align-items: center; gap: 0.8rem; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border); }
.probability-value { color: var(--navy); font-size: 1.65rem; font-weight: 800; }
.probability-caption { color: var(--muted); font-size: 0.78rem; line-height: 1.4; }
.result-explanation { color: #536579; font-size: 0.84rem; line-height: 1.5; margin: 0.75rem 0 0; }
.result-card.positive { border-color: #b8dfcc; background: #fbfefd; }
.result-card.negative { border-color: #f0c5c2; background: #fffdfd; }
.technical-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.65rem; margin-top: 0.85rem; }
.technical-item { padding: 0.7rem; background: #f7f9fb; border-radius: 8px; }
.technical-item span { display: block; color: var(--muted); font-size: 0.68rem; margin-bottom: 0.2rem; text-transform: uppercase; letter-spacing: 0.05em; }
.technical-item strong { color: #30465c; font-size: 0.8rem; }
.metric-label { color: var(--muted); font-size: 0.72rem; font-weight: 650; }
.metric-value { color: var(--navy); font-size: 1.05rem; font-weight: 800; }
.info-card { padding: 1rem; margin-bottom: 0.75rem; }
.info-card h3 { margin-bottom: 0.35rem; color: var(--navy); }
.info-card p, .info-card li { color: var(--muted); font-size: 0.81rem; line-height: 1.45; }
.info-card ul { margin: 0.65rem 0 0; padding-left: 1.15rem; }
.info-card li + li { margin-top: 0.3rem; }
.metric-container { padding: 0.75rem 0.9rem; border: 1px solid var(--border); border-radius: 10px; background: #fbfcfd; }
.assistant-panel { position: static; border: 1px solid var(--border); border-radius: 12px; background: white; overflow: hidden; min-height: 0; margin-bottom: 0.75rem; }
.assistant-header { padding: 1rem 1rem 0.9rem; border-bottom: 1px solid var(--border); background: #f7fafc; }
.assistant-header h2 { color: var(--navy); font-size: 1.05rem; margin: 0; }
.assistant-header p { color: var(--muted); font-size: 0.76rem; line-height: 1.4; margin: 0.3rem 0 0; }
.assistant-art { margin-top: 0.85rem; overflow: hidden; border: 1px solid #dce8f1; border-radius: 9px; background: #f3f8fc; }
.assistant-art img { display: block; width: 100%; height: auto; }
.assistant-art-caption { margin: 0; padding: 0.45rem 0.6rem; color: var(--muted); font-size: 0.66rem; line-height: 1.4; }
.assistant-body { padding: 0.9rem; max-height: calc(100vh - 230px); overflow-y: auto; }
[data-testid="stChatMessageContent"] { border-radius: 10px; padding: 0.15rem 0.55rem; }
[data-testid="stChatMessageContent"] p { color: inherit; font-size: 0.78rem; line-height: 1.48; }
[data-testid="stChatMessageContent"][aria-label="Chat message from user"] { background: var(--blue-soft); color: #244d6c; }
[data-testid="stChatMessageContent"][aria-label="Chat message from assistant"] { background: #f1f4f7; color: #45596c; }
[data-testid="stChatInput"] > div { border: 1px solid var(--border); border-radius: 10px; background: #ffffff; }
[data-testid="stChatInput"]:focus-within > div { border-color: var(--blue); box-shadow: 0 0 0 3px rgba(23, 105, 170, 0.10); }
[data-testid="stChatInputTextArea"] { background: #ffffff; color: var(--ink); }
.chat-author { color: var(--muted); font-size: 0.64rem; font-weight: 750; margin-bottom: 0.25rem; }
.suggestions-label { color: var(--navy); font-size: 0.75rem; font-weight: 750; margin: 0.6rem 0 0.35rem; }
.st-key-assistant_suggestions [data-testid="stBaseButton-secondary"] { min-height: 48px; padding: 0.55rem 0.7rem; border: 1px solid #d0deea; border-radius: 8px; background: #ffffff; color: var(--blue-dark); font-size: 0.78rem; line-height: 1.35; text-align: left; white-space: normal; }
.st-key-assistant_suggestions [data-testid="stBaseButton-secondary"]:hover { border-color: #8fb8d8; background: var(--blue-soft); color: var(--navy); }
.st-key-assistant_suggestions [data-testid="stBaseButton-secondary"]:focus-visible { outline: 3px solid rgba(23, 105, 170, 0.32); outline-offset: 2px; }
.st-key-assistant_suggestions [data-testid="stBaseButton-secondary"]:active { border-color: var(--blue-dark); background: var(--blue-dark); color: #ffffff; transform: translateY(1px); }
.security-note { color: #7b8795; font-size: 0.66rem; line-height: 1.4; margin: 0.55rem 0 0; }
.empty-state { padding: 1.5rem; color: var(--muted); text-align: center; font-size: 0.8rem; }
.status-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: var(--green); margin-right: 0.35rem; }
.page-content { max-width: 1180px; }
[data-testid="stExpander"] { border: 1px solid var(--border); border-radius: 11px; background: white; }
[data-testid="stExpander"] summary { color: var(--navy); font-weight: 700; }
[data-testid="stMain"] [data-testid="stBaseButton-secondary"] { border: 1px solid #c9d7e4; border-radius: 8px; background: #ffffff; color: var(--blue-dark); }
[data-testid="stMain"] [data-testid="stBaseButton-secondary"]:hover { border-color: #a9c8e0; background: var(--blue-soft); color: var(--blue-dark); }
[data-testid="stBaseButton-primary"] { width: 100%; min-height: 44px; background: var(--blue); border: 1px solid var(--blue); border-radius: 9px; color: white; font-weight: 750; box-shadow: 0 2px 6px rgba(23, 105, 170, 0.16); }
[data-testid="stBaseButton-primary"]:hover { background: var(--blue-dark); border-color: var(--blue-dark); }
@media (max-width: 1180px) {
    [data-testid="stAppViewContainer"] > .main { max-width: none; }
    [data-testid="stAppViewContainer"] .stMain > .block-container { padding-left: 1.2rem; padding-right: 1.2rem; }
}
@media (max-width: 900px) {
    .assistant-panel { position: static; min-height: 0; }
    .assistant-body { max-height: 520px; }
    .workflow { align-items: stretch; }
    .workflow-step { flex: 1 1 45%; justify-content: center; }
}
@media (max-width: 560px) {
    .technical-grid { grid-template-columns: 1fr; }
    .result-title-row { flex-direction: column; }
    .workflow-step { width: 100%; flex-basis: 100%; }
    .workflow-arrow { display: none; }
    .result-label { font-size: 1.4rem; }
    .probability-value { font-size: 1.45rem; }
    .probability-row { align-items: flex-start; flex-wrap: wrap; }
}
</style>
"""


def _render_header() -> None:
    st.markdown(
        """
        <div class="main-header">
            <div class="eyebrow">Protein–Protein Interaction Prediction</div>
            <h1>Protein Interaction<br>Prediction Using Machine Learning</h1>
            <p>Predict whether two protein sequences are likely to interact using sequence-derived features and a trained machine-learning classifier.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_workflow() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div class="workflow">
                <span class="workflow-step">1. Protein sequences</span>
                <span class="workflow-arrow">→</span>
                <span class="workflow-step">2. Feature extraction</span>
                <span class="workflow-arrow">→</span>
                <span class="workflow-step">3. Machine learning</span>
                <span class="workflow-arrow">→</span>
                <span class="workflow-step">4. Interaction prediction</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_prediction_inputs(
    protein_a: str,
    protein_b: str,
    validate_sequence,
    allow_prediction,
    predict_interaction,
    LOGGER,
    clear_prediction_inputs,
) -> None:
    st.markdown(
        """
        <div class="panel">
            <h2>Enter Protein Sequences</h2>
            <p class="panel-description">Paste the amino-acid sequences of two proteins using single-letter amino-acid codes.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.pop("clear_prediction_inputs", False):
        st.session_state["protein_a_input"] = ""
        st.session_state["protein_b_input"] = ""

    columns_a, columns_b = st.columns(2)
    with columns_a:
        protein_a = st.text_area(
            "Protein 1 Sequence",
            placeholder="e.g. MKT...",
            height=135,
            max_chars=MAX_SEQUENCE_LENGTH,
            key="protein_a_input",
        )
    with columns_b:
        protein_b = st.text_area(
            "Protein 2 Sequence",
            placeholder="e.g. GQY...",
            height=135,
            max_chars=MAX_SEQUENCE_LENGTH,
            key="protein_b_input",
        )

    if st.button("🔬 Predict Interaction", type="primary", use_container_width=True):
        st.session_state.pop("last_prediction", None)
        try:
            clean_a = validate_sequence(protein_a, "Protein A")
            clean_b = validate_sequence(protein_b, "Protein B")
            if not allow_prediction():
                st.error("Prediction limit reached. Please wait before trying again.")
            else:
                prediction, probability = predict_interaction(clean_a, clean_b)
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
            st.error("Prediction could not be completed. Please try again later.")
    if "last_prediction" in st.session_state:
        _render_prediction_result(st.session_state.last_prediction)

   
    action_left, action_right = st.columns([1, 1])

    with action_left:
        st.markdown(
            "<div class='action-hint'>Use standard single-letter amino-acid codes. Empty or invalid sequences are rejected.</div>",
            unsafe_allow_html=True,
        )

    with action_right:
        example_button, clear_button = st.columns(2)

        with example_button:
            st.button(
                "Use Example Sequences",
                key="load_example_sequences_button",
                use_container_width=True,
                on_click=_load_example_sequences,
            )

        with clear_button:
            st.button(
                "Clear sequence inputs",
                key="clear_sequence_inputs_button",
                use_container_width=True,
                on_click=_clear_prediction_ui,
                args=(clear_prediction_inputs,),
            )

def _load_example_sequences():
    st.session_state["protein_a_input"] = "MKTIIALSYIFCLVFA"
    st.session_state["protein_b_input"] = "GQYIIALSYIFCLVFA"

    # Clear the previous result, but keep the example sequences.
    st.session_state.pop("last_prediction", None)
    st.session_state.pop("clear_prediction_inputs", None)

    # Remove any previous prediction when loading a new example.
    st.session_state.pop("last_prediction", None)
    st.session_state.pop("clear_prediction_inputs", None)


def _clear_prediction_ui(clear_prediction_inputs) -> None:
    """Clear both inputs and the previous result safely."""
    # Preserve the existing application's clear callback.
    clear_prediction_inputs()

    # These updates run in the button callback, before widgets rerender.
    st.session_state["protein_a_input"] = ""
    st.session_state["protein_b_input"] = ""

    # Remove the previous result and any pending clear flag.
    st.session_state.pop("last_prediction", None)
    st.session_state.pop("clear_prediction_inputs", None)


def _render_prediction_result(result) -> None:
    label, probability, predicted_a, predicted_b = result
    is_positive = label == "YES"
    result_class = "positive" if is_positive else "negative"
    result_icon = "✓" if is_positive else "✕"
    result_title = "INTERACTION (YES)" if is_positive else "NON-INTERACTION (NO)"
    explanation = (
        "The model predicts that these protein sequences are likely to interact."
        if is_positive
        else "The model predicts that these protein sequences are unlikely to interact."
    )
    st.markdown(
        f"""
        <div class="result-card {result_class}">
            <div class="result-title-row">
                <div>
                    <div class="result-kicker">Prediction Result</div>
                    <div class="result-label">{result_icon} {result_title}</div>
                </div>
                <div class="result-badge">{result_icon} {label}</div>
            </div>
            <div class="probability-row">
                <div class="probability-value">{probability * 100:.2f}%</div>
                <div class="probability-caption">Prediction Probability<br>Model-generated probability for the positive class</div>
            </div>
            
            <p class="result-explanation">{explanation}</p>
            <p><strong>Protein A sequence:</strong><br>{predicted_a}</p>
            <p><strong>Protein B sequence:</strong><br>{predicted_b}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("View technical details", expanded=False):
        technical_a, technical_b = st.columns(2)
        technical_a.markdown(
            f"- **Model used:** Logistic Regression\n- **Task:** Protein–Protein Interaction Prediction\n- **Prediction class:** {label}\n- **Prediction probability:** {probability * 100:.2f}%"
        )
        technical_b.markdown(
            "- **Features:** 870 sequence-derived pair features\n- **Feature representation:** Pair means and absolute differences\n- **Input:** Two validated protein sequences\n- **Output:** 0 = Non-Interaction; 1 = Interaction"
        )
    st.markdown(
        "<div class='security-note'>Computational result only. It does not prove biological interaction or support medical conclusions.</div>",
        unsafe_allow_html=True,
    )


def _render_dataset_page() -> None:
    st.markdown(
        """
        <div class="main-header">
            <div class="eyebrow">Training data</div>
            <h1>Dataset Information</h1>
            <p>Information from the project’s existing processed dataset and preserved split.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("Dataset", "Human protein FASTA")
    metric_b.metric("Protein-pair records", "163,177")
    metric_c.metric("Features", "870 numerical features")

    st.subheader("Class labels")
    label_a, label_b = st.columns(2)
    label_a.markdown(
        "<div class='info-card'><h3>0 = Non-Interaction</h3><p>The pair is classified as not likely to interact.</p></div>",
        unsafe_allow_html=True,
    )
    label_b.markdown(
        "<div class='info-card'><h3>1 = Interaction</h3><p>The pair is classified as likely to interact.</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="info-card">
            <h3>Existing processed data</h3>
            <p>The project uses the provided human protein FASTA database and positive and negative interaction pair files. The model uses the preserved train/validation/test split.</p>
            <ul>
                <li>Positive interaction pairs: 3 source files</li>
                <li>Negative interaction pairs: 3 source files</li>
                <li>Processed training dataset: 163,177 records</li>
                <li>Class distribution: 81,589 positive and 81,588 negative records</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_model_page() -> None:
    st.markdown(
        """
        <div class="main-header">
            <div class="eyebrow">Model inventory</div>
            <h1>Model Details</h1>
            <p>Verified information about the model used by the current prediction interface.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    detail_a, detail_b = st.columns(2)
    detail_a.markdown(
        """
        <div class="info-card">
            <h3>Model</h3>
            <p><strong>Logistic Regression</strong></p>
            <p>Saved Experiment 3 model artifact.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    detail_b.markdown(
        """
        <div class="info-card">
            <h3>Task</h3>
            <p>Protein–Protein Interaction Prediction</p>
            <p>Binary classification using sequence-derived features.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="info-card">
            <h3>Input and output</h3>
            <ul>
                <li><strong>Input:</strong> Two protein sequences</li>
                <li><strong>Features:</strong> Sequence-derived and physicochemical numerical features</li>
                <li><strong>Output:</strong> 0 = Non-Interaction; 1 = Interaction</li>
                <li><strong>Prediction probability:</strong> Positive-class probability returned by the existing model</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.warning(
        "The saved model is loaded only from the fixed trusted project path after SHA-256 integrity validation."
    )


def _render_about_page() -> None:
    st.markdown(
        """
        <div class="main-header">
            <div class="eyebrow">Research context</div>
            <h1>About Protein AI Lab</h1>
            <p>A student-friendly computational PPI prediction dashboard.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="info-card">
            <h3>Purpose</h3>
            <p>This application predicts whether two protein sequences are likely to interact using machine learning. It is a computational screening and educational tool, not a biological proof.</p>
            <p>The result should be validated through experimental or independently verified biological evidence before drawing conclusions.</p>
        </div>
        <div class="info-card">
            <h3>Responsible use</h3>
            <ul>
                <li>It does not diagnose disease.</li>
                <li>It does not prescribe treatment or recommend antibiotics.</li>
                <li>It does not establish physical interaction by itself.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_assistant(
    initialize_chat_state,
    reset_chat_context,
    append_chat_message,
    safe_history_content,
    generate_chat_response,
    WELCOME_MESSAGE,
    MAX_CHAT_MESSAGE_LENGTH,
) -> None:
    illustration_path = Path(__file__).parent / "assets" / "ppi_interaction_schematic.svg"
    illustration_data = base64.b64encode(illustration_path.read_bytes()).decode("ascii")
    st.markdown(
        f"""
        <div class="assistant-panel">
            <div class="assistant-header">
                <h2>💬 PPI Assistant</h2>
                <p>Ask about PPI, the dataset, prediction, or the project.</p>
                <figure class="assistant-art">
                    <img src="data:image/svg+xml;base64,{illustration_data}" alt="Illustration of two stylized protein ribbons meeting at an interaction interface; not a prediction of submitted proteins.">
                    <figcaption class="assistant-art-caption">Conceptual illustration only; not generated from your sequences.</figcaption>
                </figure>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container():
        st.markdown("<div class='assistant-body'>", unsafe_allow_html=True)
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        manual_prompt = st.chat_input(
            "Ask about protein interactions...",
            max_chars=MAX_CHAT_MESSAGE_LENGTH,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    suggested_questions = (
        "What is protein-protein interaction?",
        "How does my prediction model work?",
        "What do YES and NO mean?",
        "Which dataset does this project use?",
        "What features are extracted from protein sequences?",
        "What are the limitations of this model?",
    )
    selected_suggestion = None
    with st.container(key="assistant_suggestions"):
        st.markdown(
            "<p class='suggestions-label'>Suggested questions</p>",
            unsafe_allow_html=True,
        )
        suggestion_columns = st.columns(2, gap="small")
        for index, question in enumerate(suggested_questions):
            with suggestion_columns[index % len(suggestion_columns)]:
                if st.button(
                    question,
                    key=f"assistant_suggestion_{index}",
                    use_container_width=True,
                ):
                    selected_suggestion = question

    prompt = selected_suggestion if selected_suggestion is not None else manual_prompt
    if prompt:
        if len(prompt) > MAX_CHAT_MESSAGE_LENGTH:
            st.error(
                f"Messages must not exceed {MAX_CHAT_MESSAGE_LENGTH:,} characters."
            )
        else:
            context_step = st.session_state.chat_context["step"]
            append_chat_message(
                "user",
                safe_history_content(prompt, context_step),
            )
            assistant_reply = generate_chat_response(prompt)
            append_chat_message("assistant", assistant_reply)
            st.rerun()
    st.markdown(
        "<p class='security-note'>Secure session limits and redacted sequence history are applied.</p>",
        unsafe_allow_html=True,
    )
    if st.button("Clear chat history", use_container_width=True):
        reset_chat_context()
        st.session_state.messages = [WELCOME_MESSAGE.copy()]
        st.rerun()


def render_dashboard(
    initialize_chat_state,
    reset_chat_context,
    append_chat_message,
    safe_history_content,
    generate_chat_response,
    validate_sequence,
    allow_prediction,
    predict_interaction,
    clear_prediction_inputs,
    LOGGER,
    WELCOME_MESSAGE,
    MAX_CHAT_MESSAGE_LENGTH,
) -> None:
    st.set_page_config(page_title="Protein AI Lab", page_icon="🧬", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    initialize_chat_state()

    with st.sidebar:
        st.markdown(
            """
            <div class="brand-row">
                <div class="brand-mark">🧬</div>
                <div>
                    <p class="brand-title">Protein AI Lab</p>
                    <p class="brand-subtitle">Computational biology dashboard</p>
                </div>
            </div>
            <div class="side-label">Workspace</div>
            """,
            unsafe_allow_html=True,
        )
        nav_items = {
            "home": ("🏠", "Home"),
            "predict": ("🔬", "Predict Interaction"),
            "dataset": ("🗄", "Dataset Info"),
            "model": ("⚙", "Model Details"),
            "about": ("ℹ️", "About"),
        }
        current_page = st.session_state.get("current_page", "home")
        for key, (icon, label) in nav_items.items():
            if st.button(icon + " " + label, key=key, use_container_width=True):
                st.session_state.current_page = key
                st.rerun()
        st.markdown(
            "<div class='sidebar-note'>Prediction inputs are validated and limited before feature extraction or model loading.</div>",
            unsafe_allow_html=True,
        )

    main_column, assistant_column = st.columns(
        [2, 1],
        gap="large",
        vertical_alignment="top",
    )
    with main_column:
        current_page = st.session_state.get("current_page", "home")
        if current_page == "home":
            header_column, header_actions = st.columns([1, 0.22])
            with header_column:
                _render_header()
            with header_actions:
                if st.button("About", use_container_width=True):
                    st.session_state.current_page = "about"
                    st.rerun()
                if st.button("Help", use_container_width=True):
                    st.session_state.current_page = "about"
                    st.rerun()
            _render_workflow()
            _render_prediction_inputs(
                "",
                "",
                validate_sequence,
                allow_prediction,
                predict_interaction,
                LOGGER,
                clear_prediction_inputs,
            )
            st.markdown("---")
            st.subheader("How the prediction works")
            st.info(
                "The existing validation, feature extraction, trusted model loading, integrity check, and prediction calculation are reused unchanged."
            )
        elif current_page == "predict":
            st.markdown(
                """
                <div class="main-header">
                    <div class="eyebrow">Prediction workspace</div>
                    <h1>Protein–Protein Interaction Prediction</h1>
                    <p>Enter two validated protein sequences and run the existing trained model.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            _render_workflow()
            _render_prediction_inputs(
                "",
                "",
                validate_sequence,
                allow_prediction,
                predict_interaction,
                LOGGER,
                clear_prediction_inputs,
            )
        elif current_page == "dataset":
            _render_dataset_page()
        elif current_page == "model":
            _render_model_page()
        elif current_page == "about":
            _render_about_page()

    with assistant_column:
        _render_assistant(
            initialize_chat_state,
            reset_chat_context,
            append_chat_message,
            safe_history_content,
            generate_chat_response,
            WELCOME_MESSAGE,
            MAX_CHAT_MESSAGE_LENGTH,
        )
