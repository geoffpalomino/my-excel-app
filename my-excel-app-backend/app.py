# import os
# import logging
# from flask import Flask, request, jsonify, send_file, make_response
# from flask_cors import CORS
# import pandas as pd
# import tempfile # For robust temporary file handling
# from dotenv import load_dotenv

# load_dotenv() # Load environment variables from .env or .flaskenv

# # --- Logging Configuration ---
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # --- Configuration ---
# # For production, set APP_PASSWORD in Azure App Service Configuration.
# # For local development, set it in .flaskenv or as an environment variable.
# EXPECTED_PASSWORD = os.environ.get("APP_PASSWORD", "yourSuperSecretPassword123") # CHANGE THIS!
# if EXPECTED_PASSWORD == "yourSuperSecretPassword123":
#     logging.warning("Using default APP_PASSWORD. Please change this for production!")


# UPLOAD_FOLDER = 'uploads' # Temporary storage for uploaded files
# PROCESSED_FOLDER = 'processed' # Temporary storage for processed files
# # Create these folders if they don't exist
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# app = Flask(__name__)

# # --- CORS Configuration ---
# # For development, allow localhost. For production, restrict to your frontend URL.
# # The frontend URL for Azure (e.g., https://my-excel-app-frontend.azurewebsites.net)
# # should be set as an environment variable (FRONTEND_URL) in Azure App Service configuration.
# LOCAL_FRONTEND_URL = os.environ.get("LOCAL_FRONTEND_URL", "http://localhost:5173") # Vite default dev port
# AZURE_FRONTEND_URL = os.environ.get("FRONTEND_URL") # The env var name you'll set in Azure

# origins_list = [LOCAL_FRONTEND_URL, "http://127.0.0.1:5173"] # 127.0.0.1 for good measure
# if AZURE_FRONTEND_URL:
#     origins_list.append(AZURE_FRONTEND_URL)
#     logging.info(f"CORS enabled for production frontend: {AZURE_FRONTEND_URL}")
# else:
#     logging.info(f"CORS production frontend URL (FRONTEND_URL) not set. Using defaults: {origins_list}")


# CORS(app, resources={
#     r"/api/*": {
#         "origins": origins_list,
#         "methods": ["GET", "POST", "OPTIONS"], # OPTIONS is important for preflight requests
#         "allow_headers": ["Content-Type", "Authorization"], # Add any other headers your frontend might send
#         "expose_headers": ["Content-Disposition"] # Important for filename in download response
#     }
# })

# # --- Helper: Excel Processing Function ---
# def process_excel_file(input_file_path, output_file_path):
#     """
#     Reads an Excel file, performs some processing, and saves the output.
#     Replace this with your actual pandas processing logic.
#     """
#     try:
#         df = pd.read_excel(input_file_path)

#         # --- Example Processing for My Excel App: ---
#         df['Status'] = 'Processed by My Excel App'
#         # If a column 'Value' exists and is numeric, multiply it by 2
#         if 'Value' in df.columns and pd.api.types.is_numeric_dtype(df['Value']):
#             df['Value'] = df['Value'] * 2
#         else:
#             # Add a sample 'Value' column if it doesn't exist for demonstration
#             df['Value'] = [i * 10 for i in range(len(df))]
#         # -------------------------------------------

#         df.to_excel(output_file_path, index=False)
#         logging.info(f"Successfully processed Excel file: {input_file_path} to {output_file_path}")
#         return True
#     except Exception as e:
#         logging.error(f"Error processing Excel file {input_file_path}: {e}", exc_info=True)
#         return False

# # --- API Routes ---
# @app.route('/api/validate-password', methods=['POST', 'OPTIONS']) # Add OPTIONS
# def validate_password():
#     if request.method == 'OPTIONS': # Handle preflight request
#         return _build_cors_preflight_response()

#     data = request.get_json()
#     if not data or 'password' not in data:
#         logging.warning("Password validation: Password not provided in request.")
#         return jsonify({"success": False, "message": "Password not provided."}), 400

#     entered_password = data['password']
#     if entered_password == EXPECTED_PASSWORD:
#         logging.info("Password validation successful.")
#         return jsonify({"success": True, "message": "Password correct."})
#     else:
#         logging.warning("Password validation failed: Invalid password entered.")
#         return jsonify({"success": False, "message": "Invalid password."}), 401

