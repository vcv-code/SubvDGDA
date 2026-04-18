export default function Filters({ filters, onFilterChange, years, tipos, estados }) {
  return (
    <div className="filters">
      <select
        value={filters.anio}
        onChange={(e) => onFilterChange("anio", e.target.value)}
      >
        <option value="">Año</option>
        {years.map((y) => (
          <option key={y} value={y}>{y}</option>
        ))}
      </select>

      <select
        value={filters.tipo}
        onChange={(e) => onFilterChange("tipo", e.target.value)}
      >
        <option value="">Tipo</option>
        {tipos.map((t) => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>

      <select
        value={filters.estado}
        onChange={(e) => onFilterChange("estado", e.target.value)}
      >
        <option value="">Estado</option>
        {estados.map((e2) => (
          <option key={e2} value={e2}>{e2}</option>
        ))}
      </select>
      <input
        type="text"
        placeholder="Buscar entidad..."
        value={filters.search}
        onChange={(e) => onFilterChange("search", e.target.value)}
      />

    </div>
  );
}
