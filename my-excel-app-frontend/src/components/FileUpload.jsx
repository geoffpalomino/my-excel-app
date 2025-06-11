// ./src/components/FileUpload.jsx
import React, { useState, useCallback } from "react";
import axios from "axios"; // Using axios for easier file upload and response handling

function FileUpload() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    if (
      selectedFile.type ===
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ||
      selectedFile.type === "application/vnd.ms-excel"
    ) {
      setFile(selectedFile);
      setMessage(`Selected file: ${selectedFile.name}`);
    } else {
      setMessage(
        "Invalid file type. Please upload an Excel file (.xlsx, .xls)."
      );
      setFile(null);
    }
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
    if (
      e.dataTransfer.types &&
      Array.from(e.dataTransfer.types).includes("Files")
    ) {
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("excel_file", file);
    setIsUploading(true);
    setMessage("Uploading and processing...");

    try {
      const apiUrl = `${
        import.meta.env.VITE_API_BASE_URL || "http://localhost:5000" // Changed from "localhost:5000"
      }/api/upload-excel`;
      const response = await axios.post(apiUrl, formData, {
        responseType: "blob", // Important for file download
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const blob = new Blob([response.data], {
        type: response.headers["content-type"],
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;

      const contentDisposition = response.headers["content-disposition"];
      let fileName = "processed_data.xlsx"; // Default filename
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

      setMessage("File processed and download started!");
      setFile(null); // Clear the file input after successful upload
    } catch (error) {
      console.error(
        "Upload error:",
        error.response ? error.response.data : error.message
      );
      let errorMsg = "File upload failed. ";
      if (
        error.response &&
        error.response.data &&
        error.response.data instanceof Blob
      ) {
        // Try to read error message from blob if backend sends JSON error for blob response
        try {
          const errText = await error.response.data.text();
          const errJson = JSON.parse(errText); // Assuming error response is JSON
          errorMsg += errJson.message || "Please check the file and try again.";
        } catch {
          // This may result in an error. Add back "catch (e)" and diagnose if necessary
          errorMsg += "An unexpected error occurred. Please try again.";
        }
      } else if (
        error.response &&
        error.response.data &&
        typeof error.response.data.message === "string"
      ) {
        errorMsg += error.response.data.message;
      } else {
        errorMsg += "Please check server logs or network connection.";
      }
      setMessage(errorMsg);
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
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer
                      ${
                        isDragging
                          ? "border-indigo-600 bg-indigo-50 scale-105"
                          : "border-slate-300 hover:border-slate-400"
                      }
                      transition-all duration-200 ease-in-out`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => document.getElementById("fileInput")?.click()} // Trigger hidden file input
        >
          <input
            type="file"
            id="fileInput"
            className="hidden"
            onChange={handleFileChange}
            accept=".xlsx, .xls" // Specify accepted file types
          />
          <div className="flex flex-col items-center justify-center space-y-3">
            <svg
              className={`w-16 h-16 ${
                isDragging ? "text-indigo-500" : "text-slate-400"
              } transition-colors`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.5"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              ></path>
            </svg>
            {isDragging ? (
              <p className="text-indigo-600 font-semibold">
                Drop the Excel file here...
              </p>
            ) : file ? (
              <p className="text-slate-700 font-medium">
                Selected:{" "}
                <span className="font-semibold text-indigo-600">
                  {file.name}
                </span>
              </p>
            ) : (
              <p className="text-slate-500">
                Drag & drop an Excel file here, or{" "}
                <span className="text-indigo-600 font-semibold">
                  click to select
                </span>
              </p>
            )}
          </div>
        </div>

        {file && (
          <div className="mt-8 text-center">
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="w-full sm:w-auto px-8 py-3 border border-transparent rounded-lg shadow-md text-base font-semibold text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-slate-400 disabled:cursor-not-allowed transition-colors duration-150 ease-in-out"
            >
              {isUploading ? (
                <div className="flex items-center justify-center">
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  Processing...
                </div>
              ) : (
                "Upload and Process File"
              )}
            </button>
          </div>
        )}
        {message && !message.startsWith("Selected file:") && (
          <p
            className={`mt-6 text-sm text-center font-medium ${
              message.includes("failed") ||
              message.includes("Invalid file type")
                ? "text-red-600"
                : "text-green-600"
            }`}
          >
            {message}
          </p>
        )}
      </div>
    </div>
  );
}

export default FileUpload;
