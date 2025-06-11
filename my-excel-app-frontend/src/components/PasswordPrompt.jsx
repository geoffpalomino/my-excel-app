// // ./src/components/PasswordPrompt.jsx
// import React, { useState } from "react";

// function PasswordPrompt({ onPasswordCorrect }) {
//   const [password, setPassword] = useState("");
//   const [error, setError] = useState("");

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     setError("");
//     try {
//       const apiUrl = `${
//         import.meta.env.VITE_API_BASE_URL || "http://localhost:5000" // Changed from "localhost:5000"
//       }/api/validate-password`;
//       const response = await fetch(apiUrl, {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify({ password }),
//       });
//       const data = await response.json();
//       if (response.ok && data.success) {
//         onPasswordCorrect();
//       } else {
//         setError(data.message || "Invalid password.");
//       }
//     } catch (err) {
//       setError("Failed to connect to the server. Please try again.");
//       console.error("Password validation error:", err);
//     }
//   };

//   return (
//     <div className="flex flex-col items-center justify-center min-h-screen bg-slate-100 p-4 font-sans">
//       <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
//         <h2 className="text-3xl font-bold mb-8 text-center text-slate-700">
//           Brevo Contact Organizer
//         </h2>
//         <p className="text-center text-slate-500 mb-6">
//           Please enter the password to continue.
//         </p>
//         <form onSubmit={handleSubmit} className="space-y-6">
//           <div>
//             <label htmlFor="password_input" className="sr-only">
//               Password
//             </label>
//             <input
//               id="password_input"
//               type="password"
//               value={password}
//               onChange={(e) => setPassword(e.target.value)}
//               placeholder="Password"
//               className="mt-1 block w-full px-4 py-3 border border-slate-300 rounded-lg shadow-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-shadow duration-150 ease-in-out"
//               required
//             />
//           </div>
//           {error && (
//             <p className="text-red-500 text-sm text-center font-medium">
//               {error}
//             </p>
//           )}
//           <div>
//             <button
//               type="submit"
//               className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-md text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-150 ease-in-out"
//             >
//               Submit
//             </button>
//           </div>
//         </form>
//       </div>
//     </div>
//   );
// }

// export default PasswordPrompt;

///////////////

// my-excel-app-frontend/src/components/PasswordPrompt.jsx
import React, { useState } from "react";

// Simple SVG Spinner component
const Spinner = () => (
  <svg
    className="animate-spin h-5 w-5 text-white" // Adjusted spinner size and removed margins if it's replacing text
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

function PasswordPrompt({ onPasswordCorrect }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false); // State to manage loading

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true); // Start loading
    try {
      const apiUrl = `${
        import.meta.env.VITE_API_BASE_URL || "http://localhost:5000"
      }/api/validate-password`;
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ password }),
      });
      const data = await response.json();
      if (response.ok && data.success) {
        onPasswordCorrect();
      } else {
        setError(data.message || "Invalid password.");
      }
    } catch (err) {
      setError("Failed to connect to the server. Please try again.");
      console.error("Password validation error:", err);
    } finally {
      setIsLoading(false); // Stop loading regardless of outcome
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-100 p-4 font-sans">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h2 className="text-3xl font-bold mb-8 text-center text-slate-700">
          Brevo Contacts Organizer
        </h2>
        <p className="text-center text-slate-500 mb-6">
          Please enter the password to continue.
        </p>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="password_input" className="sr-only">
              Password
            </label>
            <input
              id="password_input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="mt-1 block w-full px-4 py-3 border border-slate-300 rounded-lg shadow-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-shadow duration-150 ease-in-out"
              required
              disabled={isLoading} // Optionally disable input field while loading
            />
          </div>
          {error && (
            <p className="text-red-500 text-sm text-center font-medium">
              {error}
            </p>
          )}
          <div>
            <button
              type="submit"
              className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-md text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-150 ease-in-out disabled:bg-indigo-400 disabled:cursor-not-allowed"
              disabled={isLoading} // Disable button when loading
            >
              {isLoading ? (
                <>
                  <Spinner />
                  <span className="ml-2">Verifying...</span>
                </>
              ) : (
                "Submit"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default PasswordPrompt;
