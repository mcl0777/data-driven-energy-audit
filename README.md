# Data-Driven Energy Audit

This project is a prototype developed as part of a master's project to technically enhance the Data Energy Audit process. It aims to improve energy transparency in e.g. CNC machining by analyzing electrical consumption across distinct machine states – Standby, Ready, and Process and across the different components of the machinery. This project provides a reproducible toolchain for visualizing, analyzing, and reporting machine-level energy data. The focus is solely on electrical energy consumption.

## Features

- Upload and analyze CSV files containing energy consumption data
- Process data from different machine states (standby, ready, process)
- Calculate energy consumption for individual components
- Generate comprehensive PDF reports
- Interactive web interface for data visualization

## Project Structure

```
.
├── app.py                 # Main Flask application
├── create_energy_audit_pdf.py  # PDF generation module
├── data/
│   ├── example_data/     # Example CSV files
│   └── uploaded_data/    # Storage for uploaded files
├── static/               # Static files (CSS, JS)
├── templates/            # HTML templates
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
└── requirements.txt     # Python dependencies
```

## File Descriptions

- **app.py**: Main backend file implementing the Flask application. Defines routes and handles user requests.
  - `/`: Displays the dashboard
  - `/upload`: Receives and processes uploaded files
  - `/process_columns`: Processes column information
  - `/machine_info`: Receives machine information
  - `/generate_pdf`: Generates a PDF document based on provided data and machine information

- **create_energy_audit_pdf.py**: Contains the `create_energy_audit_pdf` function that creates a PDF document based on the provided data and machine information.

- **static/css/style.css**: Contains CSS styles for the dashboard.

- **static/js/scripts.js**: Contains JavaScript functions handling user interactions in the dashboard.

- **templates/dashboard.html**: HTML file for the dashboard containing forms and data display.

## Prerequisites

- Docker and Docker Compose
- Modern web browser

## Installation and Setup

1. Clone the repository:
```bash
git clone https://github.com/mcl0777/data-driven-energy-audit
cd data-driven-energy-audit
```

2. Start the application using Docker:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8080`

## Usage

1. Open your web browser and navigate to `http://localhost:8080`
2. Upload your  or Excel files for each machine state (standby, ready, process); You do not need to upload all of them.
3. The application will process the data and display the results
4. Generate a PDF report with the analyzed data

## Data Format

The application expects CSV and Excel (.csv, .xls, .xlsx) files with the following characteristics:
- Comma-separated values
- Headers for each column
- Numerical values for energy consumption
- Different files for different machine states (standby, ready, process)
- First column must contain time values
- Must include a total energy column for the machine (the column with the highest values will be handled as total energy)

Example data files are provided in the `data/example_data` directory.

## Known Issues

- **Component Name Editing**: Editing component names may cause issues in data processing
- **Required Column Structure**: Each uploaded file must have time values in the first column and a total energy column
- **Automatic "Other" Energy Calculation**: Energy that cannot be attributed to individual components is automatically calculated as "Sonstige [W]" (engl.:"Others [W]")

## Development

To modify the application:

1. Make your changes to the source code
2. Rebuild the Docker container:
```bash
docker-compose up --build
```

## License

This repository is intended for demonstration and educational use.
Contact the author for further details if reuse is intended.

## Author

**Author:** Moritz Lepper (github: mcl0777)
**Project:** Master's project in Industrial Data Science / Engineering
