from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from datetime import datetime
import chardet
import io
import json
from create_energy_audit_pdf import create_energy_audit_pdf
import os
import glob
import openpyxl

app = Flask(__name__)

# Ensure data directories exist
os.makedirs('data/uploaded_data', exist_ok=True)
os.makedirs('data/example_data', exist_ok=True)

def get_latest_file(state):
    """Get the latest uploaded file for a given state"""
    pattern = f'data/uploaded_data/uploaded_file_{state}_*.csv'
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def save_file(df, state):
    """Save a dataframe with timestamp in filename"""
    current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'data/uploaded_data/uploaded_file_{state}_{current_date}.csv'
    df.to_csv(filename, index=False)
    return filename

@app.route('/')
def index():
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M:%S')
    return render_template('dashboard.html', current_date=current_date, current_time=current_time)

@app.route('/upload', methods=['POST'])
def upload_file():
    files = {
        'standby': request.files.get('file-standby'),
        'ready': request.files.get('file-ready'),
        'process': request.files.get('file-process')
    }
    data_store = {}

    for state, file in files.items():
        if file:
            try:
                # Prüfe die Dateiendung
                filename = file.filename.lower()
                if filename.endswith(('.xls', '.xlsx')):
                    # Excel-Datei verarbeiten
                    df = pd.read_excel(file)
                else:
                    # CSV-Datei verarbeiten
                    raw_data = file.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding']
                    file.seek(0)  # Reset the file pointer to the beginning
                    df = pd.read_csv(io.StringIO(raw_data.decode(encoding)), delimiter=',', quotechar='"')

                # Debugging: Überprüfen der eingelesenen Daten
                print(f"Original DataFrame ({state}):")
                print(df.head())

                # Ersetze Kommas durch Punkte für die numerischen Konvertierungen
                df = df.replace(',', '.', regex=True)

                # Konvertiere alle Werte zu numerischen, nicht konvertierbare werden zu NaN
                df = df.apply(pd.to_numeric, errors='coerce')

                # Debugging: Überprüfen der konvertierten Daten
                print(f"DataFrame nach Konvertierung zu numerischen Werten ({state}):")
                print(df.head())

                # Entferne Spalten, die nur NaN enthalten
                df.dropna(axis=1, how='all', inplace=True)

                # Bestimme die Spalte mit den höchsten Werten als Gesamtenergiespalte
                total_energy_column = df.sum().idxmax()
                print(f"Bestimmte Gesamtenergiespalte ({state}): {total_energy_column}")

                if total_energy_column in df.columns:
                    # Berechnung von "Sonstige [W]"
                    def calculate_other(row, total_col, component_cols):
                        total = row[total_col]
                        components_sum = row[component_cols].sum()
                        if total != components_sum:
                            return total - components_sum
                        return 0

                    component_columns = [col for col in df.columns if col != total_energy_column and col != df.columns[0]]
                    df['Sonstige [W]'] = df.apply(lambda row: calculate_other(row, total_energy_column, component_columns), axis=1)

                    # Debugging: Überprüfen der Berechnung von "Sonstige"
                    print(f"DataFrame nach Berechnung von 'Sonstige [W]' ({state}):")
                    print(df[['Sonstige [W]']].head())

                # Debugging: Überprüfen der Daten nach dem Entfernen von leeren Spalten
                print(f"DataFrame nach dem Entfernen von leeren Spalten ({state}):")
                print(df.head())

                columns = df.columns.tolist()
                data = df.to_dict(orient='list')  # Daten im Listenformat speichern

                # Speichere den DataFrame zur weiteren Verarbeitung
                filename = save_file(df, state)

                # Debugging: Überprüfen der gespeicherten CSV-Datei
                saved_df = pd.read_csv(filename, delimiter=',')
                print(f"Gespeicherte DataFrame ({state}):")
                print(saved_df.head())

                data_store[state] = {
                    'columns': columns,
                    'data': data
                }
            except Exception as e:
                return jsonify({"error": str(e)})

    return jsonify(data_store)

@app.route('/process_columns', methods=['POST'])
def process_columns():
    data = request.json
    component_columns = data.get('columns')
    total_energy_column = data.get('total_energy_column')
    state = data.get('state')

    # Read the stored dataframe
    filename = get_latest_file(state)
    if filename is None:
        return jsonify({"error": "No file found for this state"}), 404
    df = pd.read_csv(filename, delimiter=',')

    # Berechnung von "Sonstige [W]"
    def calculate_other(row, total_col, component_cols):
        total = row[total_col]
        components_sum = row[component_cols].sum()
        if total != components_sum:
            return total - components_sum
        return 0

    df['Sonstige [W]'] = df.apply(lambda row: calculate_other(row, total_energy_column, component_columns), axis=1)

    # Debugging: Überprüfen der Berechnung von "Sonstige [W]"
    print(f"DataFrame nach Berechnung von 'Sonstige [W]' ({state}):")
    print(df[['Sonstige [W]']].head())

    # Speichere den DataFrame zur weiteren Verarbeitung
    filename = save_file(df, state)

    result_data = df.to_dict(orient='records')
    result_columns = df.columns.tolist()

    return jsonify({
        "columns": result_columns,
        "data": result_data,
        "message": "Columns processed successfully"
    })

@app.route('/machine_info', methods=['POST'])
def machine_info():
    info = request.json
    print(f"Maschineninformationen erhalten: {info}")  # Debugging
    return jsonify(success=True)

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        # Retrieve machine info
        machine_info = json.loads(request.form.get('machine_info'))
        percentages = json.loads(request.form.get('percentages'))
        pdf_filename = request.form.get('pdf_filename', 'energieeinsparungsaudit.pdf')

        print(f"Maschineninformationen: {machine_info}")  # Debugging
        print(f"Prozentangaben: {percentages}")  # Debugging

        # Load previously saved CSV data
        standby_file = get_latest_file('standby')
        ready_file = get_latest_file('ready')
        process_file = get_latest_file('process')
        
        if not all([standby_file, ready_file, process_file]):
            return jsonify({"error": "Missing data files"}), 404

        standby_data = pd.read_csv(standby_file)
        ready_data = pd.read_csv(ready_file)
        process_data = pd.read_csv(process_file)
        
        # Debugging: Überprüfen der geladenen Daten
        if standby_data is not None:
            print(f"Standby DataFrame:")
            print(standby_data.head())
        if ready_data is not None:
            print(f"Ready DataFrame:")
            print(ready_data.head())
        if process_data is not None:
            print(f"Process DataFrame:")
            print(process_data.head())

        # Prepare the data to be passed to the PDF creation function
        buffer = io.BytesIO()
        create_energy_audit_pdf(machine_info, standby_data, ready_data, process_data, percentages, buffer)

        buffer.seek(0)
        return send_file(buffer, as_attachment=True, attachment_filename=pdf_filename, mimetype='application/pdf')

    except Exception as e:
        print(f"Fehler bei der PDF-Erstellung: {e}")  # Debugging
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
