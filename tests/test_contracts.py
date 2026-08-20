# tests/test_contracts.py
def test_contracts_requires_login(client):
    response = client.get("/contracts/")
    if response.status_code == 404:
        response = client.get("/contracts")
    assert response.status_code in (302, 401)