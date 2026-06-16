def test_convocatorias_responde(client):
    response = client.get("/convocatorias/")
    assert response.status_code == 200


def test_convocatorias_devuelve_lista(client):
    response = client.get("/convocatorias/")
    assert isinstance(response.json(), list)


def test_convocatorias_lista_vacia_sin_datos(client):
    # La BD de test está vacía: tiene que devolver lista vacía, no error
    response = client.get("/convocatorias/")
    assert response.json() == []


def test_convocatorias_incluye_num_convoc(client, db):
    # num_convoc se expone para que la home pueda enlazar a la ficha BDNS
    from datetime import date
    from backend.app.models import Convocatoria
    db.add(Convocatoria(
        num_convoc="904714",
        titulo_convoc="Convocatoria de prueba",
        tipo_convoc="epa",
        anio_convocatoria=date.today().year,
        periodo_meses=12,
    ))
    db.commit()
    data = client.get("/convocatorias/").json()
    assert len(data) == 1
    assert data[0]["num_convoc"] == "904714"
