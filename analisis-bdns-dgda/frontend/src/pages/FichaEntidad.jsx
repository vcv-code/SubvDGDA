// FichaEntidad.jsx
import { useParams } from "react-router-dom";

function FichaEntidad() {
  const { cif } = useParams();
  return (
    <main style={{ padding: "2rem 5rem" }}>
      <h1>Ficha de entidad</h1>
      <p>CIF: <strong>{cif}</strong></p>
      <p style={{ color: "#888" }}>— Próximamente: historial completo de la entidad —</p>
    </main>
  );
}

export default FichaEntidad;