from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from flask import send_file
import io
from datetime import datetime, timedelta
import requests
import hashlib
import secrets
import stripe
import os
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

PRICE = os.environ.get('PRICE')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
ENDPOINT_SECRET = os.environ.get('ENDPOINT_SECRET')

USERNAMES = {'docteur-sacko', 'secretaire1'}

USERNAME = os.environ.get('USERNAME')
USERNAME1 = os.environ.get('USERNAME1')

PASSWORD = os.environ.get('PASSWORD')
PASSWORD1 = os.environ.get('PASSWORD1')

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this to a secure secret key
stripe.api_key = STRIPE_SECRET_KEY
items=[{'price': PRICE}]
endpoint_secret = ENDPOINT_SECRET

DATABASE = 'patients.db'

def hash_password(password):
    """Hash a password for storing."""
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt + pwdhash.hex()

def verify_password(stored_password, provided_password):
    """Verify a stored password against provided password."""
    salt = stored_password[:32]
    stored_hash = stored_password[32:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return pwdhash.hex() == stored_hash

# def login_required(f):
#     """Decorator to require login for routes."""
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'user_id' not in session:
#             return redirect(url_for('login'))
#         return f(*args, **kwargs)
#     return decorated_function

# def subscription_required(f):
#     """Decorator to require active subscription."""
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'user_id' not in session:
#             return redirect(url_for('login'))
        
#         # Check if user has valid subscription (active, incomplete, or trialing)
#         conn = get_db_connection()
#         subscription = conn.execute('''
#             SELECT * FROM subscriptions 
#             WHERE user_id = ? AND status IN ('active', 'incomplete', 'trialing')
#             AND current_period_end >= date('now')
#         ''', (session['user_id'],)).fetchone()
#         conn.close()
        
#         if not subscription:
#             return redirect(url_for('payment'))
        
#         return f(*args, **kwargs)
#     return decorated_function

# Set up the SMTP server
smtp_server = "smtp.gmail.com"
smtp_port = 587

your_email = "jonathanjerabe@gmail.com"
your_password = "ajrn mros lkzm urnu"

acteur_inf = "jonathanjerabe@gmail.com"
acteur_med = "jonathanjerabe@gmail.com"

import random
import string

# Add this to store verification codes temporarily (in production, use Redis or database)
verification_codes = {}

def generate_verification_code():
    """Generate a 6-digit verification code."""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code):
    """Send verification code via email."""
    subject = "Verify Your Email - Cabinet la Renaissance"
    
    msg = MIMEMultipart()
    msg['From'] = your_email
    msg['To'] = email
    msg['Subject'] = subject

    html = f"""
    <html>
    <body>
        <h2>Email Verification</h2>
        <p>Your verification code is: <strong>{code}</strong></p>
        <p>This code will expire in 10 minutes.</p>
        <br>
        <img style="width: 350px; height: 100px;" src="https://allarassemjonathan.github.io/marate_white.png">
    </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(your_email, your_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False


@app.route('/login', methods=['GET', 'POST'])
def login():
    # if 'user_id' in session:
    #     return redirect(url_for('landing'))
    
    data = request.get_json() if request.is_json else request.form
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    
    print(username, password)
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Username and password are required'}), 400
    
    if username in USERNAMES:
        print('made it here', username)
        if password == PASSWORD or  password == PASSWORD1:
            return jsonify({'status': 'success', 'redirect': url_for('index')})
        
    return jsonify({'status': 'error', 'message': 'Login failed'}), 500
    
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'GET':
#         return render_template('register.html')
    
#     data = request.get_json() if request.is_json else request.form
#     email = data.get('email', '').strip().lower()
#     password = data.get('password', '')
#     name = data.get('name', '').strip()
    
#     if not email or not password or not name:
#         return jsonify({'status': 'error', 'message': 'Name, email and password are required'}), 400
    
#     if len(password) < 6:
#         return jsonify({'status': 'error', 'message': 'Password must be at least 6 characters'}), 400
    
#     try:
#         conn = get_db_connection()
#         existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
#         if existing_user:
#             conn.close()
#             return jsonify({'status': 'error', 'message': 'Email already registered'}), 400
        
#         conn.close()
        
#         # Generate and send verification code
#         code = generate_verification_code()
#         if not send_verification_email(email, code):
#             return jsonify({'status': 'error', 'message': 'Failed to send verification email'}), 500
        
#         verification_codes[email] = {
#             'code': code,
#             'password': password,
#             'name': name,
#             'timestamp': datetime.now()
#         }
        
#         return jsonify({'status': 'success', 'message': 'Verification code sent to your email', 'email': email})
        
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': 'Registration failed'}), 500
    

# @app.route('/verify-email', methods=['POST'])
# def verify_email():
#     data = request.get_json() if request.is_json else request.form
#     email = data.get('email', '').strip().lower()
#     code = data.get('code', '').strip()
    
#     if not email or not code:
#         return jsonify({'status': 'error', 'message': 'Email and code are required'}), 400
    
#     # Check if verification data exists
#     if email not in verification_codes:
#         return jsonify({'status': 'error', 'message': 'No verification request found'}), 400
    
#     verification_data = verification_codes[email]
    
#     # Check if code has expired (10 minutes)
#     if datetime.now() - verification_data['timestamp'] > timedelta(minutes=10):
#         del verification_codes[email]
#         return jsonify({'status': 'error', 'message': 'Verification code has expired'}), 400
    
#     # Check if code matches
#     if verification_data['code'] != code:
#         return jsonify({'status': 'error', 'message': 'Invalid verification code'}), 400
    
#     try:
#         # Create the user account with name
#         conn = get_db_connection()
#         password_hash = hash_password(verification_data['password'])
#         cursor = conn.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)', 
#                              (email, password_hash))
#         user_id = cursor.lastrowid
#         conn.commit()
#         conn.close()
        
#         # Clean up verification data
#         del verification_codes[email]
        
#         # Set session
#         session['user_id'] = user_id
#         session['email'] = email
#         session['name'] = verification_data['name']
        
#         return jsonify({'status': 'success', 'redirect': url_for('payment')})
        
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': 'Account creation failed'}), 500

# @app.route('/resend-code', methods=['POST'])
# def resend_code():
#     data = request.get_json() if request.is_json else request.form
#     email = data.get('email', '').strip().lower()
    
#     if not email or email not in verification_codes:
#         return jsonify({'status': 'error', 'message': 'No verification request found'}), 400
    
#     # Generate new code
#     code = generate_verification_code()
#     if not send_verification_email(email, code):
#         return jsonify({'status': 'error', 'message': 'Failed to send verification email'}), 500
    
#     # Update verification data
#     verification_codes[email]['code'] = code
#     verification_codes[email]['timestamp'] = datetime.now()
    
#     return jsonify({'status': 'success', 'message': 'New verification code sent'})

# Function to get DB connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# PDF generation using fpdf==1.7.2
import tempfile, os
from fpdf import FPDF
from datetime import datetime
import requests

class InvoicePDF(FPDF):
    def header(self):
        try:
            logo_url = "https://allarassemjonathan.github.io/marate_white.png"
            response = requests.get(logo_url, timeout=10)
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                self.image(tmp_path, x=10, y=8, w=25)
                os.remove(tmp_path)
        except Exception as e:
            print(f"Could not load logo: {e}")

        # Right-aligned title
        self.set_xy(-80, 10)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(6, 182, 212)
        self.cell(70, 10, 'Devis Cabinet la Renaissance', ln=1, align='R')
        self.ln(5)

    def add_patient_info(self, patient):
        self.set_font('Arial', '', 11)
        self.set_text_color(0)
        line_height = 6

        left_x = 10
        right_x = 110

        # Left side: patient
        self.set_xy(left_x, self.get_y())
        self.cell(90, line_height, f"Nom: {patient['name']}", ln=0)

        self.set_xy(right_x, self.get_y())
        self.cell(90, line_height, "Cabinet dentaire la renaissance", ln=1)

        self.set_xy(left_x, self.get_y())
        self.cell(90, line_height, f"Adresse: {patient['adresse'] or 'N/A'}", ln=0)

        self.set_xy(right_x, self.get_y())
        self.cell(90, line_height, "Kantara Sacko", ln=1)

        self.set_xy(left_x, self.get_y())
        self.cell(90, line_height, f"Date de naissance: {patient['date_of_birth'] or 'N/A'}", ln=0)

        self.set_xy(right_x, self.get_y())
        self.cell(90, line_height, "Adresse Rue 22, Medina Dakar", ln=1)

        self.set_xy(left_x, self.get_y())
        self.cell(90, line_height, f"Date de facture: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=0)

        self.set_xy(right_x, self.get_y())
        self.cell(90, line_height, "cablarenaissance@gmail.com", ln=1)

        self.set_xy(right_x, self.get_y())
        self.cell(90, line_height, "(+221) 78 635 95 65", ln=1)

        self.set_xy(right_x, self.get_y())
        self.cell(90, line_height, "Ordre des Chirurgiens Dentistes: B 1506", ln=1)
        self.ln(5)

    def add_invoice_table(self, items):
        headers = ['Article', 'Quantité', 'Prix Unitaire', 'Prix Total', 'Date', '% Assurance']
        col_widths = [35, 20, 30, 30, 30, 25]

        # Header row with cyan background
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(0, 255, 255)  # Cyan background (RGB)
        self.set_text_color(0)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, header, 1, 0, 'C', True)
        self.ln()

        # Data rows with yellowish background
        self.set_font('Arial', '', 10)
        self.set_fill_color(255, 243, 205)  # Yellowish background (#fff3cd)
        self.set_text_color(0)

        total_amount = 0
        total_insured = 0

        for item in items:
            quantity = int(item['quantity'])
            price = int(item['price'])
            assurance = int(item.get('insurance', 80))
            total_price = quantity * price
            insured_part = total_price * assurance // 100
            total_amount += total_price
            total_insured += insured_part

            row = [
                item['name'],
                str(quantity),
                f"{price} Fcfa",
                f"{total_price} Fcfa",
                datetime.now().strftime('%d/%m/%Y'),
                f"{assurance} %"
            ]
            for i, value in enumerate(row):
                self.cell(col_widths[i], 10, value, 1, 0, 'L', True)
            self.ln()

        # Total row with grey background (unchanged)
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(224, 224, 224)  # Light gray (#e0e0e0)
        self.cell(sum(col_widths[:-2]), 10, 'TOTAL:', 1, 0, 'R', True)
        self.cell(col_widths[-2], 10, f"{total_amount} Fcfa", 1, 0, 'L', True)
        self.cell(col_widths[-1], 10, '', 1, 0, 'L', True)
        self.ln(10)

        # Breakdown section
        patient_amount = total_amount - total_insured
        self.set_font('Arial', '', 11)
        self.set_fill_color(255, 255, 255)
        self.ln(4)
        self.cell(0, 8, f"Total: {total_amount} Fcfa", ln=1)
        self.cell(0, 8, f"Part Assureur (80%): {total_insured} Fcfa", ln=1)
        self.cell(0, 8, f"Part Patient (20%): {patient_amount} Fcfa", ln=1)

        # Final patient amount
        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(220, 20, 60)  # Red
        self.cell(0, 10, f"MONTANT À PAYER PAR LE PATIENT: {patient_amount} Fcfa", ln=1, align='C')
        self.set_text_color(0)


@app.route('/generate_invoice/<int:patient_id>', methods=['POST'])
# @subscription_required
def generate_invoice(patient_id):
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({'status': 'error', 'message': 'Invoice items are required'}), 400

        items = data['items']
        for item in items:
            if not all(key in item for key in ['name', 'quantity', 'price']):
                return jsonify({'status': 'error', 'message': 'Each item must have name, quantity, and price'}), 400
            try:
                float(item['quantity'])
                float(item['price'])
            except (ValueError, TypeError):
                return jsonify({'status': 'error', 'message': 'Quantity and price must be numeric'}), 400

        conn = get_db_connection()
        patient = conn.execute('SELECT rowid, * FROM patients WHERE rowid = ?', (patient_id,)).fetchone()
        conn.close()

        if not patient:
            return jsonify({'status': 'error', 'message': 'Patient not found'}), 404

        pdf = InvoicePDF()
        pdf.add_page()
        pdf.add_patient_info(patient)
        pdf.add_invoice_table(items)

        pdf_data = pdf.output(dest='S').encode('latin1')  # 'S' returns PDF as str; encode to bytes
        pdf_buffer = io.BytesIO(pdf_data)
        pdf_buffer.seek(0)

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'invoice_{patient["name"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Error generating invoice: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


def email_reception(firstname, lastname, body, plot, recipient_email):

    # sending the email
    subject = f"Nouveau patient {firstname} {lastname}"
    
    # create the MIME message
    msg = MIMEMultipart()
    msg['From'] = your_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # add an HTML body with the embedded image
    html = f"""
    <html>
    <body>
        <br>
        <p>
        {body}
        </p>
        <br>
        <img style="width: 350px; height: 100px;" src="https://allarassemjonathan.github.io/marate_white.png">
    </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    if plot:
        # Embed the graph as an inline image
        image = MIMEImage(plot.getvalue(), name="graph.png")
        image.add_header("Content-ID", "<graph>")
        msg.attach(image)


    # Connect to the SMTP server and send the email
    try:
        # Establish connection to Gmail's SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection

        # Log in to the server
        server.login(your_email, your_password)

        # Send the email
        server.send_message(msg)

        print("Email sent successfully!")

    except Exception as e:
        print(f"Error sending email: {e}")

    finally:
        # Close the connection to the server
        server.quit()

    # You could include additional validation for the URL here if needed
    return jsonify(success=True)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    conn = get_db_connection()
    
    # Create patients table (existing)
    conn.execute('''CREATE TABLE IF NOT EXISTS patients (
        name TEXT NOT NULL, 
        date_of_birth DATE, 
        adresse TEXT, 
        age INTEGER,
        antecedents_tabagiques TEXT,
        statut_implants TEXT,
        frequence_fil_dentaire TEXT,
        frequence_brossage TEXT,
        allergies TEXT,
        created_at DATE
    )''')
    
    # Create visits table (existing)
    conn.execute('''CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        patient_id INTEGER,
        visit_date DATE, 
        notes TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(rowid)
    )''')
    
    # Create users table for authentication (updated with name field)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )''')
    
    # Create subscriptions table for payment tracking
    conn.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        stripe_customer_id TEXT,
        stripe_subscription_id TEXT,
        status TEXT NOT NULL,
        current_period_start DATE,
        current_period_end DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    conn.commit()
    conn.close()
    
    # Run migration if needed
    migrate_database()

