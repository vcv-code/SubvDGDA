import { Link, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { Chart, registerables } from "chart.js";
import "./Home.css";

Chart.register(...registerables);

const DISTRIBUCION = {
  labels: ["Concedida", "No beneficiaria", "Excluida", "Desistida"],
  data: [2623, 2427, 643, 705],
  colors: ["#2d6a2d", "#a8e6a8", "#e07b39", "#c0392b"],
};

const IMPORTE_POR_ANIO = {
  labels: ["2021", "2022", "2023", "2024", "2025"],
  data: [1.07, 1.99, 3.92, 3.90, 3.95],
};

const CONVOCATORIAS = [
  { anio: "2025", epa: 1995880, eell: 1950000 },
  { anio: "2024", epa: 1968611, eell: 1934433 },
  { anio: "2023", epa: 1990059, eell: 1932612 },
];

function useCounter(target, duration = 1200) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!target) return;
    let start = null;
    const num = parseFloat(target.toString().replace(/[^0-9.]/g, ""));
    const step = (ts) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.floor(eased * num));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration]);
  return value;
}

function StatCard({ icon, label, rawValue, suffix = "" }) {
  const count = useCounter(rawValue);
  return (
    <div className="home__card">
      <span className="home__card-icon">{icon}</span>
      <span className="home__card-label">{label}</span>
      <span className="home__card-value">
        {count.toLocaleString("es-ES")}{suffix}
      </span>
    </div>
  );
}

