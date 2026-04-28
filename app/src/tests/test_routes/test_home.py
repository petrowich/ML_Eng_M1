def test_root_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200

def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.text == '{"status":"healthy"}'
    assert resp.status_code == 200

