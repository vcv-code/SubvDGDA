import { useEffect, useState } from "react";
import { getConcesiones } from "../api/mockApi";

export function useDataset() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getConcesiones().then(res => {
      setData(res);
      setLoading(false);
    });
  }, []);

  return { data, loading };
}
