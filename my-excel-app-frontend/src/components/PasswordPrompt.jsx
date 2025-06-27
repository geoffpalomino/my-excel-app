// my-excel-app-frontend/src/components/PasswordPrompt.jsx
import React, { useState } from 'react';

/**
 * @component Spinner
 * @description A simple SVG spinner component to indicate loading status.
 * Not directly a function with params/returns in the traditional sense, but a presentational component.
 */
const Spinner = () => (
  <svg
    className="animate-spin h-5 w-5 text-white" // Tailwind classes for styling and animation
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
);

/**
 * @function PasswordPrompt
 * @description A React functional component that renders a password prompt form.
 * It handles user input for a password, submits it to a validation API,
 * and calls a callback function upon successful validation.
 *
 * @param {object} props - The component's props.
 * @param {function} props.onPasswordCorrect - Callback function to be executed when the entered password is validated successfully.
 *
 * @returns {JSX.Element} The rendered password prompt form.
 */
function PasswordPrompt({ onPasswordCorrect }) {
  // State for the password input field.
  // - password (string): The current value of the password input.
  // - setPassword (function): Function to update the password state.
  const [password, setPassword] = useState('');

  // State for displaying error messages.
  // - error (string): The error message to display. Empty if no error.
  // - setError (function): Function to update the error message state.
  const [error, setError] = useState('');

  // State to manage the loading status during API call.
  // - isLoading (boolean): True if the password validation is in progress, false otherwise.
  // - setIsLoading (function): Function to update the loading state.
  const [isLoading, setIsLoading] = useState(false);

  /**
   * @function handleSubmit
   * @description Handles the form submission event.
   * It prevents the default form submission, clears any previous errors, sets loading state,
   * and makes an asynchronous POST request to the password validation API.
   * Updates error state or calls `onPasswordCorrect` based on the API response.
   *
   * @param {React.SyntheticEvent} e - The form submission event object.
   *
   * @returns {Promise<void>}
   */
  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevent default browser form submission
    setError(''); // Clear previous errors
    setIsLoading(true); // Set loading state to true

    try {
      // Determine the API URL from environment variables, defaulting to localhost:5000.
      const apiUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/validate-password`;

      // Make a POST request to the validation API.
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json', // Specify JSON content type
        },
        body: JSON.stringify({ password }), // Send password in the request body
      });

      const data = await response.json(); // Parse the JSON response

      if (response.ok && data.success) {
        // If response is OK and API indicates success, call the callback.
        onPasswordCorrect();
      } else {
        // Otherwise, set an error message from the API response or a default one.
        setError(data.message || 'Invalid password.');
      }
    } catch (err) {
      // Handle network errors or other issues with the fetch call.
      setError('Failed to connect to the server. Please try again.');
      console.error('Password validation error:', err);
    } finally {
      // Reset loading state regardless of success or failure.
      setIsLoading(false);
    }
  };

  // Render the password prompt UI.
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-100 p-4 font-sans">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h2 className="text-3xl font-bold mb-8 text-center text-slate-700">My Excel App</h2>
        <p className="text-center text-slate-500 mb-6">Please enter the password to continue.</p>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="password_input" className="sr-only">Password</label>
            <input
              id="password_input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)} // Update password state on change
              placeholder="Password"
              className="mt-1 block w-full px-4 py-3 border border-slate-300 rounded-lg shadow-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-shadow duration-150 ease-in-out"
              required // HTML5 form validation
              disabled={isLoading} // Disable input when loading
            />
          </div>
          {error && <p className="text-red-500 text-sm text-center font-medium">{error}</p>} {/* Display error message if present */}
          <div>
            <button
              type="submit"
              className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-md text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-150 ease-in-out disabled:bg-indigo-400 disabled:cursor-not-allowed"
              disabled={isLoading} // Disable button when loading
            >
              {isLoading ? (
                <>
                  <Spinner /> {/* Show spinner when loading */}
                  <span className="ml-2">Verifying...</span>
                </>
              ) : (
                'Submit' // Show 'Submit' text when not loading
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default PasswordPrompt;
