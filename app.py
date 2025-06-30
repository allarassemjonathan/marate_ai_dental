from flask import Flask, render_template, request, jsonify
import sqlite3
from fpdf import FPDF
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from flask import send_file
import io
from datetime import datetime
import requests

app = Flask(__name__)
DATABASE = 'patients.db'

# Set up the SMTP server
smtp_server = "smtp.gmail.com"
smtp_port = 587

your_email = "jonathanjerabe@gmail.com"
your_password = "ajrn mros lkzm urnu"

acteur_inf = "jonathanjerabe@gmail.com"
acteur_med = "jonathanjerabe@gmail.com"

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
        self.cell(90, line_height, "N° Order Medical: B 1506", ln=1)
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
    
    # Create table with new dental-focused schema
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
    
    # Keep visits table unchanged
    conn.execute('''CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER,
        visit_date DATE, notes TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(rowid)
    )''')
    
    conn.commit()
    conn.close()
    
    # Run migration if needed (this will handle existing databases)
    migrate_database()

@app.route('/')
def index():
    init_db()
    return render_template('index.html')

@app.route('/search')
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
def delete(rowid):
    conn = get_db_connection()
    conn.execute('DELETE FROM patients WHERE rowid = ?', (rowid,))
    conn.commit()
    conn.close()    
    return jsonify({'status': 'deleted'})

@app.route('/patient/<int:patient_id>')
def patient_detail(patient_id):
    conn = get_db_connection()
    patient = conn.execute('SELECT rowid, * FROM patients WHERE rowid = ?', (patient_id,)).fetchone()
    visits = conn.execute('SELECT * FROM visits WHERE patient_id = ?', (patient_id,)).fetchall()
    conn.close()
    return render_template('patient.html', patient=patient, visits=visits) if patient else ("Patient not found", 404)

@app.route('/get_patient/<int:patient_id>')
def get_patient(patient_id):
    conn = get_db_connection()
    patient = conn.execute('SELECT rowid, * FROM patients WHERE rowid = ?', (patient_id,)).fetchone()
    conn.close()
    if patient:
        return jsonify(dict(patient))
    return jsonify({'status': 'error', 'message': 'Patient not found'}), 404

@app.route('/update/<int:patient_id>', methods=['PUT'])
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

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)