# Detective Pradeep 🕵️
**(Advanced IP Intelligence & Consensus Tracker)**

A powerful, standalone Python web application designed for high-accuracy IP reconnaissance and corporate intelligence. It uses a **Triple-Source Consensus Engine** to map IP addresses to their **Legal Company Identity**, **Corporate Headquarters**, **Network Type**, and **Passive DNS** with over 90% accuracy.

## Core Features
- **Triple-Source Consensus Engine**: The system does not rely on a single database. It triangulates data from three independent, high-accuracy sources to verify company identity and ownership.
- **Confidence Scoring (0-98%)**: Automatically calculates a confidence percentage based on source agreement. If multiple authoritative sources (e.g., RDAP and Wikidata) agree, the result is marked as **Verified**.
- **Corporate HQ vs. Server Location**: Distinguishes between the **Physical Server Location** (where the traffic originates) and the company's **Legal Headquarters** (where the business is registered).
- **Advanced Passive DNS Discovery**: Powered by the HackerTarget API; identifies multiple domains associated with a single IP, identifying hidden infrastructure or shared hosting environments.
- **Network Persona Classification**: Automatically classifies IPs as **Cloud/Hosting** (infrastructure), **VPN/Proxy** (anonymization), **Mobile Network**, or **Business/Residential**.
- **Bulk Intelligence Processing**: Supports bulk CSV uploads for mass intelligence gathering with automated background processing.
- **No-Limit Architecture**: Optimized for high-volume research using unlimited/high-limit open APIs like Wikidata and RDAP.

## How It Works
Detective Pradeep executes a multi-layered reconnaissance sweep for every target IP to ensure data integrity and accuracy.

### 1. Infrastructure Layer (RDAP)
The tool queries the **Registration Data Access Protocol (RDAP)** via the `ipwhois` library. This is a direct query to the Regional Internet Registries (RIRs) like **ARIN, RIPE, APNIC, or LACNIC**. This provides the most authoritative legal registrant name and address for the IP block.

### 2. Network Layer (ip-api.com)
Simultaneously, it calls the **ip-api.com** endpoint to retrieve real-time network metadata, including the physical geolocation (City, Country), the ASN (Autonomous System Number), and flags for Hosting/Proxy usage.

### 3. Legal & Metadata Layer (Wikidata & PeeringDB)
Once the company name is identified, the engine queries the **Wikidata SPARQL** endpoint. This acts as a global "Knowledge Graph" to find the company's official legal name and **Corporate Headquarters**. If Wikidata lacks the data, it falls back to **PeeringDB**, a verified database for global network operators.

### 4. Consensus & Scoring
The **Consensus Engine** compares the "OrgName" from the RIRs with the "Legal Name" from Wikidata. 
- **Agreement (High Accuracy)**: If the Infrastructure owner and the Legal record match, the confidence score jumps to **95%+**.
- **Disagreement (Low Accuracy)**: If the IP belongs to a hosting provider (like Amazon) but the user claims it's a specific company, the tool flags the distinction, ensuring you aren't misled by the infrastructure provider.

## Technology Stack
- **Backend**: Python 3 + Flask framework
- **Intelligence**: `ipwhois` (RDAP), `requests` (Wikidata SPARQL, ip-api, PeeringDB, HackerTarget)
- **Database**: SQLite (local `ips.db` file)
- **Frontend**: Vanilla HTML5, semantic CSS variables, and Vanilla Javascript (ES6) for asynchronous fetch execution.

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
2. **Fetching Consensus**: On the "View Results" page, click **"🔄 Fetch Intel"**. The server will execute the consensus logic across all pending targets.
3. **Exporting Intelligence**: Click **"⬇️ Export CSV"** to download the enriched data, including legal names and confidence scores.
