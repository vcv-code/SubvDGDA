import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import "./Navbar.css";

export default function Navbar() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    navigate(query.trim() ? `/buscar?q=${encodeURIComponent(query.trim())}` : "/buscar");
  };

  return (
    <header className="navbar">

      {/* LOGO izquierda */}
      <Link to="/" className="navbar__logo">
        <img src="/logo.png" alt="Logo" className="navbar__logo-img"
          onError={(e) => { e.target.style.display = "none"; }} />
        <div className="navbar__logo-text">
          <span className="navbar__logo-title">Subvenciones</span>
          <span className="navbar__logo-subtitle">Animal y Colonias Felinas</span>
          <span className="navbar__logo-desc">PROTECCIÓN ANIMAL &amp; GESTIÓN DE COLONIAS FELINAS</span>
        </div>
      </Link>

      {/* BUSCADOR centrado */}
      <form className="navbar__search" onSubmit={handleSearch}>
        <svg className="navbar__search-icon" viewBox="0 0 20 20" fill="none">
          <circle cx="8.5" cy="8.5" r="5.5" stroke="#999" strokeWidth="1.8"/>
          <path d="M13 13l3.5 3.5" stroke="#999" strokeWidth="1.8" strokeLinecap="round"/>
        </svg>
        <input
          type="text"
          placeholder="Buscar por entidad, importe, año..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="navbar__search-input"
        />
        <button type="submit" className="navbar__search-btn">Buscar</button>
      </form>

      {/* ICONOS derecha */}
      <div className="navbar__actions">
        {/* Notificaciones */}
        <Link to="/" className="navbar__icon-btn" title="Notificaciones">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
        </Link>

        {/* Ajustes */}
        <Link to="/zona-privada" className="navbar__icon-btn" title="Ajustes">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </Link>

        {/* Avatar */}
        <Link to="/login" className="navbar__avatar" title="Acceder">
          <img
            src="https://api.dicebear.com/7.x/thumbs/svg?seed=bdns&backgroundColor=47C079"
            alt="Usuario"
          />
        </Link>
      </div>

    </header>
  );
}