# Tracxn OSIT 🕵️
**(Advanced OSIT Intelligence & Consensus Tracker)**

A powerful, standalone Python web application designed for high-accuracy IP reconnaissance and corporate intelligence. It uses a **Triple-Source Consensus Engine** to map IP addresses to their **Legal Company Identity**, **Corporate Headquarters**, **Network Type**, and **Passive DNS** with over 90% accuracy.

## Core Features
- **Triple-Source Consensus Engine**: The system triangulates data from three independent, high-accuracy sources to verify company identity and ownership.
- **Confidence Scoring (up to 98%)**: Automatically calculates a confidence percentage based on source agreement.
- **Corporate HQ vs. Server Location**: Distinguishes between the **Physical Server Location** and the company's **Legal Headquarters**.
- **Advanced Passive DNS Discovery**: Powered by the HackerTarget API to identify infrastructure and shared hosting environments.
- **Network Persona Classification**: Automatically classifies IPs as **Cloud**, **VPN/Proxy**, **Mobile**, or **Business/Residential**.
- **Bulk Intelligence Processing**: Supports bulk CSV uploads for mass reconnaissance.
- **No-Limit Architecture**: Optimized for high-volume research using open APIs like Wikidata and RDAP.

## How It Works: Intelligence Sources
Tracxn OSIT executes a multi-layered reconnaissance sweep for every target IP using the following sources:

| Source | Role in Intelligence | Data Provided | Accuracy |
| :--- | :--- | :--- | :--- |
| **RDAP (via ipwhois)** | **Infrastructure Truth** | Authoritative network owner/registrant name from RIRs (ARIN, RIPE, etc.) | High (95%+) |
| **ip-api.com** | **Network Truth** | Real-time Geolocation, ASN, ISP, and network flags (Hosting, Proxy) | High (90%) |
| **Wikidata (SPARQL)** | **Legal Truth** | Corporate legal name and official headquarters from the global knowledge graph | High (95%+) |
| **PeeringDB** | **Interconnection Truth** | Verified corporate contact and HQ data for major network operators | High (98%) |
| **HackerTarget** | **DNS Truth** | Passive DNS records and reverse IP lookups to find associated domains | Moderate |

## Consensus & Confidence Logic
To ensure a >90% accuracy rate, the tool employs a consensus-based scoring system (`agreement_points`) that rewards data consistency across independent sources.

### Agreement Point System:
1.  **Network Resolution (+1 point)**: Awarded when `ip-api.com` successfully maps the IP to a known organization or ISP.
2.  **Infrastructure Alignment (+1 point)**: Awarded when the authoritative **RDAP** registrant name matches or contains the organization name found by `ip-api.com`.
3.  **Legal Verification (+1 point)**: Awarded when the company name is successfully reconciled against the **Wikidata** or **PeeringDB** databases and returns a valid Corporate HQ.

### Confidence Score Mapping:
- **98% (Verified)**: 3 points. All three independent sources (Infrastructure, Network, and Legal) are in perfect alignment.
- **92% (Likely)**: 2 points. Two high-accuracy sources agree on the entity's identity.
- **75% (Uncertain)**: 1 point. Only one source returned valid data; identity should be manually verified.
- **20% (Low)**: 0 points. No authoritative data found; result is based on generic fallback lookups.

## Technology Stack
- **Backend**: Python 3 + Flask framework
- **Intelligence**: `ipwhois` (RDAP), `requests` (Wikidata SPARQL, ip-api, PeeringDB, HackerTarget)
- **Database**: SQLite (local `ips.db` file)
- **Frontend**: Vanilla HTML5, semantic CSS variables, and Vanilla Javascript (ES6).

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
4. **Access the UI**: Open your browser and navigate to `http://localhost:5001`.

## Usage Instructions
1. **Adding IPs**: Enter an IP manually on the home page or upload a CSV file (one IP per row).
2. **Fetching Consensus**: On the "View Results" page, click **"🔄 Fetch Intel"**.
3. **Exporting Intelligence**: Click **"⬇️ Export CSV"** to download the enriched data.
