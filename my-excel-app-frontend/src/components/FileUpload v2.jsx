import React, { useState, useCallback } from "react";
import axios from "axios";

// Error Message Component for better display
const ErrorMessage = ({ message, details }) => {
  if (!message) return null;

  // Find indices of special strings to parse the details array
  const missingHeaderIndex = details.indexOf("Missing columns:");
  const availableHeaderIndex = details.indexOf("Available columns:");
  const separatorIndex = details.indexOf("---");

  // Determine if the details array has the special structure
  const isStructuredError =
    missingHeaderIndex !== -1 &&
    availableHeaderIndex !== -1 &&
    separatorIndex !== -1;

  let missingColumns = [];
  let availableColumns = [];

  if (isStructuredError) {
    missingColumns = details.slice(missingHeaderIndex + 1, separatorIndex);
    availableColumns = details.slice(availableHeaderIndex + 1);
  }

  return (
    <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg text-left">
      <p className="text-sm font-bold text-red-800">{message}</p>
      {isStructuredError ? (
        <>
          {missingColumns.length > 0 && (
            <>
              <p className="mt-2 text-sm font-semibold text-red-700">
                Missing columns:
              </p>
              <ol className="mt-1 list-decimal list-inside text-sm text-red-700">
                {missingColumns.map((col, i) => (
                  <li key={`m-${i}`}>{col}</li>
                ))}
              </ol>
            </>
          )}
          {availableColumns.length > 0 && (
            <>
              <p className="mt-4 text-sm font-semibold text-red-700">
                Available columns:
              </p>
              <ol className="mt-1 list-decimal list-inside text-sm text-red-700">
                {availableColumns.map((col, i) => (
                  <li key={`a-${i}`}>{col}</li>
                ))}
              </ol>
            </>
          )}
        </>
      ) : (
        // Fallback for simple, unstructured error details
        details &&
        details.length > 0 && (
          <ol className="mt-2 list-decimal list-inside text-sm text-red-700">
            {details.map((detail, index) => (
              <li key={index}>{detail}</li>
            ))}
          </ol>
        )
      )}
    </div>
  );
};

function FileUpload() {
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState({ message: "", details: [] });
  const [successMessage, setSuccessMessage] = useState("");

  const clearMessages = () => {
    setError({ message: "", details: [] });
    setSuccessMessage("");
  };

  const validateAndSetFile = (selectedFile) => {
    clearMessages();
    if (
      selectedFile &&
      (selectedFile.type ===
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ||
        selectedFile.type === "application/vnd.ms-excel")
    ) {
      setFile(selectedFile);
    } else {
      setError({
        message:
          "Invalid file type. Please upload an Excel file (.xlsx, .xls).",
      });
      setFile(null);
    }
  };

  const handleFileChange = (e) => {
    validateAndSetFile(e.target.files[0]);
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleUpload = async () => {
    if (!file) {
      setError({ message: "Please select a file first." });
      return;
    }

    clearMessages();
    setIsUploading(true);

    const formData = new FormData();
    formData.append("excel_file", file);

    try {
      const apiUrl = `${
        import.meta.env.VITE_API_BASE_URL || "http://localhost:5000"
      }/api/upload-excel`;
      const response = await axios.post(apiUrl, formData, {
        responseType: "blob",
      });

      const blob = new Blob([response.data], {
        type: response.headers["content-type"],
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;

      const contentDisposition = response.headers["content-disposition"];
      let fileName = "processed_data.xlsx";
      if (contentDisposition) {
        const fileNameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (fileNameMatch && fileNameMatch.length === 2)
          fileName = fileNameMatch[1];
      }
      link.setAttribute("download", fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setSuccessMessage("File processed and download started!");
      setFile(null);
    } catch (err) {
      let errorData = { message: "An unexpected error occurred.", details: [] };
      if (err.response && err.response.data instanceof Blob) {
        try {
          const errText = await err.response.data.text();
          const errJson = JSON.parse(errText);
          errorData = {
            message: errJson.message || "An error occurred during processing.",
            details: errJson.details || [],
          };
        } catch {
          // The error response was not JSON
        }
      }
      setError(errorData);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-100 p-4 font-sans">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-lg">
        <h2 className="text-3xl font-bold mb-8 text-center text-slate-700">
          Upload Excel File
        </h2>
        <div
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors duration-300 ${
            isDragging ? "border-indigo-600 bg-indigo-50" : "border-slate-300"
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => document.getElementById("fileInput")?.click()}
        >
          <input
            type="file"
            id="fileInput"
            className="hidden"
            onChange={handleFileChange}
            accept=".xlsx, .xls"
          />
          <p className="text-slate-500">
            {file
              ? `Selected: ${file.name}`
              : "Drag & drop file or click to select"}
          </p>
        </div>
        {file && (
          <div className="mt-8 text-center">
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="w-full sm:w-auto px-8 py-3 rounded-lg font-semibold text-white bg-green-600 hover:bg-green-700 disabled:bg-slate-400"
            >
              {isUploading ? "Processing..." : "Upload and Process File"}
            </button>
          </div>
        )}
        {error.message && (
          <ErrorMessage message={error.message} details={error.details} />
        )}
        {successMessage && (
          <p className="mt-6 text-sm text-center font-medium text-green-600">
            {successMessage}
          </p>
        )}
      </div>
    </div>
  );
}

export default FileUpload;
