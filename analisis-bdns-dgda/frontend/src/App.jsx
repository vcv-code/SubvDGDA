import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Buscador from "./pages/Buscador";
import Stats from "./pages/Stats";
import FichaEntidad from "./pages/FichaEntidad";
import Login from "./pages/Login";
import Registro from "./pages/Registro";
import ZonaPrivada from "./pages/ZonaPrivada";

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/buscar" element={<Buscador />} />
        <Route path="/stats" element={<Stats />} />
        <Route path="/entidad/:cif" element={<FichaEntidad />} />
        <Route path="/login" element={<Login />} />
        <Route path="/registro" element={<Registro />} />
        <Route path="/zona-privada" element={<ZonaPrivada />} />
      </Routes>
      <Footer />
    </BrowserRouter>
  );
}

export default App;