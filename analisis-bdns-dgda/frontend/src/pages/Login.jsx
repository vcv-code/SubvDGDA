// Login.jsx
import { Link } from "react-router-dom";

function Login() {
  return (
    <main style={{ padding: "4rem", maxWidth: "400px", margin: "0 auto" }}>
      <h1>Iniciar sesión</h1>
      <p style={{ color: "#888" }}>— Próximamente: formulario de login con JWT —</p>
      <p>¿No tienes cuenta? <Link to="/registro">Regístrate</Link></p>
    </main>
  );
}

export default Login;