from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import sqlite3
import socket
import os
import requests
import csv
import io
import json
from datetime import datetime
from ipwhois import IPWhois

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
            legal_name TEXT,
            corporate_hq TEXT,
            ip_address TEXT NOT NULL UNIQUE,
            location TEXT,
            provider TEXT,
            domains_associated TEXT,
            ip_type TEXT,
            confidence_score INTEGER,
            last_fetched TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def query_wikidata(company_name):
    """Fetch corporate HQ from Wikidata (Unlimited/Free)"""
    try:
        query = f"""
        SELECT ?item ?itemLabel ?hqLabel WHERE {{
          ?item rdfs:label "{company_name}"@en;
                wdt:P159 ?hq.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }} LIMIT 1
        """
        url = "https://query.wikidata.org/sparql"
        headers = {'User-Agent': 'DetectivePradeep/1.0 (https://github.com/Viz38/pradeepiptracker)'}
        resp = requests.get(url, params={'query': query, 'format': 'json'}, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get('results', {}).get('bindings', [])
            if data:
                return data[0].get('hqLabel', {}).get('value')
    except:
        pass
    return None

def check_target(ip):
    result = {
        "company": "Unknown",
        "legal_name": "N/A",
        "corporate_hq": "N/A",
        "location": "N/A",
        "provider": "N/A",
        "domains_associated": "N/A",
        "ip_type": "Unknown",
        "confidence_score": 0,
        "last_fetched": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    agreement_points = 0

    # Source 1: ip-api.com (Fast, High Limit, Network Owner)
    try:
        geo_req = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,org,as,isp,hosting,proxy", timeout=3)
        if geo_req.status_code == 200:
            geo_data = geo_req.json()
            if geo_data.get("status") == "success":
                result["location"] = f"{geo_data.get('city')}, {geo_data.get('country')}"
                result["company"] = geo_data.get("org") or geo_data.get("isp", "Unknown")
                result["provider"] = geo_data.get("as") or "Unknown"
                result["ip_type"] = "Cloud" if geo_data.get("hosting") else "VPN" if geo_data.get("proxy") else "Business/Residential"
                agreement_points += 1
    except:
        pass

    # Source 2: RDAP / ipwhois (Authoritative Registration)
    try:
        obj = IPWhois(ip)
        rdap = obj.lookup_rdap(depth=1)
        rdap_org = rdap.get('network', {}).get('name', '')
        if not rdap_org:
            objects = rdap.get('objects', {})
            for key in objects:
                name = objects[key].get('contact', {}).get('name')
                if name:
                    rdap_org = name
                    break
        
        if rdap_org:
            # Check agreement with ip-api
            if result["company"] != "Unknown":
                if rdap_org.lower() in result["company"].lower() or result["company"].lower() in rdap_org.lower():
                    agreement_points += 1
            else:
                result["company"] = rdap_org
            
            result["legal_name"] = rdap_org
    except:
        pass

    # Source 3: Wikidata (Corporate HQ & Metadata - Unlimited)
    if result["company"] != "Unknown":
        hq = query_wikidata(result["company"])
        if hq:
            result["corporate_hq"] = hq
            agreement_points += 1
        else:
            # Fallback PeeringDB (Still very accurate for infrastructure)
            try:
                pdb_req = requests.get(f"https://www.peeringdb.com/api/net?name__contains={result['company']}", timeout=3)
                if pdb_req.status_code == 200:
                    data = pdb_req.json().get('data', [])
                    if data:
                        result["corporate_hq"] = f"{data[0].get('city')}, {data[0].get('country')}"
                        agreement_points += 1
            except:
                pass

    # Passive DNS
    try:
        ht_req = requests.get(f"https://api.hackertarget.com/reverseiplookup/?q={ip}", timeout=5)
        if ht_req.status_code == 200 and "error" not in ht_req.text.lower() and "no records" not in ht_req.text.lower():
            domains = ht_req.text.strip().split("\n")
            result["domains_associated"] = ", ".join(domains[:10]) + (f" (+{len(domains)-10} more)" if len(domains) > 10 else "")
    except:
        pass

    # Confidence Score Logic
    if agreement_points >= 3:
        result["confidence_score"] = 98
    elif agreement_points == 2:
        result["confidence_score"] = 92
    elif agreement_points == 1:
        result["confidence_score"] = 75
    else:
        result["confidence_score"] = 20

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
                conn.execute('''
                    INSERT INTO targets (company, legal_name, corporate_hq, ip_address, location, provider, domains_associated, ip_type, confidence_score, last_fetched) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    ("Pending", "Pending", "Pending", ip_address, "Pending", "Pending", "Pending Fetch", "Pending", 0, "Never")
                )
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
        for row in csv_input:
            if not row: continue
            ip_address = row[0].strip()
            if ip_address.lower() in ['ip', 'ip_address', 'address'] or not ip_address: continue
            try:
                conn.execute('''
                    INSERT INTO targets (company, legal_name, corporate_hq, ip_address, location, provider, domains_associated, ip_type, confidence_score, last_fetched) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    ("Pending", "Pending", "Pending", ip_address, "Pending", "Pending", "Pending Fetch", "Pending", 0, "Never")
                )
                added_count += 1
            except:
                pass
        conn.commit()
        conn.close()
        flash(f'Successfully added {added_count} IPs!')
        return redirect(url_for('results'))
    return redirect(url_for('index'))

@app.route('/results')
def results():
    conn = get_db_connection()
    targets = conn.execute('SELECT * FROM targets ORDER BY confidence_score DESC, last_fetched DESC').fetchall()
    conn.close()
    return render_template('results.html', targets=targets)

@app.route('/fetch', methods=['POST'])
def fetch_ips():
    conn = get_db_connection()
    targets = conn.execute('SELECT id, ip_address FROM targets').fetchall()
    for target in targets:
        res = check_target(target['ip_address'])
        conn.execute('''
            UPDATE targets 
            SET company = ?, legal_name = ?, corporate_hq = ?, location = ?, provider = ?, domains_associated = ?, ip_type = ?, confidence_score = ?, last_fetched = ? 
            WHERE id = ?''', 
            (res['company'], res['legal_name'], res['corporate_hq'], res['location'], res['provider'], res['domains_associated'], res['ip_type'], res['confidence_score'], res['last_fetched'], target['id'])
        )
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Successfully updated records."})

@app.route('/delete/<int:id>', methods=['POST'])
def delete_target(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM targets WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/export')
def export_csv():
    conn = get_db_connection()
    targets = conn.execute('SELECT * FROM targets ORDER BY confidence_score DESC').fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Company', 'IP Address', 'Confidence', 'Corporate HQ', 'Server Location', 'Type', 'Domains'])
    for row in targets:
        writer.writerow([row['company'], row['ip_address'], f"{row['confidence_score']}%", row['corporate_hq'], row['location'], row['ip_type'], row['domains_associated']])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=detective_pradeep_intel.csv"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
