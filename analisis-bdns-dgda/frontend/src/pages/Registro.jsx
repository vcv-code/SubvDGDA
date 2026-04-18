// Registro.jsx
import { Link } from "react-router-dom";

function Registro() {
  return (
    <main style={{ padding: "4rem", maxWidth: "400px", margin: "0 auto" }}>
      <h1>Crear cuenta</h1>
      <p style={{ color: "#888" }}>— Próximamente: formulario de registro —</p>
      <p>¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link></p>
    </main>
  );
}

export default Registro;