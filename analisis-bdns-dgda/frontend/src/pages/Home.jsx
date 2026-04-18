import { Link, useNavigate } from "react-router-dom";
import { useEffect, useRef } from "react";
import { Chart, registerables } from "chart.js";
import "./Home.css";

Chart.register(...registerables);

const STATS = [
  { label: "Registros totales", value: "6.398", icon: "📋" },
  { label: "Importe Concedido", value: "14,8 M€", icon: "💶" },
  { label: "Entidades únicas", value: "3.103", icon: "🏛️" },
];

const DISTRIBUCION = {
  labels: ["Concedida", "No beneficiaria", "Excluida", "Desistida"],
  data: [2623, 2330, 644, 801],
  colors: ["#2d5a27", "#a8d5a2", "#e07b1a", "#c0392b"],
};

const IMPORTE_POR_ANIO = {
  labels: ["2021", "2022", "2023", "2024", "2025"],
  data: [1.07, 1.99, 3.92, 3.90, 3.95],
};

export default function Home() {
  const pieRef = useRef(null);
  const barRef = useRef(null);
  const pieChart = useRef(null);
  const barChart = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (pieRef.current) {
      if (pieChart.current) pieChart.current.destroy();
      pieChart.current = new Chart(pieRef.current, {
        type: "pie",
        data: {
          labels: DISTRIBUCION.labels,
          datasets: [{
            data: DISTRIBUCION.data,
            backgroundColor: DISTRIBUCION.colors,
            borderWidth: 3,
            borderColor: "#fff",
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: { position: "bottom", labels: { font: { size: 11 }, padding: 12 } },
          },
        },
      });
    }

    if (barRef.current) {
      if (barChart.current) barChart.current.destroy();
      barChart.current = new Chart(barRef.current, {
        type: "bar",
        data: {
          labels: IMPORTE_POR_ANIO.labels,
          datasets: [{
            label: "Millones €",
            data: IMPORTE_POR_ANIO.data,
            backgroundColor: "#2d5a27",
            borderRadius: 6,
            borderSkipped: false,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: { legend: { display: false } },
          scales: {
            y: {
              beginAtZero: true,
              grid: { color: "#f0f0f0" },
              ticks: { callback: (v) => v + " M" },
            },
            x: { grid: { display: false } },
          },
        },
      });
    }

    return () => {
      pieChart.current?.destroy();
      barChart.current?.destroy();
    };
  }, []);

  return (
    <main className="home">

      {/* ── HERO ── */}
      <section className="home__hero">
        <div className="home__hero-content">
          <span className="home__hero-badge">📊 Datos oficiales 2021–2025</span>
          <h1>Sobre el proyecto</h1>
          <p>
            Este proyecto reúne y organiza información sobre subvenciones relacionadas con el bienestar animal
            procedentes de la Base de Datos Nacional de Subvenciones (BDNS) y de la Dirección General de Derechos
            de los Animales (DGDA). El objetivo principal es ofrecer una visión clara, estructurada y accesible de las
            ayudas concedidas, denegadas o en trámite, facilitando tanto la consulta pública como el análisis técnico.
          </p>
          <div className="home__hero-actions">
            <Link to="/buscar" className="home__btn home__btn--primary">🔍 Explorar buscador</Link>
            <Link to="/stats" className="home__btn home__btn--outline">Ver estadísticas</Link>
          </div>
        </div>
        <div className="home__hero-img">
          <img src="/hero.png" alt="Perro y gato"
            onError={(e) => e.target.style.display = "none"} />
        </div>
      </section>

      {/* ── DATA SECTION ── */}
      <section className="home__data">
        <div className="home__section-header">
          <h2>Subvenciones de Bienestar Animal (2021–2025)</h2>
          <p>Consulta, filtra y analiza más de 6.398 registros de entidades, importes y líneas de ayuda.<br />
            Datos procedentes de BDNS y DGDA.</p>
        </div>

        {/* STAT CARDS */}
        <div className="home__cards">
          {STATS.map((s) => (
            <div key={s.label} className="home__card">
              <span className="home__card-icon">{s.icon}</span>
              <span className="home__card-label">{s.label}</span>
              <span className="home__card-value">{s.value}</span>
            </div>
          ))}
        </div>

        {/* CHARTS */}
        <div className="home__charts">
          <div className="home__chart-box">
            <h3>Distribución por estado</h3>
            <div className="home__chart-wrap">
              <canvas ref={pieRef}></canvas>
            </div>
          </div>
          <div className="home__chart-box">
            <h3>Importe por año</h3>
            <div className="home__chart-wrap">
              <canvas ref={barRef}></canvas>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="home__cta">
          <button className="home__btn home__btn--primary home__btn--lg" onClick={() => navigate("/buscar")}>
            🔍 Explorar el buscador
          </button>
          <button className="home__btn home__btn--outline home__btn--lg" onClick={() => navigate("/stats")}>
            📈 Ver estadísticas completas
          </button>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="home__footer">
        <div className="home__footer-inner">
          <div className="home__footer-left">
            <img src="/logo.png" alt="Logo" className="home__footer-logo"
              onError={(e) => e.target.style.display = "none"} />
            <span>Proyecto BDNS/DGDA – FP DAW 2026</span>
          </div>
          <div className="home__footer-links">
            <a href="https://github.com/vcv-code/analisis-bdns-dgda" target="_blank" rel="noreferrer">GitHub</a>
            <span className="home__footer-sep">|</span>
            <Link to="/stats">Estadísticas</Link>
            <span className="home__footer-sep">|</span>
            <Link to="/buscar">Buscador</Link>
            <span className="home__footer-sep">|</span>
            <Link to="/login">Acceder</Link>
          </div>
        </div>
      </footer>

    </main>
  );
}