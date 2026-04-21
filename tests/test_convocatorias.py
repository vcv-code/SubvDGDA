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
