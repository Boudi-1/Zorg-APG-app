from flask import Flask, request, render_template, send_file, redirect, url_for, jsonify, after_this_request, flash, current_app, Response, Blueprint
import os
import pdfplumber
import re
import openpyxl
import zipfile
from werkzeug.utils import secure_filename

# Define the blueprint at the top of the file
app2_blueprint = Blueprint('app2', __name__, template_folder='.', static_folder='static')

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "facturen_in_excel"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Vaste rijnummers voor afkortingen in de Excel-template
afkortingen_rijen = {
    "AOP": 3, "ML": 4, "BPFBA": 5, "VPBW": 6, "BEXC": 7, "BPFNTANT": 8, "BPFSGB": 9,
    "OOBW": 12, "OOBWU": 13, "COVAFB": 14, "OOAFB": 15, "FYSAFB": 16, "SFBIT": 17, 
    "WAGBIT": 18, "COVBIT": 19, "COVTIM": 20, "OOTIM": 21, "SWTIM": 22, "FBORAS": 23, 
    "SABBU": 26, "SABW": 27
}

def extract_data_from_pdf(file_path):
    """
    Extracts date and product amounts from PDF invoices.
    """
    data = {}

    try:
        with pdfplumber.open(file_path) as pdf:
            # Extract text from all pages
            full_text = " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            
            # 1. Extract date
            # Look for Factuurdatum
            datum_match = re.search(r"Factuurdatum:\s*(\d{2}\.\d{2}\.\d{4})", full_text)
            if datum_match:
                data["datum"] = datum_match.group(1)
            else:
                # Alternative date formats
                alt_datum_match = re.search(r"(\d{2}[-/.]\d{2}[-/.]\d{4})", full_text)
                if alt_datum_match:
                    data["datum"] = alt_datum_match.group(1)
                else:
                    data["datum"] = ""
            
            # 2. Extract amounts for each abbreviation
            for afkorting in afkortingen_rijen.keys():
                # Look for the abbreviation followed by an amount
                amount_match = re.search(rf"{afkorting}\s*[€]?\s*(\d+[.,]\d+)", full_text)
                if amount_match:
                    # Convert to float, replacing comma with dot if needed
                    amount_str = amount_match.group(1).replace(',', '.')
                    data[afkorting] = float(amount_str)
                else:
                    data[afkorting] = 0
    except Exception as e:
        print(f"Error extracting data from PDF {file_path}: {e}")
        # Provide default values for all fields
        data["datum"] = ""
        for afkorting in afkortingen_rijen.keys():
            data[afkorting] = 0
    
    return data

def fill_excel_template(excel_path, pdf_files, output_filename):
    """Vult de Excel-template met de geëxtraheerde data."""
    wb = openpyxl.load_workbook(excel_path, data_only=False)
    ws = wb.active

    # Verzamel data van alle PDF's
    factuur_data_list = [extract_data_from_pdf(file) for file in pdf_files]

    for col_index, factuur_data in enumerate(factuur_data_list, start=2):  # Begin in kolom B
        col_letter = openpyxl.utils.get_column_letter(col_index)
        
        # Vul datum in rij 2
        ws[f"{col_letter}2"] = factuur_data.get("datum", "")

        # Vul bedragen in voor alle gedefinieerde afkortingen
        for afkorting, rij in afkortingen_rijen.items():
            if afkorting in factuur_data:
                ws[f"{col_letter}{rij}"] = factuur_data[afkorting]

    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    wb.save(output_path)
    return output_path

@app2_blueprint.route('/')
def index():
    return render_template('app2/index.html')

