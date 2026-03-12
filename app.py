from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import sqlite3
import socket
import requests
import csv
import io
import json
import sys
from datetime import datetime
from ipwhois import IPWhois
import whois
from bs4 import BeautifulSoup
import ssl

app = Flask(__name__)
app.secret_key = 'super_secret_tracker_key_for_flash_messages'
DB_PATH = 'ips.db'

# Refined Prompt to force HQ discovery
DEFAULT_PROMPT = """Analyze the following technical and scraped data for an IP/Domain. 
Your primary task is to identify the ACTUAL Business Entity (not the CDN/ISP) and find their OFFICIAL CORPORATE HEADQUARTERS LOCATION.

Input Data:
- Target Domain: {domain}
- IP Address: {ip}
- Infrastructure Owner (RDAP): {infra}
- Network Provider (ip-api): {network}
- Brand Intelligence: {brand}
- WHOIS Registrant: {whois_org}
- Scraped Website Context: {scraped_content}

Instructions:
1. If the infrastructure owner is a CDN (AWS, Akamai, Cloudflare), look at the Domain and Brand Intelligence to find the actual user.
2. Even if 'Internal HQ Search' was N/A, you MUST use your own internal knowledge to provide the City and Country of the company's HQ.
3. Return ONLY a JSON object.

Format:
{{
  "final_company": "Full Legal Name",
  "final_hq": "City, Country",
  "reasoning": "Brief explanation of your identification process."
}}"""

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
            confidence_score INTEGER DEFAULT 0,
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

def get_live_context(domain):
    context = {"meta": "", "text": ""}
    if not domain: return context
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(f"https://{domain}", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        og_desc = soup.find('meta', property='og:description')
        context["meta"] = (meta_desc['content'] if meta_desc else "") + " " + (og_desc['content'] if og_desc else "")
        for script in soup(["script", "style"]): script.extract()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        context["text"] = " ".join(chunk for chunk in chunks if chunk)[:500]
    except: pass
    return context

def get_brand_intelligence(domain):
    brand_data = {"name": None, "source": "None"}
    if not domain: return brand_data
    try:
        res = requests.get(f"https://autocomplete.clearbit.com/v1/companies/suggest?query={domain}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            if len(data) > 0 and data[0].get('name'):
                brand_data["name"] = data[0]['name']
                brand_data["source"] = "Clearbit"
                return brand_data
    except: pass
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(f"https://{domain}", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        site_name = soup.find('meta', property='og:site_name')
        if site_name:
            brand_data["name"] = site_name.get('content')
            brand_data["source"] = "Meta Tags"
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
        registered = format_date(w.creation_date)
        expires = format_date(w.expiration_date)
        updated = format_date(w.updated_date)
        registrant_org = w.org or w.name or "N/A"
        if isinstance(registrant_org, list): registrant_org = registrant_org[0]
        raw_data = {"Registrar": w.registrar, "Registrant Org": registrant_org}
        return registered, expires, updated, raw_data, registrant_org
    except: return "N/A", "N/A", "N/A", {}, "N/A"

def call_openrouter(config, data):
    if not config or not config['openrouter_key']: return None, None, "Missing Key."
    prompt = config['ai_prompt'].format(
        domain=data.get('domain', 'N/A'),
        ip=data.get('ip', 'N/A'),
        infra=data.get('infra', 'N/A'),
        network=data.get('network', 'N/A'),
        brand=data.get('brand', 'N/A'),
        whois_org=data.get('whois_org', 'N/A'),
        scraped_content=data.get('scraped_content', 'N/A')
    )
    try:
        print(f"--- AI REQUEST: {data.get('domain')} ---", file=sys.stderr)
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config['openrouter_key']}",
                "HTTP-Referer": "https://github.com/Viz38/pradeepiptracker",
                "X-Title": "Tracxn OSIT",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "arcee-ai/trinity-large-preview:free",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }),
            timeout=20
        )
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            print(f"--- AI RESPONSE ---\n{content}", file=sys.stderr)
            ai_res = json.loads(content)
            return ai_res.get('final_company'), ai_res.get('final_hq'), ai_res.get('reasoning')
        return None, None, f"Error {response.status_code}"
    except Exception as e: return None, None, str(e)

