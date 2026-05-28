# 🚇 Ahmedabad Metro Parking Management System

A full-stack web application for managing open parking lots at Ahmedabad Metro stations.  
Built with **Python · Streamlit · Pandas · Plotly** — deployable to Streamlit Cloud in one click.

---

## 🌐 Live Demo

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

> Deploy your own: see [Deployment](#deployment) below.

---

## 🔍 The Real Problem

Gujarat Metro Rail Corporation (GMRC) currently has organised parking at only ~4 of 54 Ahmedabad metro stations.
Existing open lots have zero record-keeping, no fee system, and no slot tracking — leading to chaos, revenue loss, and commuter frustration.

This app provides the **complete software layer** for any metro station parking lot.

---

## ✨ Features

| Page | What it does |
|---|---|
| 🏠 Dashboard | Live KPIs: revenue, occupancy, overstay alerts, currently parked |
| 🚗 Park Vehicle | Register entry, validate number plate (regex), auto-assign slot |
| 🚪 Vehicle Exit | Compute fee, collect payment, free the slot |
| 🗺️ Slot Map | Visual grid of all slots — free/occupied in real time |
| 🔍 Search Vehicle | Find any vehicle by plate — current status + full history |
| 📊 Analytics | Revenue trends, hourly traffic, duration histograms (Plotly) |
| 📋 Session History | Filterable table of all sessions with CSV export |

---

## 🛠 Tech Stack

| Library | Used For |
|---|---|
| `streamlit` | Web UI, routing, session state |
| `pandas` | CSV storage, data manipulation, filtering |
| `plotly` | All charts — donuts, line, bar, histogram, heatmap |
| Core Python | OOP models, file handling, generators, regex, exceptions |

---

## 📁 Project Structure

```
metro_parking_web/
│
├── app.py                  ← Streamlit entry point (run this)
├── requirements.txt        ← pip dependencies for Streamlit Cloud
├── .gitignore
│
├── core/                   ← Pure Python business logic
│   ├── __init__.py
│   ├── models.py           ← Vehicle, ParkingSlot, ParkingLot (OOP)
│   ├── storage.py          ← Pandas CSV read/write
│   └── charts.py           ← All Plotly chart builders
│
├── data/
│   ├── .gitkeep            ← Keeps folder in git
│   └── sessions.csv        ← Auto-created on first exit (gitignored)
│
└── .streamlit/
    └── config.toml         ← Theme + layout config
```

---

## 🚀 Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/metro-parking.git
cd metro-parking

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

Open your browser at `http://localhost:8501`  
Default operator PIN: **1234**

---

## ☁️ Deployment

### Streamlit Community Cloud (free)

1. Push this repo to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select your repo → set **Main file path** to `app.py`
4. Click **Deploy** — done in ~2 minutes!

> **Note:** Streamlit Cloud's filesystem resets on redeployment.  
> For persistent data across restarts, connect a database (e.g. Supabase) or use `st.secrets`.

---

## ⚙️ Configuration

Edit the top of `app.py` to customise:

```python
STATION_NAME       = "Kalupur Metro Station"
TWO_WHEELER_SLOTS  = 20
FOUR_WHEELER_SLOTS = 10
OPERATOR_PIN       = "1234"
```

Rates are in `core/models.py`:
```python
RATE_TWO_WHEELER  = 10   # ₹ per hour
RATE_FOUR_WHEELER = 20   # ₹ per hour
OVERSTAY_HOURS    = 12
```

---

## 🧠 Python Concepts Demonstrated

This project was built as a Core Python learning project covering:

- **OOP** — `Vehicle`, `ParkingSlot`, `ParkingLot` classes with encapsulation
- **Regular Expressions** — Number plate validation (`GJ01AB1234` format)
- **File Handling** — Pandas CSV persistence with auto-creation
- **Generators** — `overstay_alerts()` and `revenue_generator()`
- **Exception Handling** — All user inputs wrapped with try/except
- **Dictionaries** — O(1) slot lookup
- **Iterators** — Slot map, occupied slot scanning
- **Modules & Packages** — Clean separation: `core/models`, `core/storage`, `core/charts`

---

## 📈 Possible Extensions

- [ ] Multi-station support (one lot per station)
- [ ] Monthly revenue reports
- [ ] EV (electric vehicle) slots with different rates
- [ ] SMS/WhatsApp receipt via Twilio
- [ ] Supabase/PostgreSQL for persistent cloud storage
- [ ] QR code ticket generation

---

## 📄 License

MIT — free to use, modify, and deploy.

---

*Inspired by the real parking problem at Ahmedabad Metro stations — documented by GMRC's 2025 request to AMC for additional parking plots.*