export default function Home() {
  const pieRef = useRef(null);
  const barRef = useRef(null);
  const pieChart = useRef(null);
  const barChart = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (pieRef.current) {
      pieChart.current?.destroy();
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
      barChart.current?.destroy();
      barChart.current = new Chart(barRef.current, {
        type: "bar",
        data: {
          labels: IMPORTE_POR_ANIO.labels,
          datasets: [{
            label: "Millones €",
            data: IMPORTE_POR_ANIO.data,
            backgroundColor: "#2d6a2d",
            borderRadius: 6,
            borderSkipped: false,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, grid: { color: "#f0f0f0" }, ticks: { callback: (v) => v + " M" } },
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
      <section className="hero">
        <div className="hero-image-side">
          <div className="hero-circle" />
          <img
            className="hero-animals"
            src="/hero.png"
            alt="Perro y gato"
            onError={(e) => (e.target.style.display = "none")}
          />
          <div className="hero-card hero-card-1">
            <span className="hero-card-icon">🐾</span>
            <div>
              <strong>EPA – Protectoras</strong>
              <span>446 entidades concedidas en 2025</span>
            </div>
          </div>
          <div className="hero-card hero-card-2">
            <span className="hero-card-icon">🏛️</span>
            <div>
              <strong>EELL – Ayuntamientos</strong>
              <span>40 municipios beneficiarios en 2025</span>
            </div>
          </div>
        </div>

        <div className="hero-text-side">
          <span className="hero-badge">📊 Datos oficiales 2021–2025</span>
          <h1>
            Subvenciones de<br />
            <span className="hero-highlight">Bienestar Animal</span>
          </h1>
          <p>
            Consulta, filtra y analiza más de 6.398 registros de subvenciones públicas
            procedentes del BOE, BDNS y DGDA.
          </p>
          <div className="hero-buttons">
            <Link to="/buscar" className="btn-primary">🔍 Explorar buscador</Link>
            <Link to="/stats" className="btn-outline">📈 Ver estadísticas</Link>
          </div>
        </div>
      </section>

      {/* ── CIFRAS CLAVE ── */}
      <section className="home__data">
        <div className="home__section-header">
          <h2>Cifras clave</h2>
          <p>Datos agregados de todas las convocatorias de bienestar animal (2021–2025)</p>
        </div>

        <div className="home__cards">
          <StatCard icon="📋" label="Registros totales" rawValue={6398} />
          <StatCard icon="💶" label="Importe concedido" rawValue={14} suffix=",8 M€" />
          <StatCard icon="🏛️" label="Entidades únicas" rawValue={3103} />
        </div>

        <div className="home__charts">
          <div className="home__chart-box">
            <h3>Distribución por estado</h3>
            <div className="home__chart-wrap">
              <canvas ref={pieRef}></canvas>
            </div>
          </div>
          <div className="home__chart-box">
            <h3>Importe por año (M€)</h3>
            <div className="home__chart-wrap">
              <canvas ref={barRef}></canvas>
            </div>
          </div>
        </div>
      </section>

      {/* ── CÓMO FUNCIONA ── */}
      <section className="home__how">
        <div className="home__section-header">
          <h2>¿Cómo funciona?</h2>
          <p>En tres pasos puedes acceder a toda la información</p>
        </div>
        <div className="home__steps">
          <div className="home__step">
            <div className="home__step-icon">🔍</div>
            <h3>Consulta</h3>
            <p>Accede al buscador con más de 6.398 registros de subvenciones públicas</p>
          </div>
          <div className="home__step-connector" />
          <div className="home__step">
            <div className="home__step-icon">⚙️</div>
            <h3>Filtra</h3>
            <p>Por año, tipo, estado, CCAA o nombre de entidad</p>
          </div>
          <div className="home__step-connector" />
          <div className="home__step">
            <div className="home__step-icon">📊</div>
            <h3>Analiza</h3>
            <p>Visualiza gráficos y estadísticas detalladas por año y convocatoria</p>
          </div>
        </div>
      </section>

      {/* ── ÚLTIMAS CONVOCATORIAS ── */}
      <section className="home__convocatorias">
        <div className="home__section-header">
          <h2>Convocatorias recientes</h2>
          <p>Importes concedidos por tipo en las últimas tres convocatorias</p>
        </div>
        <div className="home__conv-grid">
          {CONVOCATORIAS.map((c) => (
            <div
              key={c.anio}
              className="home__conv-card"
              onClick={() => navigate(`/buscar?anio=${c.anio}`)}
            >
              <div className="home__conv-anio">{c.anio}</div>
              <span className="home__conv-badge">Cerrada</span>
              <div className="home__conv-row">
                <span className="home__conv-tipo">🐾 EPA</span>
                <span className="home__conv-importe">{c.epa.toLocaleString("es-ES")} €</span>
              </div>
              <div className="home__conv-row">
                <span className="home__conv-tipo">🏛️ EELL</span>
                <span className="home__conv-importe">{c.eell.toLocaleString("es-ES")} €</span>
              </div>
              <span className="home__conv-link">Ver resultados →</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA FINAL ── */}
      <section className="cta-section">
        <div className="cta-inner">
          <div className="cta-left">
            <span className="cta-tag">🐾 Para entidades y ciudadanos</span>
            <h2>Transparencia en las<br />ayudas al bienestar animal</h2>
            <p>Todos los datos del BOE 2021–2025, organizados y accesibles sin necesidad de registro.</p>
            <div className="cta-buttons">
              <button className="cta-btn-white" onClick={() => navigate("/buscar")}>🔍 Buscar mi entidad</button>
              <button className="cta-btn-outline" onClick={() => navigate("/stats")}>📊 Ver estadísticas</button>
            </div>
          </div>
          <div className="cta-right">
            <div className="cta-stat">
              <span className="cta-stat-num">6.398</span>
              <span className="cta-stat-label">registros públicos</span>
            </div>
            <div className="cta-stat">
              <span className="cta-stat-num">14,8M€</span>
              <span className="cta-stat-label">concedidos en total</span>
            </div>
            <div className="cta-stat">
              <span className="cta-stat-num">5</span>
              <span className="cta-stat-label">años de datos</span>
            </div>
          </div>
        </div>
      </section>

    </main>
  );
}
