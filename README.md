# UK Electricity Time-of-Use Tariff Comparator

Interactive Streamlit dashboard for comparing multi-window UK electricity Time-of-Use (ToU) tariffs against a flat-rate baseline using reconciled smart-meter and utility statement data (`Jan–Sep 2026`, `3,902.262 kWh`, `273 days`, `Europe/London`).

## Repository Structure

```text
tariff-comparator/
├── app.py                  # Main Streamlit application entrypoint
├── requirements.txt        # Python package dependencies
├── .streamlit/
│   └── config.toml         # Theme and headless server configuration
├── .gitignore              # Git ignore rules
└── README.md               # Setup and deployment instructions
```

## Deploy on Streamlit Community Cloud (from GitHub)

1. Create a new repository on GitHub (public or private) and push all files in this directory to the root of `main`.
2. Sign in to [share.streamlit.io](https://share.streamlit.io/) with your GitHub account.
3. Click **New app**, select your repository, branch (`main`), and set **Main file path** to `app.py`.
4. Click **Deploy!** — Streamlit Cloud will automatically install `requirements.txt` and launch the app.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
