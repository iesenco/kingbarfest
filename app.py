from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'
DATABASE = 'banco.db'

USERS = {
    "Bruno": "Lun@2020",
    "Juninho": "Lun@2020"
}

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if USERS.get(username) == password:
            session['username'] = username
            return redirect(url_for('index'))
        flash('Usuário ou senha inválidos.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    rentals = conn.execute('SELECT * FROM rental ORDER BY date_start DESC').fetchall()
    conn.close()
    return render_template('index.html', rentals=rentals)

@app.route('/add', methods=['POST'])
def add():
    if 'username' not in session:
        return redirect(url_for('login'))
    equipment = request.form['equipment']
    date_start = request.form['date_start']
    date_end = request.form['date_end']

    conn = get_db_connection()
    existing = conn.execute(
        'SELECT * FROM rental WHERE equipment = ? AND NOT (date_end < ? OR date_start > ?)',
        (equipment, date_start, date_end)
    ).fetchone()

    if existing:
        flash(f"O equipamento {equipment} já está alugado de {existing['date_start']} a {existing['date_end']}. Por favor, escolha outro equipamento.")
    else:
        conn.execute('INSERT INTO rental (equipment, date_start, date_end) VALUES (?, ?, ?)', (equipment, date_start, date_end))
        conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:rental_id>', methods=['GET', 'POST'])
def edit(rental_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    rental = conn.execute('SELECT * FROM rental WHERE id = ?', (rental_id,)).fetchone()

    if request.method == 'POST':
        equipment = request.form['equipment']
        date_start = request.form['date_start']
        date_end = request.form['date_end']

        existing = conn.execute(
            'SELECT * FROM rental WHERE equipment = ? AND NOT (date_end < ? OR date_start > ?) AND id != ?',
            (equipment, date_start, date_end, rental_id)
        ).fetchone()

        if existing:
            flash(f"O equipamento {equipment} já está alugado de {existing['date_start']} a {existing['date_end']}. Por favor, escolha outro equipamento.")
        else:
            conn.execute('UPDATE rental SET equipment = ?, date_start = ?, date_end = ? WHERE id = ?',
                         (equipment, date_start, date_end, rental_id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    conn.close()
    return render_template('edit.html', rental=rental)

@app.route('/delete/<int:rental_id>')
def delete(rental_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM rental WHERE id = ?', (rental_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)