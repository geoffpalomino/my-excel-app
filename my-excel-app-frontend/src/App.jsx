import React, { useState, useEffect } from "react";
import PasswordPrompt from "./components/PasswordPrompt";
import FileUpload from "./components/FileUpload";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check session storage for persisted authentication state
  useEffect(() => {
    const authStatus = sessionStorage.getItem("myExcelAppIsAuthenticated");
    if (authStatus === "true") {
      setIsAuthenticated(true);
    }
  }, []);

  const handlePasswordCorrect = () => {
    setIsAuthenticated(true);
    sessionStorage.setItem("myExcelAppIsAuthenticated", "true"); // Persist state
  };

  return (
    <div className="App">
      {!isAuthenticated ? (
        <PasswordPrompt onPasswordCorrect={handlePasswordCorrect} />
      ) : (
        <FileUpload />
      )}
    </div>
  );
}

export default App;
