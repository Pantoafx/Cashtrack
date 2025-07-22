import os
os.environ['TESSDATA_PREFIX'] = r'C:\Users\Exia\AppData\Local\Tesseract-OCR\tessdata'

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from PIL import Image
import pytesseract
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Exia\AppData\Local\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_NAME = 'database.db'

def format_rupiah(angka):
    return f"Rp{int(angka):,}".replace(",", ".")

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pengeluaran (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                jumlah REAL NOT NULL
            );
        ''')

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Input manual
        if 'nama' in request.form and 'jumlah' in request.form:
            nama = request.form.get('nama')
            jumlah = request.form.get('jumlah')
            if nama and jumlah:
                try:
                    jumlah = float(jumlah)
                    with sqlite3.connect(DB_NAME) as conn:
                        conn.execute('INSERT INTO pengeluaran (nama, jumlah) VALUES (?, ?)', (nama, jumlah))
                except ValueError:
                    pass
            return redirect(url_for('index'))

        # Upload struk
        if 'struk' in request.files:
            file = request.files['struk']
            if file.filename != '':
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)

                text = pytesseract.image_to_string(Image.open(filepath))
                numbers = re.findall(r'\d+[\.,]?\d*', text.replace(',', ''))

                if numbers:
                    numbers_float = [float(n) for n in numbers]
                    total = max(numbers_float)
                    with sqlite3.connect(DB_NAME) as conn:
                        conn.execute('INSERT INTO pengeluaran (nama, jumlah) VALUES (?, ?)', ('Dari struk', total))

            return redirect(url_for('index'))

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute('SELECT * FROM pengeluaran')
        data = cursor.fetchall()
        total = sum(row[2] for row in data)

    formatted_data = [(row[0], row[1], format_rupiah(row[2])) for row in data]
    formatted_total = format_rupiah(total)

    return render_template('index.html', data=formatted_data, total=formatted_total)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        nama = request.form.get('nama')
        jumlah = request.form.get('jumlah')
        try:
            jumlah = float(jumlah)
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute('UPDATE pengeluaran SET nama = ?, jumlah = ? WHERE id = ?', (nama, jumlah, id))
        except ValueError:
            pass
        return redirect(url_for('index'))
    else:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.execute('SELECT * FROM pengeluaran WHERE id = ?', (id,))
            row = cursor.fetchone()
        if row is None:
            return redirect(url_for('index'))
        return render_template('edit.html', row=row)

@app.route('/delete/<int:id>')
def delete(id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('DELETE FROM pengeluaran WHERE id = ?', (id,))
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