@app2_blueprint.route('/upload', methods=['POST'])
def upload_files():
    """Verwerk meerdere folders en hun bestanden."""
    uploaded_files = request.files.getlist("files")

    if not uploaded_files:
        return jsonify({"error": "Geen bestanden ontvangen."}), 400

    folders = {}
    for file in uploaded_files:
        folder_name = file.filename.split('/')[0]  # Pak de mapnaam
        if folder_name not in folders:
            folders[folder_name] = {"excel": None, "pdf_files": []}

        if file.filename.endswith(".xlsx") or file.filename.endswith(".xls"):
            folders[folder_name]["excel"] = file
        elif file.filename.endswith(".pdf"):
            folders[folder_name]["pdf_files"].append(file)

    processed_files = []
    for folder_name, files in folders.items():
        if files["excel"] and files["pdf_files"]:
            folder_path = os.path.join(UPLOAD_FOLDER, secure_filename(folder_name))
            os.makedirs(folder_path, exist_ok=True)

            excel_path = os.path.join(folder_path, secure_filename(files["excel"].filename))
            files["excel"].save(excel_path)

            pdf_paths = []
            for pdf_file in files["pdf_files"]:
                pdf_path = os.path.join(folder_path, secure_filename(pdf_file.filename))
                pdf_file.save(pdf_path)
                pdf_paths.append(pdf_path)

            output_filename = f"{folder_name}_verwerkt.xlsx"
            output_path = fill_excel_template(excel_path, pdf_paths, output_filename)
            processed_files.append(output_path)

    # Maak een ZIP-bestand met alle ingevulde Excel-bestanden
    zip_path = os.path.join(OUTPUT_FOLDER, "facturen_ingevuld.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in processed_files:
            zipf.write(file, os.path.basename(file))

    # Verwerk alle bestanden en maak een ZIP
    process_all_files(folders, OUTPUT_FOLDER)
    
    # Controleer of we in de hoofdapplicatie draaien of in een subapplicatie
    if 'app2_success' in url_for.__globals__['current_app'].view_functions:
        # We draaien in de hoofdapplicatie
        return redirect('/app2/success?folders=' + ",".join(folders.keys()))
    else:
        # We draaien in de subapplicatie
        pass  # Voeg hier de juiste code toe
    return redirect(url_for('success', folders=",".join(folders.keys())))

@app2_blueprint.route('/success')
def success():
    """Toon de pagina met de verwerkte mappen en downloadknop."""
    try:
        folders = request.args.get("folders", "")
        folder_list = folders.split(",") if folders else []
        
        return render_template('success.html', folders=folder_list)
    except Exception as e:
        print(f"Error in success function: {e}")
        flash(f"Er is een fout opgetreden: {str(e)}", "error")
        return redirect(url_for('app2.index'))

@app2_blueprint.route('/download_verwerkt')
def download_verwerkt():
    """Download het verwerkte bestand"""
    # Pad naar het verwerkte bestand
    try:
        # Use a try/except block to handle the case where there's no application context
        try:
            file_path = os.path.join(current_app.root_path, 'app2', 'data', 'verwerkt.xlsx')
        except RuntimeError:
            # Fallback if there's no application context
            file_path = os.path.join('app2', 'data', 'verwerkt.xlsx')
        
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            # Try alternative locations
            alternative_paths = [
                os.path.join('data', 'verwerkt.xlsx'),
                os.path.join('app2', 'data', 'verwerkt.xlsx'),
                os.path.join('facturen_in_excel', 'verwerkt.xlsx')
            ]
            
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    file_path = alt_path
                    print(f"Found file at alternative location: {file_path}")
                    break
            else:
                print("File not found at any location")
                return "Fout: Het bestand 'verwerkt.xlsx' is niet gevonden.", 404
        
        # Send the file
        return send_file(file_path, as_attachment=True, download_name='verwerkt.xlsx')
    except Exception as e:
        print(f"Error in download_verwerkt function: {e}")
        return f"Er is een fout opgetreden bij het downloaden: {str(e)}", 500

def process_all_files(folders, output_folder):
    """Process all files in the specified folders and save results to output_folder."""
    import os
    import shutil
    from datetime import datetime
    
    print(f"Processing files from folders: {folders}")
    print(f"Output folder: {output_folder}")
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Process each folder
    for folder_name, folder_data in folders.items():
        print(f"Processing folder: {folder_name}")
        
        # Save the original Excel file
        if 'excel' in folder_data:
            excel_file = folder_data['excel']
            original_excel_path = os.path.join(output_folder, excel_file.filename.split('/')[-1])
            excel_file.save(original_excel_path)
            print(f"Saved original Excel file: {original_excel_path}")
            
            # Create a copy of the Excel file with "_verwerkt" suffix
            processed_excel_path = os.path.join(output_folder, f"{folder_name}_verwerkt.xlsx")
            shutil.copy2(original_excel_path, processed_excel_path)
            print(f"Created processed Excel file by copying: {processed_excel_path}")
        
        # Save PDF files
        if 'pdf_files' in folder_data:
            for pdf_file in folder_data['pdf_files']:
                pdf_filename = pdf_file.filename.split('/')[-1]
                pdf_path = os.path.join(output_folder, f"{folder_name}_{pdf_filename}")
                pdf_file.save(pdf_path)
                print(f"Saved PDF file: {pdf_path}")
    
    # List all files in the output folder after processing
    print("Files in output folder after processing:")
    for file in os.listdir(output_folder):
        file_path = os.path.join(output_folder, file)
        mod_time = os.path.getmtime(file_path)
        print(f"  - {file} (Modified: {mod_time})")
    
    print("All files processed successfully")
    return True

def static_files(filename):
    """Serve static files from the facturen_in_excel directory."""
    import os
    from flask import send_from_directory, current_app
    
    # Get the current directory
    current_dir = os.getcwd()
    
    # Define the output folder path
    output_folder = os.path.join(current_dir, 'facturen_in_excel')
    
    print(f"Serving static file: {filename} from {output_folder}")
    
    # Serve the file directly from the directory
    return send_from_directory(output_folder, filename, as_attachment=True)

@app2_blueprint.route('/download')
def download():
    """Let the user download the ZIP file."""
    # Use the correct path for the output folder
    OUTPUT_FOLDER = 'facturen_in_excel'  # Adjust this to the correct path
    zip_path = os.path.join(OUTPUT_FOLDER, "facturen_ingevuld.zip")

    if not os.path.exists(zip_path):
        return "Error: The file does not exist. Process invoices first.", 404
    
    @after_this_request
    def cleanup(response):
        """Cleans up folders after processing, after the response has been fully sent."""
        try:
            print("Download prepared.")
        except Exception as e:
            print(f"Error preparing download: {e}")
        
        return response
    
    # Send the ZIP file to the user
    return send_file(zip_path, as_attachment=True, download_name="facturen_ingevuld.zip")

def register_app2(app):
    """Registreert app2 bij de hoofdapplicatie."""
    # Definieer de paden relatief aan de app root
    UPLOAD_FOLDER = os.path.join(app.root_path, 'app2', 'uploads')
    OUTPUT_FOLDER = os.path.join(app.root_path, 'app2', 'facturen_in_excel')
    
    # Maak de mappen aan als ze nog niet bestaan
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Sla deze paden op in de app config voor gebruik in andere functies
    app.config['APP2_UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['APP2_OUTPUT_FOLDER'] = OUTPUT_FOLDER
    
    # Registreer de blueprint met een url_prefix
    app.register_blueprint(app2_blueprint, url_prefix='/app2')
    
    # Voeg een directe download route toe aan de hoofdapplicatie
    @app.route('/app2/download')
    def app2_download():
        """Directe implementatie van download functionaliteit in main.py"""
        zip_path = os.path.join(OUTPUT_FOLDER, "facturen_ingevuld.zip")
        
        if not os.path.exists(zip_path):
            # Check alternative locations
            alternative_paths = [
                os.path.join('facturen_in_excel', "facturen_ingevuld.zip"),
                os.path.join(app.root_path, 'facturen_in_excel', "facturen_ingevuld.zip")
            ]
            
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    zip_path = alt_path
                    break
            else:
                return "Fout: Het bestand bestaat niet. Verwerk eerst facturen.", 404
        
        # Stuur het ZIP-bestand naar de gebruiker
        return send_file(zip_path, as_attachment=True, download_name="facturen_ingevuld.zip")
    
    print("App2 succesvol geregistreerd")
    return True

@app2_blueprint.route('/debug')
def debug():
    """Debug route to check template and file paths"""
    import os
    import sys
    
    # Get information about the environment
    cwd = os.getcwd()
    python_path = sys.path
    
    # Check template locations
    template_locations = []
    try:
        from flask import current_app
        for blueprint_name, blueprint in current_app.blueprints.items():
            if hasattr(blueprint, 'template_folder'):
                template_locations.append(f"{blueprint_name}: {blueprint.template_folder}")
    except Exception as e:
        template_locations.append(f"Error getting blueprint info: {e}")
    
    # Check if success.html exists in various locations
    template_files = []
    possible_template_paths = [
        'success.html',
        'app2/success.html',
        'templates/success.html',
        'templates/app2/success.html'
    ]
    
    for path in possible_template_paths:
        exists = os.path.exists(path)
        template_files.append(f"{path}: {'Exists' if exists else 'Not found'}")
    
    return f"""
    <h1>Debug Information</h1>
    
    <h2>Current Working Directory</h2>
    <p>{cwd}</p>
    
    <h2>Python Path</h2>
    <ul>
        {"".join(f"<li>{path}</li>" for path in python_path)}
    </ul>
    
    <h2>Blueprint Template Locations</h2>
    <ul>
        {"".join(f"<li>{loc}</li>" for loc in template_locations)}
    </ul>
    
    <h2>Template Files</h2>
    <ul>
        {"".join(f"<li>{file}</li>" for file in template_files)}
    </ul>
    """

if __name__ == "__main__":
    # Create a Flask app for standalone testing
    app = Flask(__name__)
    app.register_blueprint(app2_blueprint)
    app.run(debug=True)





