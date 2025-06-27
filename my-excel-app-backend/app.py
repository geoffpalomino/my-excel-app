import os
import logging
import pandas as pd
import tempfile
import re # For sanitizing filenames
from flask import Flask, request, jsonify, send_file, make_response, after_this_request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv() # Loads environment variables from .env or .flaskenv

# Configures basic logging for the application.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Retrieves the application password from an environment variable APP_PASSWORD,
# with a default value if not set. Logs a warning if the default is used.
EXPECTED_PASSWORD = os.environ.get("APP_PASSWORD", "yourSuperSecretPassword123")
if EXPECTED_PASSWORD == "yourSuperSecretPassword123":
    logging.warning("Using default APP_PASSWORD. Please change this for production!")

# Defines base directories for temporary storage of uploaded and processed files.
# Ensures these directories are created if they don't exist.
UPLOAD_FOLDER_BASE = 'uploads_temp'
PROCESSED_FOLDER_BASE = 'processed_temp'
os.makedirs(UPLOAD_FOLDER_BASE, exist_ok=True)
os.makedirs(PROCESSED_FOLDER_BASE, exist_ok=True)

app = Flask(__name__) # Initializes the Flask application.

# Retrieves frontend URLs from environment variables for CORS configuration.
# Defaults to localhost:5173 for local development.
LOCAL_FRONTEND_URL = os.environ.get("LOCAL_FRONTEND_URL", "http://localhost:5173")
AZURE_FRONTEND_URL = os.environ.get("FRONTEND_URL")

origins_list = [LOCAL_FRONTEND_URL, "http://127.0.0.1:5173"]
if AZURE_FRONTEND_URL:
    origins_list.append(AZURE_FRONTEND_URL)
    logging.info(f"CORS enabled for production frontend: {AZURE_FRONTEND_URL}")
else:
    logging.info(f"CORS production frontend URL (FRONTEND_URL) not set. Using defaults: {origins_list}")

# Configures Cross-Origin Resource Sharing (CORS) for the Flask app.
# Allows requests from specified frontend origins to /api/* routes.
# Specifies allowed methods, headers, and exposed headers (like Content-Disposition).
CORS(app, resources={
    r"/api/*": {
        "origins": origins_list,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Disposition"]
    }
})

def _remove_file(path):
    """
    Safely removes a file at the given path.
    Logs success or errors during removal.

    Parameters:
    - path (str): The file system path to the file to be removed.

    Returns:
    - None
    """
    try:
        if path and os.path.exists(path):
            os.remove(path)
            app.logger.info(f"Successfully removed temp file: {path}")
    except OSError as e:
        app.logger.error(f"Error removing temp file {path}: {e}", exc_info=True)
    except Exception as e:
        app.logger.error(f"Unexpected error removing temp file {path}: {e}", exc_info=True)

def normalize_boolean(value):
    """
    Normalizes various input values (str, int, float, bool, pd.NA) to a boolean (True, False) or None.
    Handles string representations like "true", "1", "yes" and "false", "0", "no".

    Parameters:
    - value (any): The value to normalize.

    Returns:
    - bool | None: True, False, or None if the value cannot be confidently converted to a boolean.
    """
    if isinstance(value, bool): return value
    if isinstance(value, (int, float)):
        if value == 1: return True
        elif value == 0: return False
        return None
    if isinstance(value, str):
        val_lower = value.lower().strip()
        if val_lower in ["true", "yes", "1", "t", "on"]: return True
        elif val_lower in ["false", "no", "0", "f", "off"]: return False
    if pd.isna(value): return None # Handles pandas missing values
    return None

