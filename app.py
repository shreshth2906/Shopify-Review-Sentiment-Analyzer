import json
import os
import sys
import pandas as pd
import streamlit as st

try:
    import ollama
except ImportError:
    ollama = None

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="E-Commerce Review Insight Engine",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Custom Styling for Clean Business Dashboard
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
        /* Modern Header Banner */
        .hero-container {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            padding: 2rem 2.2rem;
            border-radius: 14px;
            color: #ffffff;
            margin-bottom: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.25);
        }
        .hero-badge {
            display: inline-block;
            background: rgba(16, 185, 129, 0.2);
            color: #34d399;
            border: 1px solid rgba(52, 211, 153, 0.3);
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 0.8rem;
        }
        .hero-title {
            font-size: 2.1rem;
            font-weight: 800;
            color: #f8fafc;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }
        .hero-sub {
            font-size: 1.05rem;
            color: #94a3b8;
            max-width: 850px;
            line-height: 1.5;
            margin-bottom: 0;
        }

        /* Metric & Card styling */
        .insight-card {
            border-radius: 10px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            border-left: 5px solid;
            background-color: #f8fafc;
        }
        .praise-card {
            border-left-color: #10b981;
            background-color: #f0fdf4;
            color: #065f46;
        }
        .complaint-card {
            border-left-color: #ef4444;
            background-color: #fef2f2;
            color: #991b1b;
        }
        .action-card {
            background-color: #eff6ff;
            border-left: 5px solid #3b82f6;
            padding: 1.5rem;
            border-radius: 10px;
            color: #1e3a8a;
        }
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            padding: 0.6rem 1.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Sidebar: Engine Configuration & Diagnostics
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://cdn-icons-png.flaticon.com/512/3081/3081559.png",
        width=60,
    )
    st.title("Settings & Diagnostics")

    model_choice = st.selectbox(
        "Local LLM Model",
        options=["llama3.2", "gemma2", "llama3.1", "mistral", "custom"],
        index=0,
        help="Make sure the selected model is pulled locally via Ollama (e.g., 'ollama pull llama3.2').",
    )

    if model_choice == "custom":
        model_name = st.text_input("Enter Model Tag", value="llama3.2")
    else:
        model_name = model_choice

    sample_size = st.slider(
        "Reviews to Analyze",
        min_value=10,
        max_value=100,
        value=50,
        step=5,
        help="Number of top reviews to extract and batch into the local model prompt.",
    )

    st.markdown("---")
    st.subheader("Ollama Status")

    # Health check for Ollama daemon
    ollama_ready = False
    if ollama is None:
        st.error("❌ `ollama` library not installed.")
    else:
        try:
            available_models = ollama.list()
            ollama_ready = True
            model_list = [m.get("name", m.get("model", "")) for m in available_models.get("models", [])]
            st.success("🟢 Local Ollama daemon active")
            
            # Check if chosen model is installed
            has_model = any(model_name in m for m in model_list)
            if has_model:
                st.caption(f"✓ Model `{model_name}` found locally.")
            else:
                st.warning(f"⚠️ Model `{model_name}` not found in local models. Run `ollama pull {model_name}`.")
        except Exception:
            st.error("🔴 Ollama is not running.")
            st.caption("Start it with `ollama serve` in your terminal.")

    st.markdown("---")
    st.markdown(
        """
        **Data Privacy Guarantee**  
        🛡️ Reviews are analyzed 100% locally on this machine.  
        🚫 Zero customer data transmitted to third-party cloud APIs.  
        💵 Zero token or subscription fees.
        """
    )

# -----------------------------------------------------------------------------
# Main Header
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-container">
        <span class="hero-badge">🔒 100% On-Device AI • Zero Cloud Leakage • Zero API Fees</span>
        <h1 class="hero-title">E-Commerce Review Insight Engine</h1>
        <p class="hero-sub">
            Transform raw Shopify and marketplace customer reviews into clear business intelligence.
            Extract recurring praises, pinpoint friction points, and generate an executive action plan
            using local open-weight LLMs without leaking sensitive customer data.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def detect_review_column(columns: list) -> str:
    """Intelligently detects the most probable review text column."""
    priority_keywords = [
        "review",
        "text",
        "feedback",
        "comment",
        "body",
        "content",
        "description",
        "customer_review",
    ]
    for kw in priority_keywords:
        for col in columns:
            clean_col = str(col).lower().strip()
            if kw == clean_col or kw in clean_col:
                return col
    return columns[0] if columns else ""


