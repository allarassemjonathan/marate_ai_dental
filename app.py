from flask import Flask, render_template, request, jsonify
import sqlite3
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from flask import send_file
import io
from datetime import datetime

app = Flask(__name__)
DATABASE = 'patients.db'

# Set up the SMTP server
smtp_server = "smtp.gmail.com"
smtp_port = 587
your_email = "jonathanjerabe@gmail.com"
your_password = "ajrn mros lkzm urnu"

acteur_inf = "jonathanjerabe@gmail.com"
acteur_med = "cablarenaissance@gmail.com"
from reportlab.lib.utils import ImageReader
import requests
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
import requests
def create_invoice_pdf(patient, items):
    """
    Create invoice PDF with patient info and itemized services
    SOC 2 Compliant: All processing done in memory, no temporary files
    """
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor=colors.HexColor('#06b6d4')
    )
    
    # Style for emphasized text
    emphasis_style = ParagraphStyle(
        'Emphasis',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#06b6d4'),
        alignment=1,  # Center alignment
        spaceAfter=20,
        spaceBefore=10
    )
    
    # Styles for left and right alignment
    left_style = ParagraphStyle(
        'LeftAlign',
        parent=styles['Normal'],
        alignment=0,  # Left alignment
        fontSize=10
    )
    
    right_style = ParagraphStyle(
        'LeftAlign',
        parent=styles['Normal'],
        alignment=0,  # Right alignment
        fontSize=10
    )
    
    # Download and add logo
    try:
        logo_url = "https://allarassemjonathan.github.io/marate_white.png"
        response = requests.get(logo_url, timeout=10)
        if response.status_code == 200:
            # Create ImageReader from the response content
            logo_buffer = io.BytesIO(response.content)
            
            # Create header table with logo and title
            header_table_data = [
                [
                    # Logo cell - pass the buffer directly to Image
                    Image(logo_buffer, width=1.7*inch, height=0.4*inch),
                    # Title cell
                    Paragraph("Devis Cabinet la Renaissance", title_style)
                ]
            ]
            
            header_table = Table(header_table_data, colWidths=[2.5*inch, 4.5*inch])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),    # Logo left aligned
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Title center aligned
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('GRID', (0, 0), (-1, -1), 0, colors.white),  # Invisible borders
            ]))
            
            elements.append(header_table)
        else:
            # Fallback if logo can't be loaded
            elements.append(Paragraph("Devis Cabinet dentaire la Renaissance", title_style))
            
    except Exception as e:
        print(f"Error loading logo: {e}")
        # Fallback if logo can't be loaded
        elements.append(Paragraph("Devis Cabinet dentaire La Renaissance", title_style))
    
    elements.append(Spacer(1, 20))
    
    # Create clinic and patient info content
    clinic_info = f"""
    <b>Cabinet dentaire la renaissance</b><br/>
    Kantara Sacko<br/>
    Adresse Rue 22, Medina Dakar<br/>
    cablarenaissance@gmail.com<br/>
    (+221) 78 635 95 65<br/>
    Ordre des Chirurgiens Dentistes/ N° Reference etablissement: B 1506
    """
    
    patient_info = f"""
    <b>Informations Patient</b><br/>
    Nom: {patient['name']}<br/>
    Adresse: {patient['adresse'] or 'N/A'}<br/>
    Date de naissance: {patient['date_of_birth'] or 'N/A'}<br/>
    Date de facture: {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>
    """
    
    # Create a table to position clinic info (right) and patient info (left)
    info_table_data = [
        [
            Paragraph(patient_info, left_style),
            Paragraph(clinic_info, right_style)
        ]
    ]
    
    info_table = Table(info_table_data, colWidths=[3.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        # Remove borders
        ('GRID', (0, 0), (-1, -1), 0, colors.white),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 30))
    
    # Create services table data
    table_data = [['Article', 'Quantité', 'Prix Unitaire', 'Prix Total', 'Date']]
    total_amount = 0
    
    for item in items:
        quantity = int(str(item['quantity']).replace(' ', ''))
        price = int(str(item['price']).replace(' ', ''))
        total_price = quantity * price
        total_amount += total_price
        
        table_data.append([
            str(item['name']),
            f"{quantity}",
            f"{price} Fcfa",
            f"{total_price} Fcfa",
            f"{datetime.now().strftime('%d/%m/%Y')}"
        ])
    
    # Add total row spanning 4 columns with total in the last column
    table_data.append(['', '', '', 'TOTAL:', f"{total_amount} Fcfa"])
    
    # Create and style services table
    services_table = Table(table_data, colWidths=[2.2*inch, 0.8*inch, 1.1*inch, 1.1*inch, 1.0*inch])
    services_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#06b6d4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Article names left aligned
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),  # Reduced header font size
        ('FONTSIZE', (0, 1), (-1, -1), 9),  # Reduced body font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(services_table)
    elements.append(Spacer(1, 20))
    
    # Calculate insurance breakdown
    insurance_coverage = 0.80  # 80%
    insurance_amount = int(total_amount * insurance_coverage)
    patient_amount = total_amount - insurance_amount
    
    # Create insurance breakdown table
    breakdown_data = [
        ['Total', 'Part Assureur (80%)', 'Part Patient (20%)'],
        [f"{total_amount} Fcfa", f"{insurance_amount} Fcfa", f"{patient_amount} Fcfa"]
    ]
    
    breakdown_table = Table(breakdown_data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
    breakdown_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#06b6d4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
        ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        # Highlight patient amount column
        ('BACKGROUND', (2, 1), (2, 1), colors.HexColor('#FFE4E1')),
        ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#DC143C')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(breakdown_table)
    
    # Add emphasized patient payment amount
    elements.append(Spacer(1, 15))
    patient_payment_text = f"<b>MONTANT À PAYER PAR LE PATIENT: {patient_amount} Fcfa</b>"
    elements.append(Paragraph(patient_payment_text, emphasis_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer

@app.route('/generate_invoice/<int:patient_id>', methods=['POST'])
def generate_invoice(patient_id):
    """
    Generate invoice PDF for a patient with itemized services
    SOC 2 Compliant: Validates input, handles errors gracefully, no external data transmission
    """
    try:
        # Get invoice items from request
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({'status': 'error', 'message': 'Invoice items are required'}), 400
        
        items = data['items']
        
        # Validate each item has required fields
        for item in items:
            if not all(key in item for key in ['name', 'quantity', 'price']):
                return jsonify({'status': 'error', 'message': 'Each item must have name, quantity, and price'}), 400
            
            # Validate numeric fields
            try:
                float(item['quantity'])
                float(item['price'])
            except (ValueError, TypeError):
                return jsonify({'status': 'error', 'message': 'Quantity and price must be numeric'}), 400
        
        # Get patient information
        conn = get_db_connection()
        patient = conn.execute('SELECT rowid, * FROM patients WHERE rowid = ?', (patient_id,)).fetchone()
        conn.close()
        
        if not patient:
            return jsonify({'status': 'error', 'message': 'Patient not found'}), 404
        
        # Generate PDF
        pdf_buffer = create_invoice_pdf(patient, items)
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'invoice_{patient["name"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        # Log error securely without exposing sensitive data
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