# Detective Pradeep 🕵️
**(Advanced IP Intelligence & Consensus Tracker)**

A powerful Python web application for high-accuracy IP reconnaissance. It uses a **Triple-Source Consensus Engine** to map IP addresses to their **Legal Company Identity**, **Corporate Headquarters**, **Network Type**, and **Passive DNS** with over 90% accuracy.

## Features
- **Triple-Source Consensus Engine**: Triangulates data from three independent, high-accuracy sources to verify company identity.
  1. **Infrastructure Truth (RDAP)**: Authoritative network registration data via RIRs (ARIN, RIPE, etc.).
  2. **Network Truth (ip-api.com)**: Real-time ISP, Org, and physical server location mapping.
  3. **Legal Truth (Wikidata/PeeringDB)**: Structured corporate metadata and global headquarters locations.
- **Confidence Scoring**: Automatically calculates a confidence percentage (up to 98%) based on source agreement.
- **Corporate HQ Mapping**: Distinguishes between the **Physical Server Location** and the company's **Legal Headquarters**.
- **Advanced Passive DNS**: Identifies associated domains using historical and current DNS records.
- **Network Type Detection**: Classifies IPs as **Cloud**, **VPN/Proxy**, or **Business/Residential**.
- **Bulk Intelligence**: Upload hundreds of IPs via CSV for automated background processing.
- **No-Limit Architecture**: Optimized for high-volume research using unlimited/high-limit open APIs.

## Technology Stack
- **Backend**: Python 3 + Flask
- **Intelligence**: `ipwhois` (RDAP), `requests` (Wikidata SPARQL, ip-api, PeeringDB)
- **Database**: SQLite
- **UI**: Vanilla HTML5/CSS3/JS (Modern, responsive dashboard)

## Installation & Setup
1. **Navigate to the directory**:
   ```bash
   cd "IP Tracker"
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python3 app.py
   ```
4. **Access the UI**: Open `http://localhost:5001` in your browser.

## Usage
1. **Add IPs**: Enter manual IPs or upload a CSV (first column: IP).
2. **Fetch Consensus**: Click **"🔄 Fetch Intel"**. The engine will query multiple sources and calculate a confidence score.
3. **Review Results**: View the legal name, verified HQ, and network type in the dashboard.
4. **Export**: Download the enriched intelligence as a CSV.
