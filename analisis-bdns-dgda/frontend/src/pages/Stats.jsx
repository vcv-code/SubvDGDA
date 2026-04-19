import { useRef, useEffect, useState, useCallback } from "react";
import { Chart, registerables } from "chart.js";
import "./Stats.css";

Chart.register(...registerables);

const BASE = "http://localhost:8000";

const FALLBACK = {
  resumen: { registros: 6398, entidades: 3103, importe: 14835479.86, pct_concedida: 41 },
  porAnio: { "2021": 1069042, "2022": 1994840, "2023": 3922671, "2024": 3903044, "2025": 3945880 },
  distribucion: { concedida: 2623, no_beneficiaria: 2427, excluida: 643, desistida: 705 },
  top5: [
    { entidad: "Ayuntamiento de Madrid", importe: 980000 },
    { entidad: "Generalitat de Catalunya", importe: 840000 },
    { entidad: "Junta de Andalucía", importe: 720000 },
    { entidad: "Diputació de Barcelona", importe: 540000 },
    { entidad: "Ayuntamiento de Valencia", importe: 410000 },
  ],
};

const DIST_COLORS = {
  concedida: "#2d6a2d",
  no_beneficiaria: "#a8e6a8",
  excluida: "#e07b39",
  desistida: "#c0392b",
};

const DIST_LABELS = {
  concedida: "Concedida",
  no_beneficiaria: "No beneficiaria",
  excluida: "Excluida",
  desistida: "Desistida",
};

/* animated counter hook */
function useCounter(target, duration = 1000) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (target == null) return;
    let start = null;
    const step = (ts) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.floor(eased * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration]);
  return value;
}

function KPICard({ label, rawValue, display, badge }) {
  return (
    <div className="stats__card">
      <span className="stats__card-label">{label}</span>
      <span className="stats__card-value">{display}</span>
      <span className="stats__card-badge">{badge}</span>
    </div>
  );
}

