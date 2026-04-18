export default function TableResults({ data }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Año</th>
          <th>Tipo</th>
          <th>Entidad</th>
          <th>Importe</th>
          <th>Estado</th>
        </tr>
      </thead>

      <tbody>
        {data.map((item, i) => (
          <tr key={i}>
            <td>{item.anio}</td>
            <td>{item.tipo}</td>
            <td>{item.entidad}</td>
            <td>{item.importe}</td>
            <td>{item.estado}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
