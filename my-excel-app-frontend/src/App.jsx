// ./src/App.jsx
import React, { useState, useEffect } from 'react';
import PasswordPrompt from './components/PasswordPrompt'; // Component for password input
import FileUpload from './components/FileUpload'; // Component for file upload functionality

/**
 * @function App
 * @description The main application component for "My Excel App".
 * It manages the authentication state of the user. If the user is not authenticated,
 * it displays the `PasswordPrompt` component. Once authenticated, it displays the
 * `FileUpload` component. Authentication status is persisted in `sessionStorage`.
 *
 * @returns {JSX.Element} The rendered application, conditionally showing PasswordPrompt or FileUpload.
 */
function App() {
  // State to track if the user is authenticated.
  // - isAuthenticated (boolean): True if the user has successfully entered the password, false otherwise.
  // - setIsAuthenticated (function): Function to update the authentication state.
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  /**
   * @effect useEffect
   * @description This effect runs once after the initial render (due to the empty dependency array `[]`).
   * It checks `sessionStorage` for a previously stored authentication status ('myExcelAppIsAuthenticated').
   * If found and true, it sets the `isAuthenticated` state to true, allowing the user to bypass
   * the password prompt if they were already authenticated in the current session.
   */
  useEffect(() => {
    const authStatus = sessionStorage.getItem('myExcelAppIsAuthenticated');
    if (authStatus === 'true') {
      setIsAuthenticated(true);
    }
  }, []); // Empty dependency array means this effect runs only once on mount.

  /**
   * @function handlePasswordCorrect
   * @description Callback function passed to the `PasswordPrompt` component.
   * This function is called when the user successfully enters the correct password.
   * It sets the `isAuthenticated` state to true and stores this status in `sessionStorage`
   * to persist authentication across page reloads within the same session.
   *
   * @returns {void}
   */
  const handlePasswordCorrect = () => {
    setIsAuthenticated(true);
    sessionStorage.setItem('myExcelAppIsAuthenticated', 'true'); // Persist auth state
  };

  // Render the main application structure.
  // Conditionally renders `PasswordPrompt` or `FileUpload` based on `isAuthenticated` state.
  return (
    <div className="App"> {/* Main container div */}
      {!isAuthenticated ? (
        // If not authenticated, show the PasswordPrompt component.
        // Pass `handlePasswordCorrect` as a prop to be called on successful password entry.
        <PasswordPrompt onPasswordCorrect={handlePasswordCorrect} />
      ) : (
        // If authenticated, show the FileUpload component.
        <FileUpload />
      )}
    </div>
  );
}

export default App;
