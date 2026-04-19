import { Link, useNavigate } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import "./Navbar.css";

export default function Navbar() {
  const [query, setQuery] = useState("");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [userName, setUserName] = useState(null);
  const navigate = useNavigate();
  const dropdownRef = useRef(null);

  /* leer auth state */
  useEffect(() => {
    const token = localStorage.getItem("token");
    const name  = localStorage.getItem("user_name");
    setUserName(token ? (name || "U") : null);
  }, []);

  /* cerrar dropdown al hacer clic fuera */
  useEffect(() => {
    if (!dropdownOpen) return;
    const handleClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [dropdownOpen]);

  const handleSearch = (e) => {
    e.preventDefault();
    navigate(query.trim() ? `/buscar?q=${encodeURIComponent(query.trim())}` : "/buscar");
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_name");
    setUserName(null);
    setDropdownOpen(false);
    navigate("/");
  };

  const initial = userName ? userName.charAt(0).toUpperCase() : "";

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

        {/* Avatar / Acceder */}
        {!userName ? (
          <Link to="/login" className="navbar__acceder" title="Iniciar sesión">
            Acceder
          </Link>
        ) : (
          <div className="navbar__user-wrap" ref={dropdownRef}>
            <button
              className="navbar__avatar-btn"
              onClick={() => setDropdownOpen((o) => !o)}
              title={userName}
              aria-expanded={dropdownOpen}
            >
              {initial}
            </button>

            {dropdownOpen && (
              <div className="navbar__dropdown">
                <div className="navbar__dropdown-user">
                  <span className="navbar__dropdown-initial">{initial}</span>
                  <span className="navbar__dropdown-name">{userName}</span>
                </div>
                <div className="navbar__dropdown-sep" />
                <button className="navbar__dropdown-item" onClick={() => setDropdownOpen(false)}>
                  Mi perfil
                </button>
                <Link to="/zona-privada" className="navbar__dropdown-item" onClick={() => setDropdownOpen(false)}>
                  Zona privada
                </Link>
                <div className="navbar__dropdown-sep" />
                <button className="navbar__dropdown-item navbar__dropdown-item--danger" onClick={handleLogout}>
                  Cerrar sesión
                </button>
              </div>
            )}
          </div>
        )}

      </div>
    </header>
  );
}
