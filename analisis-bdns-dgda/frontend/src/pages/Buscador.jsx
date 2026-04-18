// Buscador.jsx
import { useSearchParams } from "react-router-dom";

function Buscador() {
  const [searchParams] = useSearchParams();
  const q = searchParams.get("q") || "";

  return (
    <main style={{ padding: "2rem 5rem" }}>
      <h1>Buscador</h1>
      {q && <p>Resultados para: <strong>{q}</strong></p>}
      <p style={{ color: "#888" }}>— Próximamente: filtros y tabla de resultados —</p>
    </main>
  );
}

export default Buscador;