def analyze_reviews(reviews_list: list, model: str) -> dict:
    """Sends aggregated review text to Ollama and enforces strict JSON output."""
    if not reviews_list:
        raise ValueError("No reviews found to analyze.")

    # Format numbered review entries
    formatted_reviews = "\n".join(
        [f"[{i+1}] {rev}" for i, rev in enumerate(reviews_list)]
    )

    system_instruction = (
        "You are an expert e-commerce business consultant and retail strategist. "
        "Analyze the provided customer reviews and summarize key insights. "
        "You must respond ONLY with a valid JSON object matching the requested schema exactly. "
        "Do not include preamble, conversational text, or markdown code fences."
    )

    prompt = (
        f"Analyze these {len(reviews_list)} customer reviews for an e-commerce store:\n\n"
        f"{formatted_reviews}\n\n"
        "Return a strictly valid JSON object with EXACTLY three keys:\n"
        '1. "praises": A list of strings highlighting the top features, quality aspects, or services customers love.\n'
        '2. "complaints": A list of strings detailing specific customer pain points, defects, delays, or frustrations.\n'
        '3. "action_plan": A high-impact, prioritized business action plan (in string format) with actionable steps to resolve complaints and scale what works.\n\n'
        "JSON SCHEMA:\n"
        "{\n"
        '  "praises": ["praise item 1", "praise item 2", ...],\n'
        '  "complaints": ["complaint item 1", "complaint item 2", ...],\n'
        '  "action_plan": "1. Operational fix... 2. Marketing leverage..."\n'
        "}"
    )

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        format="json",
        options={"temperature": 0.2},
    )

    raw_content = response["message"]["content"]

    # Defensive parsing for JSON
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError:
        # Strip common markdown fencing if present
        clean_text = raw_content.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.split("\n", 1)[-1]
            if clean_text.endswith("```"):
                clean_text = clean_text.rsplit("\n", 1)[0]
        data = json.loads(clean_text)

    # Validate keys
    for required_key in ["praises", "complaints", "action_plan"]:
        if required_key not in data:
            data[required_key] = [] if required_key != "action_plan" else "No action plan generated."

    return data


