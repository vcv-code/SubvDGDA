import { Bar } from "react-chartjs-2";
import { useDataset } from "../hooks/useDataset";
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from "chart.js";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

export default function Stats() {
  const { data, loading } = useDataset();

  if (loading) return <p>Cargando...</p>;

  // 🔥 Importe total por año
  const totalsByYear = {};
  data.forEach(item => {
    totalsByYear[item.anio] = (totalsByYear[item.anio] || 0) + item.importe;
  });

  const chartDataYear = {
    labels: Object.keys(totalsByYear),
    datasets: [
      {
        label: "Importe total (€)",
        data: Object.values(totalsByYear),
        backgroundColor: "rgba(75, 192, 192, 0.6)"
      }
    ]
  };

  // 🔥 Número de entidades por tipo
  const countByType = {};
  data.forEach(item => {
    countByType[item.tipo] = (countByType[item.tipo] || 0) + 1;
  });

  const chartDataType = {
    labels: Object.keys(countByType),
    datasets: [
      {
        label: "Número de entidades",
        data: Object.values(countByType),
        backgroundColor: "rgba(153, 102, 255, 0.6)"
      }
    ]
  };

  return (
    <div>
      <h1>Estadísticas</h1>

      <h2>Importe total por año</h2>
      <Bar data={chartDataYear} />

      <h2>Entidades por tipo</h2>
      <Bar data={chartDataType} />
    </div>
  );
}
