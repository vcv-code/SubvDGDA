def test_convocatorias_cache_control_publico(client):
    response = client.get("/convocatorias/")
    assert "public" in response.headers.get("cache-control", "")


def test_convocatorias_cache_control_max_age(client):
    response = client.get("/convocatorias/")
    assert "max-age=86400" in response.headers.get("cache-control", "")


def test_estadisticas_cache_control_publico(client):
    response = client.get("/estadisticas/")
    assert "public" in response.headers.get("cache-control", "")


def test_estadisticas_cache_control_max_age(client):
    response = client.get("/estadisticas/")
    assert "max-age=3600" in response.headers.get("cache-control", "")
