// my-excel-app-frontend/src/components/FileUpload.jsx
import React, { useState, useCallback } from 'react';
import axios from 'axios'; // For making HTTP requests

/**
 * @function FileUpload
 * @description A React functional component for handling Excel file uploads.
 * It allows users to select or drag-and-drop an Excel file, validates the file type,
 * uploads it to a backend API for processing, and initiates a download of the processed file.
 * Displays messages regarding the status of the upload and processing.
 *
 * @returns {JSX.Element} The rendered file upload interface.
 */
function FileUpload() {
  // State for the selected file.
  // - file (File | null): The currently selected file object, or null if no file is selected.
  // - setFile (function): Function to update the file state.
  const [file, setFile] = useState(null);

  // State for displaying messages to the user (e.g., errors, success).
  // - message (string): The message to display.
  // - setMessage (function): Function to update the message state.
  const [message, setMessage] = useState('');

  // State to indicate if a file is being dragged over the drop zone.
  // - isDragging (boolean): True if a file is being dragged over, false otherwise.
  // - setIsDragging (function): Function to update the dragging state.
  const [isDragging, setIsDragging] = useState(false);

  // State to indicate if the file upload and processing is in progress.
  // - isUploading (boolean): True if uploading/processing, false otherwise.
  // - setIsUploading (function): Function to update the uploading state.
  const [isUploading, setIsUploading] = useState(false);

  /**
   * @function handleFileChange
   * @description Event handler for the file input element's change event.
   * Triggered when a user selects a file using the file dialog.
   * Calls `validateAndSetFile` with the selected file.
   *
   * @param {React.ChangeEvent<HTMLInputElement>} e - The change event object from the file input.
   */
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  /**
   * @function validateAndSetFile
   * @description Validates if the selected file is an Excel file (.xlsx or .xls).
   * If valid, sets the file state and a message indicating the selected file.
   * If invalid, sets an error message and clears the file state.
   *
   * @param {File} selectedFile - The file object to validate and set.
   */
  const validateAndSetFile = (selectedFile) => {
    // Check MIME types for Excel files.
    if (selectedFile.type === "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ||
        selectedFile.type === "application/vnd.ms-excel") {
      setFile(selectedFile);
      setMessage(`Selected file: ${selectedFile.name}`);
    } else {
      setMessage("Invalid file type. Please upload an Excel file (.xlsx, .xls).");
      setFile(null); // Clear invalid file
    }
  };

  /**
   * @function handleDrop
   * @description Event handler for the drop event on the drag-and-drop area.
   * Prevents default behavior, stops propagation, resets dragging state,
   * and calls `validateAndSetFile` with the dropped file.
   * Uses `useCallback` for memoization as this function might be passed to child components or used in effects.
   *
   * @param {React.DragEvent<HTMLDivElement>} e - The drag event object.
   */
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  }, []); // Empty dependency array: function memoized and created once.

  /**
   * @function handleDragOver
   * @description Event handler for the dragOver event on the drag-and-drop area.
   * Prevents default behavior and sets dragging state to true if files are being dragged.
   * Uses `useCallback` for memoization.
   *
   * @param {React.DragEvent<HTMLDivElement>} e - The drag event object.
   */
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.types && Array.from(e.dataTransfer.types).includes('Files')) {
        setIsDragging(true);
    }
  }, []); // Empty dependency array.

  /**
   * @function handleDragLeave
   * @description Event handler for the dragLeave event on the drag-and-drop area.
   * Prevents default behavior and resets dragging state to false.
   * Uses `useCallback` for memoization.
   *
   * @param {React.DragEvent<HTMLDivElement>} e - The drag event object.
   */
  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []); // Empty dependency array.

  /**
   * @function handleUpload
   * @description Handles the file upload process.
   * If no file is selected, it sets an appropriate message.
   * Otherwise, it creates a FormData object, appends the file, sets uploading state,
   * and makes an asynchronous POST request to the backend API (`/api/upload-excel`).
   * On successful response, it initiates a download of the processed file.
   * Handles errors and updates the message state accordingly.
   *
   * @returns {Promise<void>}
   */
  const handleUpload = async () => {
    if (!file) {
      setMessage('Please select a file first.');
      return;
    }

    const formData = new FormData(); // FormData for sending file data
    formData.append('excel_file', file); // 'excel_file' should match backend expectation
    setIsUploading(true);
    setMessage('Uploading and processing...');

    try {
      // Determine API URL from environment variables or default.
      const apiUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/upload-excel`;

      // Make POST request with axios.
      // 'responseType: blob' is crucial for handling file downloads.
      const response = await axios.post(apiUrl, formData, {
        responseType: 'blob',
        headers: {
          'Content-Type': 'multipart/form-data', // Standard for file uploads
        },
      });

      // Create a Blob from the response data with the correct content type.
      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const downloadUrl = window.URL.createObjectURL(blob); // Create a temporary URL for the blob.

      const link = document.createElement('a'); // Create a temporary anchor element for download.
      link.href = downloadUrl;

      // Attempt to get filename from Content-Disposition header, otherwise use a default.
      const contentDisposition = response.headers['content-disposition'];
      let fileName = 'processed_data.xlsx'; // Default filename
      if (contentDisposition) {
        const fileNameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (fileNameMatch && fileNameMatch.length === 2) fileName = fileNameMatch[1];
      }
      link.setAttribute('download', fileName); // Set the download attribute with the filename.

      document.body.appendChild(link); // Append link to body.
      link.click(); // Programmatically click the link to trigger download.
      link.remove(); // Remove the temporary link.
      window.URL.revokeObjectURL(downloadUrl); // Clean up the blob URL.

      setMessage('File processed and download started!');
      setFile(null); // Clear the selected file after successful upload and download.
    } catch (error) {
      console.error('Upload error:', error.response ? error.response.data : error.message);
      let errorMsg = 'File upload failed. ';
      // Try to parse error message if the response data is a Blob (often for JSON errors from server).
      if (error.response && error.response.data && error.response.data instanceof Blob) {
        try {
            const errText = await error.response.data.text(); // Read blob as text
            const errJson = JSON.parse(errText); // Parse text as JSON
            errorMsg += errJson.message || 'Please check the file and try again.';
        } catch (e) {
            // If blob parsing fails, use a generic message.
            errorMsg += 'An unexpected error occurred reading server error. Please try again.';
        }
      } else if (error.response && error.response.data && typeof error.response.data.message === 'string') {
         // If error response has a direct message string.
         errorMsg += error.response.data.message;
      }
      else {
        // Generic network or server error.
        errorMsg += 'Please check server logs or network connection.';
      }
      setMessage(errorMsg);
    } finally {
      setIsUploading(false); // Reset uploading state.
    }
  };

  // Render the file upload UI.
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-100 p-4 font-sans">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-lg">
        <h2 className="text-3xl font-bold mb-8 text-center text-slate-700">Upload Excel File</h2>
        {/* Drag-and-drop area */}
        <div
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer
                      ${isDragging ? 'border-indigo-600 bg-indigo-50 scale-105' : 'border-slate-300 hover:border-slate-400'}
                      transition-all duration-200 ease-in-out`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => document.getElementById('fileInput')?.click()} // Trigger hidden file input click
        >
          <input
            type="file"
            id="fileInput"
            className="hidden" // Keep the actual input hidden, styled area is used.
            onChange={handleFileChange}
            accept=".xlsx, .xls" // Specify accepted file types.
          />
          <div className="flex flex-col items-center justify-center space-y-3">
            {/* Cloud upload icon */}
            <svg className={`w-16 h-16 ${isDragging ? 'text-indigo-500' : 'text-slate-400'} transition-colors`} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
            {/* Conditional text based on dragging state or if a file is selected */}
            {isDragging ? (
              <p className="text-indigo-600 font-semibold">Drop the Excel file here...</p>
            ) : file ? (
              <p className="text-slate-700 font-medium">Selected: <span className="font-semibold text-indigo-600">{file.name}</span></p>
            ) : (
              <p className="text-slate-500">Drag & drop an Excel file here, or <span className="text-indigo-600 font-semibold">click to select</span></p>
            )}
          </div>
        </div>

        {/* Upload button, shown only if a file is selected */}
        {file && (
          <div className="mt-8 text-center">
            <button
              onClick={handleUpload}
              disabled={isUploading} // Disable button during upload
              className="w-full sm:w-auto px-8 py-3 border border-transparent rounded-lg shadow-md text-base font-semibold text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-slate-400 disabled:cursor-not-allowed transition-colors duration-150 ease-in-out"
            >
              {isUploading ? (
                // Show spinner and "Processing..." text during upload
                <div className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing...
                </div>
              ) : 'Upload and Process File'}
            </button>
          </div>
        )}
        {/* Display messages (errors or success), but not the "Selected file:" message */}
        {message && !message.startsWith('Selected file:') && (
            <p className={`mt-6 text-sm text-center font-medium ${
                message.includes('failed') || message.includes('Invalid file type') ? 'text-red-600' : 'text-green-600'
            }`}>
                {message}
            </p>
        )}
      </div>
    </div>
  );
}

export default FileUpload;
