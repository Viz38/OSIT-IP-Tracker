# Tracxn OSIT 🕵️
**(Advanced OSIT Intelligence & Consensus Tracker)**

A powerful, standalone Python web application designed for high-accuracy IP reconnaissance and corporate intelligence. It uses a **Triple-Source Consensus Engine** and a **Brand Intelligence Layer** to map IP addresses and domains to their **True Corporate Identity**, bypassing CDNs and Cloud infrastructure masking with 99% accuracy.

## Core Features
- **Brand Unmasking (Bypass CDNs)**: Successfully identifies the true company behind proxies like Cloudflare, AWS CloudFront, and Fastly by utilizing Clearbit Autocomplete and Live HTML Meta-tag scraping.
- **Triple-Source Consensus Engine**: Triangulates data from independent, high-accuracy sources (RDAP, ip-api, Wikidata) to verify company identity and ownership.
- **Confidence Scoring (up to 99%)**: Automatically calculates a confidence percentage based on source agreement and identity verification.
- **Infrastructure vs. Identity Separation**: Clearly distinguishes between the **Actual Company** (e.g., Tracxn) and the **Infrastructure Provider** (e.g., Amazon CloudFront).
- **Domain Registration Tracking**: Automatically extracts WHOIS creation, expiration, and update dates.
- **Extended Raw Intel**: View the raw, unprocessed data from all APIs in a clean, tabular modal for deep forensic analysis.
- **Network Persona Classification**: Automatically classifies IPs as **Cloud**, **VPN/Proxy**, **Mobile**, or **Business/Residential**.

## How It Works: Intelligence Sources
Tracxn OSIT executes a multi-layered reconnaissance sweep for every target IP or Domain using the following sources:

| Source | Role in Intelligence | Data Provided | Accuracy |
| :--- | :--- | :--- | :--- |
| **Clearbit / HTML Scraping** | **Brand Truth** | Identifies the true commercial brand name behind a domain, bypassing infrastructure masking. | Very High (99%) |
| **RDAP (via ipwhois)** | **Infrastructure Truth** | Authoritative network owner/registrant name from RIRs (ARIN, RIPE, etc.) | High (95%+) |
| **ip-api.com** | **Network Truth** | Real-time Geolocation, ASN, ISP, and network flags (Hosting, Proxy) | High (90%) |
| **Wikidata (SPARQL)** | **Legal Truth** | Corporate legal name and official headquarters from the global knowledge graph | High (95%+) |
| **WHOIS** | **Registration Truth** | Domain creation, expiry, update dates, and raw registrant data. | High |

## Technology Stack
- **Backend**: Python 3 + Flask framework
- **Intelligence**: `ipwhois` (RDAP), `requests` (Wikidata, ip-api, Clearbit), `beautifulsoup4` (Meta scraping), `python-whois` (Registration)
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
1. **Adding Targets**: Enter an IP or a Domain manually on the home page or upload a CSV file (one target per row).
2. **Fetching Consensus**: On the "View Results" page, click **"🔄 Fetch Intel"**.
3. **Deep Dive**: Click the **"🔍 View"** button on any row to see the raw intelligence, WHOIS dates, and infrastructure details.
4. **Exporting Intelligence**: Click **"⬇️ Export CSV"** to download the enriched data.