def generate_output_download_name(original_input_basename):
    """
    Generates a standardized download filename for the processed Excel file.
    It takes the base name of the original uploaded file (without extension),
    sanitizes it, extracts a prefix (e.g., from 'School Name - Details' it might take 'School Name'),
    and appends '- Brevo Contacts.xlsx'.

    Parameters:
    - original_input_basename (str): The basename (filename without directory) of the originally uploaded file.

    Returns:
    - str: The generated filename for the output file (e.g., "School Name- Brevo Contacts.xlsx").
    """
    if not original_input_basename:
        app.logger.warning("generate_output_download_name called with no basename, using default.")
        return "ProcessedData- Brevo Contacts.xlsx"

    name_part_without_ext = os.path.splitext(original_input_basename)[0]

    sanitized_base = str(name_part_without_ext)
    sanitized_base = re.sub(r'[^\w\s-]', '', sanitized_base) # Remove non-alphanumeric (except spaces, hyphens)
    sanitized_base = re.sub(r'\s+', ' ', sanitized_base).strip() # Replace multiple spaces with one, trim

    parts = sanitized_base.split('-', 1) # Split by the first hyphen
    if len(parts) > 1:
        prefix = parts[0].strip()
    else:
        prefix = sanitized_base.strip()

    if not prefix: # Default if prefix becomes empty after sanitization
        prefix = "ProcessedData"

    MAX_PREFIX_LEN = 50
    prefix = prefix[:MAX_PREFIX_LEN] # Truncate prefix if too long
    prefix = prefix.strip()
    if not prefix: # Ensure prefix is not empty after stripping
        prefix = "ProcessedData"

    final_download_name = f"{prefix}- Brevo Contacts.xlsx"

    app.logger.info(f"Original basename for download name gen: '{original_input_basename}'")
    app.logger.info(f"Sanitized base for prefix: '{sanitized_base}'")
    app.logger.info(f"Calculated prefix: '{prefix}'")
    app.logger.info(f"Final generated download name: '{final_download_name}' (Length: {len(final_download_name)})")

    return final_download_name

