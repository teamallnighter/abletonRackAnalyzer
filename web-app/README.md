# Ableton Rack Analyzer Web App

A clean, vanilla web application for analyzing Ableton Live rack (.adg) files.

## Features

- Drag & drop .adg files for instant analysis
- Wide layout using 95% of screen width for better visibility
- Visualize rack structure with chains and devices
- View macro controls with current values
- See nested racks within the signal flow
- Export analysis results as JSON
- Shows correct device names (not preset names)

## Structure

```
web-app/
├── index.html          # Main HTML file
├── styles.css          # All styling
├── app.js             # Frontend JavaScript
├── backend/           # Flask backend server
│   ├── app.py        # Flask API
│   └── abletonRackAnalyzer.py  # Rack analysis engine
└── testracks/         # Sample rack files for testing
```

## Running the App

1. Start the backend server:
   ```bash
   ./start_backend.sh
   ```
   Or manually:
   ```bash
   cd backend
   python3 app.py
   ```

2. Open `index.html` in your web browser

The backend runs on http://localhost:5001

## Usage

1. Drop an .adg file onto the upload area or click to browse
2. View the analyzed rack structure
3. Export results as JSON if needed

## No Dependencies!

This is a vanilla HTML/CSS/JavaScript frontend - no React, no build process, no npm packages needed for the frontend. Just pure, simple web technologies.

The backend uses Flask with minimal dependencies.
