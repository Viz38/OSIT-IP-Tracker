from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import socket
import os

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
            ip_address TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def resolve_ip(domain):
    try:
        # basic resolution
        ip = socket.gethostbyname(domain)
        return ip
    except socket.error:
        return "Resolution Failed"

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
                # Initially set IP to pending so it can be fetched later
                conn.execute('INSERT INTO targets (company, domain, ip_address) VALUES (?, ?, ?)',
                             (company, domain, "Pending Fetch"))
                conn.commit()
                flash('Target successfully added!')
                return redirect(url_for('results'))
            except sqlite3.IntegrityError:
                flash('This domain already exists in the tracker.')
            finally:
                conn.close()

    return render_template('index.html')

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
        ip = resolve_ip(target['domain'])
        conn.execute('UPDATE targets SET ip_address = ? WHERE id = ?', (ip, target['id']))
        updated_count += 1
        
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": f"Successfully updated {updated_count} records."})

@app.route('/export')
def export_csv():
    import csv
    from flask import Response
    import io

    conn = get_db_connection()
    targets = conn.execute('SELECT company, domain, ip_address FROM targets ORDER BY company ASC').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Company', 'Domain', 'IP Address'])
    
    for row in targets:
        writer.writerow([row['company'], row['domain'], row['ip_address']])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=recon_ips.csv"}
    )

if __name__ == '__main__':
    init_db()
    # Run on 5001 so it doesn't conflict with recon-web
    app.run(host='0.0.0.0', port=5001, debug=True)
