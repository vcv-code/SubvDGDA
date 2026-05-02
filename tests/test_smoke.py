def test_api_responde(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"mensaje": "API funcionando"}


def test_health_devuelve_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_estructura(client):
    data = client.get("/health").json()
    assert data == {"status": "ok"}