# @app.route('/api/upload-excel', methods=['POST', 'OPTIONS']) # Add OPTIONS
# def upload_excel():
#     if request.method == 'OPTIONS': # Handle preflight request
#         return _build_cors_preflight_response()

#     if 'excel_file' not in request.files:
#         logging.warning("Excel upload: No 'excel_file' part in the request.")
#         return jsonify({"success": False, "message": "No file part in the request."}), 400

#     file = request.files['excel_file']
#     if file.filename == '':
#         logging.warning("Excel upload: No file selected (empty filename).")
#         return jsonify({"success": False, "message": "No selected file."}), 400

#     if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
#         original_filename = file.filename
#         logging.info(f"Excel upload: Received file '{original_filename}'.")

#         uploaded_file_path = None 
#         processed_file_path = None
#         try:
#             # Use tempfile for secure and automatic cleanup
#             with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1], dir=UPLOAD_FOLDER) as tmp_uploaded_file:
#                 file.save(tmp_uploaded_file.name)
#                 uploaded_file_path = tmp_uploaded_file.name
#             logging.info(f"File '{original_filename}' saved temporarily to '{uploaded_file_path}'.")

#             with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx', dir=PROCESSED_FOLDER) as tmp_processed_file:
#                 processed_file_path = tmp_processed_file.name

#             if process_excel_file(uploaded_file_path, processed_file_path):
#                 logging.info(f"File '{uploaded_file_path}' processed to '{processed_file_path}'. Preparing to send.")
#                 try:
#                     return send_file(
#                         processed_file_path,
#                         as_attachment=True,
#                         download_name=f"processed_my_app_{original_filename}",
#                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#                     )
#                 finally: # This finally ensures cleanup of processed_file_path AFTER send_file is attempted
#                     if os.path.exists(processed_file_path):
#                         os.remove(processed_file_path)
#                         logging.info(f"Cleaned up processed file: {processed_file_path}")
#             else:
#                 logging.error(f"Processing failed for uploaded file {uploaded_file_path}.")
#                 # Ensure uploaded file is cleaned up if processing fails
#                 if uploaded_file_path and os.path.exists(uploaded_file_path):
#                     os.remove(uploaded_file_path)
#                     logging.info(f"Cleaned up uploaded file after processing failure: {uploaded_file_path}")
#                 return jsonify({"success": False, "message": "Error processing file."}), 500

#         except Exception as e:
#             logging.error(f"An unexpected error occurred during file handling for My Excel App: {e}", exc_info=True)
#             return jsonify({"success": False, "message": "An internal server error occurred."}), 500
#         finally: # This finally ensures cleanup of the originally uploaded file if it still exists
#             if uploaded_file_path and os.path.exists(uploaded_file_path):
#                 os.remove(uploaded_file_path)
#                 logging.info(f"Ensured cleanup of uploaded file: {uploaded_file_path}")
#     else:
#         logging.warning(f"Excel upload: Invalid file type received - '{file.filename}'.")
#         return jsonify({"success": False, "message": "Invalid file type. Please upload an Excel file (.xlsx or .xls)."}), 400

# @app.route('/')
# def index():
#     logging.info("Root endpoint '/' accessed.")
#     return "My Excel App Backend is running!"

# # Helper for CORS preflight
# def _build_cors_preflight_response():
#     response = make_response()
#     # These headers are set by Flask-CORS based on the configuration,
#     # but explicitly setting them here can be useful for debugging or specific needs.
#     # response.headers.add("Access-Control-Allow-Origin", "*") # Or specific origin
#     # response.headers.add('Access-Control-Allow-Headers', "*") # Or specific headers
#     # response.headers.add('Access-Control-Allow-Methods', "*") # Or specific methods
#     return response

# if __name__ == '__main__':
#     # For local development only. Gunicorn will be used in production.
#     # The host 0.0.0.0 makes it accessible from other devices on the same network.
#     app.run(host='0.0.0.0', port=5000, debug=True)

##############

import os
import logging
import pandas as pd
import tempfile
import re # Import regular expressions for more advanced sanitization
from flask import Flask, request, jsonify, send_file, make_response, after_this_request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
EXPECTED_PASSWORD = os.environ.get("APP_PASSWORD", "yourSuperSecretPassword123")
if EXPECTED_PASSWORD == "yourSuperSecretPassword123":
    logging.warning("Using default APP_PASSWORD. Please change this for production!")

