// my-excel-app-frontend/server.cjs
// This file sets up a simple Express server.
// It's primarily used to serve the static build of the React application (from the 'dist' folder)
// and to handle client-side routing for a Single Page Application (SPA).

const express = require('express'); // Import the Express framework
const path = require('path');     // Import Node.js 'path' module for working with file and directory paths
const fs = require('fs');         // Import Node.js 'fs' (File System) module for file system operations

const app = express(); // Create an instance of an Express application
const port = process.env.PORT || 8080; // Define the port the server will listen on.
                                       // Uses the PORT environment variable if set (common in hosting platforms),
                                       // otherwise defaults to 8080.

// Define the path to the directory containing static frontend assets (e.g., HTML, CSS, JS).
// `__dirname` is the directory of the current module (server.cjs).
// `path.join` creates a platform-independent path.
const staticFilesPath = path.join(__dirname, 'dist');
// Define the full path to the main HTML file of the SPA.
const indexPath = path.join(staticFilesPath, 'index.html');

console.log(`Serving static files from: ${staticFilesPath}`);

// This block checks for the existence of index.html at startup if the server is run directly.
// This is a diagnostic check to help ensure the 'dist' folder is correctly populated before starting.
// `require.main === module` is true when this file is run directly with `node server.cjs`.
if (require.main === module) {
    try {
        // `fs.statSync` checks if the file exists. Throws an error if not.
        fs.statSync(indexPath);
        console.log(`Confirmed index.html exists at: ${indexPath}`);
    } catch (error) {
        // Log a fatal error if index.html is not found, as the SPA cannot be served.
        console.error(`FATAL ERROR: index.html not found at ${indexPath}.`);
        console.error(`Ensure your 'dist' folder is correctly populated and included in your deployment.`);
        console.error(`This typically means running 'npm run build' before starting the server.`);
        console.error(`Error details: ${error.message}`);
        // Optionally, you might want to exit the process here if index.html is critical and not found:
        // process.exit(1);
    }
}

// Serve static files (HTML, CSS, JS) from the `staticFilesPath` directory (e.g., 'dist').
// `express.static` is middleware that serves static assets.
app.use(express.static(staticFilesPath));

// Middleware for Single Page Application (SPA) routing.
// This ensures that any GET request that is not for an API endpoint (not starting with '/api')
// and does not look like a request for a static file (does not contain a '.')
// will be served the `index.html` file. This allows client-side routing (e.g., React Router) to handle the path.
app.use((req, res, next) => {
  // Check if the request is a GET request, not an API call, and not for a specific file.
  if (req.method === 'GET' && !req.path.startsWith('/api') && !req.path.includes('.')) {
    console.log(`SPA fallback (middleware) for path: ${req.path}, sending: ${indexPath}`);
    // Send the main index.html file.
    res.sendFile(indexPath, (err) => {
      if (err) {
        // If there's an error sending the file, log it and send a 500 response.
        console.error(`Error sending index.html from ${indexPath} for ${req.path}:`, err);
        res.status(500).send(err.message || 'Error sending index.html');
      }
    });
  } else {
    // If the request doesn't meet the SPA fallback criteria, pass it to the next middleware.
    next();
  }
});

// Start the Express server and listen for incoming requests on the defined port.
app.listen(port, () => {
  console.log(`My Excel App Frontend server listening on port ${port}`);
});
