import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./ZonaPrivada.css";

const CARDS = [
  {
    icon: "📋",
    title: "Guía SIGES",
    text: "Aprende a usar la plataforma SIGES del Ministerio de Derechos Sociales para gestionar tu solicitud de subvención paso a paso.",
    href: "https://www.mdsocialesa2030.gob.es",
    linkText: "Ir a SIGES",
  },
  {
    icon: "💡",
    title: "Consejos para solicitar",
    text: "Recomendaciones clave para mejorar tu puntuación: documentación necesaria, plazos, errores frecuentes y cómo evitarlos.",
    href: "#",
    linkText: "Ver consejos",
  },
  {
    icon: "📄",
    title: "Normativa vigente",
    text: "Accede a la normativa reguladora de las subvenciones de bienestar animal: bases reguladoras, convocatorias y resoluciones.",
    href: "https://www.boe.es",
    linkText: "Ver normativa en BOE",
  },
];

const STEPS = [
  "Regístrate en SIGES con certificado digital o Cl@ve.",
  "Descarga las bases reguladoras de la convocatoria activa.",
  "Prepara la memoria técnica y el presupuesto detallado.",
  "Adjunta la documentación acreditativa de tu entidad.",
  "Envía la solicitud antes del plazo indicado en la convocatoria.",
  "Haz seguimiento del expediente desde tu área de SIGES.",
];

export default function ZonaPrivada() {
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) navigate("/login");
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  return (
    <main className="zona">
      <div className="zona__header">
        <span className="zona__user-badge">🔒 Área privada</span>
        <h1>Zona exclusiva</h1>
        <p>Recursos y guías para entidades que solicitan subvenciones de bienestar animal.</p>
      </div>

      {/* ── CARDS ── */}
      <div className="zona__cards">
        {CARDS.map((c) => (
          <div key={c.title} className="zona__card">
            <span className="zona__card-icon">{c.icon}</span>
            <h3 className="zona__card-title">{c.title}</h3>
            <p className="zona__card-text">{c.text}</p>
            <a href={c.href} className="zona__card-link" target="_blank" rel="noreferrer">
              {c.linkText} →
            </a>
          </div>
        ))}
      </div>

      {/* ── STEPS ── */}
      <div className="zona__info">
        <h3 className="zona__info-title">¿Cómo solicitar una subvención? — Pasos clave</h3>
        <div className="zona__steps">
          {STEPS.map((step, i) => (
            <div key={i} className="zona__step">
              <span className="zona__step-num">{i + 1}</span>
              <p className="zona__step-text">{step}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="zona__logout">
        <button className="zona__logout-btn" onClick={handleLogout}>Cerrar sesión</button>
      </div>
    </main>
  );
}
