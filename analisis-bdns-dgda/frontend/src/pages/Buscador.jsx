import { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import "./Buscador.css";

const BASE = "http://localhost:8000";
const PAGE_SIZE = 20;

const CCAA = [
  "Andalucía", "Aragón", "Asturias", "Baleares", "Canarias", "Cantabria",
  "Castilla-La Mancha", "Castilla y León", "Cataluña", "Ceuta",
  "Comunidad Valenciana", "Extremadura", "Galicia", "La Rioja",
  "Madrid", "Melilla", "Murcia", "Navarra", "País Vasco",
];

const PROVINCIAS = [
  "Álava", "Albacete", "Alicante", "Almería", "Asturias", "Ávila", "Badajoz",
  "Barcelona", "Burgos", "Cáceres", "Cádiz", "Cantabria", "Castellón",
  "Ciudad Real", "Córdoba", "Cuenca", "Girona", "Granada", "Guadalajara",
  "Gipuzkoa", "Huelva", "Huesca", "Jaén", "La Rioja", "Las Palmas",
  "León", "Lleida", "Lugo", "Madrid", "Málaga", "Murcia", "Navarra",
  "Ourense", "Palencia", "Pontevedra", "Salamanca", "Santa Cruz de Tenerife",
  "Segovia", "Sevilla", "Soria", "Tarragona", "Teruel", "Toledo",
  "Valencia", "Valladolid", "Bizkaia", "Zamora", "Zaragoza",
];

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

const EMPTY_FILTERS = {
  anio: "", tipo: "", estado: "", ccaa: "", provincia: "", linea: "", entidad: "",
};

export default function Buscador() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  /* DIAGNÓSTICO TEMPORAL */
  useEffect(() => {
    fetch("http://localhost:8000/")
      .then((r) => r.json())
      .then((d) => console.log("Backend OK:", d))
      .catch((e) => console.error("Backend no responde:", e));

    fetch("http://localhost:8000/solicitudes")
      .then((r) => r.json())
      .then((d) => console.log("Solicitudes OK, total:", d.length || d.total || d))
      .catch((e) => console.error("Error solicitudes:", e));
  }, []);

  const [filters, setFilters] = useState({
    ...EMPTY_FILTERS,
    entidad: searchParams.get("q") || "",
  });
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [netError, setNetError] = useState(false);

  const buildQuery = useCallback((f, p) => {
    const params = new URLSearchParams();
    if (f.anio)     params.append("anio", f.anio);
    if (f.tipo)     params.append("tipo", f.tipo);
    if (f.estado)   params.append("estado", f.estado);
    if (f.ccaa)     params.append("ccaa", f.ccaa);
    if (f.provincia) params.append("provincia", f.provincia);
    if (f.linea)    params.append("linea", f.linea);
    if (f.entidad)  params.append("entidad", f.entidad);
    params.append("page", p);
    params.append("page_size", PAGE_SIZE);
    return params.toString();
  }, []);

  const doSearch = useCallback(async (f, p) => {
    setLoading(true);
    setNetError(false);
    try {
      const res = await fetch(`${BASE}/solicitudes?${buildQuery(f, p)}`, { mode: "cors" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResults(data.items ?? (Array.isArray(data) ? data : []));
      setTotal(data.total ?? null);
    } catch (err) {
      console.error("Error buscador:", err);
      setNetError(true);
      setResults([]);
      setTotal(null);
    } finally {
      setLoading(false);
    }
  }, [buildQuery]);

  /* carga inicial sin filtros */
  useEffect(() => {
    doSearch(EMPTY_FILTERS, 1);
  }, [doSearch]);

  const handleChange = (field, value) => {
    setFilters((prev) => {
      const next = { ...prev, [field]: value };
      if (field === "tipo" && value !== "EELL") { next.ccaa = ""; next.provincia = ""; }
      if (field === "tipo" && !(value === "EPA" && prev.anio === "2025")) next.linea = "";
      if (field === "anio" && !(prev.tipo === "EPA" && value === "2025")) next.linea = "";
      return next;
    });
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    doSearch(filters, 1);
  };

  const handleClear = () => {
    setFilters({ ...EMPTY_FILTERS });
    setPage(1);
    doSearch(EMPTY_FILTERS, 1);
  };

  const handlePage = (p) => {
    setPage(p);
    doSearch(filters, p);
  };

  const totalPages = total != null ? Math.ceil(total / PAGE_SIZE) : 0;
  const eellActive = filters.tipo === "EELL";
  const lineaActive = filters.tipo === "EPA" && filters.anio === "2025";

  return (
    <div className="buscador">
      {/* ── SIDEBAR ── */}
      <aside className="buscador__sidebar">
        <p className="buscador__sidebar-title">Filtros</p>

        <form onSubmit={handleSearch}>
          <div className="buscador__filter-group">
            <label className="buscador__filter-label">Año</label>
            <select className="buscador__select" value={filters.anio} onChange={(e) => handleChange("anio", e.target.value)}>
              <option value="">Todos</option>
              {["2021", "2022", "2023", "2024", "2025"].map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>

          <div className="buscador__filter-group">
            <label className="buscador__filter-label">Tipo</label>
            <select className="buscador__select" value={filters.tipo} onChange={(e) => handleChange("tipo", e.target.value)}>
              <option value="">Todos</option>
              <option value="EPA">EPA</option>
              <option value="EELL">EELL</option>
            </select>
          </div>

          <div className="buscador__filter-group">
            <label className="buscador__filter-label">Estado</label>
            <select className="buscador__select" value={filters.estado} onChange={(e) => handleChange("estado", e.target.value)}>
              <option value="">Todos</option>
              <option value="Concedida">Concedida</option>
              <option value="No beneficiaria">No beneficiaria</option>
              <option value="Excluida">Excluida</option>
              <option value="Desistida">Desistida</option>
            </select>
          </div>

          <div className="buscador__filter-group">
            <label className="buscador__filter-label">CCAA</label>
            <select className="buscador__select" value={filters.ccaa} onChange={(e) => handleChange("ccaa", e.target.value)} disabled={!eellActive}>
              <option value="">Todas</option>
              {CCAA.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div className="buscador__filter-group">
            <label className="buscador__filter-label">Provincia</label>
            <select className="buscador__select" value={filters.provincia} onChange={(e) => handleChange("provincia", e.target.value)} disabled={!eellActive}>
              <option value="">Todas</option>
              {PROVINCIAS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          <div className="buscador__filter-group">
            <label className="buscador__filter-label">Línea</label>
            <select className="buscador__select" value={filters.linea} onChange={(e) => handleChange("linea", e.target.value)} disabled={!lineaActive}>
              <option value="">Todas</option>
              <option value="animales_abandonados">Animales abandonados</option>
              <option value="colonias_felinas">Colonias felinas</option>
            </select>
          </div>

          <div className="buscador__filter-group">
            <label className="buscador__filter-label">Nombre entidad</label>
            <input type="text" className="buscador__input" placeholder="Buscar por nombre…"
              value={filters.entidad} onChange={(e) => handleChange("entidad", e.target.value)} />
          </div>

          <div className="buscador__filter-actions">
            <button type="submit" className="buscador__btn-search">Buscar</button>
            <button type="button" className="buscador__btn-clear" onClick={handleClear}>Limpiar</button>
          </div>
        </form>
      </aside>

      {/* ── MAIN ── */}
      <main className="buscador__main">

        {loading && (
          <div className="buscador__empty">
            <div className="buscador__spinner" />
            Cargando resultados...
          </div>
        )}

        {!loading && netError && (
          <div className="buscador__net-error">
            No se pudo conectar con el servidor. Comprueba que el backend está activo.
          </div>
        )}

        {!loading && !netError && (
          <>
            <div className="buscador__results-header">
              <span className="buscador__results-count">
                {total != null
                  ? <><strong>{total}</strong> resultados encontrados</>
                  : <><strong>{results.length}</strong> resultados</>}
              </span>
            </div>

            {results.length === 0 ? (
              <div className="buscador__empty">No se encontraron resultados para los filtros aplicados.</div>
            ) : (
              <div className="buscador__table-wrap">
                <table className="buscador__table">
                  <thead>
                    <tr>
                      <th>Entidad</th>
                      <th>CIF</th>
                      <th>Año</th>
                      <th>Tipo</th>
                      <th>Estado</th>
                      <th>Importe €</th>
                      <th>Puntuación</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((row, i) => (
                      <tr key={row.cif ?? i} onClick={() => row.cif && navigate(`/entidad/${row.cif}`)}>
                        <td>{row.entidad ?? row.nombre ?? "—"}</td>
                        <td>{row.cif ?? "—"}</td>
                        <td>{row.anio ?? "—"}</td>
                        <td>{row.tipo ?? "—"}</td>
                        <td>{estadoBadge(row.estado)}</td>
                        <td>{row.importe != null ? Number(row.importe).toLocaleString("es-ES") : "—"}</td>
                        <td>{row.puntuacion ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {totalPages > 1 && (
              <div className="buscador__pagination">
                <button className="buscador__page-btn" onClick={() => handlePage(page - 1)} disabled={page === 1}>
                  Anterior
                </button>
                <span style={{ fontSize: "0.88rem", color: "#5a8a6a", padding: "0 0.5rem" }}>
                  Página {page} de {totalPages}
                </span>
                <button className="buscador__page-btn" onClick={() => handlePage(page + 1)} disabled={page >= totalPages}>
                  Siguiente
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
