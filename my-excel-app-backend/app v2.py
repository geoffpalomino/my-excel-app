import os
import logging
import pandas as pd
import tempfile
import re
from flask import Flask, request, jsonify, send_file, make_response, after_this_request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# --- Basic Configuration & Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
EXPECTED_PASSWORD = os.environ.get("APP_PASSWORD", "yourSuperSecretPassword123")
UPLOAD_FOLDER_BASE = 'uploads_temp'
PROCESSED_FOLDER_BASE = 'processed_temp'
os.makedirs(UPLOAD_FOLDER_BASE, exist_ok=True)
os.makedirs(PROCESSED_FOLDER_BASE, exist_ok=True)

# --- CORS Configuration ---
LOCAL_FRONTEND_URL = os.environ.get("LOCAL_FRONTEND_URL", "http://localhost:5173")
AZURE_FRONTEND_URL = os.environ.get("FRONTEND_URL")
origins_list = [LOCAL_FRONTEND_URL, "http://127.0.0.1:5173"]
if AZURE_FRONTEND_URL:
    origins_list.append(AZURE_FRONTEND_URL)
CORS(app, resources={
    r"/api/*": {
        "origins": origins_list,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Disposition"]
    }
})

# --- Helper Functions ---
def _remove_file(path):
    """Safely remove a file if it exists."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
            app.logger.info(f"Successfully removed temp file: {path}")
    except OSError as e:
        app.logger.error(f"Error removing temp file {path}: {e}", exc_info=True)

def _validate_columns(df_columns, expected_cols):
    """Check for missing columns and return a list of them."""
    return [col for col in expected_cols if col not in df_columns]

def _process_student_parent_info(df):
    """Processes the Student-Parent information spreadsheet."""
    expected_cols = [
        'School Name', 'ID Number', 'Student First Name', 'Student Last Name', 
        'Student Grade Level', 'Student Homeroom', 'Parent 1 First Name', 'Parent 1 Last Name', 
        'Parent 1 Email', 'Parent 1 Phone Number', 'Parent 1 Street Address', 'Parent 1 City', 
        'Parent 1 State', 'Parent 1 ZIP Code', 'Parent 2 First Name', 'Parent 2 Last Name', 
        'Parent 2 Email', 'Parent 2 Phone Number', 'Parent 2 Street Address', 'Parent 2 City', 
        'Parent 2 State', 'Parent 2 ZIP Code'
    ]
    missing_cols = _validate_columns(df.columns, expected_cols)
    if missing_cols:
        # MODIFICATION: Create a detailed, multi-line error list.
        error_details = ["Missing columns:", *missing_cols, "---", "Available columns:", *list(df.columns)]
        return False, {"message": "Column mismatch in Student-Parent file.", "details": error_details}

    processed_data = {}
    for _, row in df.iterrows():
        student_info = {
            "ID Number": row.get('ID Number'),
            "First Name": row.get('Student First Name'),
            "Last Name": row.get('Student Last Name'),
            "Grade Level": row.get('Student Grade Level'),
            "Homeroom": row.get('Student Homeroom')
        }
        school_name = row.get("School Name")

        for i in [1, 2]:
            email = row.get(f'Parent {i} Email')
            if pd.notna(email) and str(email).strip():
                email_key = str(email).lower().strip()
                parent_details = {
                    "Firstname": row.get(f'Parent {i} First Name'),
                    "Lastname": row.get(f'Parent {i} Last Name'),
                    "SMS": row.get(f'Parent {i} Phone Number'),
                    "Street Address": row.get(f'Parent {i} Street Address'),
                    "City": row.get(f'Parent {i} City'),
                    "State": row.get(f'Parent {i} State'),
                    "ZIP Code": row.get(f'Parent {i} ZIP Code')
                }
                
                if email_key not in processed_data:
                    processed_data[email_key] = {"Parent_Info": {}, "Students_Info": [], "School_Name": school_name}
                
                processed_data[email_key]["Parent_Info"].update({k:v for k,v in parent_details.items() if v})
                
                current_students = processed_data[email_key]["Students_Info"]
                if len(current_students) < 4 and not any(s.get("ID Number") == student_info.get("ID Number") for s in current_students):
                    current_students.append(student_info)

    output_rows = []
    for email, data in processed_data.items():
        row_data = {"Email": email, "School Name": data.get("School_Name")}
        row_data.update(data["Parent_Info"])
        for i, s in enumerate(data["Students_Info"]):
            for key, value in s.items():
                row_data[f"{key} Student {i+1}"] = value
        output_rows.append(row_data)
    
    return True, pd.DataFrame(output_rows)

def _process_faculty_staff_info(df):
    """Processes the Faculty-Staff information spreadsheet."""
    expected_cols = ['School Name', 'ID Number', 'First Name', 'Last Name', 'Email', 'Phone Number', 'Street Address', 'City', 'State', 'ZIP Code']
    missing_cols = _validate_columns(df.columns, expected_cols)
    if missing_cols:
        # MODIFICATION: Create a detailed, multi-line error list.
        error_details = ["Missing columns:", *missing_cols, "---", "Available columns:", *list(df.columns)]
        return False, {"message": "Column mismatch in Faculty-Staff file.", "details": error_details}

    df_renamed = df.rename(columns={
        'First Name': 'Firstname',
        'Last Name': 'Lastname',
        'Phone Number': 'SMS'
    })
    
    output_cols = ['Email', 'School Name', 'Firstname', 'Lastname', 'SMS', 'Street Address', 'City', 'State', 'ZIP Code']
    return True, df_renamed[output_cols]

def process_spreadsheet(filepath, original_filename):
    """Main router function to process spreadsheets based on filename."""
    name_part = os.path.splitext(original_filename)[0]
    
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        app.logger.error(f"Error reading Excel file {original_filename}: {e}", exc_info=True)
        return False, {"message": f"Could not read the Excel file. It may be corrupted or in an unsupported format.", "details": [str(e)]}

    if name_part.endswith("- StudentParent Information"):
        return _process_student_parent_info(df)
    elif name_part.endswith("- FacultyStaff Information"):
        return _process_faculty_staff_info(df)
    else:
        err_msg = "Invalid file name. Name must end with '- StudentParent Information' or '- FacultyStaff Information'."
        return False, {"message": err_msg, "details": [f"Your filename: '{original_filename}'"]}

def generate_output_download_name(original_input_basename):
    """Generates a sanitized output filename."""
    name_part_without_ext = os.path.splitext(original_input_basename)[0]
    
    if name_part_without_ext.endswith("- StudentParent Information"):
        base_name = name_part_without_ext.replace("- StudentParent Information", "")
    elif name_part_without_ext.endswith("- FacultyStaff Information"):
        base_name = name_part_without_ext.replace("- FacultyStaff Information", "")
    else:
        base_name = name_part_without_ext

    sanitized_base = re.sub(r'[^\w\s-]', '', base_name).strip()
    return f"{sanitized_base} - Brevo Contacts.xlsx"

# --- API Routes ---
@app.route('/api/validate-password', methods=['POST', 'OPTIONS'])
def validate_password():
    if request.method == 'OPTIONS': return make_response(), 200
    data = request.get_json()
    if data and data.get('password') == EXPECTED_PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid password."}), 401

@app.route('/api/upload-excel', methods=['POST', 'OPTIONS'])
def upload_excel():
    if request.method == 'OPTIONS': return make_response(), 200

    if 'excel_file' not in request.files or not request.files['excel_file'].filename:
        return jsonify({"success": False, "message": "No file selected."}), 400

    file = request.files['excel_file']
    original_filename = file.filename
    
    if not (original_filename.endswith('.xlsx') or original_filename.endswith('.xls')):
        return jsonify({"success": False, "message": "Invalid file type. Please upload an .xlsx or .xls file."}), 400

    uploaded_file_path = None
    processed_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1], dir=UPLOAD_FOLDER_BASE) as tmp_upload:
            file.save(tmp_upload)
            uploaded_file_path = tmp_upload.name

        success, result = process_spreadsheet(uploaded_file_path, original_filename)
        
        if not success:
            app.logger.error(f"Processing failed for {original_filename}: {result}")
            return jsonify({"success": False, **result}), 400

        output_df = result
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx', dir=PROCESSED_FOLDER_BASE) as tmp_processed:
            processed_file_path = tmp_processed.name
        output_df.to_excel(processed_file_path, index=False)
        
        download_name = generate_output_download_name(original_filename)

        @after_this_request
        def cleanup(response):
            _remove_file(uploaded_file_path)
            _remove_file(processed_file_path)
            return response
            
        return send_file(
            processed_file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        app.logger.error(f"An unexpected error occurred in upload_excel: {e}", exc_info=True)
        _remove_file(uploaded_file_path)
        _remove_file(processed_file_path)
        return jsonify({"success": False, "message": "An internal server error occurred.", "details": [str(e)]}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