def check_target(ip, domain=None):
    config = get_config()
    result = {
        "company": "Unknown", "legal_name": "N/A", "corporate_hq": "N/A",
        "location": "N/A", "provider": "N/A", "domains_associated": "N/A",
        "ip_type": "Unknown", "confidence_score": 0, "registered_on": "N/A",
        "expires_on": "N/A", "last_updated_on": "N/A", "raw_intel": "{}",
        "ai_reasoning": "N/A", "last_fetched": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    raw_intel_dict = {"WHOIS": {}, "Network": {}, "Infrastructure": {}}
    actual_org_found = "N/A"
    scraped = get_live_context(domain)
    if domain:
        reg, exp, upd, whois_raw, registrant_org = get_domain_whois(domain)
        result["registered_on"], result["expires_on"], result["last_updated_on"] = reg, exp, upd
        raw_intel_dict["WHOIS"] = whois_raw
        actual_org_found = registrant_org if registrant_org != "N/A" else "N/A"
    try:
        geo_req = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,org,as,isp,hosting,proxy", timeout=3)
        if geo_req.status_code == 200:
            geo_data = geo_req.json()
            if geo_data.get("status") == "success":
                result["location"] = f"{geo_data.get('city')}, {geo_data.get('country')}"
                result["legal_name"] = geo_data.get("org") or "Unknown"
                result["provider"] = geo_data.get("as") or "Unknown"
                result["ip_type"] = "Cloud" if geo_data.get("hosting") else "VPN" if geo_data.get("proxy") else "Business"
                raw_intel_dict["Network"] = {"ISP": result["legal_name"], "Type": result["ip_type"]}
    except: pass
    try:
        obj = IPWhois(ip)
        rdap = obj.lookup_rdap(depth=1)
        rdap_org = rdap.get('network', {}).get('name', '')
        raw_intel_dict["Infrastructure"] = {"RDAP Org": rdap_org, "CIDR": rdap.get('network', {}).get('cidr')}
    except: rdap_org = "N/A"
    brand = get_brand_intelligence(domain)
    if config and config['openrouter_key']:
        ai_name, ai_hq, ai_reason = call_openrouter(config, {
            "domain": domain, "ip": ip, "infra": rdap_org,
            "network": result["provider"], "brand": brand.get("name", "N/A"),
            "whois_org": actual_org_found,
            "scraped_content": f"{scraped['meta']} | {scraped['text']}"
        })
        if ai_name:
            result["company"], result["corporate_hq"], result["ai_reasoning"], result["confidence_score"] = ai_name, ai_hq or "N/A", ai_reason, 100
        else:
            result["company"], result["ai_reasoning"], result["confidence_score"] = brand.get("name") or actual_org_found or result["legal_name"], ai_reason, 70
    else:
        result["company"], result["ai_reasoning"], result["confidence_score"] = brand.get("name") or actual_org_found or result["legal_name"], "No API Key.", 50
    result["raw_intel"] = json.dumps(raw_intel_dict)
    return result

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        target_input = request.form['target'].strip()
        if target_input:
            ip_address, domain = resolve_domain(target_input)
            if ip_address:
                conn = get_db_connection()
                try:
                    conn.execute('INSERT INTO targets (domain, ip_address, company, last_fetched) VALUES (?, ?, ?, ?)',
                                 (domain, ip_address, "Pending", "Never"))
                    conn.commit()
                    return redirect(url_for('results'))
                except sqlite3.IntegrityError: flash('Exists.')
                finally: conn.close()
            else: flash('Unresolved.')
    return render_template('index.html')

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'csv_file' in request.files:
        file = request.files['csv_file']
        if file.filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.reader(stream)
            conn = get_db_connection()
            added = 0
            for row in csv_input:
                if not row: continue
                target_input = row[0].strip()
                if target_input.lower() in ['ip', 'domain', 'url']: continue
                ip, domain = resolve_domain(target_input)
                if ip:
                    try:
                        conn.execute('INSERT INTO targets (domain, ip_address, company, last_fetched) VALUES (?, ?, ?, ?)', (domain, ip, "Pending", "Never"))
                        added += 1
                    except: pass
            conn.commit()
            conn.close()
            flash(f'Added {added} targets.')
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
        conn.execute('UPDATE config SET openrouter_key = ?, ai_prompt = ? WHERE id = 1', (request.form['openrouter_key'].strip(), request.form['ai_prompt'].strip()))
        conn.commit()
        flash('Saved!')
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
    writer.writerow(['Domain', 'IP', 'Company', 'HQ', 'Reasoning'])
    for r in targets: writer.writerow([r['domain'], r['ip_address'], r['company'], r['corporate_hq'], r['ai_reasoning']])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=tracxn_osit.csv"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
