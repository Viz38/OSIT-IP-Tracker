# IP Tracker

A standalone, lightweight Python web application to track the IP addresses of companies by resolving their domain names. Includes a sleek, modern UI to manage targets and export results to CSV.

## Features
- **Add Targets:** Easily input a company name and its domain.
- **Fetch IPs:** Resolves all pending domains to their corresponding IP addresses with a single click.
- **Export Data:** Download all tracked domains and IPs into a structured CSV file.
- **Minimalist UI:** Built with HTML/CSS and zero complex frontend frameworks.
- **Local Database:** Uses SQLite so all your targets are saved automatically between restarts.

## Prerequisites
- Python 3.7+

## Installation
1. Clone or download this folder to your machine.
2. Open your terminal and navigate into the folder:
   ```bash
   cd "IP Tracker"
   ```
3. Install the required dependency (Flask):
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
1. **Adding Targets:** On the home page (`/`), fill in the "Company Name" and "Domain" fields, then click "Add Target". 
2. **Fetching IPs:** Navigate to the "View Results" page. Any newly added domains will be marked as *Pending*. Click the blue **"🔄 Fetch IPs"** button in the top right. The server will resolve all pending domains.
3. **Exporting:** On the "View Results" page, click the **"⬇️ Export CSV"** button to download a file containing all your tracking data.
