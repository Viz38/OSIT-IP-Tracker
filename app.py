from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import sqlite3
import socket
import requests
import csv
import io
import json
from datetime import datetime
from ipwhois import IPWhois
import whois
from bs4 import BeautifulSoup
import ssl

app = Flask(__name__)
app.secret_key = 'super_secret_tracker_key_for_flash_messages'
DB_PATH = 'ips.db'

DEFAULT_PROMPT = """Analyze the following technical data gathered for an IP/Domain and provide the final verified organization name. 
Data gathered:
- Target Domain: {domain}
- IP Address: {ip}
- Infrastructure Owner (RDAP): {infra}
- Network Provider (ip-api): {network}
- Brand Intelligence: {brand}
- WHOIS Registrant: {whois_org}

The infrastructure owner might be a CDN (like AWS, Cloudflare) or an ISP. Your goal is to identify the actual business or entity that is using this infrastructure.
Return only a JSON object with two keys: "final_company" and "reasoning"."""

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
            raw_intel TEXT,
            ai_reasoning TEXT,
            last_fetched TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY,
            openrouter_key TEXT,
            ai_prompt TEXT
        )
    ''')
    c.execute('SELECT count(*) FROM config')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO config (id, openrouter_key, ai_prompt) VALUES (1, ?, ?)', ('', DEFAULT_PROMPT))
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_config():
    conn = get_db_connection()
    config = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
    conn.close()
    return config

def resolve_domain(target):
    target = target.strip().lower()
    if "://" in target: target = target.split("://")[1]
    if "/" in target: target = target.split("/")[0]
    try:
        socket.inet_aton(target)
        return target, None
    except socket.error:
        try:
            ip = socket.gethostbyname(target)
            return ip, target
        except:
            return None, target

def get_brand_intelligence(domain):
    brand_data = {"name": None, "source": "None"}
    if not domain: return brand_data
    try:
        res = requests.get(f"https://autocomplete.clearbit.com/v1/companies/suggest?query={domain}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            if len(data) > 0 and data[0].get('name'):
                brand_data["name"] = data[0]['name']
                brand_data["source"] = "Clearbit Intelligence API"
                return brand_data
    except: pass
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(f"https://{domain}", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        site_name = soup.find('meta', property='og:site_name')
        if site_name and site_name.get('content'):
            brand_data["name"] = site_name['content'].strip()
            brand_data["source"] = "Live Website Meta (og:site_name)"
            return brand_data
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            if '|' in title: brand_data["name"] = title.split('|')[-1].strip()
            elif '-' in title: brand_data["name"] = title.split('-')[-1].strip()
            else: brand_data["name"] = title
            brand_data["source"] = "Live Website Title"
            return brand_data
    except: pass
    return brand_data

def get_domain_whois(domain_name):
    if not domain_name: return "N/A", "N/A", "N/A", {}, "N/A"
    try:
        w = whois.whois(domain_name)
        def format_date(d):
            if isinstance(d, list): d = d[0]
            if isinstance(d, datetime): return d.strftime("%Y-%m-%d")
            return str(d)
        registered = format_date(w.creation_date) if w.creation_date else "N/A"
        expires = format_date(w.expiration_date) if w.expiration_date else "N/A"
        updated = format_date(w.updated_date) if w.updated_date else "N/A"
        registrant_org = w.org or w.name or "N/A"
        if isinstance(registrant_org, list): registrant_org = registrant_org[0]
        raw_data = {"Registrar": w.registrar, "Registrant Org": registrant_org}
        return registered, expires, updated, raw_data, registrant_org
    except: return "N/A", "N/A", "N/A", {}, "N/A"

def call_openrouter(config, data):
    if not config or not config['openrouter_key']:
        return None, "OpenRouter API Key not set."
    prompt = config['ai_prompt'].format(
        domain=data.get('domain', 'N/A'),
        ip=data.get('ip', 'N/A'),
        infra=data.get('infra', 'N/A'),
        network=data.get('network', 'N/A'),
        brand=data.get('brand', 'N/A'),
        whois_org=data.get('whois_org', 'N/A')
    )
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config['openrouter_key']}",
                "HTTP-Referer": "https://github.com/Viz38/pradeepiptracker",
                "X-Title": "Tracxn OSIT",
            },
            data=json.dumps({
                "model": "openrouter/trinity-large-preview",
                "messages": [{"role": "user", "content": prompt}]
            }),
            timeout=10
        )
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            try:
                if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
                ai_res = json.loads(content)
                return ai_res.get('final_company'), ai_res.get('reasoning')
            except: return content, "Raw AI response returned."
    except Exception as e: return None, f"AI Error: {str(e)}"
    return None, "No response from AI."

def check_target(ip, domain=None):
    config = get_config()
    result = {
        "company": "Unknown", "legal_name": "N/A", "corporate_hq": "N/A",
        "location": "N/A", "provider": "N/A", "domains_associated": "N/A",
        "ip_type": "Unknown", "confidence_score": 0, "registered_on": "N/A",
        "expires_on": "N/A", "last_updated_on": "N/A", "raw_intel": "{}",
        "ai_reasoning": "N/A", "last_fetched": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    raw_intel_dict = {"WHOIS": {}, "Network (ip-api)": {}, "Infrastructure (RDAP)": {}}
    agreement_points = 0
    actual_org_found = "N/A"

    if domain:
        reg, exp, upd, whois_raw, registrant_org = get_domain_whois(domain)
        result["registered_on"], result["expires_on"], result["last_updated_on"] = reg, exp, upd
        raw_intel_dict["WHOIS"] = whois_raw
        if registrant_org and registrant_org != "N/A" and "privacy" not in registrant_org.lower():
            actual_org_found = registrant_org
            agreement_points += 1

    try:
        geo_req = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,org,as,isp,hosting,proxy", timeout=3)
        if geo_req.status_code == 200:
            geo_data = geo_req.json()
            if geo_data.get("status") == "success":
                result["location"] = f"{geo_data.get('city')}, {geo_data.get('country')}"
                result["legal_name"] = geo_data.get("org") or geo_data.get("isp", "Unknown")
                result["provider"] = geo_data.get("as") or "Unknown"
                result["ip_type"] = "Cloud" if geo_data.get("hosting") else "VPN" if geo_data.get("proxy") else "Business/Residential"
                raw_intel_dict["Network (ip-api)"] = {"ISP": result["legal_name"], "Is Cloud": geo_data.get("hosting")}
    except: pass

    try:
        obj = IPWhois(ip)
        rdap = obj.lookup_rdap(depth=1)
        rdap_org = rdap.get('network', {}).get('name', '')
        if rdap_org:
            result["legal_name"] = rdap_org
            if actual_org_found != "N/A" and (rdap_org.lower() in actual_org_found.lower() or actual_org_found.lower() in rdap_org.lower()):
                agreement_points += 2
        raw_intel_dict["Infrastructure (RDAP)"] = {"Registrant": rdap_org, "CIDR": rdap.get('network', {}).get('cidr')}
    except: pass

    brand = get_brand_intelligence(domain)
    if brand.get("name"):
        result["company"] = brand["name"]
        result["confidence_score"] = 99
    else:
        result["company"] = actual_org_found if actual_org_found != "N/A" else result["legal_name"]
        result["confidence_score"] = 70 if agreement_points > 1 else 30

    if config and config['openrouter_key']:
        ai_name, ai_reason = call_openrouter(config, {
            "domain": domain, "ip": ip, "infra": result["legal_name"],
            "network": result["provider"], "brand": brand.get("name", "N/A"),
            "whois_org": actual_org_found
        })
        if ai_name:
            result["company"] = ai_name
            result["ai_reasoning"] = ai_reason
            result["confidence_score"] = 100

    result["raw_intel"] = json.dumps(raw_intel_dict)
    return result

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        target_input = request.form['target'].strip()
        if not target_input: flash('Target required!')
        else:
            ip_address, domain = resolve_domain(target_input)
            if not ip_address: flash(f'Could not resolve: {target_input}')
            else:
                conn = get_db_connection()
                try:
                    conn.execute('INSERT INTO targets (domain, ip_address, company, legal_name, last_fetched) VALUES (?, ?, ?, ?, ?)',
                                 (domain, ip_address, "Pending", "Pending", "Never"))
                    conn.commit()
                    return redirect(url_for('results'))
                except sqlite3.IntegrityError: flash('Target exists.')
                finally: conn.close()
    return render_template('index.html')

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'csv_file' not in request.files: return redirect(url_for('index'))
    file = request.files['csv_file']
    if file.filename == '': return redirect(url_for('index'))
    if file and file.filename.endswith('.csv'):
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        conn = get_db_connection()
        added_count = 0
        for row in csv_input:
            if not row: continue
            target_input = row[0].strip()
            if target_input.lower() in ['ip', 'ip_address', 'address', 'domain', 'url']: continue
            ip_address, domain = resolve_domain(target_input)
            if ip_address:
                try:
                    conn.execute('INSERT INTO targets (domain, ip_address, company, legal_name, last_fetched) VALUES (?, ?, ?, ?, ?)',
                                 (domain, ip_address, "Pending", "Pending", "Never"))
                    added_count += 1
                except: pass
        conn.commit()
        conn.close()
        flash(f'Processed {added_count} targets!')
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
            UPDATE targets SET company=?, legal_name=?, corporate_hq=?, location=?, provider=?, 
            domains_associated=?, ip_type=?, confidence_score=?, registered_on=?, expires_on=?, 
            last_updated_on=?, raw_intel=?, ai_reasoning=?, last_fetched=? WHERE id=?''', 
            (res['company'], res['legal_name'], res['corporate_hq'], res['location'], res['provider'], 
             res['domains_associated'], res['ip_type'], res['confidence_score'], res['registered_on'], 
             res['expires_on'], res['last_updated_on'], res['raw_intel'], res['ai_reasoning'], res['last_fetched'], target['id']))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/settings', methods=('GET', 'POST'))
def settings():
    conn = get_db_connection()
    if request.method == 'POST':
        key = request.form['openrouter_key'].strip()
        prompt = request.form['ai_prompt'].strip()
        conn.execute('UPDATE config SET openrouter_key = ?, ai_prompt = ? WHERE id = 1', (key, prompt))
        conn.commit()
        flash('Settings updated!')
    config = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
    conn.close()
    return render_template('settings.html', config=config)

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
    targets = conn.execute('SELECT * FROM targets ORDER BY id DESC').fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Domain', 'IP', 'Company', 'AI Reasoning', 'Confidence'])
    for r in targets: writer.writerow([r['domain'], r['ip_address'], r['company'], r['ai_reasoning'], r['confidence_score']])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=tracxn_osit.csv"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
