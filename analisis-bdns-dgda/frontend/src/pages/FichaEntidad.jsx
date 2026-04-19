import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import "./FichaEntidad.css";

function estadoBadge(estado) {
  const map = {
    concedida: "badge--concedida",
    excluida: "badge--excluida",
    no_beneficiaria: "badge--no_beneficiaria",
    desistida: "badge--desistida",
  };
  const key = estado?.toLowerCase().replace(/ /g, "_") || "";
  return <span className={`badge ${map[key] || ""}`}>{estado}</span>;
}

export default function FichaEntidad() {
  const { cif } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    api.get(`/entidad/${cif}`)
      .then(setData)
      .catch((err) => setError(err.message || "Error al cargar la entidad"))
      .finally(() => setLoading(false));
  }, [cif]);

  if (loading) return <main className="ficha"><p className="ficha__loading">Cargando…</p></main>;
  if (error) return <main className="ficha"><p className="ficha__error">{error}</p></main>;
  if (!data) return null;

  const historial = data.historial ?? [];
  const municipios = data.municipios ?? [];

  const totalImporte = historial.reduce((sum, h) => sum + (h.importe ?? 0), 0);

  return (
    <main className="ficha">
      <Link to="/buscar" className="ficha__back">← Volver al buscador</Link>

      {/* ── HEADER ── */}
      <div className="ficha__header">
        <div className="ficha__header-left">
          <h1>{data.nombre ?? data.entidad ?? cif}</h1>
          <div className="ficha__meta">
            <div className="ficha__meta-item">
              <span className="ficha__meta-label">CIF</span>
              <span className="ficha__meta-value">{data.cif ?? cif}</span>
            </div>
            <div className="ficha__meta-item">
              <span className="ficha__meta-label">Importe total recibido</span>
              <span className="ficha__meta-value">{totalImporte.toLocaleString("es-ES")} €</span>
            </div>
            {data.ccaa && (
              <div className="ficha__meta-item">
                <span className="ficha__meta-label">CCAA</span>
                <span className="ficha__meta-value">{data.ccaa}</span>
              </div>
            )}
            {data.provincia && (
              <div className="ficha__meta-item">
                <span className="ficha__meta-label">Provincia</span>
                <span className="ficha__meta-value">{data.provincia}</span>
              </div>
            )}
          </div>
        </div>
        {data.tipo && <span className="ficha__tipo-badge">{data.tipo}</span>}
      </div>

      {/* ── HISTORIAL ── */}
      {historial.length > 0 && (
        <div className="ficha__section">
          <h2 className="ficha__section-title">Historial de solicitudes</h2>
          <table className="ficha__table">
            <thead>
              <tr>
                <th>Año</th>
                <th>Estado</th>
                <th>Importe €</th>
                <th>Puntuación</th>
                <th>Línea</th>
              </tr>
            </thead>
            <tbody>
              {historial.map((h, i) => (
                <tr key={i}>
                  <td>{h.anio ?? "—"}</td>
                  <td>{estadoBadge(h.estado)}</td>
                  <td>{h.importe != null ? Number(h.importe).toLocaleString("es-ES") : "—"}</td>
                  <td>{h.puntuacion ?? "—"}</td>
                  <td>{h.linea ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── MUNICIPIOS (agrupaciones EELL 2025) ── */}
      {municipios.length > 0 && (
        <div className="ficha__section">
          <h2 className="ficha__section-title">Municipios miembro (agrupación EELL 2025)</h2>
          <table className="ficha__table">
            <thead>
              <tr>
                <th>Municipio</th>
                <th>Importe asignado €</th>
              </tr>
            </thead>
            <tbody>
              {municipios.map((m, i) => (
                <tr key={i}>
                  <td>{m.municipio ?? m.nombre ?? "—"}</td>
                  <td>{m.importe != null ? Number(m.importe).toLocaleString("es-ES") : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
