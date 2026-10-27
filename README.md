# WindWise — Wind Generation Forecast Analysis

## Project Overview

WindWise is a web application designed to help energy purchasing teams understand national wind power generation forecasts and evaluate forecast accuracy. It compares forecast wind generation with actual generation for selected dates using data from the Elexon API.

## Features

- Select a date to analyze wind generation.
- Retrieve actual wind generation and forecast data from Elexon.
- Visualize forecast versus actual generation in an interactive chart.
- Display forecast accuracy metrics.
- View hourly forecast and actual generation values in a data table.
- Provide a REST API using FastAPI.
- Run the frontend and backend using Docker Compose.

## Technology Stack

**Frontend**
- React
- JavaScript
- Vite
- Recharts
- CSS

**Backend**
- Python
- FastAPI
- HTTPX

**Deployment and Infrastructure**
- Docker
- Docker Compose
- Nginx

## Data Source

WindWise uses the Elexon Insights API.

- **Actual generation:** `FUELHH` dataset, filtered to the `WIND` fuel type.
- **Forecast generation:** `WINDFOR` dataset.
- **Actual generation fields:** `startTime`, `generation`.
- **Forecast generation fields:** `startTime`, `publishTime`, `generation`.

The application processes half-hourly actual generation data into hourly values, selects the applicable forecast publication, and matches forecast and actual values by delivery time.

## Forecast Accuracy Metrics

The application calculates the following metrics from matched forecast and actual values:

- **MAE (Mean Absolute Error):** Average absolute difference between forecast and actual generation.
- **RMSE (Root Mean Squared Error):** Square root of the average squared forecast error.
- **MAPE (Mean Absolute Percentage Error):** Average absolute percentage error, where the actual generation values allow the percentage to be calculated.

Lower MAE and RMSE values generally indicate smaller forecast errors.

## Project Structure

```text
full_stack/
├── backend/
│   ├── main.py
│   ├── wind_service.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── package.json
│   ├── Dockerfile
│   ├── nginx.conf
│   └── README.md
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Prerequisites

To run the application locally, install:

- Python 3.12 or a compatible version.
- Node.js and npm.
- Docker Desktop, if using Docker Compose.
- Git.

## Run with Docker Compose

1. Clone the repository:

   ```bash
   git clone https://github.com/sampreetharamesh11-cloud/windwise.git
   ```

2. Open the project directory:

   ```bash
   cd windwise
   ```

3. Build and start the application:

   ```bash
   docker compose up --build
   ```

4. Open the dashboard:

   `http://localhost:5175`

5. Open the backend API documentation:

   `http://localhost:8000/docs`

To stop the containers, press `Ctrl+C` in the terminal running Docker Compose. If you started the containers in detached mode, use:

```bash
docker compose down
```

## Run Locally Without Docker

### Backend

Open a terminal in the project root and run:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
python -m uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite in the terminal. The backend must be running for data requests to work.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API information |
| GET | `/api/health` | Health check |
| GET | `/api/wind` | Wind generation analysis |

The wind analysis endpoint accepts optional `start_date` and `end_date` query parameters in `YYYY-MM-DD` format.

Example:

```text
http://localhost:8000/api/wind?start_date=2026-01-15&end_date=2026-01-15
```

## Limitations

- The analysis focuses on national-level wind generation data from Elexon.
- Results depend on the availability and completeness of the upstream API data.
- Forecast accuracy is calculated only for matched forecast and actual generation periods.
- This application is an analytical aid and does not make energy purchasing decisions automatically.

## Deployment

**Live application:** To be added after deployment.

**Backend API:** To be added after deployment, if deployed separately.

## AI Tools Acknowledgment

AI assistance was used during development for guidance, debugging, code explanation, and documentation preparation. The application integrates with the Elexon API for wind generation data and performs forecast accuracy calculations in the backend.

## License

This project was developed as part of a software engineering assessment.
