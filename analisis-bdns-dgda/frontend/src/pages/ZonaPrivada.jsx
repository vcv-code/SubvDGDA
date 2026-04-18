// ZonaPrivada.jsx
import { Link } from "react-router-dom";

function ZonaPrivada() {
  return (
    <main style={{ padding: "4rem", textAlign: "center" }}>
      <h1>🔒 Zona exclusiva</h1>
      <p style={{ color: "#888" }}>Contenido solo para usuarios registrados.</p>
      <Link to="/login" style={{
        display: "inline-block", marginTop: "1rem",
        background: "#2d5a27", color: "#fff",
        padding: "0.65rem 1.6rem", borderRadius: "8px",
        textDecoration: "none", fontWeight: 600
      }}>
        Iniciar sesión
      </Link>
    </main>
  );
}

export default ZonaPrivada;