@app.route('/')
# @subscription_required
def index():
    """Main application page - only accessible with valid subscription."""
    init_db()
    return render_template('index.html')

@app.route('/search')
# @subscription_required
def search():
    q = request.args.get('q', '')
    conn = get_db_connection()
    results = conn.execute(
        "SELECT rowid, * FROM patients WHERE name LIKE ? OR adresse LIKE ?",
        tuple(f'%{q}%' for _ in range(2))
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in results])
from datetime import date

@app.route('/add', methods=['POST'])
# @subscription_required
def add():
    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify({'status': 'error', 'message': 'Name is required'}), 400

    try:
        data['created_at'] = date.today().isoformat()  # Add today's date
        allowed_columns = {
            'name', 'date_of_birth', 'adresse', 'age', 
            'antecedents_tabagiques', 'statut_implants', 
            'frequence_fil_dentaire', 'frequence_brossage', 'allergies', 'created_at'
        }
        filtered_data = {k: v for k, v in data.items() if k in allowed_columns}

        columns = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?'] * len(filtered_data))
        values = list(filtered_data.values())

        # send email to physician
        email_reception(filtered_data['name'], '', 'Cher medecin, vous avez un nouveau patient! Faite-le entrer dès que vous êtes prêt', None, acteur_med)
            
        conn = get_db_connection()
        conn.execute(f'INSERT INTO patients ({columns}) VALUES ({placeholders})', values)
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@app.route('/delete/<int:rowid>', methods=['DELETE'])
# @subscription_required
def delete(rowid):
    conn = get_db_connection()
    conn.execute('DELETE FROM patients WHERE rowid = ?', (rowid,))
    conn.commit()
    conn.close()    
    return jsonify({'status': 'deleted'})

