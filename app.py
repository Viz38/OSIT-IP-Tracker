from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import sqlite3
import socket
import os
import requests
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_tracker_key_for_flash_messages'
DB_PATH = 'ips.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            ip_address TEXT NOT NULL UNIQUE,
            location TEXT,
            provider TEXT,
            domains_associated TEXT,
            ip_type TEXT,
            last_fetched TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def check_target(ip):
    result = {
        "company": "Unknown",
        "location": "N/A",
        "provider": "N/A",
        "domains_associated": "N/A",
        "ip_type": "Business/Static",
        "last_fetched": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 1. Reverse IP Lookup (Passive DNS) - Much more accurate than basic PTR
    try:
        # Using HackerTarget's free API for Reverse IP
        # Note: This is rate-limited but provides a list of domains
        ht_req = requests.get(f"https://api.hackertarget.com/reverseiplookup/?q={ip}", timeout=5)
        if ht_req.status_code == 200 and "error" not in ht_req.text.lower() and "no records" not in ht_req.text.lower():
            domains = ht_req.text.strip().split("\n")
            if len(domains) > 10:
                result["domains_associated"] = f"{', '.join(domains[:10])} (+{len(domains)-10} more)"
            else:
                result["domains_associated"] = ", ".join(domains)
        else:
            # Fallback to basic PTR
            try:
                host, alias, _ = socket.gethostbyaddr(ip)
                result["domains_associated"] = ", ".join([host] + alias)
            except:
                result["domains_associated"] = "No associated domains found"
    except Exception as e:
        result["domains_associated"] = "Lookup failed"
        
    # 2. Get Geolocation and Provider/Company
    try:
        geo_req = requests.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,city,org,as,isp,mobile,proxy,hosting", timeout=3)
        if geo_req.status_code == 200:
            geo_data = geo_req.json()
            if geo_data.get("status") == "success":
                country = geo_data.get("country", "Unknown")
                city = geo_data.get("city", "Unknown")
                result["location"] = f"{city}, {country}"
                
                # Company identification
                result["company"] = geo_data.get("org") or geo_data.get("isp", "Unknown")
                result["provider"] = geo_data.get("as") or "Unknown"
                
                # Determine IP Type
                if geo_data.get("hosting"):
                    result["ip_type"] = "Cloud/Hosting"
                elif geo_data.get("proxy"):
                    result["ip_type"] = "VPN/Proxy"
                elif geo_data.get("mobile"):
                    result["ip_type"] = "Mobile Network"
                else:
                    result["ip_type"] = "Business/Residential"
                    
    except:
        pass
        
    return result

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        ip_address = request.form['ip_address'].strip()

        if not ip_address:
            flash('IP Address is required!')
        else:
            conn = get_db_connection()
            try:
                conn.execute('INSERT INTO targets (company, ip_address, location, provider, domains_associated, ip_type, last_fetched) VALUES (?, ?, ?, ?, ?, ?, ?)',
                             ("Pending", ip_address, "Pending", "Pending", "Pending Fetch", "Pending", "Never"))
                conn.commit()
                flash('IP successfully added!')
                return redirect(url_for('results'))
            except sqlite3.IntegrityError:
                flash('This IP address already exists in the tracker.')
            finally:
                conn.close()

    return render_template('index.html')

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'csv_file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
        
    if file and file.filename.endswith('.csv'):
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        
        conn = get_db_connection()
        added_count = 0
        duplicate_count = 0
        
        for row in csv_input:
            if not row: continue
            ip_address = row[0].strip()
            if ip_address.lower() in ['ip', 'ip_address', 'address'] or not ip_address:
                continue

            try:
                conn.execute('INSERT INTO targets (company, ip_address, location, provider, domains_associated, ip_type, last_fetched) VALUES (?, ?, ?, ?, ?, ?, ?)',
                             ("Pending", ip_address, "Pending", "Pending", "Pending Fetch", "Pending", "Never"))
                added_count += 1
            except sqlite3.IntegrityError:
                duplicate_count += 1
                        
        conn.commit()
        conn.close()
        
        flash(f'Successfully added {added_count} IPs from CSV!')
        return redirect(url_for('results'))
    else:
        flash('Invalid file format. Please upload a .csv file')
        return redirect(url_for('index'))

@app.route('/results')
def results():
    conn = get_db_connection()
    targets = conn.execute('SELECT * FROM targets ORDER BY last_fetched DESC').fetchall()
    conn.close()
    return render_template('results.html', targets=targets)

@app.route('/fetch', methods=['POST'])
def fetch_ips():
    conn = get_db_connection()
    targets = conn.execute('SELECT id, ip_address FROM targets').fetchall()
    
    updated_count = 0
    for target in targets:
        res = check_target(target['ip_address'])
        conn.execute('''
            UPDATE targets 
            SET company = ?, location = ?, provider = ?, domains_associated = ?, ip_type = ?, last_fetched = ? 
            WHERE id = ?''', 
            (res['company'], res['location'], res['provider'], res['domains_associated'], res['ip_type'], res['last_fetched'], target['id'])
        )
        updated_count += 1
        
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": f"Successfully updated {updated_count} records."})

@app.route('/delete/<int:id>', methods=['POST'])
def delete_target(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM targets WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Target deleted."})

@app.route('/export')
def export_csv():
    conn = get_db_connection()
    targets = conn.execute('SELECT * FROM targets ORDER BY last_fetched DESC').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Company', 'IP Address', 'Type', 'Domains', 'Location', 'AS/Provider', 'Last Fetched'])
    
    for row in targets:
        writer.writerow([row['company'], row['ip_address'], row['ip_type'], row['domains_associated'], row['location'], row['provider'], row['last_fetched']])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=detective_pradeep_intel_results.csv"}
    )

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
