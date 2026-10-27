import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/wind";

const formatNumber = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }

  return Number(value).toLocaleString("en-US", {
    maximumFractionDigits: 2,
  });
};

function App() {
  const [selectedDate, setSelectedDate] = useState("2026-01-15");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadWindData() {
      setLoading(true);
      setError("");

      try {
        const params = new URLSearchParams({
          start_date: selectedDate,
          end_date: selectedDate,
        });

        const response = await fetch(`${API_URL}?${params.toString()}`);
        const result = await response.json();

        if (!response.ok) {
          throw new Error(
            result.detail || "Unable to retrieve wind generation data."
          );
        }

        if (!cancelled) {
          setData(result);
        }
      } catch (err) {
        if (!cancelled) {
          setData(null);
          setError(
            err.message ||
              "Unable to connect to the backend. Check that the API is running."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadWindData();

    return () => {
      cancelled = true;
    };
  }, [selectedDate]);

  const records = data?.records ?? [];
  const metrics = data?.metrics;

  const averageForecast =
    records.length > 0
      ? records.reduce((sum, row) => sum + Number(row.forecast), 0) /
        records.length
      : null;

  const averageActual =
    records.length > 0
      ? records.reduce((sum, row) => sum + Number(row.actual), 0) /
        records.length
      : null;

  const chartData = records.map((row) => ({
    ...row,
    time: new Date(row.time).toISOString().slice(11, 16),
  }));

  const statusMessage = error
    ? error
    : loading
      ? "Fetching actual wind generation and historical forecasts from Elexon..."
      : `Elexon data for ${selectedDate}. Forecasts were selected from publications before the delivery day.`;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">W</div>
          <div>
            <h2>WindWise</h2>
            <span>Energy Intelligence</span>
          </div>
        </div>

        <p className="nav-heading">WORKSPACE</p>

        <div className="nav-item active">▦ &nbsp; Overview</div>
        <div className="nav-item">↗ &nbsp; Forecast Analysis</div>
        <div className="nav-item">▤ &nbsp; Generation Data</div>

        <div className="sidebar-bottom">
          <div className="status-dot" />
          <span>
            {loading
              ? "Loading data..."
              : error
                ? "API unavailable"
                : "Elexon data connected"}
          </span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">ENERGY PROCUREMENT / ANALYTICS</p>
            <h1>Wind Generation Dashboard</h1>
            <p className="subtitle">
              Understand forecasts. Evaluate uncertainty. Make informed
              decisions.
            </p>
          </div>

          <div className="date-control">
            <label htmlFor="forecast-date">Delivery date</label>
            <input
              id="forecast-date"
              type="date"
              min="2026-01-01"
              max="2026-01-31"
              value={selectedDate}
              onChange={(event) => setSelectedDate(event.target.value)}
            />
          </div>
        </header>

        <div className="demo-notice">
          <strong>
            {error ? "DATA ERROR" : loading ? "LOADING" : "LIVE API DATA"}
          </strong>
          <span>{statusMessage}</span>
        </div>

        <section className="metrics-grid">
          <article className="metric-card">
            <div className="metric-label">Average forecast</div>
            <div className="metric-value">
              {loading ? "…" : formatNumber(averageForecast)} <span>MW</span>
            </div>
            <p>Average across matched hourly intervals</p>
          </article>

          <article className="metric-card">
            <div className="metric-label">Average actual generation</div>
            <div className="metric-value">
              {loading ? "…" : formatNumber(averageActual)} <span>MW</span>
            </div>
            <p>Observed wind generation</p>
          </article>

          <article className="metric-card">
            <div className="metric-label">Mean absolute error</div>
            <div className="metric-value">
              {loading ? "…" : formatNumber(metrics?.maeMW)} <span>MW</span>
            </div>
            <p>MAE · Lower is better</p>
          </article>

          <article className="metric-card">
            <div className="metric-label">Root mean squared error</div>
            <div className="metric-value">
              {loading ? "…" : formatNumber(metrics?.rmseMW)} <span>MW</span>
            </div>
            <p>RMSE · Penalizes larger errors</p>
          </article>

          <article className="metric-card">
            <div className="metric-label">Mean absolute percentage error</div>
            <div className="metric-value">
              {loading
                ? "…"
                : metrics?.mapePercent == null
                  ? "—"
                  : `${formatNumber(metrics.mapePercent)}%`}
            </div>
            <p>MAPE · Average percentage error</p>
          </article>
        </section>

        <section className="panel chart-panel">
          <div className="panel-heading">
            <div>
              <h2>Forecast vs. Actual Generation</h2>
              <p>Hourly wind generation for {selectedDate} (UTC)</p>
            </div>
            <span className="unit-tag">Unit: MW</span>
          </div>

          <div className="chart-container">
            {loading ? (
              <p>Loading chart data...</p>
            ) : chartData.length === 0 ? (
              <p>
                {error ||
                  data?.message ||
                  "No matched forecast and actual records are available for this date."}
              </p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={chartData}
                  margin={{ top: 15, right: 20, left: 5, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8edf3" />

                  <XAxis
                    dataKey="time"
                    tick={{ fill: "#758196", fontSize: 12 }}
                  />

                  <YAxis
                    tick={{ fill: "#758196", fontSize: 12 }}
                    tickFormatter={(value) =>
                      `${Math.round(value / 1000)}k`
                    }
                  />

                  <Tooltip
                    formatter={(value) => [`${formatNumber(value)} MW`]}
                    labelFormatter={(label) => `${label} UTC`}
                  />

                  <Legend />

                  <Line
                    type="monotone"
                    dataKey="forecast"
                    name="Forecast"
                    stroke="#3278e8"
                    strokeWidth={3}
                    dot={false}
                  />

                  <Line
                    type="monotone"
                    dataKey="actual"
                    name="Actual"
                    stroke="#17a673"
                    strokeWidth={3}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </section>

        <section className="panel table-panel">
          <div className="panel-heading">
            <div>
              <h2>Generation Details</h2>
              <p>Matched forecast and actual observations in UTC</p>
            </div>
            <span className="unit-tag">
              {loading ? "Loading..." : `${records.length} hourly records`}
            </span>
          </div>

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Time (UTC)</th>
                  <th>Forecast (MW)</th>
                  <th>Actual (MW)</th>
                  <th>Error (MW)</th>
                  <th>Absolute error (MW)</th>
                </tr>
              </thead>

              <tbody>
                {records.map((item) => (
                  <tr key={item.time}>
                    <td>
                      {new Date(item.time).toISOString().slice(11, 16)}
                    </td>

                    <td>{formatNumber(item.forecast)}</td>
                    <td>{formatNumber(item.actual)}</td>

                    <td
                      className={
                        item.error > 0
                          ? "positive"
                          : item.error < 0
                            ? "negative"
                            : ""
                      }
                    >
                      {item.error > 0 ? "+" : ""}
                      {formatNumber(item.error)}
                    </td>

                    <td>{formatNumber(Math.abs(item.error))}</td>
                  </tr>
                ))}

                {!loading && records.length === 0 && (
                  <tr>
                    <td colSpan="5">
                      {error ||
                        data?.message ||
                        "No matching records available for this date."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <footer>
          WindWise · UK wind generation analysis · Elexon FUELHH and WINDFOR
        </footer>
      </main>
    </div>
  );
}

export default App;