def process_uploaded_spreadsheet(input_server_filepath, output_server_filepath):
    """
    Processes the uploaded Excel spreadsheet according to defined business logic.
    It reads student and parent information, consolidates data per parent email,
    associates up to 4 students per parent, and structures the data into a new format.

    Parameters:
    - input_server_filepath (str): The server-side path to the uploaded Excel file.
    - output_server_filepath (str): The server-side path where the processed Excel file will be saved.

    Returns:
    - tuple (bool, str | None): A tuple containing:
        - success (bool): True if processing was successful, False otherwise.
        - error_message (str | None): An error message if processing failed, otherwise None.
    """
    try:
        # Read Excel, specifying object dtype for potentially mixed-type columns to preserve data like IDs.
        df = pd.read_excel(input_server_filepath, dtype={'Parent 1 Is FacultyStaff': object, 'Parent 2 Is FacultyStaff': object, 'ID Number': object, 'School Name': object})
        app.logger.info(f"Read {len(df)} rows from {input_server_filepath}")
    except FileNotFoundError:
        app.logger.error(f"Input file not found: {input_server_filepath}")
        return False, "Input file not found by server."
    except Exception as e:
        app.logger.error(f"Error reading Excel {input_server_filepath}: {e}", exc_info=True)
        return False, f"Error reading Excel file: {e}"

    # Define expected columns and check if they are all present in the uploaded file.
    expected_cols = ['School Name', 'SLC Name', 'ID Number', 'Student First Name', 'Student Last Name', 'Student Grade Level', 'Student Homeroom', 'Parent 1 First Name', 'Parent 1 Last Name', 'Parent 1 Email', 'Parent 1 Phone Number', 'Parent 1 Is FacultyStaff', 'Parent 1 Street Address', 'Parent 1 City', 'Parent 1 State', 'Parent 1 ZIP Code', 'Parent 2 First Name', 'Parent 2 Last Name', 'Parent 2 Email', 'Parent 2 Phone Number', 'Parent 2 Is FacultyStaff', 'Parent 2 Street Address', 'Parent 2 City', 'Parent 2 State', 'Parent 2 ZIP Code']
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        msg = f"Missing columns: {', '.join(missing_cols)}. Available: {', '.join(df.columns)}"
        app.logger.error(msg)
        return False, msg

    processed_data = {} # Dictionary to store consolidated data, keyed by parent email.
    max_students = 4    # Maximum number of students to associate per parent email.

    # Columns to extract for each student from the input.
    input_student_cols = ["School Name", "SLC Name", "ID Number", "Student First Name", "Student Last Name", "Student Grade Level", "Student Homeroom"]
    # Mapping from input student column names to output base names (e.g., 'Student First Name' -> 'First Name').
    output_student_base_names = {"SLC Name": "SLC Name", "ID Number": "ID Number", "Student First Name": "First Name", "Student Last Name": "Last Name", "Student Grade Level": "Grade Level", "Student Homeroom": "Homeroom"}

    # Iterate through each row of the input DataFrame.
    for _, row in df.iterrows():
        student_info = {col: row.get(col) for col in input_student_cols}
        school_name = student_info.get("School Name") # School name for this student's record.

        parents_this_student = [] # List to hold parent(s) info from this row.
        # Process Parent 1 and Parent 2 information.
        for i in [1, 2]:
            email_val = row.get(f'Parent {i} Email')
            # Only process if parent email is present and not empty.
            if pd.notna(email_val) and str(email_val).strip():
                parents_this_student.append({
                    "email": str(email_val).lower().strip(), # Normalize email to lowercase and strip whitespace.
                    "details": {
                        "Firstname": row.get(f'Parent {i} First Name'),
                        "Lastname": row.get(f'Parent {i} Last Name'),
                        "SMS": row.get(f'Parent {i} Phone Number'),
                        "Is FacultyStaff": normalize_boolean(row.get(f'Parent {i} Is FacultyStaff')),
                        "Street Address": row.get(f'Parent {i} Street Address'),
                        "City": row.get(f'Parent {i} City'),
                        "State": row.get(f'Parent {i} State'),
                        "ZIP Code": row.get(f'Parent {i} ZIP Code')
                    }
                })

        # For each valid parent found in the row, update processed_data.
        for p_info in parents_this_student:
            email_key = p_info["email"]
            # If this parent email is new, initialize their entry.
            if email_key not in processed_data:
                processed_data[email_key] = {"Parent_Info": p_info["details"], "Students_Info": [], "School_Name": school_name}
            else:
                # If parent email exists, update their info (e.g., if P2 info from another row adds details).
                processed_data[email_key]["Parent_Info"].update(p_info["details"])

            current_students = processed_data[email_key]["Students_Info"]
            # Add student to this parent if under max_students limit and student ID is not already listed for this parent.
            if len(current_students) < max_students and \
               (student_info.get("ID Number") is None or not any(s.get("ID Number") == student_info.get("ID Number") for s in current_students)):
                current_students.append(student_info)

    output_rows = [] # List to hold data for the output DataFrame.
    # Define parent-related columns for the output.
    parent_cols = ["Firstname", "Lastname", "SMS", "Is FacultyStaff", "Street Address", "City", "State", "ZIP Code"]
    output_cols = ["Email", "School Name"] + parent_cols # Initial output columns.
    # Add columns for each of the max_students (e.g., "First Name Student 1", "Last Name Student 1", ...).
    for i in range(1, max_students + 1):
        for base_name in output_student_base_names.values():
            output_cols.append(f"{base_name} Student {i}")

    # Transform the processed_data dictionary into a list of rows for the output DataFrame.
    for email, data in processed_data.items():
        row_data = {"Email": email, "School Name": data.get("School_Name")}
        row_data.update(data["Parent_Info"]) # Add parent information.
        s_list = data["Students_Info"]
        # Add information for each student, up to max_students.
        for i in range(max_students):
            s_suffix = i + 1 # Student number suffix (1 to max_students).
            if i < len(s_list):
                s_item = s_list[i]
                for orig_col, base_name in output_student_base_names.items():
                    row_data[f"{base_name} Student {s_suffix}"] = s_item.get(orig_col)
            else:
                # If no more students for this parent, fill remaining student columns with None.
                for base_name in output_student_base_names.values():
                    row_data[f"{base_name} Student {s_suffix}"] = None
        output_rows.append(row_data)

    # Create the output DataFrame from the list of rows, ensuring specified column order.
    output_df = pd.DataFrame(output_rows, columns=output_cols)
    try:
        # Save the output DataFrame to an Excel file.
        output_df.to_excel(output_server_filepath, index=False)
        app.logger.info(f"Processed data saved to: {output_server_filepath}")
        return True, None
    except Exception as e:
        app.logger.error(f"Error writing output Excel {output_server_filepath}: {e}", exc_info=True)
        return False, f"Error writing output Excel file: {e}"