UPLOAD_FOLDER_BASE = 'uploads_temp'
PROCESSED_FOLDER_BASE = 'processed_temp'
os.makedirs(UPLOAD_FOLDER_BASE, exist_ok=True)
os.makedirs(PROCESSED_FOLDER_BASE, exist_ok=True)

app = Flask(__name__)

# --- CORS Configuration ---
# This configuration allows your frontend to make requests and to read the Content-Disposition header.
# It does not modify the Content-Disposition header's content itself.
LOCAL_FRONTEND_URL = os.environ.get("LOCAL_FRONTEND_URL", "http://localhost:5173")
AZURE_FRONTEND_URL = os.environ.get("FRONTEND_URL")

origins_list = [LOCAL_FRONTEND_URL, "http://127.0.0.1:5173"]
if AZURE_FRONTEND_URL:
    origins_list.append(AZURE_FRONTEND_URL)
    logging.info(f"CORS enabled for production frontend: {AZURE_FRONTEND_URL}")
else:
    logging.info(f"CORS production frontend URL (FRONTEND_URL) not set. Using defaults: {origins_list}")

CORS(app, resources={
    r"/api/*": {
        "origins": origins_list,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Disposition"] # Crucial for client to read this header if needed
    }
})

def _remove_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
            app.logger.info(f"Successfully removed temp file: {path}")
    except OSError as e:
        app.logger.error(f"Error removing temp file {path}: {e}", exc_info=True)
    except Exception as e:
        app.logger.error(f"Unexpected error removing temp file {path}: {e}", exc_info=True)

def normalize_boolean(value):
    if isinstance(value, bool): return value
    if isinstance(value, (int, float)):
        if value == 1: return True
        elif value == 0: return False
        return None
    if isinstance(value, str):
        val_lower = value.lower().strip()
        if val_lower in ["true", "yes", "1", "t", "on"]: return True
        elif val_lower in ["false", "no", "0", "f", "off"]: return False
    if pd.isna(value): return None
    return None

def generate_output_download_name(original_input_basename):
    """
    Generates a sanitized output filename for download, ensuring it cleanly ends with '.xlsx'.
    More aggressively sanitizes the prefix part of the filename.
    """
    if not original_input_basename:
        app.logger.warning("generate_output_download_name called with no basename, using default.")
        return "ProcessedData- Brevo Contacts.xlsx"
        
    # Get the main part of the filename, without its original extension
    name_part_without_ext = os.path.splitext(original_input_basename)[0]
    
    # Aggressively sanitize the name_part_without_ext to form the base of our prefix.
    # Allow alphanumeric characters, spaces, and hyphens. Replace others.
    # Convert to string first to handle potential non-string inputs if any.
    sanitized_base = str(name_part_without_ext)
    sanitized_base = re.sub(r'[^\w\s-]', '', sanitized_base) # Keep word chars, whitespace, hyphens
    sanitized_base = re.sub(r'\s+', ' ', sanitized_base).strip() # Collapse multiple spaces, strip ends

    # Use the existing logic to determine the prefix from this sanitized base
    parts = sanitized_base.split('-', 1)
    if len(parts) > 1:
        prefix = parts[0].strip() 
    else:
        prefix = sanitized_base.strip() # Already stripped, but good practice

    # Handle cases where the prefix might become empty after sanitization or splitting
    if not prefix:
        prefix = "ProcessedData"

    # Ensure prefix is not excessively long (browsers/OS have filename length limits)
    MAX_PREFIX_LEN = 50 
    prefix = prefix[:MAX_PREFIX_LEN]

    # Construct the final name, explicitly appending ".xlsx"
    final_download_name = f"{prefix}- Brevo Contacts.xlsx"
    
    app.logger.info(f"Original basename: '{original_input_basename}'")
    app.logger.info(f"Name part without ext: '{name_part_without_ext}'")
    app.logger.info(f"Sanitized base for prefix: '{sanitized_base}'")
    app.logger.info(f"Calculated prefix: '{prefix}'")
    app.logger.info(f"Final generated download name: '{final_download_name}' (Length: {len(final_download_name)})")
    # For intense debugging, uncomment to see ASCII values:
    # app.logger.info(f"ASCII values for final_download_name: {[ord(c) for c in final_download_name]}")
    
    return final_download_name

