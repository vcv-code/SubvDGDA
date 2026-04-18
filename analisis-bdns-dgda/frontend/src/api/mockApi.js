export async function getConcesiones() {
  const res = await fetch("/dataset_unificado.json");
  return res.json();
}