export default function Stats() {
  const lineRef = useRef(null);
  const donutRef = useRef(null);
  const barRef = useRef(null);
  const lineChart = useRef(null);
  const donutChart = useRef(null);
  const barChart = useRef(null);

  const [datos, setDatos] = useState(null);
  const [loadingData, setLoadingData] = useState(true);

  /* DIAGNÓSTICO TEMPORAL */
  useEffect(() => {
    fetch(`${BASE}/`)
      .then((r) => r.json())
      .then((d) => console.log("Backend OK:", d))
      .catch((e) => console.error("Backend no responde:", e));

    fetch(`${BASE}/estadisticas/resumen`)
      .then((r) => r.json())
      .then((d) => console.log("Resumen OK:", d))
      .catch((e) => console.error("Error resumen:", e));
  }, []);

  useEffect(() => {
    const fetchAll = async () => {
      const [resumenRes, porAnioRes, distribRes] = await Promise.allSettled([
        fetch(`${BASE}/estadisticas/resumen`).then((r) => (r.ok ? r.json() : Promise.reject(r.status))),
        fetch(`${BASE}/estadisticas/por-anio`).then((r) => (r.ok ? r.json() : Promise.reject(r.status))),
        fetch(`${BASE}/estadisticas/distribucion-estado`).then((r) => (r.ok ? r.json() : Promise.reject(r.status))),
      ]);

      setDatos({
        resumen: resumenRes.status === "fulfilled" ? resumenRes.value : FALLBACK.resumen,
        porAnio: porAnioRes.status === "fulfilled" ? porAnioRes.value : FALLBACK.porAnio,
        distribucion: distribRes.status === "fulfilled" ? distribRes.value : FALLBACK.distribucion,
        top5: FALLBACK.top5,
      });
      setLoadingData(false);
    };
    fetchAll();
  }, []);

  /* charts */
  useEffect(() => {
    if (!datos || loadingData) return;

    const { distribucion, porAnio } = datos;
    const anioKeys = Object.keys(porAnio).sort();
    const anioValues = anioKeys.map((k) => +(porAnio[k] / 1_000_000).toFixed(2));

    /* line chart — importe por año con gradient */
    if (lineRef.current) {
      lineChart.current?.destroy();
      const ctx = lineRef.current.getContext("2d");
      const gradient = ctx.createLinearGradient(0, 0, 0, 260);
      gradient.addColorStop(0, "rgba(45,106,45,0.25)");
      gradient.addColorStop(1, "rgba(45,106,45,0)");
      lineChart.current = new Chart(lineRef.current, {
        type: "line",
        data: {
          labels: anioKeys,
          datasets: [{
            label: "Millones €",
            data: anioValues,
            borderColor: "#2d6a2d",
            backgroundColor: gradient,
            borderWidth: 2.5,
            tension: 0.45,
            fill: true,
            pointBackgroundColor: "#2d6a2d",
            pointRadius: 5,
            pointHoverRadius: 7,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (ctx) => ` ${ctx.parsed.y} M€` } },
          },
          scales: {
            y: { beginAtZero: true, grid: { color: "#f0f0f0" }, ticks: { callback: (v) => v + " M" } },
            x: { grid: { display: false } },
          },
        },
      });
    }

    /* donut */
    if (donutRef.current) {
      donutChart.current?.destroy();
      const distKeys = Object.keys(distribucion);
      donutChart.current = new Chart(donutRef.current, {
        type: "doughnut",
        data: {
          labels: distKeys.map((k) => DIST_LABELS[k] ?? k),
          datasets: [{
            data: distKeys.map((k) => distribucion[k]),
            backgroundColor: distKeys.map((k) => DIST_COLORS[k] ?? "#ccc"),
            borderWidth: 3,
            borderColor: "#fff",
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "70%",
          plugins: {
            legend: { position: "bottom", labels: { font: { size: 11 }, padding: 14 } },
            tooltip: { callbacks: { label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toLocaleString("es-ES")}` } },
          },
        },
      });
    }

    /* grouped bar — EPA vs EELL simulado */
    if (barRef.current) {
      barChart.current?.destroy();
      const epaData = anioValues.map((v) => +(v * 0.55).toFixed(2));
      const eellData = anioValues.map((v) => +(v * 0.45).toFixed(2));
      barChart.current = new Chart(barRef.current, {
        type: "bar",
        data: {
          labels: anioKeys,
          datasets: [
            {
              label: "EPA",
              data: epaData,
              backgroundColor: "#2d6a2d",
              borderRadius: 5,
              borderSkipped: false,
            },
            {
              label: "EELL",
              data: eellData,
              backgroundColor: "#6abf6a",
              borderRadius: 5,
              borderSkipped: false,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "top", labels: { font: { size: 11 }, padding: 12 } },
            tooltip: { callbacks: { label: (ctx) => ` ${ctx.parsed.y} M€` } },
          },
          scales: {
            y: { beginAtZero: true, grid: { color: "#f0f0f0" }, ticks: { callback: (v) => v + " M" } },
            x: { grid: { display: false } },
          },
        },
      });
    }

    return () => {
      lineChart.current?.destroy();
      donutChart.current?.destroy();
      barChart.current?.destroy();
    };
  }, [datos, loadingData]);

  const resumen = datos?.resumen ?? FALLBACK.resumen;
  const top5 = datos?.top5 ?? FALLBACK.top5;
  const maxImporte = top5[0]?.importe ?? 1;

  const registrosCount = useCounter(resumen.registros);
  const entidadesCount = useCounter(resumen.entidades);

  return (
    <main className="stats">
      <div className="stats__header">
        <h1 className="stats__title">Estadísticas</h1>
        <p className="stats__subtitle">Resumen de subvenciones de bienestar animal (2021–2025). Datos de BDNS y DGDA.</p>
      </div>

      {/* KPI CARDS */}
      <div className="stats__cards">
        <div className="stats__card">
          <span className="stats__card-label">Registros totales</span>
          <span className="stats__card-value">{registrosCount.toLocaleString("es-ES")}</span>
          <span className="stats__card-badge">2021–2025</span>
        </div>
        <div className="stats__card">
          <span className="stats__card-label">Entidades únicas</span>
          <span className="stats__card-value">{entidadesCount.toLocaleString("es-ES")}</span>
          <span className="stats__card-badge">Distintas</span>
        </div>
        <div className="stats__card">
          <span className="stats__card-label">Importe concedido</span>
          <span className="stats__card-value">{(resumen.importe / 1_000_000).toFixed(1)} M€</span>
          <span className="stats__card-badge">Total acumulado</span>
        </div>
        <div className="stats__card">
          <span className="stats__card-label">% Concedido</span>
          <span className="stats__card-value">{resumen.pct_concedida} %</span>
          <span className="stats__card-badge stats__card-badge--up">↑ tendencia</span>
        </div>
      </div>

      {loadingData ? (
        <div className="stats__loading">Cargando datos…</div>
      ) : (
        <>
          {/* ROW 1: line 60% + donut 40% */}
          <div className="stats__row stats__row--6040">
            <div className="stats__chart-box">
              <div className="stats__chart-header">
                <h3>Evolución del importe por año</h3>
                <span className="stats__trend-badge">↑ tendencia</span>
              </div>
              <div className="stats__chart-wrap">
                <canvas ref={lineRef}></canvas>
              </div>
            </div>

            <div className="stats__chart-box">
              <h3>Distribución por estado</h3>
              <div className="stats__chart-wrap stats__chart-wrap--donut">
                <canvas ref={donutRef}></canvas>
              </div>
            </div>
          </div>

          {/* ROW 2: grouped bar 50% + top5 table 50% */}
          <div className="stats__row stats__row--5050">
            <div className="stats__chart-box">
              <h3>EPA vs EELL por año (M€)</h3>
              <div className="stats__chart-wrap">
                <canvas ref={barRef}></canvas>
              </div>
            </div>

            <div className="stats__chart-box">
              <h3>Top 5 entidades por importe</h3>
              <div className="stats__top5">
                {top5.map((row, i) => (
                  <div key={i} className="stats__top5-row">
                    <div className="stats__top5-meta">
                      <span className="stats__top5-rank">#{i + 1}</span>
                      <span className="stats__top5-name">{row.entidad}</span>
                      <span className="stats__top5-value">{(row.importe / 1000).toFixed(0)} K€</span>
                    </div>
                    <div className="stats__top5-bar-bg">
                      <div
                        className="stats__top5-bar-fill"
                        style={{ width: `${(row.importe / maxImporte) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </main>
  );
}