def process_uploaded_spreadsheet(input_server_filepath, output_server_filepath):
    try:
        df = pd.read_excel(input_server_filepath, dtype={'Parent 1 Is FacultyStaff': object, 'Parent 2 Is FacultyStaff': object, 'ID Number': object, 'School Name': object})
        app.logger.info(f"Read {len(df)} rows from {input_server_filepath}")
    except FileNotFoundError:
        app.logger.error(f"Input file not found: {input_server_filepath}")
        return False, "Input file not found by server."
    except Exception as e:
        app.logger.error(f"Error reading Excel {input_server_filepath}: {e}", exc_info=True)
        return False, f"Error reading Excel file: {e}"

    expected_cols = ['School Name', 'SLC Name', 'ID Number', 'Student First Name', 'Student Last Name', 'Student Grade Level', 'Student Homeroom', 'Parent 1 First Name', 'Parent 1 Last Name', 'Parent 1 Email', 'Parent 1 Phone Number', 'Parent 1 Is FacultyStaff', 'Parent 1 Street Address', 'Parent 1 City', 'Parent 1 State', 'Parent 1 ZIP Code', 'Parent 2 First Name', 'Parent 2 Last Name', 'Parent 2 Email', 'Parent 2 Phone Number', 'Parent 2 Is FacultyStaff', 'Parent 2 Street Address', 'Parent 2 City', 'Parent 2 State', 'Parent 2 ZIP Code']
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        msg = f"Missing columns: {', '.join(missing_cols)}. Available: {', '.join(df.columns)}"
        app.logger.error(msg)
        return False, msg

    processed_data = {}
    max_students = 4
    input_student_cols = ["School Name", "SLC Name", "ID Number", "Student First Name", "Student Last Name", "Student Grade Level", "Student Homeroom"]
    output_student_base_names = {"SLC Name": "SLC Name", "ID Number": "ID Number", "Student First Name": "First Name", "Student Last Name": "Last Name", "Student Grade Level": "Grade Level", "Student Homeroom": "Homeroom"}

    for _, row in df.iterrows():
        student_info = {col: row.get(col) for col in input_student_cols}
        school_name = student_info.get("School Name")
        parents_this_student = []
        for i in [1, 2]:
            email = row.get(f'Parent {i} Email')
            if pd.notna(email) and str(email).strip():
                parents_this_student.append({"email": str(email).lower().strip(), "details": {"Firstname": row.get(f'Parent {i} First Name'), "Lastname": row.get(f'Parent {i} Last Name'), "SMS": row.get(f'Parent {i} Phone Number'), "Is FacultyStaff": normalize_boolean(row.get(f'Parent {i} Is FacultyStaff')), "Street Address": row.get(f'Parent {i} Street Address'), "City": row.get(f'Parent {i} City'), "State": row.get(f'Parent {i} State'), "ZIP Code": row.get(f'Parent {i} ZIP Code')}})
        for p_info in parents_this_student:
            email_key = p_info["email"]
            if email_key not in processed_data:
                processed_data[email_key] = {"Parent_Info": p_info["details"], "Students_Info": [], "School_Name": school_name}
            else:
                processed_data[email_key]["Parent_Info"].update(p_info["details"])
            current_students = processed_data[email_key]["Students_Info"]
            if len(current_students) < max_students and (student_info.get("ID Number") is None or not any(s.get("ID Number") == student_info.get("ID Number") for s in current_students)):
                current_students.append(student_info)

    output_rows = []
    parent_cols = ["Firstname", "Lastname", "SMS", "Is FacultyStaff", "Street Address", "City", "State", "ZIP Code"]
    output_cols = ["Email", "School Name"] + parent_cols
    for i in range(1, max_students + 1):
        for base_name in output_student_base_names.values(): output_cols.append(f"{base_name} Student {i}")

    for email, data in processed_data.items():
        row_data = {"Email": email, "School Name": data.get("School_Name")}
        row_data.update(data["Parent_Info"])
        s_list = data["Students_Info"]
        for i in range(max_students):
            s_suffix = i + 1
            if i < len(s_list):
                s = s_list[i]
                for orig_col, base_name in output_student_base_names.items(): row_data[f"{base_name} Student {s_suffix}"] = s.get(orig_col)
            else:
                for base_name in output_student_base_names.values(): row_data[f"{base_name} Student {s_suffix}"] = None
        output_rows.append(row_data)
    
    output_df = pd.DataFrame(output_rows, columns=output_cols)
    try:
        output_df.to_excel(output_server_filepath, index=False)
        app.logger.info(f"Processed data saved to: {output_server_filepath}")
        return True, None
    except Exception as e:
        app.logger.error(f"Error writing output Excel {output_server_filepath}: {e}", exc_info=True)
        return False, f"Error writing output Excel file: {e}"

