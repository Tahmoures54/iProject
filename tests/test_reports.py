# tests/test_reports.py
def test_reports_requires_login(client):
    response = client.get("/reports/")
    if response.status_code == 404:
        response = client.get("/reports")
    assert response.status_code in (302, 401)