@app.route('/patient/<int:patient_id>')
# @subscription_required
def patient_detail(patient_id):
    conn = get_db_connection()
    patient = conn.execute('SELECT rowid, * FROM patients WHERE rowid = ?', (patient_id,)).fetchone()
    visits = conn.execute('SELECT * FROM visits WHERE patient_id = ?', (patient_id,)).fetchall()
    conn.close()
    return render_template('patient.html', patient=patient, visits=visits) if patient else ("Patient not found", 404)

@app.route('/get_patient/<int:patient_id>')
# @subscription_required
def get_patient(patient_id):
    conn = get_db_connection()
    patient = conn.execute('SELECT rowid, * FROM patients WHERE rowid = ?', (patient_id,)).fetchone()
    conn.close()
    if patient:
        return jsonify(dict(patient))
    return jsonify({'status': 'error', 'message': 'Patient not found'}), 404

@app.route('/update/<int:patient_id>', methods=['PUT'])
# @subscription_required
def update_patient(patient_id):
    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify({'status': 'error', 'message': 'Name is required'}), 400

    patient_name = data.get('name')
    try:   
         # Define allowed columns for the new schema
        allowed_columns = {
            'name', 'date_of_birth', 'adresse', 'age', 
            'antecedents_tabagiques', 'statut_implants', 
            'frequence_fil_dentaire', 'frequence_brossage', 'allergies'
        }

        # Filter out any old/invalid columns that might be sent
        filtered_data = {k: v for k, v in data.items() if k in allowed_columns}

        if not filtered_data:
            return jsonify({'status': 'error', 'message': 'No valid data to update'}), 400
        
        # Prepare SQL UPDATE statement
        set_clause = ", ".join([f"{k} = ?" for k in filtered_data.keys()])
        values = list(filtered_data.values())
        values.append(patient_id)  # For the WHERE clause
        
        conn = get_db_connection()
        conn.execute(f'UPDATE patients SET {set_clause} WHERE rowid = ?', values)
        conn.commit()
        conn.close()
        
        # send email because the patient is updated
        email_reception(data['name'], '', f'Cher medecin, certaines infos par rapport au patient {patient_name} ont été modifié', None, acteur_med)
        
        return jsonify({'status': 'success'})   
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def migrate_database():
    """
    Migrate the database to the new schema - removing medical vitals, adding dental fields + visit_date
    """
    conn = get_db_connection()
    
    try:
        # Check if migration is needed by looking for old columns
        cursor = conn.execute("PRAGMA table_info(patients)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Check if we still have old columns (indicating migration needed)
        old_columns = ['Poids', 'Taille', 'TA', 'T°', 'FC', 'PC', 'SaO2', 'hypothese_de_diagnostique', 'ordonnance', 'bilan']
        needs_migration = any(col in columns for col in old_columns)
        
        # Also check if visit_date column is missing
        if 'visit_date' not in columns:
            needs_migration = True
        
        if needs_migration:
            print("Starting database migration...")
            
            # Create backup table
            conn.execute('ALTER TABLE patients RENAME TO patients_backup')
            
            # Create new table with updated schema (dental-focused + visit_date)
            conn.execute('''CREATE TABLE patients (
                name TEXT NOT NULL, 
                date_of_birth DATE, 
                adresse TEXT, 
                age INTEGER,
                antecedents_tabagiques TEXT,
                statut_implants TEXT,
                frequence_fil_dentaire TEXT,
                frequence_brossage TEXT,
                allergies TEXT,
                visit_date DATE,
                created_at DATE
            )''')
            
            # Copy existing data (only the columns that exist in both tables)
            conn.execute('''INSERT INTO patients 
                (name, date_of_birth, adresse, age, created_at)
                SELECT name, date_of_birth, adresse, age, created_at
                FROM patients_backup''')
            
            # Drop backup table
            conn.execute('DROP TABLE patients_backup')
            
            print("Database migration completed successfully!")
        else:
            print("No migration needed - database is already up to date")
            
    except Exception as e:
        print(f"Migration error: {e}")
        # Rollback if there's an error
        try:
            conn.execute('DROP TABLE IF EXISTS patients')
            conn.execute('ALTER TABLE patients_backup RENAME TO patients')
        except:
            pass
        raise e
    finally:
        conn.commit()
        conn.close()

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'GET':
        # Check if user already has valid subscription
        conn = get_db_connection()
        subscription = conn.execute('''
            SELECT * FROM subscriptions 
            WHERE user_id = ? AND status IN ('active', 'incomplete', 'trialing')
            AND current_period_end >= date('now')
        ''', (session['user_id'],)).fetchone()
        conn.close()
        
        if subscription:
            return redirect(url_for('index'))
        
        return render_template('payment.html')
    
    # Handle payment processing
    try:
        data = request.get_json() if request.is_json else request.form
        payment_method_id = data.get('payment_method_id')
        
        if not payment_method_id:
            return jsonify({'status': 'error', 'message': 'Payment method required'}), 400
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        # Create or retrieve Stripe customer
        existing_subscription = conn.execute(
            'SELECT stripe_customer_id FROM subscriptions WHERE user_id = ?', 
            (session['user_id'],)
        ).fetchone()
        
        if existing_subscription and existing_subscription['stripe_customer_id']:
            customer_id = existing_subscription['stripe_customer_id']
            customer = stripe.Customer.retrieve(customer_id)
            # Update payment method
            stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
            stripe.Customer.modify(customer_id, invoice_settings={'default_payment_method': payment_method_id})
        else:
            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=user['email'],
                payment_method=payment_method_id,
                invoice_settings={'default_payment_method': payment_method_id}
            )
            customer_id = customer.id
        
        # Create subscription with immediate payment
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{'price': PRICE }],
            default_payment_method=payment_method_id,
            expand=['latest_invoice.payment_intent']
        )
        
        # Save subscription to database with the actual status from Stripe
        conn.execute('''
            INSERT OR REPLACE INTO subscriptions 
            (user_id, stripe_customer_id, stripe_subscription_id, status, current_period_start, current_period_end)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            customer_id,
            subscription.id,
            subscription.status,  # This will be 'active', 'incomplete', or 'trialing'
            datetime.fromtimestamp(subscription.current_period_start).date(),
            datetime.fromtimestamp(subscription.current_period_end).date()
        ))
        conn.commit()
        conn.close()
        
        # Return success with redirect
        return jsonify({
            'status': 'success',
            'subscription_status': subscription.status,
            'redirect': url_for('index')
        })
        
    except stripe.error.StripeError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Payment processing failed'}), 500
    
@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for subscription updates."""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = 'whsec_your_webhook_secret'  # Your webhook secret from Stripe
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Handle subscription events
    if event['type'] == 'invoice.payment_succeeded':
        subscription = event['data']['object']['subscription']
        update_subscription_status(subscription, 'active')
    elif event['type'] == 'invoice.payment_failed':
        subscription = event['data']['object']['subscription']
        update_subscription_status(subscription, 'past_due')
    elif event['type'] == 'customer.subscription.deleted':
        subscription_id = event['data']['object']['id']
        update_subscription_status(subscription_id, 'cancelled')
    
    return 'Success', 200

def update_subscription_status(subscription_id, status):
    """Update subscription status in database."""
    try:
        # Get subscription details from Stripe
        if status != 'cancelled':
            stripe_sub = stripe.Subscription.retrieve(subscription_id)
            conn = get_db_connection()
            conn.execute('''
                UPDATE subscriptions 
                SET status = ?, current_period_start = ?, current_period_end = ?
                WHERE stripe_subscription_id = ?
            ''', (
                status,
                datetime.fromtimestamp(stripe_sub.current_period_start).date(),
                datetime.fromtimestamp(stripe_sub.current_period_end).date(),
                subscription_id
            ))
        else:
            conn = get_db_connection()
            conn.execute('UPDATE subscriptions SET status = ? WHERE stripe_subscription_id = ?', 
                        (status, subscription_id))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating subscription status: {e}")

@app.route('/landing')
def landing():
    """Landing page that checks subscription status and redirects accordingly."""
    # Check if user has active subscription
    conn = get_db_connection()
    subscription = conn.execute('''
        SELECT * FROM subscriptions 
        WHERE user_id = ? AND status IN ('active', 'incomplete', 'trialing')
        AND current_period_end >= date('now')
    ''', (session['user_id'],)).fetchone()
    conn.close()
    
    if subscription:
        return redirect(url_for('index'))  # Go to main app
    else:
        return redirect(url_for('payment'))  # Go to payment

@app.route('/start')
def start():
    """Main entry point - redirects based on authentication status."""
    if 'user_id' in session:
        return redirect(url_for('landing'))  # Go to landing which handles subscription check
    else:
        return redirect(url_for('login'))  # Go to login

@app.route('/logout')
def logout():
    """Clear session and redirect to start."""
    # session.clear()
    return render_template('login.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)