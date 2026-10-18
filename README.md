# 🛍️ E-Commerce Review Insight Engine
> **A 100% local, privacy-first AI dashboard for Shopify & DTC e-commerce merchants.**  
> Built for the Hacktoberfest Side Hustle Challenge.

---

## 💡 Why This Project?
Most Shopify and DTC store owners receive hundreds of customer reviews every month through apps like Judge.me, Loox, Yotpo, or Shopify Reviews. However:
1. **Cloud AI is expensive:** Sending thousands of reviews to OpenAI or proprietary APIs incurs heavy recurring token costs.
2. **Data privacy risks:** Customer feedback often contains personal details, order IDs, and proprietary product feedback that brands prefer not to leak to third-party cloud AI vendors.
3. **The Solution:** The **E-Commerce Review Insight Engine** uses open-weight LLMs (`llama3.2`, `gemma2`) running **100% locally on your machine via Ollama**. Zero API fees, zero cloud data transfer, and strict structured JSON business intelligence.

---

## ✨ Features
- **Zero API Costs & Total Privacy:** Uses Ollama locally on your hardware.
- **Smart Column Detection:** Automatically identifies review columns (`Review`, `Text`, `Feedback`, `Body`, etc.).
- **Strict JSON Enforcement:** Utilizes Ollama's `format="json"` API parameter to ensure reliable, structured output.
- **Three Core Deliverables:**
  - 🟢 **Customer Praises (`praises`)**: What's driving 5-star ratings and brand loyalty.
  - 🔴 **Customer Complaints (`complaints`)**: Pain points, sizing issues, hardware faults, and shipping delays.
  - 🎯 **Executive Action Plan (`action_plan`)**: Prioritized operational improvements.
- **One-Click Demo Data:** Includes a realistic 30-review sample dataset (`sample_reviews.csv`) for instant testing.
- **Export Ready:** Download the analysis directly as a JSON report for store teams.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
Install [Ollama](https://ollama.com/) on your system (macOS, Windows, or Linux).

### 2. Pull the Local Model
Open your terminal and run:
```bash
ollama pull llama3.2
```
*(Alternative lightweight model: `ollama pull gemma2`)*

Make sure the Ollama daemon is running:
```bash
ollama serve
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 📂 Project Structure
```text
Shopify Review Sentiment Analyzer/
├── app.py                 # Streamlit UI & Ollama orchestration
├── requirements.txt       # Python dependencies (streamlit, pandas, ollama)
├── sample_reviews.csv     # Demo Shopify customer reviews dataset
└── README.md              # Project documentation & instructions
```
