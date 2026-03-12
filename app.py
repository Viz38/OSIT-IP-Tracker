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
import whois

app = Flask(__name__)
app.secret_key = 'super_secret_tracker_key_for_flash_messages'
DB_PATH = 'ips.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            company TEXT,
            legal_name TEXT,
            corporate_hq TEXT,
            ip_address TEXT NOT NULL UNIQUE,
            location TEXT,
            provider TEXT,
            domains_associated TEXT,
            ip_type TEXT,
            confidence_score INTEGER,
            registered_on TEXT,
            expires_on TEXT,
            last_updated_on TEXT,
            last_fetched TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def resolve_domain(target):
    """Resolve domain to IP or return target if already IP"""
    target = target.strip().lower()
    if "://" in target:
        target = target.split("://")[1]
    if "/" in target:
        target = target.split("/")[0]
        
    try:
        socket.inet_aton(target)
        return target, None
    except socket.error:
        try:
            ip = socket.gethostbyname(target)
            return ip, target
        except:
            return None, target

def get_domain_whois(domain_name):
    """Fetch Domain WHOIS dates (Registered, Expires, Updated)"""
    if not domain_name:
        return "N/A", "N/A", "N/A"
    
    try:
        w = whois.whois(domain_name)
        
        def format_date(d):
            if isinstance(d, list):
                d = d[0]
            if isinstance(d, datetime):
                return d.strftime("%Y-%m-%d")
            return str(d)

        registered = format_date(w.creation_date) if w.creation_date else "N/A"
        expires = format_date(w.expiration_date) if w.expiration_date else "N/A"
        updated = format_date(w.updated_date) if w.updated_date else "N/A"
        
        return registered, expires, updated
    except:
        return "N/A", "N/A", "N/A"

def query_wikidata(company_name):
    """Fetch corporate HQ from Wikidata"""
    try:
        query = f"""
        SELECT ?item ?itemLabel ?hqLabel WHERE {{
          ?item rdfs:label "{company_name}"@en;
                wdt:P159 ?hq.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }} LIMIT 1
        """
        url = "https://query.wikidata.org/sparql"
        headers = {'User-Agent': 'TracxnOSIT/1.0 (https://github.com/Viz38/pradeepiptracker)'}
        resp = requests.get(url, params={'query': query, 'format': 'json'}, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get('results', {}).get('bindings', [])
            if data:
                return data[0].get('hqLabel', {}).get('value')
    except:
        pass
    return None

def check_target(ip, domain=None):
    result = {
        "company": "Unknown",
        "legal_name": "N/A",
        "corporate_hq": "N/A",
        "location": "N/A",
        "provider": "N/A",
        "domains_associated": "N/A",
        "ip_type": "Unknown",
        "confidence_score": 0,
        "registered_on": "N/A",
        "expires_on": "N/A",
        "last_updated_on": "N/A",
        "last_fetched": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    agreement_points = 0

    # Domain WHOIS Dates
    if domain:
        reg, exp, upd = get_domain_whois(domain)
        result["registered_on"] = reg
        result["expires_on"] = exp
        result["last_updated_on"] = upd

    # Source 1: ip-api.com
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

    # Source 2: RDAP
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
            if result["company"] != "Unknown":
                if rdap_org.lower() in result["company"].lower() or result["company"].lower() in rdap_org.lower():
                    agreement_points += 1
            else:
                result["company"] = rdap_org
            result["legal_name"] = rdap_org
    except:
        pass

    # Source 3: Wikidata
    if result["company"] != "Unknown":
        hq = query_wikidata(result["company"])
        if hq:
            result["corporate_hq"] = hq
            agreement_points += 1
        else:
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

    if agreement_points >= 3: result["confidence_score"] = 98
    elif agreement_points == 2: result["confidence_score"] = 92
    elif agreement_points == 1: result["confidence_score"] = 75
    else: result["confidence_score"] = 20

    return result

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        target_input = request.form['target'].strip()
        if not target_input:
            flash('Target (IP or Domain) is required!')
        else:
            ip_address, domain = resolve_domain(target_input)
            if not ip_address:
                flash(f'Could not resolve domain: {target_input}')
            else:
                conn = get_db_connection()
                try:
                    conn.execute('''
                        INSERT INTO targets (domain, company, legal_name, corporate_hq, ip_address, location, provider, domains_associated, ip_type, confidence_score, registered_on, expires_on, last_updated_on, last_fetched) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (domain, "Pending", "Pending", "Pending", ip_address, "Pending", "Pending", "Pending Fetch", "Pending", 0, "Pending", "Pending", "Pending", "Never")
                    )
                    conn.commit()
                    flash(f'Target successfully added: {ip_address}')
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
            target_input = row[0].strip()
            if target_input.lower() in ['ip', 'ip_address', 'address', 'domain', 'url'] or not target_input: continue
            
            ip_address, domain = resolve_domain(target_input)
            if ip_address:
                try:
                    conn.execute('''
                        INSERT INTO targets (domain, company, legal_name, corporate_hq, ip_address, location, provider, domains_associated, ip_type, confidence_score, registered_on, expires_on, last_updated_on, last_fetched) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (domain, "Pending", "Pending", "Pending", ip_address, "Pending", "Pending", "Pending Fetch", "Pending", 0, "Pending", "Pending", "Pending", "Never")
                    )
                    added_count += 1
                except:
                    pass
        conn.commit()
        conn.close()
        flash(f'Successfully processed {added_count} targets from CSV!')
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
    targets = conn.execute('SELECT id, ip_address, domain FROM targets').fetchall()
    for target in targets:
        res = check_target(target['ip_address'], target['domain'])
        conn.execute('''
            UPDATE targets 
            SET company = ?, legal_name = ?, corporate_hq = ?, location = ?, provider = ?, domains_associated = ?, ip_type = ?, confidence_score = ?, registered_on = ?, expires_on = ?, last_updated_on = ?, last_fetched = ? 
            WHERE id = ?''', 
            (res['company'], res['legal_name'], res['corporate_hq'], res['location'], res['provider'], res['domains_associated'], res['ip_type'], res['confidence_score'], res['registered_on'], res['expires_on'], res['last_updated_on'], res['last_fetched'], target['id'])
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
    writer.writerow(['Domain', 'Company', 'IP Address', 'Confidence', 'Corporate HQ', 'Registered On', 'Expires On', 'Last Updated', 'Server Location', 'Type', 'Domains'])
    for row in targets:
        writer.writerow([row['domain'], row['company'], row['ip_address'], f"{row['confidence_score']}%", row['corporate_hq'], row['registered_on'], row['expires_on'], row['last_updated_on'], row['location'], row['ip_type'], row['domains_associated']])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=tracxn_osit_intel.csv"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
