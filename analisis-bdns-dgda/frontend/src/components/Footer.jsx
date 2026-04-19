import "./Footer.css";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer__inner">
        <div className="footer__left">
          <img
            src="/logo.png"
            alt="Logo"
            className="footer__logo"
            onError={(e) => (e.target.style.display = "none")}
          />
          <span className="footer__text">Proyecto BDNS/DGDA – FP DAW 2026</span>
        </div>
        <div className="footer__links">
          <a href="https://github.com/vcv-code/analisis-bdns-dgda" target="_blank" rel="noreferrer">GitHub</a>
          <span className="footer__sep">|</span>
          <a href="/docs" target="_blank" rel="noreferrer">Documentación</a>
          <span className="footer__sep">|</span>
          <a href="mailto:contacto@bdns-dgda.es">Contacto</a>
        </div>
      </div>
    </footer>
  );
}
