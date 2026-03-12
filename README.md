# Detective Pradeep 🕵️
**(Advanced IP Intelligence Tracker)**

A powerful, standalone Python web application designed for IP intelligence and reconnaissance. Input a list of IP addresses to automatically map their **Company/Organization**, **Geolocation**, **Network Type (Cloud, VPN, Mobile)**, and **Passive DNS (Associated Domains)**.

## Features
- **Add IP Targets:** Input an IP address manually. Company information is fetched automatically.
- **Bulk IP Upload:** Upload a list of IP addresses via CSV for mass intelligence gathering.
- **Advanced Intelligence (Passive DNS):** Powered by the HackerTarget API; identifies multiple domains associated with a single IP, mimicking professional OSINT tools like Recon-ng and Amass.
- **Network Type Detection:** Automatically classifies IPs as **Cloud/Hosting**, **VPN/Proxy**, **Mobile Network**, or **Business/Residential**.
- **Geolocation & Infrastructure Tracking:** Powered by `ip-api.com`; find the city, country, and AS (Autonomous System) owner for every target.
- **Export Intelligence:** Download all enriched results into a structured CSV file for reporting.
- **Minimalist UI:** Sleek, modern dashboard built with HTML/CSS and vanilla JavaScript.
- **Local Database:** Uses SQLite to store your intelligence data locally and persistently.

## How It Works
Detective Pradeep is designed for security researchers and OSINT analysts. When you click "Fetch Intel", the Flask backend performs a multi-layered reconnaissance sweep:

### Intelligence Layers
1. **Company & Org Mapping:** Uses the `org` and `isp` fields from the IP Geolocation API to identify the legal entity owning the IP space.
2. **Passive DNS Lookup:** Instead of basic PTR lookups, the tool queries a Passive DNS database to find all historical and current domain mappings for the IP.
3. **Network Classification:** Analyzes the IP's attributes (hosting, proxy, mobile flags) to determine its "Persona" (e.g., distinguishing between a user's home connection and a cloud server).
4. **Geolocation:** Provides precise city and country mapping.

### Technology Stack
- **Backend:** Python 3 + Flask framework
- **Database:** SQLite (local `ips.db` file)
- **Frontend:** Vanilla HTML5, semantic CSS variables, and Vanilla Javascript (ES6).
- **Styling:** Custom "Detective Pradeep" theme optimized for analytical data display.

## Prerequisites
- Python 3.7+
- Internet connection (for API-based intelligence)

## Installation
1. Clone or download this folder to your machine.
2. Open your terminal and navigate into the folder:
   ```bash
   cd "IP Tracker"
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application
1. Start the Flask server:
   ```bash
   python3 app.py
   ```
2. By default, the app runs on port `5001`. Open your web browser and navigate to:
   ```
   http://localhost:5001
   ```

## Usage Instructions
1. **Adding IPs:** On the home page (`/`), enter an IP address. Company and domain info will be fetched later.
2. **Bulk Upload:** Upload a CSV with one IP per row (headers like "IP" are automatically ignored).
3. **Fetching Intel:** On the "View Results" page, click the blue **"🔄 Fetch Intel"** button. The server will populate all metadata.
4. **Exporting:** Click **"⬇️ Export CSV"** to save your research.
