from flask import Flask, request, render_template, send_file, redirect, url_for, flash
import os
import zipfile
import pandas as pd
import re
import docx2txt
from docx import Document
from werkzeug.utils import secure_filename
import shutil
import subprocess
import time

app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'een_willekeurige_geheime_string'  # Nodig voor flash messages

# Mappen definiëren
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Mappen aanmaken als ze niet bestaan
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def extract_dossiernummer(doc_path):
    """Haalt het dossiernummer uit een Word document"""
    try:
        full_text = docx2txt.process(doc_path)
        matches = re.findall(r'Dossier:\s*(\d{8,9})', full_text, re.MULTILINE)
        return matches[-1].strip().zfill(8) if matches else None
    except Exception as e:
        print(f"Fout bij extractie dossiernummer: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    """Hoofdpagina om bestanden te uploaden"""
    if request.method == 'POST':
        # Maak uploads map leeg voor nieuwe bestanden
        shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # Check of bestanden zijn geüpload
        if 'files' not in request.files:
            flash('Geen bestanden geselecteerd', 'danger')
            return redirect(request.url)
            
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or uploaded_files[0].filename == '':
            flash('Geen bestanden geselecteerd', 'danger')
            return redirect(request.url)
            
        # Sla alle geüploade bestanden op
        for file in uploaded_files:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        flash('Bestanden succesvol geüpload', 'success')
        return process_and_zip_files()

    return render_template('index.html')

def process_document_directly(excel_path, word_path, output_path):
    """Verwerk documenten direct zonder subprocess aanroep naar main.py"""
    try:
        # Import functie uit main.py
        from main import process_document
        
        # Direct document verwerken
        success = process_document(excel_path, word_path, output_path)
        return success, None if success else "Fout tijdens verwerking"
    except Exception as e:
        return False, str(e)

def process_and_zip_files():
    """Verwerk alle Excel- en Word-bestanden en maak een ZIP bestand"""
    # Maak processed map leeg
    shutil.rmtree(PROCESSED_FOLDER, ignore_errors=True)
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)

    excel_files, word_files = {}, {}
    processed_count = 0
    error_count = 0

    # Verzamel alle Excel- en Word-bestanden
    for root, dirs, files in os.walk(UPLOAD_FOLDER):
        for f in files:
            full_path = os.path.join(root, f)
            if f.lower().endswith(('.xlsx', '.xls')):
                excel_files[f] = full_path
            elif f.lower().endswith(('.docx')):
                word_files[f] = full_path

    # Als er geen bestanden zijn, geef een foutmelding
    if not excel_files or not word_files:
        flash('Geen Excel- of Word-bestanden gevonden', 'danger')
        return redirect(url_for('upload_files'))

    # Loop door alle Excel-bestanden
    for excel_file, excel_path in excel_files.items():
        try:
            df_excel = pd.read_excel(excel_path, header=None)
            
            # Eerst proberen of het een automatisch dossier is
            try:
                dossiernummer = str(df_excel.iat[0, 0]).strip()
            except Exception as e:
                print(f"Kan dossiernummer niet uit Excel halen: {e}")
                dossiernummer = None
            
            # Voor bulk verwerking, vind het bijbehorende Word-bestand
            matched_word = None
            if dossiernummer:
                for word_file, word_path in word_files.items():
                    doc_nummer = extract_dossiernummer(word_path)
                    if doc_nummer and doc_nummer == dossiernummer:
                        matched_word = word_path
                        break
            
            # Als er geen match is, gebruik dan gewoon beide bestanden als we maar één Excel en één Word bestand hebben
            if not matched_word and len(excel_files) == 1 and len(word_files) == 1:
                matched_word = list(word_files.values())[0]
                print(f"Geen dossiernummer match, maar slechts één Word bestand beschikbaar. Gebruik: {os.path.basename(matched_word)}")

            if matched_word:
                # Bepaal de naam van het outputbestand
                output_name = f"processed_{os.path.basename(matched_word)}"
                output_path = os.path.join(PROCESSED_FOLDER, output_name)
                
                # Verwerk het document direct (geen subprocess meer)
                print(f"Verwerken van Excel: {excel_file} en Word: {os.path.basename(matched_word)}")
                
                success, error_msg = process_document_directly(excel_path, matched_word, output_path)
                
                if success:
                    processed_count += 1
                    print(f"Document succesvol verwerkt: {output_path}")
                else:
                    error_count += 1
                    print(f"Fout bij verwerking van {excel_file}: {error_msg}")
                    flash(f'Fout bij verwerking van {excel_file}: {error_msg}', 'danger')
            else:
                print(f"Geen bijpassend Word-document gevonden voor Excel-bestand {excel_file}")
                flash(f'Geen bijpassend Word-document gevonden voor {excel_file}', 'warning')

        except Exception as e:
            error_count += 1
            print(f"Fout bij verwerken van {excel_file}: {str(e)}")
            flash(f'Fout bij verwerken van {excel_file}: {str(e)}', 'danger')

    # Als er helemaal niets is verwerkt, ga terug naar de uploadpagina
    if processed_count == 0:
        flash('Geen documenten konden worden verwerkt', 'danger')
        return redirect(url_for('upload_files'))

    # Maak een ZIP-bestand van de verwerkte documenten
    zip_filename = "processed_documents.zip"
    zip_path = os.path.join(PROCESSED_FOLDER, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in os.listdir(PROCESSED_FOLDER):
            file_path = os.path.join(PROCESSED_FOLDER, file)
            if file.endswith(".docx") and os.path.isfile(file_path):
                zipf.write(file_path, os.path.basename(file_path))

    # Stuur statistieken naar de gebruiker
    flash(f'{processed_count} documenten succesvol verwerkt', 'success')
    if error_count > 0:
        flash(f'{error_count} documenten konden niet worden verwerkt', 'danger')

    # Controleer of we in de hoofdapplicatie draaien of in een subapplicatie
    if 'app3_success' in url_for.__globals__['current_app'].view_functions:
        # We draaien in de hoofdapplicatie
        return redirect(f'/app3/success?zip_filename={zip_filename}')
    else:
        # We draaien in de subapplicatie
        return render_template('success.html', zip_filename=zip_filename)

@app.route('/download/<filename>')
def download_file(filename):
    """Download een bestand uit de processed map"""
    # Get the current directory
    current_dir = os.getcwd()
    
    # Define possible paths for the processed file
    possible_paths = [
        os.path.join(current_dir, 'processed', filename),
        os.path.join(current_dir, 'app3', 'processed', filename),
        os.path.join(current_dir, 'app3', filename)
    ]
    
    print(f"Current directory: {current_dir}")
    print(f"Looking for file: {filename}")
    
    # Check if the file exists in any of the possible locations
    file_path = None
    for path in possible_paths:
        print(f"Checking path: {path}")
        if os.path.exists(path):
            file_path = path
            print(f"File found at: {file_path}")
            break
    
    # If file not found, check if there are any processed files in the directories
    if not file_path:
        print("File not found in expected locations. Searching for any processed files...")
        for folder in ['processed', os.path.join('app3', 'processed'), 'app3']:
            folder_path = os.path.join(current_dir, folder)
            if os.path.exists(folder_path):
                print(f"Checking folder: {folder_path}")
                for file in os.listdir(folder_path):
                    if file.startswith('verwerkt_') or 'processed' in file:
                        file_path = os.path.join(folder_path, file)
                        print(f"Found processed file: {file_path}")
                        break
            if file_path:
                break
    
    # If still no file found, create a test file
    if not file_path:
        print("No processed files found. Creating a test file.")
        processed_folder = os.path.join(current_dir, 'app3', 'processed')
        os.makedirs(processed_folder, exist_ok=True)
        test_file_path = os.path.join(processed_folder, 'test_file.txt')
        with open(test_file_path, 'w') as f:
            f.write('This is a test file created because no processed files were found.')
        file_path = test_file_path
    
    # Send the file
    try:
        if os.path.exists(file_path):
            print(f"Sending file: {file_path}")
            
            # Get the filename from the path
            download_name = os.path.basename(file_path)
            
            # Determine the mimetype based on the file extension
            mimetype = None
            if download_name.endswith('.docx'):
                mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif download_name.endswith('.doc'):
                mimetype = 'application/msword'
            elif download_name.endswith('.pdf'):
                mimetype = 'application/pdf'
            elif download_name.endswith('.txt'):
                mimetype = 'text/plain'
            
            # Force download as attachment
            return send_file(
                file_path,
                as_attachment=True,
                download_name=download_name,
                mimetype=mimetype
            )
        else:
            print(f"File not found at: {file_path}")
            flash('Bestand niet gevonden', 'error')
            return redirect(url_for('app3_index') if current_app.name == 'main' else url_for('index'))
    
    except Exception as e:
        print(f"Error sending file: {str(e)}")
        flash(f'Fout bij het downloaden van het bestand: {str(e)}', 'error')
        return redirect(url_for('app3_index') if current_app.name == 'main' else url_for('index'))

@app.route('/upload_single', methods=['POST'])
def upload_single_files():
    """Endpoint om een enkel Excel- en Word-bestand te verwerken"""
    if 'excel_file' not in request.files or 'word_file' not in request.files:
        flash('Beide bestanden moeten worden geüpload', 'danger')
        return redirect(url_for('upload_files'))
    
    excel_file = request.files['excel_file']
    word_file = request.files['word_file']
    
    if excel_file.filename == '' or word_file.filename == '':
        flash('Geen bestand geselecteerd', 'danger')
        return redirect(url_for('upload_files'))
    
    # Bestanden opslaan
    excel_filename = secure_filename(excel_file.filename)
    word_filename = secure_filename(word_file.filename)
    
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
    word_path = os.path.join(app.config['UPLOAD_FOLDER'], word_filename)
    
    excel_file.save(excel_path)
    word_file.save(word_path)
    
    # Verwerk het document
    output_filename = f"verwerkt_{word_filename}"
    output_path = os.path.join(PROCESSED_FOLDER, output_filename)
    
    try:
        # Maak processed map als die niet bestaat
        os.makedirs(PROCESSED_FOLDER, exist_ok=True)
        
        # Direct verwerken zonder subprocess
        success, error_msg = process_document_directly(excel_path, word_path, output_path)
        
        if success:
            flash('Document succesvol verwerkt!', 'success')
            # Controleer of we in de hoofdapplicatie draaien of in een subapplicatie
            if 'app3_success' in url_for.__globals__['current_app'].view_functions:
                # We draaien in de hoofdapplicatie
                return redirect(f'/app3/success?zip_filename={output_filename}')
            else:
                # We draaien in de subapplicatie
                return render_template('success.html', zip_filename=output_filename)
        else:
            flash(f'Fout bij verwerken: {error_msg}', 'danger')
            return redirect(url_for('upload_files'))
    except Exception as e:
        flash(f'Fout bij verwerken: {str(e)}', 'danger')
        return redirect(url_for('upload_files'))

if __name__ == '__main__':
    app.run(debug=True)