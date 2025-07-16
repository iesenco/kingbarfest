from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
DATABASE = 'db/kingbar.db'

def init_db():
    os.makedirs("db", exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS rental (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_code TEXT,
            customer TEXT,
            date_start TEXT,
            date_end TEXT,
            FOREIGN KEY(equipment_code) REFERENCES equipment(code)
        )
    ''')

    for i in range(1, 12):
        code = f'KBF-{i:03d}'
        c.execute('INSERT OR IGNORE INTO equipment (code) VALUES (?)', (code,))

    conn.commit()
    conn.close()

def get_available_equipments(date_start, date_end):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    query = '''
        SELECT code FROM equipment
        WHERE code NOT IN (
            SELECT equipment_code FROM rental
            WHERE NOT (date_end < ? OR date_start > ?)
        )
    '''
    c.execute(query, (date_start, date_end))
    available = [row[0] for row in c.fetchall()]
    conn.close()
    return available

@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM rental ORDER BY date_start DESC')
    rentals = c.fetchall()
    conn.close()
    return render_template('index.html', rentals=rentals)

@app.route('/new', methods=['GET', 'POST'])
def new_rental():
    if request.method == 'POST':
        customer = request.form['customer']
        equipment_code = request.form['equipment_code']
        date_start = request.form['date_start']
        date_end = request.form['date_end']

        available = get_available_equipments(date_start, date_end)
        if equipment_code not in available:
            return "Erro: Equipamento não disponível nessa data.", 400

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('INSERT INTO rental (equipment_code, customer, date_start, date_end) VALUES (?, ?, ?, ?)',
                  (equipment_code, customer, date_start, date_end))
        conn.commit()
        conn.close()
        return redirect('/')
    else:
        today = datetime.now().date().isoformat()
        future = today
        available = get_available_equipments(today, future)
        return render_template('new_rental.html', equipments=available)

@app.route('/equipamentos', methods=['GET', 'POST'])
def manage_equipments():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    if request.method == 'POST':
        code = request.form['code'].strip().upper()
        try:
            c.execute('INSERT INTO equipment (code) VALUES (?)', (code,))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Erro: Código já existente.", 400

    c.execute('SELECT * FROM equipment ORDER BY code')
    equipments = c.fetchall()
    conn.close()
    return render_template('equipments.html', equipments=equipments)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)