# -----------------------------------------------------------------------------
# Data Ingestion Panel
# -----------------------------------------------------------------------------
col_upload, col_demo = st.columns([3, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload Customer Reviews CSV (Shopify export, Judge.me, Loox, Yotpo, etc.)",
        type=["csv"],
        help="Upload any standard CSV file containing customer feedback or reviews.",
    )

with col_demo:
    st.write(" ")
    st.write(" ")
    load_sample = st.button("📂 Load Demo Reviews", use_container_width=True)

df = None
sample_file_path = os.path.join(os.path.dirname(__file__), "sample_reviews.csv")

if load_sample and os.path.exists(sample_file_path):
    df = pd.read_csv(sample_file_path)
    st.session_state["review_df"] = df
    st.toast("Loaded sample Shopify review dataset!", icon="🛍️")
elif uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state["review_df"] = df
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
elif "review_df" in st.session_state:
    df = st.session_state["review_df"]

# -----------------------------------------------------------------------------
# Data Processing & Column Selection
# -----------------------------------------------------------------------------
if df is not None and not df.empty:
    all_columns = df.columns.tolist()
    default_review_col = detect_review_column(all_columns)
    default_idx = all_columns.index(default_review_col) if default_review_col in all_columns else 0

    st.markdown("### 📋 Dataset Overview")

    col_meta1, col_meta2, col_meta3 = st.columns([1, 1, 2])
    with col_meta1:
        st.metric("Total Rows in CSV", len(df))
    with col_meta2:
        st.metric("Review Batch Size", min(sample_size, len(df)))
    with col_meta3:
        selected_col = st.selectbox(
            "Column Containing Review Text",
            options=all_columns,
            index=default_idx,
            help="Select the specific CSV column that holds the customer feedback text.",
        )

    # Preview Dataset
    with st.expander("🔍 View Raw CSV Data (First 5 Rows)", expanded=False):
        st.dataframe(df.head(5), use_container_width=True)

    # Clean & Extract Target Reviews
    clean_series = df[selected_col].dropna().astype(str).str.strip()
    valid_reviews = clean_series[clean_series != ""].tolist()
    analysis_batch = valid_reviews[:sample_size]

    if not analysis_batch:
        st.warning("The selected column contains no readable reviews. Please choose another column.")
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button(
            f"🚀 Run AI Insight Engine on Top {len(analysis_batch)} Reviews",
            type="primary",
            use_container_width=True,
        )

        # -----------------------------------------------------------------------------
        # Analysis Execution & State Persistence
        # -----------------------------------------------------------------------------
        if analyze_btn:
            with st.spinner(f"Running local `{model_name}` inference... Analyzing {len(analysis_batch)} reviews."):
                try:
                    insights = analyze_reviews(analysis_batch, model_name)
                    st.session_state["insights"] = insights
                    st.session_state["analyzed_count"] = len(analysis_batch)
                    st.success("Analysis complete!")
                except Exception as ex:
                    error_msg = str(ex)
                    st.error("### ⚠️ Analysis Execution Failed")
                    if "connection refused" in error_msg.lower() or "connect" in error_msg.lower():
                        st.markdown(
                            """
                            **Could not connect to Ollama.**  
                            1. Ensure Ollama is installed from [ollama.com](https://ollama.com).  
                            2. Start the daemon in your terminal: `ollama serve`.  
                            3. Ensure your desired model is pulled: `ollama pull llama3.2`.
                            """
                        )
                    elif "not found" in error_msg.lower() or "model" in error_msg.lower():
                        st.markdown(
                            f"""
                            **Model not found.**  
                            Please run the following command in your terminal:  
                            ```bash
                            ollama pull {model_name}
                            ```
                            """
                        )
                    else:
                        st.exception(ex)

# -----------------------------------------------------------------------------
# Dashboard Display
# -----------------------------------------------------------------------------
if "insights" in st.session_state and st.session_state["insights"]:
    data = st.session_state["insights"]
    analyzed_count = st.session_state.get("analyzed_count", sample_size)

    praises = data.get("praises", [])
    complaints = data.get("complaints", [])
    action_plan = data.get("action_plan", "")

    st.markdown("---")
    st.markdown("## 📊 Executive Insight Report")
    st.caption(f"Generated via `{model_name}` across {analyzed_count} customer reviews.")

    # Top metric summary cards
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Praises Identified", len(praises))
    with m2:
        st.metric("Friction Points Flagged", len(complaints))
    with m3:
        praise_ratio = (
            round((len(praises) / (len(praises) + len(complaints))) * 100)
            if (len(praises) + len(complaints)) > 0
            else 0
        )
        st.metric("Positive Sentiment Index", f"{praise_ratio}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # Side-by-Side: Praises vs Complaints
    col_praise, col_complaint = st.columns(2)

    with col_praise:
        st.subheader("🟢 Top Customer Praises")
        st.caption("What your customers love and what builds brand loyalty.")
        if praises:
            for item in praises:
                st.success(f"✓ {item}")
        else:
            st.info("No explicit praises noted in this batch.")

    with col_complaint:
        st.subheader("🔴 Critical Friction Points")
        st.caption("Root causes of returns, negative reviews, and lost conversions.")
        if complaints:
            for item in complaints:
                st.error(f"⚠️ {item}")
        else:
            st.info("No critical complaints noted in this batch.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Executive Action Plan
    st.subheader("🎯 Prioritized Business Action Plan")
    st.caption("Recommended tactical and strategic operations for your e-commerce store.")

    st.markdown(
        f"""
        <div class="action-card">
            <h4 style="margin-top:0; color:#1e40af;">💼 Recommended Operational Roadmap</h4>
            <div style="font-size: 1rem; line-height: 1.6; white-space: pre-wrap;">{action_plan}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Report Export
    st.markdown("<br>", unsafe_allow_html=True)
    report_json_str = json.dumps(data, indent=2)
    st.download_button(
        label="📥 Download Insight Report (JSON)",
        data=report_json_str,
        file_name="ecommerce_review_insights.json",
        mime="application/json",
        use_container_width=False,
    )
else:
    if df is None:
        st.info("👆 Upload your store reviews CSV or click 'Load Demo Reviews' above to begin.")
