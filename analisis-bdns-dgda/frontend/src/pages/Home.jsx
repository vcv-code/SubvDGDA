import { useDataset } from "../hooks/useDataset";
import Filters from "../components/Filters";
import TableResults from "../components/TableResults";
import { useState, useMemo } from "react";

export default function Home() {
  const { data, loading } = useDataset();

  const [filters, setFilters] = useState({
    anio: "",
    tipo: "",
    estado: "",
    search: "" // buscar
  });

  const handleFilterChange = (name, value) => {
    setFilters(prev => ({ ...prev, [name]: value }));
    setPage(1); // reset paginación al cambiar filtros
  };

  // 🔥 Generar opciones dinámicas
  const uniqueYears = [...new Set(data.map(item => item.anio))].sort();
  const uniqueTipos = [...new Set(data.map(item => item.tipo))].sort();
  const uniqueEstados = [...new Set(data.map(item => item.estado))].sort();

  // 🔥 Filtrado optimizado
  const filteredData = useMemo(() => {
    return data.filter(item => {
      return (
        (filters.anio === "" || item.anio == filters.anio) &&
        (filters.tipo === "" || item.tipo === filters.tipo) &&
        (filters.estado === "" || item.estado === filters.estado) &&
        (filters.search === "" || item.entidad.toLowerCase().includes(filters.search.toLowerCase()))
      );
    });
  }, [data, filters]);

  // 🔥 Paginación
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const totalPages = Math.ceil(filteredData.length / pageSize);

  const paginatedData = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredData.slice(start, start + pageSize);
  }, [filteredData, page]);

  if (loading) return <p>Cargando datos...</p>;

  return (
    <div>
      <h1>Subvenciones DGDA</h1>

      <Filters
        filters={filters}
        onFilterChange={handleFilterChange}
        years={uniqueYears}
        tipos={uniqueTipos}
        estados={uniqueEstados}
      />

      <TableResults data={paginatedData} />

      <div className="pagination">
        <button disabled={page === 1} onClick={() => setPage(page - 1)}>
          Anterior
        </button>

        <span>Página {page} de {totalPages}</span>

        <button disabled={page === totalPages} onClick={() => setPage(page + 1)}>
          Siguiente
        </button>
      </div>
    </div>
  );
}