@app.route('/api/validate-password', methods=['POST', 'OPTIONS'])
def validate_password():
    """
    API endpoint to validate a submitted password.
    Handles POST requests for validation and OPTIONS for CORS preflight.

    Request JSON Body:
    - password (str): The password to validate.

    Returns:
    - JSON response with success (bool) and message (str).
    - HTTP status 200 on success, 400 for bad request (no password), 401 for invalid password.
    """
    if request.method == 'OPTIONS': return _build_cors_preflight_response() # Handle CORS preflight
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
    """
    API endpoint to upload an Excel file, process it, and return the processed file.
    Handles POST requests for upload and OPTIONS for CORS preflight.

    Request Form Data:
    - excel_file (File): The Excel file to be uploaded.

    Returns:
    - On success: The processed Excel file as an attachment for download (mimetype application/vnd.openxmlformats-officedocument.spreadsheetml.sheet).
    - On failure: JSON response with success (bool) and message (str).
    - HTTP status 200 on success, 400 for bad request (no file, invalid type), 500 for server errors.
    """
    if request.method == 'OPTIONS': return _build_cors_preflight_response() # Handle CORS preflight

    if 'excel_file' not in request.files:
        logging.warning("Excel upload: No 'excel_file' part in request.")
        return jsonify({"success": False, "message": "No file part in the request."}), 400

    file = request.files['excel_file']
    if file.filename == '':
        logging.warning("Excel upload: No file selected.")
        return jsonify({"success": False, "message": "No selected file."}), 400

    original_filename = file.filename
    # Validate file extension.
    if file and (original_filename.endswith('.xlsx') or original_filename.endswith('.xls')):
        logging.info(f"Excel upload: Received file '{original_filename}'.")

        uploaded_file_path = None
        processed_file_path_to_send = None

        try:
            # Save uploaded file to a temporary location within UPLOAD_FOLDER_BASE.
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1], dir=UPLOAD_FOLDER_BASE, mode='wb') as tmp_upload_obj:
                file.save(tmp_upload_obj)
                uploaded_file_path = tmp_upload_obj.name
            logging.info(f"File '{original_filename}' saved temporarily to '{uploaded_file_path}'.")

            # Create a temporary file path for the processed output within PROCESSED_FOLDER_BASE.
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx', dir=PROCESSED_FOLDER_BASE) as tmp_processed_obj:
                processed_file_path_to_send = tmp_processed_obj.name

            # Call the main processing function.
            success, error_message = process_uploaded_spreadsheet(uploaded_file_path, processed_file_path_to_send)

            _remove_file(uploaded_file_path) # Clean up original uploaded temp file.
            uploaded_file_path = None

            if success:
                download_name_str = generate_output_download_name(original_filename)
                app.logger.info(f"Attempting to send file with download_name: '{download_name_str}'")

                # Register a function to clean up the processed temp file after the request is completed.
                @after_this_request
                def cleanup_sent_file(response):
                    _remove_file(processed_file_path_to_send)
                    return response

                # Send the processed file as an attachment.
                return send_file(
                    processed_file_path_to_send,
                    as_attachment=True,
                    download_name=download_name_str,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            else:
                logging.error(f"Processing failed for uploaded file '{original_filename}': {error_message}")
                _remove_file(processed_file_path_to_send) # Clean up processed temp file if processing failed.
                processed_file_path_to_send = None
                return jsonify({"success": False, "message": error_message or "Error processing file."}), 500

        except Exception as e:
            logging.error(f"An unexpected error occurred in upload_excel: {e}", exc_info=True)
            _remove_file(uploaded_file_path) # Ensure cleanup on unexpected errors.
            _remove_file(processed_file_path_to_send)
            return jsonify({"success": False, "message": "An internal server error occurred."}), 500

    else:
        logging.warning(f"Excel upload: Invalid file type received - '{original_filename}'.")
        return jsonify({"success": False, "message": "Invalid file type. Please upload an Excel file (.xlsx or .xls)."}), 400


@app.route('/')
def index():
    """
    Root endpoint to indicate the backend is running.

    Returns:
    - str: A simple message "My Excel App Backend is running!".
    """
    logging.info("Root endpoint '/' accessed.")
    return "My Excel App Backend is running!"

def _build_cors_preflight_response():
    """
    Helper function to build a response for CORS preflight (OPTIONS) requests.
    The actual CORS headers are handled by the Flask-CORS extension globally or per-resource.
    This function just returns an empty response with HTTP 200, which is typical for preflight.

    Returns:
    - tuple (Response, int): A Flask Response object and HTTP status code 200.
    """
    response = make_response()
    # CORS headers are typically added by the Flask-CORS extension based on its configuration.
    # No need to manually add them here if Flask-CORS is properly set up for the route.
    return response, 200

if __name__ == '__main__':
    # Runs the Flask development server if the script is executed directly.
    # Binds to 0.0.0.0 to be accessible externally (e.g., within a container or LAN).
    app.run(host='0.0.0.0', port=5000, debug=True)
