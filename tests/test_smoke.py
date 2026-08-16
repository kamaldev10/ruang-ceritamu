def test_app_boots(app):
    assert app.testing is True


def test_landing_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
