// // my-excel-app-frontend/server.cjs
// const express = require("express");
// const path = require("path");

// const app = express();
// const port = process.env.PORT || 8080;

// const staticFilesPath = path.join(__dirname, "dist");
// console.log(`Serving static files from: ${staticFilesPath}`); // Log the path

// app.use(express.static(staticFilesPath));

// // app.get("/*", (req, res) => {
// //   console.log(`SPA fallback for path: ${req.path}`); // Log which paths hit this
// //   const indexPath = path.join(staticFilesPath, "index.html");
// //   res.sendFile(indexPath, (err) => {
// //     if (err) {
// //       console.error(`Error sending index.html from ${indexPath}:`, err);
// //       res.status(err.status || 500).end(); // Send error status
// //     }
// //   });
// // });

// app.listen(port, () => {
//   console.log(`My Excel App Frontend server listening on port ${port}`);
// });

/////////////////////

// my-excel-app-frontend/server.cjs
const express = require("express");
const path = require("path");
const fs = require("fs"); // Import fs to check if a static file exists

const app = express();
const port = process.env.PORT || 8080;

const staticFilesPath = path.join(__dirname, "dist");
const indexPath = path.join(staticFilesPath, "index.html");
console.log(`Serving static files from: ${staticFilesPath}`);
console.log(`Index path: ${indexPath}`);

// 1. Serve static files from the 'dist' directory
app.use(express.static(staticFilesPath));

// 2. SPA Fallback Middleware
app.use((req, res, next) => {
  // We only want to fallback for GET requests that haven't been handled yet
  // and aren't for API calls (if you had any defined before this middleware)
  if (req.method === "GET" && !req.path.startsWith("/api")) {
    // Check if a file exists for the request path in the static directory.
    // This is a more robust way to ensure we don't override actual static files
    // that express.static might have missed or if express.static is configured differently.
    // However, express.static should typically handle this.
    // This check is more for illustration if express.static alone isn't enough.

    // A simpler approach if express.static is trusted to handle all static files:
    // Just send index.html for any remaining GET requests.
    console.log(`SPA fallback (middleware) for path: ${req.path}`);
    res.sendFile(indexPath, (err) => {
      if (err) {
        console.error(
          `Error sending index.html from ${indexPath} for ${req.path}:`,
          err
        );
        // If index.html itself can't be sent, that's a server error.
        res.status(500).send(err.message || "Error sending index.html");
      }
    });
  } else {
    // For non-GET requests or if it's an API path, pass to next handler (which might be a 404)
    next();
  }
});

app.listen(port, () => {
  console.log(`My Excel App Frontend server listening on port ${port}`);
});
