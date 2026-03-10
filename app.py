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
            company TEXT NOT NULL,
            domain TEXT NOT NULL UNIQUE,
            ip_address TEXT,
            location TEXT,
            provider TEXT,
            status_code TEXT,
            last_fetched TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def check_target(domain):
    result = {
        "ip_address": "Resolution Failed",
        "location": "N/A",
        "provider": "N/A",
        "status_code": "N/A",
        "last_fetched": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 1. Resolve IP
    try:
        ip = socket.gethostbyname(domain)
        result["ip_address"] = ip
        
        # 2. Get Geolocation and Provider
        try:
            geo_req = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
            if geo_req.status_code == 200:
                geo_data = geo_req.json()
                if geo_data.get("status") == "success":
                    country = geo_data.get("country", "Unknown")
                    city = geo_data.get("city", "Unknown")
                    result["location"] = f"{city}, {country}"
                    result["provider"] = geo_data.get("org") or geo_data.get("isp", "Unknown")
        except:
            pass
            
    except Exception:
        pass
        
    # 3. Check HTTP Status
    try:
        http_req = requests.get(f"http://{domain}", timeout=3, allow_redirects=True)
        result["status_code"] = str(http_req.status_code)
    except requests.exceptions.Timeout:
        result["status_code"] = "Timeout"
    except requests.exceptions.ConnectionError:
        try:
            https_req = requests.get(f"https://{domain}", timeout=3, allow_redirects=True)
            result["status_code"] = str(https_req.status_code)
        except:
            result["status_code"] = "Offline"
    except Exception:
        result["status_code"] = "Error"
        
    return result

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        company = request.form['company'].strip()
        domain = request.form['domain'].strip()

        if not company or not domain:
            flash('Company and Domain are required!')
        else:
            conn = get_db_connection()
            try:
                conn.execute('INSERT INTO targets (company, domain, ip_address, location, provider, status_code, last_fetched) VALUES (?, ?, ?, ?, ?, ?, ?)',
                             (company, domain, "Pending Fetch", "Pending", "Pending", "Pending", "Never"))
                conn.commit()
                flash('Target successfully added!')
                return redirect(url_for('results'))
            except sqlite3.IntegrityError:
                flash('This domain already exists in the tracker.')
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
        
        # Skip header if present
        header_skipped = False
        
        conn = get_db_connection()
        added_count = 0
        duplicate_count = 0
        
        for row in csv_input:
            if not header_skipped and row and row[0].lower() in ['company', 'name']:
                header_skipped = True
                continue
                
            if len(row) >= 2:
                company = row[0].strip()
                domain = row[1].strip()
                if company and domain:
                    try:
                        conn.execute('INSERT INTO targets (company, domain, ip_address, location, provider, status_code, last_fetched) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                     (company, domain, "Pending Fetch", "Pending", "Pending", "Pending", "Never"))
                        added_count += 1
                    except sqlite3.IntegrityError:
                        duplicate_count += 1
                        
        conn.commit()
        conn.close()
        
        flash(f'Successfully added {added_count} targets from CSV! ({duplicate_count} duplicates skipped)')
        return redirect(url_for('results'))
    else:
        flash('Invalid file format. Please upload a .csv file')
        return redirect(url_for('index'))

@app.route('/results')
def results():
    conn = get_db_connection()
    targets = conn.execute('SELECT * FROM targets ORDER BY company ASC').fetchall()
    conn.close()
    return render_template('results.html', targets=targets)

@app.route('/fetch', methods=['POST'])
def fetch_ips():
    conn = get_db_connection()
    targets = conn.execute('SELECT id, domain FROM targets').fetchall()
    
    updated_count = 0
    for target in targets:
        res = check_target(target['domain'])
        conn.execute('''
            UPDATE targets 
            SET ip_address = ?, location = ?, provider = ?, status_code = ?, last_fetched = ? 
            WHERE id = ?''', 
            (res['ip_address'], res['location'], res['provider'], res['status_code'], res['last_fetched'], target['id'])
        )
        updated_count += 1
        
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": f"Successfully updated {updated_count} records."})

@app.route('/export')
def export_csv():
    conn = get_db_connection()
    targets = conn.execute('SELECT * FROM targets ORDER BY company ASC').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Company', 'Domain', 'IP Address', 'Location', 'Provider', 'HTTP Status', 'Last Fetched'])
    
    for row in targets:
        writer.writerow([row['company'], row['domain'], row['ip_address'], row['location'], row['provider'], row['status_code'], row['last_fetched']])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=detective_pradeep_results.csv"}
    )

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
