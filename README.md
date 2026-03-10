# Detective Pradeep 🕵️
**(Formerly OSIT-IP-Tracker)**

A standalone, lightweight Python web application to track the intelligence of companies by resolving their domain names. Includes a sleek, modern UI to manage targets, fetch advanced intel, and export results to CSV.

## Features
- **Add Targets:** Easily input a company name and its domain manually.
- **Bulk Upload:** Upload tens or hundreds of targets simultaneously via a simple CSV file structure.
- **Fetch Intel:** Resolves all pending domains to their corresponding IP addresses automatically.
- **Geolocation & Infrastructure Tracking:** Powered by `ip-api.com`; immediately find out where the server is located and who owns it (e.g., AWS, Cloudflare, etc.).
- **Live HTTP Status:** Instantly see if a website is online or not by pinging its live HTTP status code (200, 403, 500, Offline, etc) displayed via colored badges.
- **Export Data:** Download all tracked domains, statuses, regions, and IPs into a structured CSV file.
- **Minimalist UI:** Built with HTML/CSS and zero complex frontend frameworks.
- **Local Database:** Uses SQLite so all your targets are saved automatically between restarts.

## How It Works
Detective Pradeep is designed as a standalone, lightweight OSINT intelligence tool. When a user requests data via the "Fetch Data" button, the Flask backend executes a synchronous sweep across the added domains.

### Data Sources
1. **IP Resolution:** It leverages Python's native `socket.gethostbyname()` module to parse the provided HTTP Domain and query the local system's DNS to retrieve the IPv4 Address.
2. **Geolocation & Provider Specs:** The resolved IP is passed in a `GET` request to **ip-api.com** (a free IP geolocation API) to capture `City`, `Country`, and the associated Autonomous System (AS) Internet Service Provider (`org`/`isp`).
3. **HTTP Status Context:** The application uses the `requests` library to actively probe the live HTTP/HTTPS status code. It handles timeouts, connection errors, and redirects gracefully to determine whether the remote host is alive.

### Technology Stack
- **Backend:** Python 3 + Flask framework
- **Database:** SQLite (local `ips.db` file)
- **Frontend:** Vanilla HTML5, semantic CSS variables, and Vanilla Javascript (ES6) for asynchronous fetch execution.
- **Styling:** Custom "Detective Pradeep" CSS theme for a sleek, modern, and highly-responsive analytical table.

## Prerequisites
- Python 3.7+

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
   python app.py
   ```
2. By default, the app runs on port `5001`. Open your web browser and navigate to:
   ```
   http://localhost:5001
   ```

## Usage Instructions
1. **Adding Targets:** On the home page (`/`), fill in the "Company Name" and "Domain" fields, then click "Add Target". Alternatively, drop a CSV into the bulk uploader form.
2. **Fetching IPs:** Navigate to the "View Results" page. Any newly added domains will be marked as *Pending*. Click the blue **"🔄 Fetch Data"** button in the top right. The server will resolve all pending domains, pull geolocations, and verify the websites are alive.
3. **Exporting:** On the "View Results" page, click the **"⬇️ Export CSV"** button to download a file containing all your tracking data.
