from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
import zipfile
from werkzeug.utils import secure_filename
from process import determine_variant, process_documents

app = Flask(__name__, template_folder='.')

UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed_documents"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    # Add debug print to see where files are being saved
    import os
    print(f"Current working directory: {os.getcwd()}")
    
    files = request.files.getlist("files")

    if not files:
        return "Geen bestanden ontvangen.", 400

    # Sla bestanden op
    excel_path = None
    word_folder = os.path.join(UPLOAD_FOLDER, "word_docs")
    os.makedirs(word_folder, exist_ok=True)

    for file in files:
        filename = secure_filename(file.filename)
        if filename.endswith(".xlsx"):
            excel_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(excel_path)
        elif filename.endswith(".docx"):
            file.save(os.path.join(word_folder, filename))

    if not excel_path:
        return "Excel bestand ontbreekt!", 400

    # Varianten bepalen en documenten verwerken
    selected_variants = determine_variant(excel_path)
    process_documents(word_folder, PROCESSED_FOLDER, selected_variants)

    # ZIP-bestand maken
    zip_path = os.path.join(PROCESSED_FOLDER, "verwerkte_documenten.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for root, dirs, files in os.walk(PROCESSED_FOLDER):
            for file in files:
                if file.endswith('.docx'):
                    zipf.write(os.path.join(root, file), arcname=file)

    # Controleer of we in de hoofdapplicatie draaien of in een subapplicatie
    if 'app1_success' in url_for.__globals__['current_app'].view_functions:
        # We draaien in de hoofdapplicatie
        return redirect('/app1/success')
    else:
        # We draaien in de subapplicatie
        return redirect(url_for('success'))

@app.route('/success')
def success():
    return render_template('success.html')

def is_main_app():
    """Check if the application is running as the main app or as a subapp."""
    from flask import current_app
    return current_app.name == 'main'

@app.route('/download')
def download():
    import os
    import zipfile
    import time
    from flask import flash, redirect, url_for, send_file, current_app
    
    # Get the current directory (which is app1)
    current_dir = os.getcwd()
    
    # Define paths with absolute paths
    processed_folder = os.path.join(current_dir, 'processed_documents')
    zip_filename = 'verwerkte_documenten.zip'
    zip_path = os.path.join(processed_folder, zip_filename)
    
    print(f"Current directory: {current_dir}")
    print(f"Looking for files in: {processed_folder}")
    
    # List the contents of the processed_documents folder
    if os.path.exists(processed_folder):
        print(f"Contents of processed_documents directory:")
        for item in os.listdir(processed_folder):
            print(f"  - {item}")
    
    # Check for files in the processed_documents folder
    files_to_zip = []
    if os.path.exists(processed_folder):
        for root, _, files in os.walk(processed_folder):
            for file in files:
                # Skip existing zip files to avoid including them
                if file.endswith('.zip'):
                    continue
                file_path = os.path.join(root, file)
                files_to_zip.append(file_path)
                print(f"Found file to zip: {file_path}")
    
    # Create the zip file
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in files_to_zip:
                # Add file to zip with just the filename (not the full path)
                arcname = os.path.basename(file)
                zipf.write(file, arcname)
                print(f"Added to zip: {file} as {arcname}")
        
        print(f"Zip file created at: {zip_path}")
        
        # Check if zip was created successfully
        if os.path.exists(zip_path):
            print(f"Sending file: {zip_path}")
            
            # Force download as attachment with specific mimetype
            return send_file(
                zip_path,
                as_attachment=True,
                download_name='verwerkte_documenten.zip',
                mimetype='application/zip'
            )
        else:
            print(f"Zip file not found at: {zip_path}")
            flash('Fout bij het maken van het zip-bestand', 'error')
            return redirect(url_for('app1_index') if current_app.name == 'main' else url_for('index'))
    
    except Exception as e:
        print(f"Error creating zip file: {str(e)}")
        flash(f'Fout bij het maken van het zip-bestand: {str(e)}', 'error')
        return redirect(url_for('app1_index') if current_app.name == 'main' else url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)



