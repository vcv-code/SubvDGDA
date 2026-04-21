def test_api_responde(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"mensaje": "API funcionando"}