# --- API Routes ---
@app.route('/api/validate-password', methods=['POST', 'OPTIONS'])
def validate_password():
    if request.method == 'OPTIONS': return _build_cors_preflight_response()
    data = request.get_json()
    if not data or 'password' not in data:
        logging.warning("Password validation: Password not provided.")
        return jsonify({"success": False, "message": "Password not provided."}), 400
    if data['password'] == EXPECTED_PASSWORD:
        logging.info("Password validation successful.")
        return jsonify({"success": True, "message": "Password correct."})
    else:
        logging.warning("Password validation failed.")
        return jsonify({"success": False, "message": "Invalid password."}), 401

@app.route('/api/upload-excel', methods=['POST', 'OPTIONS'])
def upload_excel():
    if request.method == 'OPTIONS': return _build_cors_preflight_response()

    if 'excel_file' not in request.files:
        logging.warning("Excel upload: No 'excel_file' part in request.")
        return jsonify({"success": False, "message": "No file part in the request."}), 400

    file = request.files['excel_file']
    if file.filename == '':
        logging.warning("Excel upload: No file selected.")
        return jsonify({"success": False, "message": "No selected file."}), 400

    original_filename = file.filename
    if file and (original_filename.endswith('.xlsx') or original_filename.endswith('.xls')):
        logging.info(f"Excel upload: Received file '{original_filename}'.")
        
        uploaded_file_path = None
        processed_file_path_to_send = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1], dir=UPLOAD_FOLDER_BASE, mode='wb') as tmp_upload_obj:
                file.save(tmp_upload_obj)
                uploaded_file_path = tmp_upload_obj.name
            logging.info(f"File '{original_filename}' saved temporarily to '{uploaded_file_path}'.")

            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx', dir=PROCESSED_FOLDER_BASE) as tmp_processed_obj:
                processed_file_path_to_send = tmp_processed_obj.name
            
            success, error_message = process_uploaded_spreadsheet(uploaded_file_path, processed_file_path_to_send)
            _remove_file(uploaded_file_path) 
            uploaded_file_path = None

            if success:
                download_name_str = generate_output_download_name(original_filename)
                
                # Log the exact string being passed to send_file
                app.logger.info(f"Attempting to send file with download_name: '{download_name_str}'")

                @after_this_request
                def cleanup_sent_file(response):
                    _remove_file(processed_file_path_to_send)
                    return response
                
                return send_file(
                    processed_file_path_to_send,
                    as_attachment=True,
                    download_name=download_name_str, # Use the sanitized and logged name
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            else:
                logging.error(f"Processing failed for uploaded file '{original_filename}': {error_message}")
                _remove_file(processed_file_path_to_send)
                processed_file_path_to_send = None
                return jsonify({"success": False, "message": error_message or "Error processing file."}), 500

        except Exception as e:
            logging.error(f"An unexpected error occurred in upload_excel: {e}", exc_info=True)
            _remove_file(uploaded_file_path)
            _remove_file(processed_file_path_to_send)
            return jsonify({"success": False, "message": "An internal server error occurred."}), 500

    else: 
        logging.warning(f"Excel upload: Invalid file type received - '{original_filename}'.")
        return jsonify({"success": False, "message": "Invalid file type. Please upload an Excel file (.xlsx or .xls)."}), 400

@app.route('/')
def index():
    logging.info("Root endpoint '/' accessed.")
    return "My Excel App Backend is running!"

def _build_cors_preflight_response():
    response = make_response()
    return response, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

